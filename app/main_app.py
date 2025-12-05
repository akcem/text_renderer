# app/main_app.py

import tkinter as tk
from tkinter import ttk
import os
import sys

# 导入子模块
# 确保父目录在 sys.path 中，以便导入 child_app
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from app.core.label_generation import LabelGeneratorModule
from app.core.dataset_merge import DatasetMergeModule
from app.core.text_renderer_module import TextRendererModule

class PaddleOCRLabelGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("PaddleOCR标签文件生成（来自renderer）")
        self.root.geometry("1000x700")

        # 共享配置变量
        self.train_ratio = tk.DoubleVar(value=0.8)  # 共享给两个模块使用

        # 状态栏变量
        self.status_var = tk.StringVar(value="就绪")

        # 模块实例
        self.label_generator_module = None
        self.dataset_merge_module = None
        self.text_renderer_module = None

        self.setup_ui()

    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)  # 确保选项卡占据空间

        # 标题
        title_label = ttk.Label(main_frame, text="PaddleOCR标签文件生成（来自renderer）",
                                font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 20))

        # 创建选项卡
        self.setup_tabs(main_frame)

        # 状态栏
        status_label = ttk.Label(main_frame, textvariable=self.status_var,
                                 relief=tk.SUNKEN, anchor=tk.W)
        status_label.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

    def setup_tabs(self, parent):
        """设置选项卡，并实例化子模块"""
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # 创建两个选项卡框架
        self.tab2_frame = ttk.Frame(self.notebook)  # Tab 2
        self.tab1_frame = ttk.Frame(self.notebook)  # Tab 1
        self.tab3_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.tab2_frame, text="renderer数据集合并(不需就点标签文件生成)")
        self.notebook.add(self.tab1_frame, text="标签文件生成（paddle的）")
        self.notebook.add(self.tab3_frame, text="文本识别数据集生成")

        # 实例化并设置 Tab 1 内容
        self.label_generator_module = LabelGeneratorModule(
            parent_frame=self.tab1_frame,
            status_var=self.status_var,
            train_ratio_var=self.train_ratio  # 传入共享变量
        )

        # 实例化并设置 Tab 2 内容
        self.dataset_merge_module = DatasetMergeModule(
            root=self.root,
            parent_frame=self.tab2_frame,
            status_var=self.status_var,
            train_ratio_var=self.train_ratio  # 传入共享变量
        )
        # 实例化并设置 Tab 3 内容
        self.text_renderer_module = TextRendererModule(
            root=self.root,
            parent_frame=self.tab3_frame,
            status_var=self.status_var
        )
        # 激活第一个选项卡 (保持原代码顺序)
        self.notebook.select(self.tab2_frame)


def main():
    root = tk.Tk()
    app = PaddleOCRLabelGenerator(root)

    # 设置图标（如果有的话）
    try:
        root.iconbitmap('icon.ico')  # 可选：添加应用图标
    except:
        pass

    root.mainloop()


if __name__ == "__main__":
    # 为了在项目结构中正确运行，需要设置好 Python 路径
    # 如果运行 main_app.py 报错找不到 child_app，请确保项目根目录在 PYTHONPATH 中
    # 或在 IDE 中将 app 目录标记为 Source Root
    main()