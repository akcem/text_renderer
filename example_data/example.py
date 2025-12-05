import inspect
import os
from pathlib import Path

from text_renderer.config import (
    FixedTextColorCfg,
    GeneratorCfg,
    NormPerspectiveTransformCfg,
    RangeTextColorCfg,
    RenderCfg,
)
from text_renderer.corpus import *
from text_renderer.effect import *
from text_renderer.layout.extra_text_line import ExtraTextLineLayout
from text_renderer.layout.same_line import SameLineLayout

# 当前目录
CURRENT_DIR = Path(os.path.abspath(os.path.dirname(__file__)))

# 输出目录
OUT_DIR = CURRENT_DIR / "output"

# 数据目录：背景、字符、字体、文本文件
DATA_DIR = CURRENT_DIR
BG_DIR = DATA_DIR / "bg"
CHAR_DIR = DATA_DIR / "char"
FONT_DIR = DATA_DIR / "font"
FONT_LIST_DIR = DATA_DIR / "font_list"
TEXT_DIR = DATA_DIR / "text"

# 基础字体配置
font_cfg = dict(
    font_dir=FONT_DIR,                          # 字体文件夹
    font_list_file=FONT_LIST_DIR / "font_list.txt",  # 字体列表文件
    font_size=(30, 31),                         # 字体大小范围
)

# 透视变换配置：最大偏移 20、20，倍率 1.5
perspective_transform = NormPerspectiveTransformCfg(20, 20, 1.5)


# --------------------------
# 文本语料规则
# --------------------------
def get_char_corpus():
    """中英文字符语料"""
    return CharCorpus(
        CharCorpusCfg(
            text_paths=[TEXT_DIR / "chn_text.txt", TEXT_DIR / "eng_text.txt"],
            filter_by_chars=True,
            chars_file=CHAR_DIR / "chn.txt",
            length=(5, 10),             # 文本长度范围
            char_spacing=(-0.3, 1.3),   # 字间距随机范围
            **font_cfg
        ),
    )


# --------------------------
# 基础生成器模板
# --------------------------
def base_cfg(
    name: str, corpus, corpus_effects=None, layout=None,layout_effects=None,  gray=True
):
    """
    通用生成器配置模板
    """
    return GeneratorCfg(
        num_image=50,                     # 生成 50 张
        save_dir=OUT_DIR / name,          # 保存路径
        render_cfg=RenderCfg(
        bg_dir=BG_DIR,                # 背景图目录
        perspective_transform=perspective_transform,
        gray=gray,                    # 是否灰度
        layout_effects=layout_effects,
        layout=layout,
        corpus=corpus,
        corpus_effects=corpus_effects,
        ),
    )


# --------------------------
# 1) 基础字符数据
# --------------------------
def chn_data():
    """中文字符数据生成"""
    return base_cfg(
        inspect.currentframe().f_code.co_name,
        corpus=get_char_corpus(),
        corpus_effects=Effects(
            [
                Line(0.5, color_cfg=FixedTextColorCfg()),        # 加虚线
                OneOf([DropoutRand(), DropoutVertical()]),       # 文字缺失效果
            ]
        ),
    )


# --------------------------
# 2) 枚举语料数据
# --------------------------
def enum_data():
    """枚举语料（从 enum_text.txt 读取）"""
    return base_cfg(
        inspect.currentframe().f_code.co_name,
        corpus=EnumCorpus(
            EnumCorpusCfg(
                text_paths=[TEXT_DIR / "enum_text.txt"],
                filter_by_chars=True,
                chars_file=CHAR_DIR / "chn.txt",
                **font_cfg
            ),
        ),
    )


# --------------------------
# 3) 随机字符数据
# --------------------------
def rand_data():
    """使用随机字符语料"""
    return base_cfg(
        inspect.currentframe().f_code.co_name,
        corpus=RandCorpus(
            RandCorpusCfg(chars_file=CHAR_DIR / "chn.txt", **font_cfg),
        ),
    )


# --------------------------
# 4) 英文单词数据
# --------------------------
def eng_word_data():
    """英文单词语料"""
    return base_cfg(
        inspect.currentframe().f_code.co_name,
        corpus=WordCorpus(
            WordCorpusCfg(
                text_paths=[TEXT_DIR / "eng_text.txt"],
                filter_by_chars=True,
                chars_file=CHAR_DIR / "eng.txt",
                **font_cfg
            ),
        ),
    )


# --------------------------
# 5) 多语料同行布局
# --------------------------
def same_line_data():
    """两种语料在同一行输出"""
    return base_cfg(
        inspect.currentframe().f_code.co_name,
        layout=SameLineLayout(),          # 同行布局
        gray=False,
        corpus=[
            # 第一段语料：枚举
            EnumCorpus(
                EnumCorpusCfg(
                    text_paths=[TEXT_DIR / "enum_text.txt"],
                    filter_by_chars=True,
                    chars_file=CHAR_DIR / "chn.txt",
                    **font_cfg
                ),
            ),
            # 第二段语料：中英文
            CharCorpus(
                CharCorpusCfg(
                    text_paths=[
                        TEXT_DIR / "chn_text.txt",
                        TEXT_DIR / "eng_text.txt",
                    ],
                    filter_by_chars=True,
                    chars_file=CHAR_DIR / "chn.txt",
                    length=(5, 10),
                    font_dir=font_cfg["font_dir"],
                    font_list_file=font_cfg["font_list_file"],
                    font_size=(30, 35),
                ),
            ),
        ],
        corpus_effects=[Effects([Padding(), DropoutRand()]), NoEffects()],
        layout_effects=Effects(Line(p=1)),
    )


# --------------------------
# 6) 额外行布局示例
# --------------------------
def extra_text_line_data():
    """上下两行文本布局示例"""
    return base_cfg(
        inspect.currentframe().f_code.co_name,
        layout=ExtraTextLineLayout(),     # 上下布局
        corpus=[
            # 第一行
            CharCorpus(
                CharCorpusCfg(
                    text_paths=[
                        TEXT_DIR / "chn_text.txt",
                        TEXT_DIR / "eng_text.txt",
                    ],
                    filter_by_chars=True,
                    chars_file=CHAR_DIR / "chn.txt",
                    length=(9, 10),
                    font_dir=font_cfg["font_dir"],
                    font_list_file=font_cfg["font_list_file"],
                    font_size=(30, 35),
                ),
            ),
            # 第二行
            CharCorpus(
                CharCorpusCfg(
                    text_paths=[
                        TEXT_DIR / "chn_text.txt",
                        TEXT_DIR / "eng_text.txt",
                    ],
                    filter_by_chars=True,
                    chars_file=CHAR_DIR / "chn.txt",
                    length=(9, 10),
                    font_dir=font_cfg["font_dir"],
                    font_list_file=font_cfg["font_list_file"],
                    font_size=(30, 35),
                ),
            ),
        ],
        corpus_effects=[Effects([Padding()]), NoEffects()],
        layout_effects=Effects(Line(p=1)),
    )


# --------------------------
# 7) Albumentations 浮雕 & 模糊
# --------------------------
def albumentations_emboss_example():
    """浮雕 + 高斯模糊 示例"""
    return base_cfg(
        inspect.currentframe().f_code.co_name,
        corpus=get_char_corpus(),
        corpus_effects=Effects(
            [
                Padding(p=1, w_ratio=[0.2, 0.21], h_ratio=[0.7, 0.71], center=True),
                AlbumentationsEmboss(alpha=(0.9, 1.0), strength=(1.5, 1.6)),
                GaussianBlur(blur_limit=(3, 7)),
            ]
        ),
    )


# --------------------------
# 8) 颜色范围生成
# --------------------------
def range_color_example():
    """
    使用 RangeTextColorCfg 示例（蓝色 + 棕色）
    """

    color_ranges = {
        "blue": {
            "fraction": 0.5,
            "l_boundary": [0, 0, 150],
            "h_boundary": [60, 60, 253],
        },
        "brown": {
            "fraction": 0.5,
            "l_boundary": [139, 70, 19],
            "h_boundary": [160, 82, 43],
        },
    }

    return base_cfg(
        inspect.currentframe().f_code.co_name,
        corpus=get_char_corpus(),
        gray=False,    # 关闭灰度
        corpus_effects=Effects(
            [
                Line(0.5, color_cfg=RangeTextColorCfg(color_ranges=color_ranges)),
                OneOf([DropoutRand(), DropoutVertical()]),
            ]
        ),
    )


# --------------------------
# 9) 文本描边示例（实线、虚线、点线）
# --------------------------
def text_border_example():
    """多种文本描边效果"""
    return base_cfg(
        inspect.currentframe().f_code.co_name,
        corpus=get_char_corpus(),
        gray=False,
        corpus_effects=Effects(
            [
                # 红色实线描边
                TextBorder(
                    p=0.7,
                    border_width=(2, 4),
                    border_color_cfg=FixedTextColorCfg(),
                    border_style="solid",
                    blur_radius=0,
                ),
                # 蓝色虚线描边
                TextBorder(
                    p=0.3,
                    border_width=(1, 2),
                    border_color_cfg=RangeTextColorCfg(
                        {
                            "blue": {
                                "fraction": 1.0,
                                "l_boundary": [0, 0, 200],
                                "h_boundary": [50, 50, 255],
                            }
                        }
                    ),
                    border_style="dashed",
                    blur_radius=0,
                ),
                # 绿色点线描边
                TextBorder(
                    p=0.2,
                    border_width=(1, 3),
                    border_color_cfg=RangeTextColorCfg(
                        {
                            "green": {
                                "fraction": 1.0,
                                "l_boundary": [0, 150, 0],
                                "h_boundary": [50, 255, 50],
                            }
                        }
                    ),
                    border_style="dotted",
                    blur_radius=1,
                ),
            ]
        ),
    )


# --------------------------
# 10) 文本描边（浅色/深色比例）
# --------------------------
def text_border_light_dark_example():
    """浅色/深色描边混合示例"""
    return base_cfg(
        inspect.currentframe().f_code.co_name,
        corpus=get_char_corpus(),
        gray=False,
        corpus_effects=Effects(
            [
                TextBorder(
                    p=1.0,
                    border_width=(2, 3),
                    border_style="solid",
                    blur_radius=0,

                    # 描边亮色/暗色比例配置
                    enable=True,
                    fraction=0.5,
                    light_enable=True,
                    light_fraction=0.5,
                    dark_enable=True,
                    dark_fraction=0.5,
                ),
                OneOf([DropoutRand(), DropoutVertical()]),
            ]
        ),
    )


# -------------------------------------------------
# config 列表（text_renderer 要求必须有 configs）
# -------------------------------------------------
configs = [
    chn_data(),
    enum_data(),
    rand_data(),
    eng_word_data(),
    same_line_data(),
    extra_text_line_data(),
    albumentations_emboss_example(),
    range_color_example(),
    text_border_example(),
    text_border_light_dark_example(),
]
