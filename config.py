import os
import inspect
from pathlib import Path

from text_renderer.effect import *
from text_renderer.corpus import *
from text_renderer.config import (
    RenderCfg,
    NormPerspectiveTransformCfg,
    GeneratorCfg,
    SimpleTextColorCfg,
)
from text_renderer.layout.same_line import SameLineLayout
from text_renderer.layout.extra_text_line import ExtraTextLineLayout

CURRENT_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
OUT_DIR = CURRENT_DIR / "my_output"
FONT_DIR = CURRENT_DIR / "my_data" / "font"
FONT_LIST_DIR = CURRENT_DIR / "my_data" / "font_list"
TEXT_DIR = CURRENT_DIR / "my_data" / "text"
CHAR_DIR = CURRENT_DIR / "my_data" / "char"
from app.core.config_helpers import BlackTextColorCfg
# 自定义黑色文字配置

# 基础字体配置
font_cfg = dict(
    font_dir=FONT_DIR,
    font_list_file=FONT_LIST_DIR / "font_list.txt",
    font_size=(30, 31),
)


def base_cfg(
        name: str,
        corpus,
        corpus_effects=None,
        layout_effects=None,
        layout=None,
        gray=False,
        num_image=100,
        override_num_image=None,
        override_gray=None,
        bg_type="default"  # <--- 新增参数：用于切换背景
):
    """
    简化的基础配置函数（已修复运行时覆盖参数未生效的问题）

    Args:
        name: 配置名称
        corpus: 文本语料配置
        corpus_effects: 文本效果
        layout_effects: 布局效果
        layout: 布局类型
        gray: 是否灰度图（默认 False）
        num_image: 生成图像数量（默认 100）
        override_num_image: 运行时覆盖生成数量
        override_gray: 运行时覆盖灰度设置
    """

    # 1. 计算最终配置值 (已修正)
    final_num_image = override_num_image if override_num_image is not None else num_image
    final_gray = override_gray if override_gray is not None else gray

    # 背景逻辑切换
    if bg_type == "white":
        # 请确保该文件夹下有一张纯白图片
        bg_dir = CURRENT_DIR / "my_data" / "bg_white"
    else:
        bg_dir = CURRENT_DIR / "my_data" / "bg"

    text_color_cfg = BlackTextColorCfg()

    return GeneratorCfg(
        num_image=final_num_image,
        save_dir=OUT_DIR / name,
        render_cfg=RenderCfg(
            bg_dir=bg_dir,  # <--- 使用选定的背景目录
            perspective_transform=NormPerspectiveTransformCfg(20, 20, 1.5),
            gray=final_gray,
            text_color_cfg=text_color_cfg,
            layout_effects=layout_effects,
            layout=layout,
            corpus=corpus,
            corpus_effects=corpus_effects or NoEffects(),
        ),
    )


# 移除的参数说明：
# 1. font_size: 在辅助函数 create_*_corpus 中处理，base_cfg 不需要。
# 2. use_black_text: 因为 BlackTextColorCfg() 已经硬编码，该参数是冗余的。
# =============================================================================
# 新增方法：纯白色背景数据生成
# =============================================================================

# =============================================================================
# 新增方法：白色背景 + 随机字符
# =============================================================================

def white_bg_rand_char_data():
    """
    纯白色背景 + 随机中英文/工程字符
    最适合训练 0, 45, 90, 180, 270, 315 角度分类模型的基础数据
    """
    return base_cfg(
        name='bg_white_rand_char',
        # 使用随机语料助手
        corpus=create_rand_corpus(
            chars_file=CHAR_DIR / "eng.txt",  # 或者使用 engineering.txt 包含工程符号
            length=(2, 8),         # 字符长度随机 2 到 8 位
            font_size=(28, 35)     # 字体大小
        ),
        num_image=5000,            # 建议生成较多数量（如2000张以上）
        bg_type="white",           # 强制使用白色背景
        # 移除透视变换，保证初始状态是绝对水平的，方便后续精准旋转
        # 如果需要，可以在这里覆盖渲染配置
    )
def engineering_math_data():
    """生成工程数学表达式数据"""
    return base_cfg(
        inspect.currentframe().f_code.co_name,
        corpus=EnumCorpus(
            EnumCorpusCfg(
                # 使用刚才脚本生成的语料文件
                text_paths=[TEXT_DIR / "engineering_mix.txt"],
                filter_by_chars=True,
                chars_file=CHAR_DIR / "engineering.txt", # 必须包含 ± = X .
                **font_cfg
            ),
        ),
        corpus_effects=Effects(
            [
                # 1. 模拟轻微的模糊感
                GaussianBlur(p=0.5, blur_limit=(1, 3)),
                # 2. 模拟工程图扫描的噪点
                Noise(p=0.2),
                # 3. 模拟打印不清晰的缺失感
                DropoutRand(p=0.3, dropout_p=(0.01, 0.05)),
            ]
        ),
        num_image=5000,
        bg_type="white" # 建议用白底，方便后续旋转
    )


# =============================================================================
# 更新配置列表
# =============================================================================

def create_enum_corpus(text_file, font_size=None, filter_chars=False, chars_file=None):
    """创建枚举语料的辅助函数"""
    cfg = {
        "text_paths": [TEXT_DIR / text_file],
        "filter_by_chars": filter_chars,
        **font_cfg
    }
    
    if font_size:
        cfg["font_size"] = font_size
    if chars_file:
        cfg["chars_file"] = CHAR_DIR / chars_file
        
    return EnumCorpus(EnumCorpusCfg(**cfg))

def create_rand_corpus(chars_file, length=(3, 8), font_size=None):
    """创建随机语料的辅助函数"""
    cfg = {
        "chars_file": CHAR_DIR / chars_file,
        "length": length,
        **font_cfg
    }
    
    if font_size:
        cfg["font_size"] = font_size
        
    return RandCorpus(RandCorpusCfg(**cfg))

# =============================================================================
# 配置函数
# =============================================================================

def engineering_dimensions():
    """工程图基础尺寸配置"""
    return base_cfg(
        inspect.currentframe().f_code.co_name,
        corpus=create_enum_corpus("dimensions.txt", font_size=(24, 28)),
        num_image=500,
    )

def tolerance_dimensions():
    """公差尺寸配置 - 主尺寸+公差"""
    return base_cfg(
        inspect.currentframe().f_code.co_name,
        layout=SameLineLayout(),
        corpus=[
            create_enum_corpus("dimensions.txt", font_size=(28, 32)),
            create_enum_corpus("tolerances.txt", font_size=(18, 22)),
        ],
        corpus_effects=[NoEffects(), NoEffects()],
        num_image=500,
    )

def precision_dimensions():
    """精密尺寸配置 - 高精度数值"""
    return base_cfg(
        inspect.currentframe().f_code.co_name,
        corpus=create_enum_corpus("precision_values.txt", font_size=(26, 30)),
        num_image=500,
    )

def stacked_tolerance():
    """上下公差配置 - 主尺寸左边，公差右边垂直堆叠"""
    return base_cfg(
        inspect.currentframe().f_code.co_name,
        layout=SameLineLayout(),
        corpus=[
            create_enum_corpus("dimensions.txt", font_size=(32, 36)),
            create_enum_corpus("tolerances.txt", font_size=(18, 22)),
        ],
        corpus_effects=[NoEffects(), NoEffects()],
        num_image=500,
    )

def random_engineering_text():
    """随机工程字符组合"""
    return base_cfg(
        inspect.currentframe().f_code.co_name,
        corpus=create_rand_corpus("engineering.txt", length=(3, 8), font_size=(24, 28)),
        num_image=500,
    )

def vertical_tolerance():
    """垂直公差标注配置 - 上下公差"""
    return base_cfg(
        inspect.currentframe().f_code.co_name,
        layout=ExtraTextLineLayout(),
        corpus=[
            create_enum_corpus("dimensions.txt", font_size=(32, 36)),
            create_enum_corpus("tolerance_pairs.txt", font_size=(18, 22)),
            create_enum_corpus("tolerance_pairs.txt", font_size=(18, 22)),
        ],
        corpus_effects=[NoEffects(), NoEffects(), NoEffects()],
        num_image=500,
    )

def large_scale_engineering():
    """大批量工程尺寸配置"""
    return base_cfg(
        inspect.currentframe().f_code.co_name,
        corpus=EnumCorpus(
            EnumCorpusCfg(
                text_paths=[
                    TEXT_DIR / "dimensions.txt",
                    TEXT_DIR / "tolerances.txt"
                ],
                filter_by_chars=False,
                font_size=(20, 35),
                **{k: v for k, v in font_cfg.items() if k != 'font_size'}
            ),
        ),
        num_image=1000,
    )

def simple_dimensions():
    """简单尺寸配置 - 快速测试"""
    return base_cfg(
        inspect.currentframe().f_code.co_name,
        corpus=create_enum_corpus("dimensions.txt"),
        num_image=200,
    )
def alnum_rand_data():
    """使用随机字母数字字符语料，长度为 2"""
    return base_cfg(
        # 使用函数名作为输出目录名
        inspect.currentframe().f_code.co_name,

        # 使用 RandCorpus (随机语料)
        corpus=RandCorpus(
            RandCorpusCfg(
                chars_file=CHAR_DIR / "eng.txt", # 假设您创建了这个文件
                length=(1, 3),                     # 【关键】：固定长度为 2
                **font_cfg
            ),
        ),
        # 添加一些效果使其更真实
        corpus_effects=Effects(
            [
                # 随机增加一些模糊和噪点
                OneOf([GaussianBlur(p=0.5, blur_limit=(1, 2))]),
                DropoutRand(p=0.3),
            ]
        ),
    )
# =============================================================================
# 配置列表
# =============================================================================

configs = [
    engineering_math_data(),
    white_bg_rand_char_data(),      # 纯白背景随机字符
    simple_dimensions(),           # 简单测试
    engineering_dimensions(),      # 基础工程尺寸  
    tolerance_dimensions(),        # 水平公差布局
    stacked_tolerance(),          # 垂直公差布局
    random_engineering_text(),    # 随机工程字符
    # large_scale_engineering(),  # 大批量生成（可选）
    # vertical_tolerance()
    alnum_rand_data()
]