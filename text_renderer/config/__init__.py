import importlib
import os
import typing
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Union

import numpy as np
from PIL.Image import Image as PILImage

from text_renderer.effect import Effects
from text_renderer.layout import Layout
from text_renderer.layout.same_line import SameLineLayout

if typing.TYPE_CHECKING:
    from text_renderer.corpus import Corpus


@dataclass
class PerspectiveTransformCfg:
    """
    透视变换基类
    """

    x: float = 10
    y: float = 5
    z: float = 1.5
    scale: int = 1
    fovy: int = 50

    @abstractmethod
    def get_xyz(self) -> Tuple[int, int, int]:
        pass


@dataclass
class FixedPerspectiveTransformCfg(PerspectiveTransformCfg):
    def get_xyz(self) -> Tuple[float, float, float]:
        return 15, 15, 1.2


@dataclass
class UniformPerspectiveTransformCfg(PerspectiveTransformCfg):
    """
    x、y、z 服从均匀分布
    """

    def get_xyz(self) -> Tuple[float, float, float]:
        x = np.random.uniform(-self.x, self.x)
        y = np.random.uniform(-self.y, self.y)
        z = np.random.uniform(-self.z, self.z)
        return x, y, z


@dataclass
class NormPerspectiveTransformCfg(PerspectiveTransformCfg):
    """
    x、y、z 服从正态分布
    """

    def cliped_rand_norm(self, mu=0, sigma3: float = 1):
        """
        :param mu: 均值
        :param sigma3: 99% 范围 (mu-3*sigma, mu+3*sigma)
        :return:
            float
        """
        # 标准差
        sigma = sigma3 / 3
        dst = sigma * np.random.randn() + mu
        dst = np.clip(dst, 0 - sigma3, sigma3)
        return dst

    def get_xyz(self) -> Tuple[float, float, float]:
        x = self.cliped_rand_norm(0, self.x)
        y = self.cliped_rand_norm(0, self.y)
        z = self.cliped_rand_norm(0, self.z)
        return x, y, z


class TextColorCfg:
    """
    文本颜色配置基类
    """

    @abstractmethod
    def get_color(self, bg_img: PILImage) -> Tuple[int, int, int, int]:
        pass


@dataclass
class FixedTextColorCfg(TextColorCfg):
    # 用于生成 effect/layout 示例
    def get_color(self, bg_img: PILImage) -> Tuple[int, int, int, int]:
        alpha = 255
        text_color = (255, 50, 0, alpha)

        return text_color


@dataclass
class SimpleTextColorCfg(TextColorCfg):
    """
    随机使用背景图像的均值作为颜色参考
    """

    alpha: Tuple[int, int] = (110, 255)

    def get_color(self, bg_img: PILImage) -> Tuple[int, int, int, int]:
        np_img = np.array(bg_img)
        mean = np.mean(np_img)

        alpha = np.random.randint(*self.alpha)
        r = np.random.randint(0, int(mean * 0.7))
        g = np.random.randint(0, int(mean * 0.7))
        b = np.random.randint(0, int(mean * 0.7))
        text_color = (r, g, b, alpha)

        # return text_color
        return (0, 0, 0, 255)


@dataclass
class BlackTextColorCfg:
    def get_color(self, bg_img):
        return (0, 0, 0, 255)


@dataclass
class RangeTextColorCfg(TextColorCfg):
    """
    根据指定颜色范围和概率生成文本颜色
    """

    color_ranges: dict  # 例如：{"blue": {"fraction": 0.5, "l_boundary": [0,0,150], "h_boundary": [60,60,253]}}
    alpha: Tuple[int, int] = (200, 255)

    def get_color(self, bg_img: PILImage) -> Tuple[int, int, int, int]:
        # 根据概率选择颜色范围
        colors = list(self.color_ranges.keys())
        fractions = [self.color_ranges[color]["fraction"] for color in colors]

        # 归一化使概率和为 1
        total_fraction = sum(fractions)
        normalized_fractions = [f / total_fraction for f in fractions]

        # 按概率选择颜色
        rand_val = np.random.random()
        cumulative_fraction = 0
        selected_color = colors[0]  # 默认

        for i, fraction in enumerate(normalized_fractions):
            cumulative_fraction += fraction
            if rand_val <= cumulative_fraction:
                selected_color = colors[i]
                break

        # 获取颜色边界
        color_config = self.color_ranges[selected_color]
        l_boundary = color_config["l_boundary"]
        h_boundary = color_config["h_boundary"]

        # 在边界范围生成随机颜色
        r = np.random.randint(l_boundary[0], h_boundary[0] + 1)
        g = np.random.randint(l_boundary[1], h_boundary[1] + 1)
        b = np.random.randint(l_boundary[2], h_boundary[2] + 1)
        alpha = np.random.randint(*self.alpha)

        return (r, g, b, alpha)


# noinspection PyUnresolvedReferences
@dataclass
class RenderCfg:
    """
    参数说明
    ----------
    corpus : Union[Corpus, List[Corpus]]
        文本语料配置

    corpus_effects : Union[Effects, List[Effects]]
        对每个 corpus 文本 mask 图像应用的特效。
        在此阶段使用的 Effects 必须返回修改后的 bbox（如果发生改变）。

    bg_dir : Path
        背景图像目录

    pre_load_bg_img : bool
        True: 将所有背景图加载到内存

    layout : Layout
        如果 corpus 为列表，将应用 layout 合并文本

    perspective_transform : PerspectiveTransformCfg
        透视变换配置

    layout_effects : Effects
        针对 Layout 合并后的文本 mask 应用的特效

    render_effects : Effects
        最终图像输出时应用的特效

    height : int
        生成图像按照高度等比例缩放；-1 表示不缩放

    gray : bool
        图像是否保存为灰度

    text_color_cfg : TextColorCfg
        如果不为 None，将覆盖 CorpusCfg 中的文本颜色设置
        适用于多语料设置相同文字颜色

    return_bg_and_mask: bool
        是否返回背景和 mask 信息;用于语义分割
    """

    corpus: Union["Corpus", List["Corpus"]]
    corpus_effects: Union[Effects, List[Effects]] = None
    bg_dir: Path = None
    pre_load_bg_img: bool = True
    layout: Layout = SameLineLayout()
    perspective_transform: PerspectiveTransformCfg = None
    layout_effects: Effects = None
    render_effects: Effects = None
    height: int = 32
    gray: bool = True
    text_color_cfg: TextColorCfg = None
    return_bg_and_mask: bool = False


# noinspection PyUnresolvedReferences
@dataclass
class GeneratorCfg:
    """
    参数说明
    ----------
    num_image : int
        生成图像数量

    save_dir : Path
        数据保存目录

    render_cfg : RenderCfg
        渲染配置
    """

    num_image: int
    save_dir: Path
    render_cfg: RenderCfg


def get_cfg(config_file: str) -> List[GeneratorCfg]:
    """
    从配置文件加载配置

    Args:
        config_file: 配置文件的完整路径

    Returns:
        配置列表
    """
    module = import_module_from_file(config_file)
    cfgs = getattr(module, "configs", None)
    if cfgs is None:
        raise RuntimeError(f"Load configs failed: {config_file}")

    assert all(
        [isinstance(cfg, GeneratorCfg) for cfg in cfgs]
    ), "请确保 configs 中所有元素均为 GeneratorCfg 类型"

    return cfgs


def import_module_from_file(full_path_to_module:str):
    """
    根据 .py 文件路径动态导入模块

    参考：
    https://stackoverflow.com/questions/28836713/from-folder-name-import-variable-python-3-4-2
    """
    module = None
    try:
        # 从完整路径拿到目录和文件名
        module_dir, module_file = os.path.split(full_path_to_module)
        module_name, module_ext = os.path.splitext(module_file)

        # 读取模块规格 spec
        spec = importlib.util.spec_from_file_location(module_name, full_path_to_module)

        module = spec.loader.load_module()

    except Exception as ec:
        # 简单错误输出
        print(ec)

    finally:
        return module
