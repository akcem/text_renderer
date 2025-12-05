import sys
import os
import multiprocessing as mp
from PyQt5.QtWidgets import QApplication

# 确保 views 目录可以被正确导入
# 如果 main.py 在项目根目录，views 是一个子包
# 需要确保 Python 路径正确，如果直接运行，可能需要调整导入方式
try:
    # 假设项目结构正确，使用相对导入（如果 main.py 只是一个启动脚本）
    from views.main_window import MainWindow
except ImportError:
    # 如果作为独立脚本运行，且当前目录不是项目根目录，可能需要调整路径
    # 这里我们采用更安全的绝对导入路径方式
    # 假设项目根目录已在 sys.path 中，或者通过 __init__.py 结构化

    # 这是一个通用的 PyQT5 导入结构
    # 由于您的结构是 views/main_window.py，导入方式如下：
    from app.view.main_window import MainWindow


def main():
    """
    程序主入口函数
    """

    # --- 1. 多进程兼容性处理 ---
    # 这对于使用了 multiprocessing 模块的程序（例如您的 Text Generation Tab）至关重要
    # 确保在 Windows 或使用 pyinstaller 打包时，子进程能正确启动
    # 在 __main__ 保护下调用 freeze_support()
    if sys.platform.startswith('win'):
        mp.freeze_support()

    # --- 2. PyQT5 应用初始化 ---
    app = QApplication(sys.argv)

    # --- 3. 实例化并显示主窗口 ---
    # 创建主窗口实例
    main_window = MainWindow()

    # 显示主窗口
    main_window.show()

    # --- 4. 启动事件循环 ---
    # 启动 PyQT5 的事件循环，等待用户操作
    sys.exit(app.exec_())


if __name__ == '__main__':
    # 确保 main() 函数只在直接运行此文件时被调用
    main()