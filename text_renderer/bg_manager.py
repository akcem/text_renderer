from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

import numpy as np
from loguru import logger
from PIL import Image
from PIL.Image import Image as PILImage

from text_renderer.utils.utils import random_choice

# 允许的图像文件扩展名集合
IMAGE_EXTENSIONS = {".jpeg", ".jpg", ".JPG", ".JPEG", ".PNG", ".png", ".bmp", ".BMP"}


class BgManager:
    """
    背景图像管理器

    负责加载、管理和提供背景图像。
    """
    def __init__(self, bg_dir: Path = None, pre_load: bool = True):
        self.bg_paths: List[str] = []
        self.bg_imgs: List[PILImage] = []
        # 是否预先加载所有背景图像到内存
        self.pre_load = pre_load

        if bg_dir is not None:
            # 遍历背景目录及其所有子目录中的文件
            for p in bg_dir.glob("**/*"):
                if p.suffix in IMAGE_EXTENSIONS:
                    # 忽略透明背景图像
                    if self._is_transparent_image(p):
                        logger.warning(
                            f"忽略透明背景图像，请将其转换为 JPEG: {p}"
                        )
                        continue
                    self.bg_paths.append(str(p))
                    # 如果开启预加载，则将图像加载到内存列表
                    if pre_load:
                        self.bg_imgs.append(self._get_bg(str(p)))

        # 如果没有找到任何背景图
        if len(self.bg_imgs) == 0:
            logger.warning("未找到任何背景图像。创建一个默认的白色背景。")
            # 创建一个默认的白色背景
            default_bg = Image.new('RGB', (800, 600), (255, 255, 255))
            self.bg_imgs = [default_bg]
            self.bg_paths = ['default_white']

    def _is_transparent_image(self, p: Path):
        """
        检查图像是否包含透明度 (Alpha) 通道，且透明度不完全为 255（即包含部分透明区域）。
        """
        pil_img: PILImage = Image.open(p)
        pil_img = pil_img.convert("RGBA")
        np_img = np.array(pil_img)
        # 检查 alpha 通道是否所有像素都为 255
        return not np.all(np_img[:, :, 3] == 255)

    def get_bg(self) -> PILImage:
        """
        获取一个随机的背景图像。

        如果开启预加载，从内存中随机选择；否则，从磁盘随机读取。
        """
        # TODO: 添加高效的数据增强
        if self.pre_load:
            return random_choice(self.bg_imgs)

        bg_path = random_choice(self.bg_paths)
        pil_img = self._get_bg(bg_path)

        return pil_img

    def guard_bg_size(self, pil_img: PILImage, size: Tuple[int, int]) -> PILImage:
        """
        确保背景图像的大小大于输入尺寸 (size)。

        参数:
            pil_img (PILImage): 背景图像
            size (Tuple[int, int]): 文本图像的宽度和高度

        返回:
            PILImage: 调整大小后的背景图像
        """
        width, height = size
        # 计算缩放比例，防止背景图像小于文本尺寸
        scale = max(width / pil_img.size[0], height / pil_img.size[1])
        if scale > 1:
            img_width, img_height = pil_img.size
            scaled_width = int(img_width * scale)
            scaled_height = int(img_height * scale)
            # 使用 PIL.resize 进行放大
            pil_img = pil_img.resize((scaled_width, scaled_height))
        return pil_img

    @lru_cache(maxsize=32)
    def _get_bg(self, bg_path: str) -> PILImage:
        """
        返回 RGBA 格式的 Pillow 图像。

        此方法实现了缓存机制，可以在一定次数内重复使用相同的图片文件（即使没有开启预加载）。

        参数:
            bg_path (str): 背景图像的文件路径

        返回:
            PILImage: RGBA 格式的 Pillow 图像
        """
        # lru_cache 装饰器实现了缓存机制
        pil_img: PILImage = Image.open(bg_path)
        # 转换为 RGBA 格式，确保有 alpha 通道以便后续的文本粘贴
        pil_img = pil_img.convert("RGBA")
        return pil_img