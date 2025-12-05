import multiprocessing as mp
import os
import time
from multiprocessing.context import Process
from pathlib import Path
import numpy as np
import cv2
from loguru import logger
import importlib.util
import inspect
from text_renderer.config import GeneratorCfg, get_cfg
from text_renderer.dataset import ImgDataset, LmdbDataset
from text_renderer.render import Render

cv2.setNumThreads(1)
STOP_TOKEN = "kill"
render: 'Render'


# *******************************************************************
# 核心多进程逻辑 - 与 UI 无关
# *******************************************************************

class DBWriterProcess(Process):
    """
    数据库写入进程 (用于接收数据和日志)
    log_queue 必须是 multiprocessing.Queue，用于向主进程发送日志和状态
    """

    def __init__(
            self,
            dataset_cls,
            data_queue: mp.Queue,
            generator_cfg: GeneratorCfg,
            log_period: float,
            log_queue: mp.Queue,
    ):
        super().__init__()
        self.dataset_cls = dataset_cls
        self.data_queue = data_queue
        self.generator_cfg = generator_cfg
        self.log_period = log_period
        self.log_queue = log_queue  # 用于向主进程发送日志 (通过 Queue)

    def _log(self, message):
        """发送日志到主进程队列"""
        if self.log_queue:
            self.log_queue.put(message)
        else:
            logger.info(message)

    def run(self):
        """主进程循环，从数据队列读取并写入数据集"""
        num_image = self.generator_cfg.num_image
        save_dir = self.generator_cfg.save_dir
        # log_period: 原代码中是百分比，这里转换为绝对计数
        log_period_count = max(1, int(self.log_period / 100 * num_image))
        try:
            with self.dataset_cls(str(save_dir)) as db:
                exist_count = db.read_count()
                count = 0
                self._log(f"Exist image count in {save_dir}: {exist_count}")
                start = time.time()
                while True:
                    m = self.data_queue.get()
                    if m == STOP_TOKEN:
                        self._log("DBWriterProcess receive stop token")
                        break

                    name = "{:09d}".format(exist_count + count)
                    db.write(name, m["image"], m["label"])
                    count += 1

                    if count % log_period_count == 0:
                        self._log(
                            f"{(count / num_image) * 100:.2f}%({count}/{num_image}) {log_period_count / (time.time() - start + 1e-8):.1f} img/s"
                        )
                        start = time.time()

                db.write_count(count + exist_count)
                self._log(f"{(count / num_image) * 100:.2f}%({count}/{num_image})")
                self._log(f"Finish generate: {count}. Total: {exist_count + count}")
        except Exception as e:
            self._log(f"DBWriterProcess error: {e}")
            self.log_queue.put("STOP_GUI_UPDATE")
            raise e

        self.log_queue.put("STOP_GUI_UPDATE")


def generate_img(data_queue, render_cfg):
    """生成一个图像并放入数据队列。"""
    global render

    try:
        data = render()
        if data is not None:
            data_queue.put({"image": data[0], "label": data[1]})
    except Exception as e:
        # logger.error(f"Generate image error in process {os.getpid()}: {e}")
        pass


def process_setup(render_cfg):
    """为工作进程初始化全局 render 实例。"""
    global render
    np.random.seed()
    render = Render(render_cfg)
    # logger.info(f"Finish setup image generate process: {os.getpid()}")


# *******************************************************************
# 核心控制服务
# *******************************************************************

class TextRendererService:
    """
    负责启动和协调多进程生成任务的纯逻辑类。
    """

    def __init__(self):
        self.manager = None
        self.data_queue = None
        self.log_queue = None
        self.is_running = False

    def _load_config_module(self, config_file: str):
        """动态导入配置模块"""
        # 确保使用绝对路径，否则动态导入可能出错
        abs_config_file = Path(config_file).resolve()

        spec = importlib.util.spec_from_file_location("runtime_config_module", str(abs_config_file))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _get_selected_cfgs(self, module, func_names: list, log_callback: callable,override_params: dict):
        """
        根据选中的函数名，从模块中获取并调用它们，返回 GeneratorCfg 列表
         override_params: 用于覆盖配置函数中的默认参数
        """
        selected_cfgs = []
        for name in func_names:
            try:
                func = getattr(module, name)
                if inspect.isfunction(func):
                    log_callback(f"Loading config from function: {name}...")
                    cfg = func(
                        **{k: v for k, v in override_params.items() if k in inspect.signature(func).parameters}
                    )
                    if isinstance(cfg, GeneratorCfg):
                        selected_cfgs.append(cfg)
                    else:
                        log_callback(f"WARN: Function '{name}' did not return a GeneratorCfg.")
            except Exception as e:
                log_callback(f"ERROR: Failed to call config function '{name}'. Error: {e}")

        return selected_cfgs

    def start_generation(self, config_file: str, dataset_type: str, num_processes: int, log_period: float,
                         log_callback: callable, config_func_names: list, override_params: dict):
        """
        启动生成的主入口。
        log_callback: 用于接收日志信息的函数 (例如 PyQt5 的 Signal.emit)
        config_func_names: 选中的配置函数名称列表
        """
        if self.is_running:
            return

        self.is_running = True
        log_callback("--- 启动生成进程 ---")
        # 0. 获取选中的配置
        try:
            config_module = self._load_config_module(config_file)
            # 使用新的辅助方法加载用户选中的配置
            generator_cfgs = self._get_selected_cfgs(config_module, config_func_names, log_callback, override_params)
        except Exception as e:
            log_callback(f"CRITICAL ERROR: Failed to load config file: {e}")
            self.is_running = False
            raise e

        if not generator_cfgs:
            log_callback("CRITICAL ERROR: No valid configurations selected or loaded.")
            self.is_running = False
            return
        try:
            # 必须在启动任何进程之前设置 start method
            mp.set_start_method("spawn", force=True)
            self.manager = mp.Manager()
            self.data_queue = self.manager.Queue()
            self.log_queue = self.manager.Queue()

            dataset_cls = LmdbDataset if dataset_type == "lmdb" else ImgDataset

            # ！！！删除或注释掉这一行，因为配置已经在上面加载了！！！
            # generator_cfgs = get_cfg(config_file)
            # -------------------------------------------------------------

            # --- 1. 启动 DBWriter 进程 ---
            db_writers = []
            # 循环遍历用户选中的配置 (现在 generator_cfgs 列表只包含选中的配置)
            for generator_cfg in generator_cfgs:
                db_writer_process = DBWriterProcess(
                    dataset_cls,
                    self.data_queue,
                    generator_cfg,
                    log_period,
                    self.log_queue
                )
                db_writer_process.start()
                db_writers.append(db_writer_process)

                # 修改 log_callback 里的信息，显示当前正在处理哪个配置
                log_callback(
                    f"配置 '{generator_cfg.save_dir.name}' 加载完成。生成图片总数: {generator_cfg.num_image}，使用进程数: {num_processes}")

                num_image = generator_cfg.num_image
                # log_callback(f"配置加载完成。生成图片总数: {num_image}，使用进程数: {num_processes}") # 原始行

                # --- 2. 启动图像生成 worker ---
                if num_processes == 0:
                    # 单进程/单线程模式 (简化为在当前线程中运行 setup 并生成)
                    log_callback("WARN: num_processes=0. Running single-process generation.")
                    process_setup(generator_cfg.render_cfg)
                    for i in range(num_image):
                        generate_img(self.data_queue, generator_cfg.render_cfg)
                        if i % 100 == 0:
                            log_callback(f"Main thread: {i}/{num_image} images generated.")

                    self.data_queue.put(STOP_TOKEN)

                else:
                    # 多进程 Pool 运行
                    with mp.Pool(
                            processes=num_processes,
                            initializer=process_setup,
                            initargs=(generator_cfg.render_cfg,),
                    ) as pool:
                        log_callback(f"启动 {num_processes} 个 worker 进程...")

                        results = []
                        for _ in range(num_image):
                            results.append(
                                pool.apply_async(generate_img, args=(self.data_queue, generator_cfg.render_cfg,)))

                        pool.close()
                        # 等待所有任务完成 (res.get() 会阻塞，但在 QThread 中是安全的)
                        for res in results:
                            res.get()

                        pool.join()

                    self.data_queue.put(STOP_TOKEN)  # 停止 DBWriter

                # 等待 DBWriter 进程结束
                # 注意：这里需要确保只等待当前配置对应的 writer 进程。
                # 由于你的逻辑是一个配置运行完成后才开始下一个配置的进程，
                # 所以应该只等待**当前**的 writer 结束，但是你的 db_writers 列表一直在累加，
                # 并且在循环内部等待了 `db_writers` 中的所有进程。
                #
                # 对于你的原始逻辑，为了只等待当前配置的 writer：
                # current_writer = db_writers[-1]
                # current_writer.join()
                #
                # 但由于你的原始逻辑中 `db_writers` 一直在累加，如果你的原始逻辑设计就是一次性启动所有 writer，
                # 那么应该保留循环外的等待。如果是一个配置一个配置地跑，那么内层的等待逻辑需要修改。
                #
                # 假设你的原始设计是一个配置运行完毕，等待其 writer 结束后再开始下一个配置：
                # (修正后的代码，只等待当前配置的 writer)
                db_writers[-1].join()  # 仅等待最近添加的 writer 进程

            log_callback("所有配置的生成任务均已完成。")

        except Exception as e:
            log_callback(f"CRITICAL ERROR in generation: {e}")
            raise e
        finally:
            self.is_running = False
            self.shutdown_manager()
            return True  # 正常结束

    def shutdown_manager(self):
        """关闭 Manager"""
        if self.manager:
            try:
                self.manager.shutdown()
            except Exception:
                pass
        self.manager = None

    def get_log_queue(self) -> mp.Queue:
        """返回日志队列供 UI 线程读取"""
        return self.log_queue

    def stop_all(self):
        """尝试向队列发送 STOP_TOKEN 以停止所有进程"""
        if self.is_running and self.data_queue:
            self.data_queue.put(STOP_TOKEN)
            self.data_queue.put(STOP_TOKEN)  # 多放一个确保