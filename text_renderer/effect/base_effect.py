"""
文本渲染增强的基础效果类。

本模块提供基础类和工具，用于在文本渲染操作中实现图像增强效果。
"""

import random
from abc import abstractmethod
from typing import List, Tuple, Union

from text_renderer.effect.selector import Selector
from text_renderer.utils.bbox import BBox
from text_renderer.utils.types import PILImage
from text_renderer.utils.utils import prob


class Effect:
    """
    应用于图像不同增强的基础类。

    这个抽象基类定义了文本渲染中使用的所有图像效果的接口。
    效果可以修改图像，并可能更新文本边界框坐标。

    效果的例子包括：添加噪声、文字缺失、填充等。

    参数:
        p (float): 应用此效果的概率（默认值: 0.5）
    """

    def __init__(self, p: float = 0.5):
        self.p = p

    def __call__(self, img: PILImage, text_bbox: BBox) -> Tuple[PILImage, BBox]:
        """
        以配置的概率应用效果。

        参数:
            img (PILImage): 要应用效果的输入图像
            text_bbox (BBox): 图像中文本的边界框

        返回:
            Tuple[PILImage, BBox]: 修改后的图像和更新后的边界框
        """
        if prob(self.p):
            # 创建一个副本以确保图像是可写的
            img = img.copy()
            return self.apply(img, text_bbox)
        return img, text_bbox

    @abstractmethod
    def apply(self, img: PILImage, text_bbox: BBox) -> Tuple[PILImage, BBox]:
        """
        将效果应用于图像。

        所有子类都必须实现此方法，以定义特定的增强行为。

        参数:
            img (PILImage): 要应用效果的图像
            text_bbox (BBox): 图像中文本的边界框

        返回:
            Tuple[PILImage, BBox]: 修改后的图像和更新后的边界框。
                某些效果（如填充）可能会修改文本在图像中的相对位置。
        """
        pass

    @staticmethod
    def rand_pick(pim, col: int, row: int):
        """
        随机重置 [col, row] 处的像素值。

        此实用方法随机减少指定位置的像素值。
        新的像素值是 0 和原始像素值之间的一个随机整数。

        参数:
            pim: 来自 pil_img.load() 的像素访问对象
            col (int): 列坐标
            row (int): 行坐标
        """
        pim[col, row] = (
            random.randint(0, pim[col, row][0]),
            random.randint(0, pim[col, row][1]),
            random.randint(0, pim[col, row][2]),
            random.randint(0, pim[col, row][3]),
        )

    @staticmethod
    def fix_pick(pim, col: int, row: int, value_range: Tuple[int, int]):
        """
        将像素值设置为指定范围内的随机值。

        参数:
            pim: 来自 pil_img.load() 的像素访问对象
            col (int): 列坐标
            row (int): 行坐标
            value_range (Tuple[int, int]): 随机值选择的范围
        """
        value = random.randint(*value_range)
        pim[col, row] = (value, value, value, value)


class NoEffects:
    """
    在多语料场景下不需要效果时的占位符类。

    此类提供一个无操作实现，简单地返回未更改的输入图像和边界框。
    """

    def apply_effects(self, img: PILImage, bbox: BBox) -> Tuple[PILImage, BBox]:
        """
        返回未更改的输入图像和边界框。

        参数:
            img (PILImage): 输入图像
            bbox (BBox): 输入边界框

        返回:
            Tuple[PILImage, BBox]: 未更改的图像和边界框
        """
        return img, bbox


class Effects:
    """
    按顺序应用多个效果。

    此类管理将多个效果应用于图像的操作。
    它可以处理单个效果、效果列表或效果选择器。

    参数:
        effects (Union[Effect, List[Effect], Selector, List[Selector]]):
            要应用的效果。可以是一个单一效果、效果列表、选择器或选择器列表。
    """

    def __init__(self, effects: Union[Effect, List[Effect], Selector, List[Selector]]):
        """
        初始化 Effects 容器。

        参数:
            effects (Union[Effect, List[Effect], Selector, List[Selector]]):
                要应用的效果。可以是一个单一效果、效果列表、选择器或选择器列表。
        """
        if not isinstance(effects, list):
            effects = [effects]
        self.effects = effects

    def apply_effects(self, img: PILImage, bbox: BBox) -> Tuple[PILImage, BBox]:
        """
        将所有配置的效果应用于图像。

        参数:
            img (PILImage): 要应用效果的输入图像
            bbox (BBox): 图像中文本的边界框

        返回:
            Tuple[PILImage, BBox]: 应用了所有效果的图像和更新后的边界框
        """
        # 创建一个副本以确保图像是可写的
        img = img.copy()
        for e in self.effects:
            img, bbox = e(img, bbox)
        return img, bbox