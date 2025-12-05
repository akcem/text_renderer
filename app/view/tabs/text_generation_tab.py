import multiprocessing as mp
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLineEdit, QListWidget,
    QPushButton, QLabel, QFileDialog, QMessageBox, QSpinBox,
    QDoubleSpinBox, QPlainTextEdit, QGridLayout, QRadioButton, QSpacerItem, QSizePolicy, QCheckBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# 导入核心逻辑服务
from app.core.text_renderer_module import TextRendererService


# ------------------------------------------------
# 辅助函数：读取配置函数名
# ------------------------------------------------
def get_config_func_names(file_path):
    """
    通过文本解析读取 config.py 文件中 configs = [...] 列表里的函数名
    """
    names = []
    if not file_path:
        return names

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 简单查找 configs = [...] 块
        start_line = -1
        end_line = -1
        lines = content.split('\n')
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line.startswith('configs = ['):
                start_line = i
            if start_line != -1 and stripped_line.endswith(']'):
                end_line = i
                break

        if start_line != -1 and end_line != -1:
            config_block = "\n".join(lines[start_line:end_line + 1])
            # 使用正则表达式匹配 函数名()
            import re
            matches = re.findall(r'(\w+)\s*\(\s*\)', config_block)
            names.extend(matches)
    except Exception as e:
        print(f"Error reading config file: {e}")
        pass

    # 过滤掉重复项，并按原顺序保留
    return list(dict.fromkeys(names))
# ------------------------------------------------
# QThread Worker: 运行 TextRendererService
# ------------------------------------------------

class GenerationWorker(QThread):
    """
    负责运行 TextRendererService 的独立线程
    """
    log_signal = pyqtSignal(str)  # 用于发送日志消息
    finished_signal = pyqtSignal(bool)  # 用于发送任务完成或失败信号

    def __init__(self, service: TextRendererService, config: dict):
        super().__init__()
        self.service = service
        self.config = config

    def run(self):
        try:
            # 运行核心逻辑，并传入日志回调
            self.service.start_generation(
                config_file=self.config['config_file'],
                dataset_type=self.config['dataset_type'],
                num_processes=self.config['num_processes'],
                log_period=self.config['log_period'],
                log_callback=self.log_signal.emit,  # 使用 Signal 作为回调
                config_func_names = self.config.get('config_func_names', []),
                override_params=self.config.get('override_params', {})
            )
            self.finished_signal.emit(True)  # 正常完成
        except Exception as e:
            self.log_signal.emit(f"CRITICAL ERROR: {e}")
            self.finished_signal.emit(False)  # 失败
        finally:
            # 即使失败，也需要清理
            self.service.shutdown_manager()


# ------------------------------------------------
# Log Reader Thread: 从多进程 Queue 中读取日志
# ------------------------------------------------
class LogReader(QThread):
    """
    专门用于从 TextRendererService 的 multiprocessing.Queue 中读取日志
    并将日志通过 Signal 发送到 UI 线程
    """
    log_signal = pyqtSignal(str)
    stop_ui_update_signal = pyqtSignal()

    def __init__(self, log_queue: mp.Queue):
        super().__init__()
        self._log_queue = log_queue
        self._running = True

    def run(self):
        while self._running:
            try:
                # 阻塞读取，直到有日志进入队列
                log_entry = self._log_queue.get(timeout=0.1)

                if log_entry == "STOP_GUI_UPDATE":
                    self.stop_ui_update_signal.emit()
                    break

                self.log_signal.emit(log_entry)
            except Exception:
                # 队列空超时，继续循环
                pass

    def stop(self):
        self._running = False
        self.wait()  # 等待线程结束


# ------------------------------------------------
# UI 标签页
# ------------------------------------------------

class TextGenerationTab(QWidget):
    """
    第三个标签页：文本识别数据集生成 (PyQT5 View + Controller)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.generator_service = TextRendererService()
        self.worker_thread: GenerationWorker = None
        self.log_reader_thread: LogReader = None
        self.is_running = False
        self.config_func_names = []

        self.setup_ui()
        self._connect_signals()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # 1. 配置区域
        config_frame = QGroupBox("配置参数")
        config_layout = QGridLayout(config_frame)
        # Row 0: Config File
        config_layout.addWidget(QLabel("配置文件 (.py):"), 0, 0)
        self.config_lineedit = QLineEdit()
        self.config_lineedit.setReadOnly(True)
        config_layout.addWidget(self.config_lineedit, 0, 1)
        self.select_config_btn = QPushButton("选择文件")
        config_layout.addWidget(self.select_config_btn, 0, 2)
        # Row 1: Config Function Selector
        config_layout.addWidget(QLabel("选择配置函数:"), 1, 0, alignment=Qt.AlignTop)
        self.config_list_widget = QListWidget()
        self.config_list_widget.setSelectionMode(QListWidget.ExtendedSelection)  # 允许多选
        self.config_list_widget.setMaximumHeight(150)  # 限制高度
        config_layout.addWidget(self.config_list_widget, 1, 1, 1, 2)
        # Row 2: Dataset Type & Num Processes
        config_layout.addWidget(QLabel("数据集类型:"), 2, 0, alignment=Qt.AlignTop)

        # Radio buttons for dataset type
        radio_layout = QHBoxLayout()

        self.img_radio = QRadioButton("img")
        self.lmdb_radio = QRadioButton("lmdb")
        self.img_radio.setChecked(True)  # 默认选中 img
        radio_layout.addWidget(self.img_radio)
        radio_layout.addWidget(self.lmdb_radio)
        radio_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        config_layout.addLayout(radio_layout, 2,1)

        config_layout.addWidget(QLabel("进程数:"), 2, 2)
        self.num_processes_spin = QSpinBox()
        self.num_processes_spin.setRange(0, mp.cpu_count())
        self.num_processes_spin.setValue(mp.cpu_count() if mp.cpu_count() > 1 else 1)
        config_layout.addWidget(self.num_processes_spin, 1, 4)

        # Row 3: Log Period
        config_layout.addWidget(QLabel("日志周期 (%):"), 3, 0)
        self.log_period_spin = QDoubleSpinBox()
        self.log_period_spin.setRange(0.1, 100.0)
        self.log_period_spin.setSingleStep(0.1)
        self.log_period_spin.setValue(1.0)
        config_layout.addWidget(self.log_period_spin, 3, 1)

        main_layout.addWidget(config_frame)
        # -----------------------------------------------------
        # 新增：运行时参数覆盖区域
        # -----------------------------------------------------
        override_frame = QGroupBox("运行时参数覆盖")
        override_layout = QHBoxLayout(override_frame)

        # 覆盖：num_image
        override_layout.addWidget(QLabel("生成数量 (覆盖):"))
        self.override_num_image_spin = QSpinBox()
        self.override_num_image_spin.setRange(1, 999999)
        self.override_num_image_spin.setValue(100)
        override_layout.addWidget(self.override_num_image_spin)

        # 覆盖：gray
        self.override_gray_checkbox = QCheckBox("强制灰度")
        self.override_gray_checkbox.setCheckState(Qt.Unchecked)
        override_layout.addWidget(self.override_gray_checkbox)

        override_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        main_layout.addWidget(override_frame)  # 将新的 GroupBox 加入主布局
        # 2. 运行按钮
        button_layout = QHBoxLayout()
        button_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.run_btn = QPushButton("开始生成")
        self.stop_btn = QPushButton("停止生成")
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.run_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        main_layout.addLayout(button_layout)

        # 3. 日志区域
        log_frame = QGroupBox("生成日志")
        log_layout = QVBoxLayout(log_frame)
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        main_layout.addWidget(log_frame)
        main_layout.setStretch(2, 1)  # 让日志区域占据额外空间

        main_layout.addWidget(QLabel("致谢"))

    def _connect_signals(self):
        self.select_config_btn.clicked.connect(self.select_config)
        self.run_btn.clicked.connect(self.start_generation)
        self.stop_btn.clicked.connect(self.stop_generation)

    def select_config(self):
        """选择配置文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 Python 配置文件", "", "Python files (*.py);;All files (*.*)"
        )
        if file_path:
            self.config_lineedit.setText(file_path)
            # --- 新增逻辑：读取并填充配置函数列表 ---
            self.config_list_widget.clear()
            self.config_func_names = get_config_func_names(file_path)

            if not self.config_func_names:
                self.config_list_widget.addItem("未找到配置函数 (configs = [...] 列表为空)")
            else:
                self.config_list_widget.addItems(self.config_func_names)
                # 默认选中所有配置
                for i in range(self.config_list_widget.count()):
                    self.config_list_widget.item(i).setSelected(True)
    def log_to_gui(self, message):
        """将消息写入 QPlainTextEdit"""
        import time
        self.log_text.appendPlainText(f"[{time.strftime('%H:%M:%S')}] {message}")

    def start_generation(self):
        """启动生成流程"""
        config_file = self.config_lineedit.text()
        # --- 新增逻辑：获取选中的配置函数名 ---
        selected_funcs = [
            item.text() for item in self.config_list_widget.selectedItems()
        ]
        if not config_file or not selected_funcs:
            QMessageBox.warning(self, "警告", "请选择配置文件")
            return

        if self.is_running:
            return

        self.log_text.clear()
        self.is_running = True
        self.set_ui_state(True)  # 禁用输入，启用停止
        self.log_to_gui("--- 启动生成进程 ---")

        # 1. 收集配置
        config = {
            'config_file': config_file,
            'dataset_type': "lmdb" if self.lmdb_radio.isChecked() else "img",
            'num_processes': self.num_processes_spin.value(),
            'log_period': self.log_period_spin.value(),
            'config_func_names': selected_funcs,  # 新增：传递选中的函数名列表
            # --- ！！！新增运行时覆盖参数 ！！！---
            'override_params': {
                'override_num_image': self.override_num_image_spin.value(),
                'override_gray': self.override_gray_checkbox.isChecked(),}
        }

        # 2. 启动 Worker 线程 (运行主生成逻辑)
        self.worker_thread = GenerationWorker(self.generator_service, config)
        self.worker_thread.log_signal.connect(self.log_to_gui)  # 连接 Worker 的日志信号
        self.worker_thread.finished_signal.connect(self.on_generation_finished)  # 连接完成信号
        self.worker_thread.start()

        # 3. 启动 Log Reader 线程 (读取多进程日志)
        log_queue = self.generator_service.get_log_queue()
        if log_queue:
            self.log_reader_thread = LogReader(log_queue)
            self.log_reader_thread.log_signal.connect(self.log_to_gui)
            self.log_reader_thread.stop_ui_update_signal.connect(self.on_generation_finished)
            self.log_reader_thread.start()

    def stop_generation(self):
        """停止生成流程"""
        if not self.is_running:
            return

        self.run_btn.setEnabled(False)  # 禁用启动按钮
        self.stop_btn.setEnabled(False)  # 禁用停止按钮，直到完全停止

        self.log_to_gui("--- 收到停止信号，正在尝试安全停止进程 ---")

        # 向服务发送停止信号
        self.generator_service.stop_all()
        # LogReader 会收到 STOP_GUI_UPDATE 信号并调用 on_generation_finished

    def on_generation_finished(self, success: bool = True):
        """生成完成后调用，清理并恢复 UI"""
        if not self.is_running:
            return

        self.is_running = False

        # 清理 Worker 线程
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()

        # 清理 Log Reader 线程
        if self.log_reader_thread and self.log_reader_thread.isRunning():
            self.log_reader_thread.stop()

        self.set_ui_state(False)  # 恢复 UI 状态

        self.log_to_gui("--- 生成进程已结束 ---")
        if not success:
            QMessageBox.critical(self, "错误", "生成过程中发生错误，请检查日志。")

    def set_ui_state(self, running: bool):
        """设置 UI 控件的启用/禁用状态"""
        self.run_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.select_config_btn.setEnabled(not running)
        self.config_lineedit.setReadOnly(running)
        self.img_radio.setEnabled(not running)
        self.lmdb_radio.setEnabled(not running)
        self.num_processes_spin.setEnabled(not running)
        self.log_period_spin.setEnabled(not running)