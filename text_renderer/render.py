from typing import List, Tuple

import cv2
import numpy as np
from loguru import logger
from PIL import Image
from PIL.Image import Image as PILImage
from PIL.ImageFont import FreeTypeFont
from tenacity import retry

from text_renderer.bg_manager import BgManager
from text_renderer.config import RenderCfg
from text_renderer.utils import utils
from text_renderer.utils.bbox import BBox
from text_renderer.utils.draw_utils import draw_text_on_bg, transparent_img
from text_renderer.utils.errors import PanicError
from text_renderer.utils.font_text import FontText
from text_renderer.utils.math_utils import PerspectiveTransform
from text_renderer.utils.types import FontColor, is_list


class Render:
    """
    用于生成合成文本图像的主文本渲染引擎。

    此类处理完整的文本渲染流水线，包括：
    - 从语料库生成文本
    - 字体选择和文本渲染
    - 背景图像管理
    - 在不同阶段应用效果
    - 透视变换
    - 多语料场景的布局管理

    参数:
        cfg (RenderCfg): 包含所有渲染参数的配置对象

    抛出:
        PanicError: 如果 corpus 和 corpus_effects 配置不一致
    """

    def __init__(self, cfg: RenderCfg):
        self.cfg = cfg
        self.layout = cfg.layout
        # 如果 corpus 是一个只包含一个元素的列表，将其解包
        if isinstance(cfg.corpus, list) and len(cfg.corpus) == 1:
            self.corpus = cfg.corpus[0]
        else:
            self.corpus = cfg.corpus

        # 检查多语料和效果列表长度是否一致
        if is_list(self.corpus) and is_list(self.cfg.corpus_effects):
            if len(self.corpus) != len(self.cfg.corpus_effects):
                raise PanicError(
                    f"corpus 长度({self.corpus}) 与 corpus_effects 长度({self.cfg.corpus_effects}) 不相等"
                )

        # 检查 corpus 是列表但 corpus_effects 不是列表的情况
        if is_list(self.corpus) and (
                self.cfg.corpus_effects and not is_list(self.cfg.corpus_effects)
        ):
            raise PanicError("corpus 是列表，但 corpus_effects 不是列表")

        # 检查 corpus_effects 是列表但 corpus 不是列表的情况
        if not is_list(self.corpus) and is_list(self.cfg.corpus_effects):
            raise PanicError("corpus_effects 是列表，但 corpus 不是列表")

        self.bg_manager = BgManager(cfg.bg_dir, cfg.pre_load_bg_img)

    @retry
    def __call__(self, *args, **kwargs) -> Tuple[np.ndarray, str]:
        """
        使用配置的设置生成一个合成文本图像。

        此方法是文本渲染的主入口点。它处理从文本生成到最终图像输出的完整流水线。

        返回:
            Tuple[np.ndarray, str]: 一个元组，包含：
                - np.ndarray: 生成的图像，以 numpy 数组形式（BGR 格式）
                - str: 渲染的文本内容

        抛出:
            Exception: 渲染过程中发生的任何异常
        """
        try:
            # 根据语料数量判断使用单语料还是多语料生成
            if self._should_apply_layout():
                img, text, cropped_bg, transformed_text_mask = self.gen_multi_corpus()
            else:
                img, text, cropped_bg, transformed_text_mask = self.gen_single_corpus()

            # 应用最终渲染效果
            if self.cfg.render_effects is not None:
                img, _ = self.cfg.render_effects.apply_effects(
                    img, BBox.from_size(img.size)
                )

            # 处理返回背景和掩码的特殊需求（用于训练语义分割等）
            if self.cfg.return_bg_and_mask:
                gray_text_mask = np.array(transformed_text_mask.convert("L"))
                _, gray_text_mask = cv2.threshold(
                    gray_text_mask, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
                )
                transformed_text_mask = Image.fromarray(255 - gray_text_mask)

                # 合并 图像、背景 和 掩码
                merge_target = Image.new("RGBA", (img.width * 3, img.height))
                merge_target.paste(img, (0, 0))
                merge_target.paste(cropped_bg, (img.width, 0))
                merge_target.paste(
                    transformed_text_mask,
                    (img.width * 2, 0),
                    mask=transformed_text_mask,
                )

                np_img = np.array(merge_target)
                np_img = cv2.cvtColor(np_img, cv2.COLOR_RGBA2BGR)
                np_img = self.norm(np_img)
            else:
                # 标准 RGB 输出
                img = img.convert("RGB")
                np_img = np.array(img)
                np_img = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)
                np_img = self.norm(np_img)
            return np_img, text
        except Exception as e:
            logger.exception(e)
            raise e

    def gen_single_corpus(self) -> Tuple[PILImage, str, PILImage, PILImage]:
        """
        从单个语料生成文本图像。

        此方法处理单个语料的渲染流水线：
        1. 从语料中采样文本
        2. 获取背景图像
        3. 确定文本颜色
        4. 渲染文本掩码
        5. 应用语料效果 (corpus effects)
        6. 应用透视变换
        7. 将文本粘贴到背景上

        返回:
            Tuple[PILImage, str, PILImage, PILImage]: 一个元组，包含：
                - PILImage: 最终渲染的图像
                - str: 渲染的文本
                - PILImage: 裁剪后的背景图像
                - PILImage: 经过变换的文本掩码
        """
        font_text = self.corpus.sample()

        bg = self.bg_manager.get_bg()
        text_color = None
        if self.cfg.text_color_cfg is not None:
            text_color = self.cfg.text_color_cfg.get_color(bg)

        # 语料库的 text_color 优先于 RenderCfg.text_color_cfg
        if self.corpus.cfg.text_color_cfg is not None:
            text_color = self.corpus.cfg.text_color_cfg.get_color(bg)

        text_mask = draw_text_on_bg(
            font_text, text_color, char_spacing=self.corpus.cfg.char_spacing
        )

        # 应用语料效果 (corpus_effects)
        if self.cfg.corpus_effects is not None:
            text_mask, _ = self.cfg.corpus_effects.apply_effects(
                text_mask, BBox.from_size(text_mask.size)
            )

        # 应用透视变换
        if self.cfg.perspective_transform is not None:
            transformer = PerspectiveTransform(self.cfg.perspective_transform)
            # TODO: 重构这里，现在必须调用 get_transformed_size 才能调用 gen_warp_matrix
            _ = transformer.get_transformed_size(text_mask.size)

            try:
                (
                    transformed_text_mask,
                    transformed_text_pnts,
                ) = transformer.do_warp_perspective(text_mask)
            except Exception as e:
                logger.exception(e)
                logger.error(font_text.font_path, "text", font_text.text)
                raise e
        else:
            transformed_text_mask = text_mask

        img, cropped_bg = self.paste_text_mask_on_bg(bg, transformed_text_mask)

        return img, font_text.text, cropped_bg, transformed_text_mask

    def gen_multi_corpus(self) -> Tuple[PILImage, str, PILImage, PILImage]:
        """
        使用布局管理从多个语料生成文本图像。

        此方法处理多个语料的渲染流水线：
        1. 从每个语料中采样文本
        2. 获取背景图像
        3. 确定文本颜色
        4. 为每个语料渲染文本掩码
        5. 对每个文本掩码应用语料效果
        6. 使用布局定位多个文本掩码
        7. 应用透视变换
        8. 应用布局效果 (layout effects)
        9. 将合并后的文本粘贴到背景上

        返回:
            Tuple[PILImage, str, PILImage, PILImage]: 一个元组，包含：
                - PILImage: 最终渲染的图像
                - str: 合并后的渲染文本
                - PILImage: 裁剪后的背景图像
                - PILImage: 经过变换的文本掩码
        """
        font_texts: List[FontText] = [it.sample() for it in self.corpus]

        bg = self.bg_manager.get_bg()

        text_color = None
        if self.cfg.text_color_cfg is not None:
            text_color = self.cfg.text_color_cfg.get_color(bg)

        text_masks, text_bboxes = [], []
        for i in range(len(font_texts)):
            font_text = font_texts[i]

            # 颜色优先级：RenderCfg 颜色 -> 语料配置颜色
            if text_color is None:
                _text_color = self.corpus[i].cfg.text_color_cfg.get_color(bg)
            else:
                _text_color = text_color
            text_mask = draw_text_on_bg(
                font_text, _text_color, char_spacing=self.corpus[i].cfg.char_spacing
            )

            text_bbox = BBox.from_size(text_mask.size)
            # 应用对应的 corpus_effects
            if self.cfg.corpus_effects is not None:
                effects = self.cfg.corpus_effects[i]
                if effects is not None:
                    text_mask, text_bbox = effects.apply_effects(text_mask, text_bbox)
            text_masks.append(text_mask)
            text_bboxes.append(text_bbox)

        # 使用布局管理器来计算多个文本的位置和最终的合并文本
        text_mask_bboxes, merged_text = self.layout(
            font_texts,
            [it.copy() for it in text_bboxes],
            [BBox.from_size(it.size) for it in text_masks],
        )
        if len(text_mask_bboxes) != len(text_bboxes):
            raise PanicError(
                "布局输出的点和 text_bboxes 应该有相同的长度"
            )

        # 将所有文本掩码合并到一个大掩码上
        merged_bbox = BBox.from_bboxes(text_mask_bboxes)
        merged_text_mask = transparent_img(merged_bbox.size)
        for text_mask, bbox in zip(text_masks, text_mask_bboxes):
            merged_text_mask.paste(text_mask, bbox.left_top)

        # 应用透视变换
        if self.cfg.perspective_transform is not None:
            transformer = PerspectiveTransform(self.cfg.perspective_transform)
            # TODO: 重构这里，现在必须调用 get_transformed_size 才能调用 gen_warp_matrix
            _ = transformer.get_transformed_size(merged_text_mask.size)

            (
                transformed_text_mask,
                transformed_text_pnts,
            ) = transformer.do_warp_perspective(merged_text_mask)
        else:
            transformed_text_mask = merged_text_mask

        # 应用布局效果 (layout_effects)
        if self.cfg.layout_effects is not None:
            transformed_text_mask, _ = self.cfg.layout_effects.apply_effects(
                transformed_text_mask, BBox.from_size(transformed_text_mask.size)
            )

        img, cropped_bg = self.paste_text_mask_on_bg(bg, transformed_text_mask)

        return img, merged_text, cropped_bg, transformed_text_mask

    def paste_text_mask_on_bg(
            self, bg: PILImage, transformed_text_mask: PILImage
    ) -> Tuple[PILImage, PILImage]:
        """
        将文本掩码随机粘贴到背景图像上。

        参数:
            bg (PILImage): 要粘贴文本的背景图像
            transformed_text_mask (PILImage): 要粘贴的文本掩码

        返回:
            Tuple[PILImage, PILImage]: 一个元组，包含：
                - PILImage: 最终图像（文本已粘贴到背景上）
                - PILImage: 裁剪后的背景图像（如果 return_bg_and_mask 为 True）
        """
        # 随机计算文本在背景上的偏移量
        x_offset, y_offset = utils.random_xy_offset(transformed_text_mask.size, bg.size)
        # 确保背景大小足够容纳文本
        bg = self.bg_manager.guard_bg_size(bg, transformed_text_mask.size)
        # 裁剪出用于粘贴文本的背景区域
        bg = bg.crop(
            (
                x_offset,
                y_offset,
                x_offset + transformed_text_mask.width,
                y_offset + transformed_text_mask.height,
            )
        )
        if self.cfg.return_bg_and_mask:
            _bg = bg.copy()
        else:
            _bg = bg
        # 将文本掩码粘贴到裁剪后的背景上
        bg.paste(transformed_text_mask, (0, 0), mask=transformed_text_mask)
        return bg, _bg

    def get_text_color(self, bg: PILImage, text: str, font: FreeTypeFont) -> FontColor:
        """
        根据背景图像特征生成文本颜色。

        此方法分析背景图像，并生成一个应能提供良好对比度的颜色。

        参数:
            bg (PILImage): 要分析的背景图像
            text (str): 要渲染的文本（当前实现中未使用）
            font (FreeTypeFont): 字体对象（当前实现中未使用）

        返回:
            FontColor: 用于文本渲染的 RGBA 颜色元组

        注意:
            这是一个 TODO 方法，需要改进以获得更好的颜色选择。
        """
        # TODO: 更好地获取文本颜色
        # text_mask = self.draw_text_on_transparent_bg(text, font)
        np_img = np.array(bg)
        # mean = np.mean(np_img, axis=2)
        mean = np.mean(np_img)

        alpha = np.random.randint(110, 255)
        r = np.random.randint(0, int(mean * 0.7))
        g = np.random.randint(0, int(mean * 0.7))
        b = np.random.randint(0, int(mean * 0.7))
        fg_text_color = (r, g, b, alpha)

        return fg_text_color

    def _should_apply_layout(self) -> bool:
        """
        判断是否应应用布局管理。

        当需要管理多个语料时，应用布局。

        返回:
            bool: 如果应应用布局则为 True，否则为 False
        """
        return isinstance(self.corpus, list) and len(self.corpus) > 1

    def norm(self, image: np.ndarray) -> np.ndarray:
        """
        根据配置设置对图像进行归一化。

        此方法应用最终的图像处理，包括：
        - 灰度转换（如果已配置）
        - 高度归一化（如果已配置）

        参数:
            image (np.ndarray): 输入图像的 numpy 数组形式

        返回:
            np.ndarray: 归一化后的图像
        """
        # 灰度转换
        if self.cfg.gray:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 高度归一化
        if self.cfg.height != -1 and self.cfg.height != image.shape[0]:
            height, width = image.shape[:2]
            width = int(width // (height / self.cfg.height))
            image = cv2.resize(
                image, (width, self.cfg.height), interpolation=cv2.INTER_CUBIC
            )

        return image