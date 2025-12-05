# app/core/config_helpers.py

from text_renderer.config import TextColorCfg

# 移动 BlackTextColorCfg 到这里
class BlackTextColorCfg(TextColorCfg):
    """自定义黑色文字配置，移至此可导入模块以解决多进程Pickle问题"""
    def get_color(self, bg_img):
        return (0, 0, 0, 255)  # 纯黑色，完全不透明

# 如果有其他自定义的 Corpus 或 Effect 类，也应该移到这里