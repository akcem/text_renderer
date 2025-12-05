"""
文本渲染器应用程序的主入口点。

本模块提供命令行接口和多进程基础设施，用于使用 text_renderer 库生成合成文本图像。
"""

import argparse
import multiprocessing as mp
import os
import time
from multiprocessing.context import Process

import cv2
from loguru import logger

from text_renderer.config import GeneratorCfg, get_cfg
from text_renderer.dataset import ImgDataset, LmdbDataset
from text_renderer.render import Render

cv2.setNumThreads(1)

STOP_TOKEN = "kill"

# 每个子进程将在 process_setup 中初始化 Render
render: Render


class DBWriterProcess(Process):
    """
    数据库写入进程，用于处理数据集存储操作。

    此进程在一个单独的进程中运行，负责将生成的图像和标签写入数据集存储
    （可以是 LMDB 或图像文件）。它提供存储操作的进度日志记录和错误处理。

    参数:
        dataset_cls: 用于存储的数据集类 (LmdbDataset 或 ImgDataset)
        data_queue: 用于接收图像数据的多进程队列
        generator_cfg (GeneratorCfg): 生成过程的配置
        log_period (float): 日志记录周期，占总图像数的百分比（默认值: 1）
    """

    def __init__(
        self,
        dataset_cls,
        data_queue,
        generator_cfg: GeneratorCfg,
        log_period: float = 1,
    ):
        super().__init__()
        self.dataset_cls = dataset_cls
        self.data_queue = data_queue
        self.generator_cfg = generator_cfg
        self.log_period = log_period

    def run(self):
        """
        处理数据集存储操作的主进程循环。

        此方法不断从数据队列中读取数据，并将图像写入数据集，直到收到停止令牌。
        它提供进度日志记录并处理完整的存储流水线。
        """
        num_image = self.generator_cfg.num_image
        save_dir = self.generator_cfg.save_dir
        # 将 log_period（百分比）转换为实际的图像数量，确保至少为 1
        log_period = max(1, int(self.log_period / 100 * num_image))
        try:
            with self.dataset_cls(str(save_dir)) as db:
                exist_count = db.read_count()
                count = 0
                logger.info(f"目录 {save_dir} 中已存在的图像数量: {exist_count}")
                start = time.time()
                while True:
                    m = self.data_queue.get()
                    if m == STOP_TOKEN:
                        logger.info("DBWriterProcess 接收到停止令牌")
                        break

                    name = "{:09d}".format(exist_count + count)
                    db.write(name, m["image"], m["label"])
                    count += 1
                    if count % log_period == 0:
                        logger.info(
                            f"{(count/num_image)*100:.2f}%({count}/{num_image}) {log_period/(time.time() - start + 1e-8):.1f} img/s"
                        )
                        start = time.time()
                db.write_count(count + exist_count)
                logger.info(f"{(count / num_image) * 100:.2f}%({count}/{num_image})")
                logger.info(f"完成生成: {count} 张。总计: {exist_count+count}")
        except Exception as e:
            logger.exception("DBWriterProcess 发生错误")
            raise e


def generate_img(data_queue):
    """
    生成单个图像并将其放入数据队列。

    此函数由工作进程调用，用于使用全局渲染器实例生成图像，并将结果放入队列。

    参数:
        data_queue: 用于发送图像数据的多进程队列
    """
    data = render()
    if data is not None:
        data_queue.put({"image": data[0], "label": data[1]})


def process_setup(*args):
    """
    为工作进程初始化渲染器实例。

    此函数由每个工作进程调用，用于使用唯一的随机种子设置其自身的渲染器实例。

    参数:
        *args: 传递给进程的参数，第一个参数应为 RenderCfg
    """
    global render
    import numpy as np

    # 确保不同进程具有不同的随机种子,改变 NumPy 全局随机数生成器的内部状态
    np.random.seed()

    render = Render(args[0])
    logger.info(f"完成设置图像生成进程: {os.getpid()}")


def parse_args():
    """
    解析文本渲染器应用程序的命令行参数。

    返回:
        argparse.Namespace: 解析后的命令行参数
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="python 文件路径")
    parser.add_argument("--dataset", default="img", choices=["lmdb", "img"])
    parser.add_argument("--num_processes", type=int, default=2)
    parser.add_argument("--log_period", type=float, default=10)
    return parser.parse_args()


if __name__ == "__main__":
    # 强制使用 'spawn' 启动方法，以确保在不同操作系统上的一致性和安全性
    mp.set_start_method("spawn", force=True)
    manager = mp.Manager()
    data_queue = manager.Queue()
    args = parse_args()

    # 根据命令行参数选择数据集类 (LmdbDataset 或 ImgDataset)
    dataset_cls = LmdbDataset if args.dataset == "lmdb" else ImgDataset

    # 从配置文件中加载所有 GeneratorCfg 对象
    generator_cfgs = get_cfg(args.config)

    # 遍历所有配置，依次生成数据集
    for generator_cfg in generator_cfgs:
        # 1. 启动数据库写入进程 (消费者)
        db_writer_process = DBWriterProcess(
            dataset_cls, data_queue, generator_cfg, args.log_period
        )
        db_writer_process.start()

        # 2. 图像生成逻辑 (生产者)
        if args.num_processes == 0:
            # 单进程模式 (用于调试或低核数机器)
            process_setup(generator_cfg.render_cfg)
            for _ in range(generator_cfg.num_image):
                generate_img(data_queue)
            data_queue.put(STOP_TOKEN)
            db_writer_process.join()
        else:
            # 多进程模式
            with mp.Pool(
                processes=args.num_processes,
                initializer=process_setup,
                initargs=(generator_cfg.render_cfg,), # 传递 RenderCfg 给初始化函数
            ) as pool:
                # 异步提交所有生成任务到进程池
                for _ in range(generator_cfg.num_image):
                    pool.apply_async(generate_img, args=(data_queue,))

                # 关闭进程池，不再接受新任务
                pool.close()
                # 等待所有提交的任务完成
                pool.join()

            # 发送停止信号给 DBWriterProcess
            data_queue.put(STOP_TOKEN)
            # 等待 DBWriterProcess 结束写入工作
            db_writer_process.join()