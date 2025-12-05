import sys
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QApplication, QStatusBar, QLabel,
    QDoubleSpinBox, QHBoxLayout, QWidget
)
from PyQt5.QtCore import Qt

# 假设这三个文件都在 views/tabs/ 目录下
from .tabs.data_merge_tab import DataMergeTab
from .tabs.label_generation_tab import LabelGenerationTab
from .tabs.text_generation_tab import TextGenerationTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PaddleOCR工具")
        self.resize(1000, 750)  # 适当增大初始窗口大小

        # ----------------------------------------------------
        # 1. 共享状态管理 (Shared State)
        # ----------------------------------------------------
        # 训练集比例是 Tab 1 和 Tab 2 共享的变量
        # 我们使用 Getter/Setter 模式来传递这个状态

        def train_ratio_getter() -> float:
            """获取训练集比例"""
            # 为了简化，假设我们有一个共享的 QDoubleSpinBox 负责这个值
            # 但在这个主窗口中，我们没有一个全局的 SpinBox。
            # 更好的方法是让一个 Tab 作为“主”设置者。
            # 因为 LabelGenerationTab 有 SpinBox，我们让它来管理。
            # 首次实例化前，我们使用一个临时变量或默认值。
            if hasattr(self, 'label_generation_tab'):
                return self.label_generation_tab.get_train_ratio()
            return 0.8  # 默认值

        def train_ratio_setter(value: float):
            """设置训练集比例，并通知所有需要同步的组件"""
            # 通知 DataMergeTab 更新其显示（如果需要）
            # 通知 LabelGenerationTab 保持其 SpinBox 的值
            if hasattr(self, 'label_generation_tab'):
                self.label_generation_tab.set_train_ratio(value)

            # 由于 DataMergeTab 只需要在开始合并时 "获取" 最新值，这里无需通知

        # ----------------------------------------------------
        # 2. 实例化和连接标签页 (Tabs)
        # ----------------------------------------------------

        # 实例化各个标签页，并传入共享状态的 Getter/Setter
        # DataMergeTab 只需要 Getter
        self.data_merge_tab = DataMergeTab(train_ratio_getter=train_ratio_getter)

        # LabelGenerationTab 既需要 Getter 也需要 Setter
        self.label_generation_tab = LabelGenerationTab(
            train_ratio_var_setter=train_ratio_setter,
            train_ratio_getter=train_ratio_getter
        )

        # TextGenerationTab 独立
        self.text_generation_tab = TextGenerationTab()

        # ----------------------------------------------------
        # 3. 设置 QTabWidget
        # ----------------------------------------------------
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tabs.addTab(self.data_merge_tab, "renderer数据集合并 (不需跳点标签文件生成)")
        self.tabs.addTab(self.label_generation_tab, "标签文件生成 (paddle)")
        self.tabs.addTab(self.text_generation_tab, "文本识别数据集生成")

        # ----------------------------------------------------
        # 4. 状态栏 (可选，用于显示全局状态)
        # ----------------------------------------------------
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("应用已准备就绪")
        self.status_bar.addWidget(self.status_label)

        # 示例：让 TextGenerationTab 报告状态
        # 可以在 TextGenerationTab 中定义一个 status_signal，并在 MainWindow 中连接它
        # self.text_generation_tab.status_signal.connect(self.status_label.setText)


# ----------------------------------------------------
# 5. 应用入口 (main.py)
# ----------------------------------------------------
# (这部分代码应放在项目根目录的 main.py 中)

if __name__ == '__main__':
    # 确保 multiprocessing start method 在应用启动前设置 (PyQt5 兼容性)
    import multiprocessing as mp

    mp.freeze_support()  # Windows/PyInstaller 兼容

    app = QApplication(sys.argv)

    # 延迟初始化，确保所有模块和信号准备就绪
    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())