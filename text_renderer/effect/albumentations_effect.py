from typing import List, Tuple, Union

import albumentations as A
import numpy as np
from PIL import Image

from text_renderer.utils.bbox import BBox
from text_renderer.utils.types import PILImage

from .base_effect import Effect


class AlbumentationsEffect(Effect):
    """
    使用 Albumentations 对图像应用变换。
    """

    def __init__(self, p=1.0, transform: A.BasicTransform = None):
        super().__init__(p)
        self.transform = transform

    def apply(self, img: PILImage, text_bbox: BBox) -> Tuple[PILImage, BBox]:
        if self.transform is None:
            return img, text_bbox

        # 将 PIL 图像转换为 numpy 数组
        img_array = np.array(img)

        # 检查图像是否具有 alpha 通道 (RGBA)
        has_alpha = img_array.shape[-1] == 4

        if has_alpha:
            # Albumentations 不支持 RGBA，因此转换为 RGB
            # 创建白色背景，将 RGBA 图像叠加到其上
            rgb_array = np.zeros((img_array.shape[0], img_array.shape[1], 3), dtype=np.uint8)
            alpha = img_array[:, :, 3:4] / 255.0
            rgb_array = (img_array[:, :, :3] * alpha + (1 - alpha) * 255).astype(np.uint8)
        else:
            rgb_array = img_array

        # 应用 Albumentations 变换
        transformed = self.transform(image=rgb_array)
        transformed_img = transformed["image"]

        # 转回 PIL 图像
        if has_alpha:
            # 添加原始 alpha 通道，恢复为 RGBA
            rgba_array = np.zeros((transformed_img.shape[0], transformed_img.shape[1], 4), dtype=np.uint8)
            rgba_array[:, :, :3] = transformed_img
            rgba_array[:, :, 3] = img_array[:, :, 3]  # 保留原始 alpha
            return Image.fromarray(rgba_array, mode='RGBA'), text_bbox
        else:
            return Image.fromarray(transformed_img), text_bbox


class Emboss(AlbumentationsEffect):
    def __init__(self, p=1.0, alpha=(0.9, 1.0), strength=(1.5, 1.6)):
        """
        使用 Albumentations 实现浮雕效果（模拟实现）

        参数
        ----------
        p: float
            应用该效果的概率
        alpha: tuple
            混合系数范围
        strength: tuple
            浮雕效果强度范围
        """
        # 注意：Albumentations 没有直接的浮雕滤波器
        # 这里使用亮度对比调整 + 高斯噪声来模拟浮雕纹理
        transform = A.Compose(
            [
                A.RandomBrightnessContrast(
                    brightness_limit=0.1, contrast_limit=0.2, p=1.0
                ),
                A.GaussNoise(p=1.0),
            ]
        )
        super().__init__(p, transform)


class MotionBlur(AlbumentationsEffect):
    def __init__(self, p=1.0, blur_limit=(3, 7), angle=(0, 360), direction=(-1.0, 1.0)):
        """
        运动模糊效果

        参数
        ----------
        p: float
            应用概率
        blur_limit: tuple
            模糊卷积核大小范围
        angle: tuple
            模糊角度范围（Albumentations 中不直接使用）
        direction: tuple
            模糊方向（Albumentations 不支持）
        """
        transform = A.MotionBlur(blur_limit=blur_limit, p=1.0)
        super().__init__(p, transform)


class GaussianBlur(AlbumentationsEffect):
    def __init__(self, p=1.0, blur_limit=(3, 7)):
        """
        高斯模糊效果

        参数
        ----------
        p: float
            应用概率
        blur_limit: tuple
            模糊强度范围
        """
        transform = A.GaussianBlur(blur_limit=blur_limit, p=1.0)
        super().__init__(p, transform)


class Noise(AlbumentationsEffect):
    def __init__(self, p=1.0, var_limit=(10.0, 50.0)):
        """
        高斯噪声效果

        参数
        ----------
        p: float
            应用概率
        var_limit: tuple
            噪声方差范围
        """
        transform = A.GaussNoise(p=1.0)
        super().__init__(p, transform)


class UniformNoise(AlbumentationsEffect):
    def __init__(self, p=1.0, intensity_range=(0.1, 0.3)):
        """
        均匀噪声效果

        参数
        ----------
        p: float
            应用概率
        intensity_range: tuple
            噪声强度范围（0–1）
        """
        transform = A.MultiplicativeNoise(
            multiplier=(0.9, 1.1), per_channel=True, p=1.0
        )
        super().__init__(p, transform)


class SaltPepperNoise(AlbumentationsEffect):
    def __init__(self, p=1.0):
        """
        椒盐噪声效果

        参数
        ----------
        p: float
            应用概率
        """
        transform = A.SaltAndPepper(
            p=p, salt_vs_pepper=(0.4, 0.6), amount=(0.02, 0.06)
        )
        super().__init__(p, transform)


class PoissonNoise(AlbumentationsEffect):
    def __init__(self, p=1.0, intensity=(0.1, 0.5), color_shift=(0.01, 0.05)):
        """
        泊松噪声（通过 Albumentations ISONoise）

        注：ISONoise 模拟相机传感器噪声，符合光子统计特性（泊松分布）

        参数
        ----------
        p: float
            应用概率
        intensity: tuple
            噪声强度范围
        color_shift: tuple
            颜色偏移范围
        """
        transform = A.ISONoise(
            intensity=intensity,
            color_shift=color_shift,
            p=1.0
        )
        super().__init__(p, transform)


class BrightnessContrast(AlbumentationsEffect):
    def __init__(self, p=1.0, brightness_limit=0.2, contrast_limit=0.2):
        """
        亮度与对比度调整

        参数
        ----------
        p: float
            应用概率
        brightness_limit: float or tuple
            亮度调整范围
        contrast_limit: float or tuple
            对比度调整范围
        """
        transform = A.RandomBrightnessContrast(
            brightness_limit=brightness_limit, contrast_limit=contrast_limit, p=1.0
        )
        super().__init__(p, transform)


class Rotate(AlbumentationsEffect):
    def __init__(self, p=1.0, limit=10):
        """
        旋转效果

        参数
        ----------
        p: float
            应用概率
        limit: int
            最大旋转角度（度）
        """
        transform = A.Rotate(limit=limit, p=1.0)
        super().__init__(p, transform)


class ShiftScaleRotate(AlbumentationsEffect):
    def __init__(self, p=1.0, shift_limit=0.1, scale_limit=0.1, rotate_limit=10):
        """
        平移、缩放与旋转混合变换

        参数
        ----------
        p: float
            应用概率
        shift_limit: float
            最大平移比例
        scale_limit: float
            最大缩放变化
        rotate_limit: int
            最大旋转角度
        """
        transform = A.ShiftScaleRotate(
            shift_limit=shift_limit,
            scale_limit=scale_limit,
            rotate_limit=rotate_limit,
            p=1.0,
        )
        super().__init__(p, transform)


class ElasticTransform(AlbumentationsEffect):
    def __init__(self, p=1.0, alpha=1, sigma=50, alpha_affine=50):
        """
        弹性形变

        参数
        ----------
        p: float
            应用概率
        alpha: float
            弹性形变参数
        sigma: float
            高斯模糊参数
        alpha_affine: float
            仿射变换参数（未在此实现中使用）
        """
        transform = A.ElasticTransform(alpha=alpha, sigma=sigma, p=1.0)
        super().__init__(p, transform)


class GridDistortion(AlbumentationsEffect):
    def __init__(self, p=1.0, num_steps=5, distort_limit=0.3):
        """
        网格扭曲

        参数
        ----------
        p: float
            应用概率
        num_steps: int
            网格划分数量
        distort_limit: float
            最⼤扭曲强度
        """
        transform = A.GridDistortion(
            num_steps=num_steps, distort_limit=distort_limit, p=1.0
        )
        super().__init__(p, transform)


class OpticalDistortion(AlbumentationsEffect):
    def __init__(self, p=1.0, distort_limit=0.05, shift_limit=0.05):
        """
        光学畸变

        参数
        ----------
        p: float
            应用概率
        distort_limit: float
            最大畸变量
        shift_limit: float
            最大位移量
        """
        transform = A.OpticalDistortion(distort_limit=distort_limit, p=1.0)
        super().__init__(p, transform)
