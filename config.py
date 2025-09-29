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

# 自定义黑色文字配置
class BlackTextColorCfg:
    def get_color(self, bg_img):
        return (0, 0, 0, 255)  # 纯黑色，完全不透明

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
    font_size=None,
    
    use_black_text=True
):
    """
    优化的基础配置函数
    
    Args:
        name: 配置名称
        corpus: 文本语料配置
        corpus_effects: 文本效果
        layout_effects: 布局效果  
        layout: 布局类型
        gray: 是否灰度图
        num_image: 生成图像数量
        font_size: 字体大小覆盖
        use_black_text: 是否使用纯黑文字
    """
    text_color_cfg=BlackTextColorCfg()
    # print(text_color_cfg.get_color())
    return GeneratorCfg(
        num_image=num_image,
        save_dir=OUT_DIR / name,
        render_cfg=RenderCfg(
            bg_dir=CURRENT_DIR / "my_data" / "bg",
            perspective_transform=NormPerspectiveTransformCfg(20, 20, 1.5),
            gray=gray,
            text_color_cfg=text_color_cfg,
            layout_effects=layout_effects,
            layout=layout,
            corpus=corpus,
            corpus_effects=corpus_effects or NoEffects(),
        ),
    )

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

# =============================================================================
# 配置列表
# =============================================================================

configs = [
    simple_dimensions(),           # 简单测试
    engineering_dimensions(),      # 基础工程尺寸  
    tolerance_dimensions(),        # 水平公差布局
    stacked_tolerance(),          # 垂直公差布局
    random_engineering_text(),    # 随机工程字符
    # large_scale_engineering(),  # 大批量生成（可选）
]