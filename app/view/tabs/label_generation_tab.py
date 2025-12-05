import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLineEdit,
    QPushButton, QLabel, QFileDialog, QMessageBox, QDoubleSpinBox,
    QPlainTextEdit, QSpacerItem, QSizePolicy, QGridLayout
)
from typing import Callable, Dict,Any

# 导入核心业务逻辑服务
from app.core.label_generation import LabelGeneratorService, GenerationResult


class LabelGenerationTab(QWidget):
    """
    第二个标签页：标签文件生成 (PyQT5 View)
    """

    def __init__(self, train_ratio_var_setter: Callable[[float], None], train_ratio_getter: Callable[[], float], *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

        # 依赖注入/引用
        self.generator_service = LabelGeneratorService()
        self.train_ratio_var_setter = train_ratio_var_setter  # 设置主应用共享的比例
        self.train_ratio_getter = train_ratio_getter  # 获取主应用共享的比例

        # 状态数据
        self.json_data: Dict[str, Any] = {}
        self.generated_files: Dict[str, str] = {'train': '', 'val': ''}

        self.setup_ui()
        self._connect_signals()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # 1. 文件上传区域
        upload_frame = QGroupBox("文件上传")
        upload_layout = QGridLayout(upload_frame)

        upload_layout.addWidget(QLabel("JSON文件:"), 0, 0)
        self.file_lineedit = QLineEdit()
        self.file_lineedit.setReadOnly(True)
        upload_layout.addWidget(self.file_lineedit, 0, 1)
        self.select_file_btn = QPushButton("选择文件")
        upload_layout.addWidget(self.select_file_btn, 0, 2)

        self.file_info_label = QLabel("")
        upload_layout.addWidget(self.file_info_label, 1, 0, 1, 3)  # 跨三列

        main_layout.addWidget(upload_frame)

        # 2. 配置区域
        config_frame = QGroupBox("生成配置")
        config_layout = QGridLayout(config_frame)

        # 训练集比例 (使用 QDoubleSpinBox)
        config_layout.addWidget(QLabel("训练集比例:"), 0, 0)
        self.train_ratio_spin = QDoubleSpinBox()
        self.train_ratio_spin.setRange(0.1, 0.9)
        self.train_ratio_spin.setSingleStep(0.1)
        self.train_ratio_spin.setValue(self.train_ratio_getter())  # 初始化为共享变量的值
        config_layout.addWidget(self.train_ratio_spin, 0, 1)

        # 图片路径前缀
        config_layout.addWidget(QLabel("图片路径前缀:"), 0, 2)
        self.image_prefix_lineedit = QLineEdit("images/")
        config_layout.addWidget(self.image_prefix_lineedit, 0, 3)

        # 图片文件后缀
        config_layout.addWidget(QLabel("图片文件后缀:"), 1, 0)
        self.image_suffix_lineedit = QLineEdit(".jpg")
        config_layout.addWidget(self.image_suffix_lineedit, 1, 1)

        # 训练集文件名
        config_layout.addWidget(QLabel("训练集文件名:"), 2, 0)
        self.train_filename_lineedit = QLineEdit("train.txt")
        config_layout.addWidget(self.train_filename_lineedit, 2, 1)

        # 验证集文件名
        config_layout.addWidget(QLabel("验证集文件名:"), 2, 2)
        self.val_filename_lineedit = QLineEdit("val.txt")
        config_layout.addWidget(self.val_filename_lineedit, 2, 3)

        main_layout.addWidget(config_frame)

        # 3. 操作按钮区域
        button_layout = QHBoxLayout()
        button_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.generate_btn = QPushButton("生成标签文件")
        button_layout.addWidget(self.generate_btn)
        self.download_all_btn = QPushButton("下载所有文件")
        button_layout.addWidget(self.download_all_btn)
        button_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        main_layout.addLayout(button_layout)

        # 4. 预览区域
        preview_group = QGroupBox("文件预览")
        preview_layout = QGridLayout(preview_group)

        # 训练集预览
        preview_layout.addWidget(QLabel("训练集预览"), 0, 0)
        self.download_train_btn = QPushButton("下载")
        preview_layout.addWidget(self.download_train_btn, 0, 1)
        self.train_text = QPlainTextEdit()
        self.train_text.setReadOnly(True)
        preview_layout.addWidget(self.train_text, 1, 0, 1, 2)

        # 验证集预览
        preview_layout.addWidget(QLabel("验证集预览"), 0, 2)
        self.download_val_btn = QPushButton("下载")
        preview_layout.addWidget(self.download_val_btn, 0, 3)
        self.val_text = QPlainTextEdit()
        self.val_text.setReadOnly(True)
        preview_layout.addWidget(self.val_text, 1, 2, 1, 2)

        main_layout.addWidget(preview_group)
        main_layout.setStretch(3, 1)  # 让预览区域占据额外空间

        main_layout.addWidget(QLabel("致谢"))

    def _connect_signals(self):
        """连接所有按钮的点击事件到相应的方法"""
        self.select_file_btn.clicked.connect(self.select_json_file)
        self.generate_btn.clicked.connect(self.handle_generate_labels)
        self.download_all_btn.clicked.connect(self.download_all_files)
        self.download_train_btn.clicked.connect(lambda: self.download_file('train'))
        self.download_val_btn.clicked.connect(lambda: self.download_file('val'))
        # 共享变量的双向绑定（UI变动，更新主应用）
        self.train_ratio_spin.valueChanged.connect(self.train_ratio_var_setter)

        # ------------------------------------------------

    # UI 交互方法 (调用核心逻辑)
    # ------------------------------------------------

    def select_json_file(self):
        """选择 JSON 文件 (原 select_file/load_json_file)"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择JSON文件", "", "JSON files (*.json);;All files (*.*)"
        )

        if file_path:
            self.file_lineedit.setText(file_path)
            try:
                self.json_data, has_filenames = self.generator_service.load_json_data(file_path)
                num_labels = len(self.json_data['labels'])
                filename_info = '(包含文件名映射)' if has_filenames else '(无文件名映射)'

                self.file_info_label.setText(f"✓ 已加载 {num_labels} 个标签 {filename_info}")
                self.file_info_label.setStyleSheet("color: green;")
                # self.status_var.set(f"已加载JSON文件，包含 {num_labels} 个标签") # 状态栏逻辑应在主应用

            except Exception as e:
                QMessageBox.critical(self, "错误", str(e))
                self.json_data = {}
                self.file_info_label.setText("❌ 文件加载失败")
                self.file_info_label.setStyleSheet("color: red;")
                self.file_lineedit.clear()

    def handle_generate_labels(self):
        """处理生成标签文件的点击事件 (原 generate_label_files)"""
        if not self.json_data:
            QMessageBox.warning(self, "警告", "请先加载有效的JSON文件")
            return

        self.generate_btn.setEnabled(False)

        try:
            # 1. 收集参数
            train_ratio = self.train_ratio_spin.value()  # 直接从 SpinBox 获取
            image_prefix = self.image_prefix_lineedit.text()
            image_suffix = self.image_suffix_lineedit.text()

            # 2. 调用核心业务逻辑服务
            result: GenerationResult = self.generator_service.generate_labels(
                json_data=self.json_data,
                train_ratio=train_ratio,
                image_prefix=image_prefix,
                image_suffix=image_suffix
            )

            # 3. 更新 UI 状态
            self.generated_files['train'] = result.train_content
            self.generated_files['val'] = result.val_content
            self.update_preview()

            filename_type = "实际文件名" if result.used_filenames else "默认文件名"
            QMessageBox.information(self, "完成",
                                    f"生成完成！训练集: {result.train_count} 条，验证集: {result.val_count} 条 (使用{filename_type})")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成标签文件失败：{str(e)}")

        finally:
            self.generate_btn.setEnabled(True)

    def update_preview(self):
        """更新预览文本框 (原 update_preview)"""
        self.train_text.setPlainText(self.generated_files['train'])
        self.val_text.setPlainText(self.generated_files['val'])

    def download_file(self, file_type: str):
        """下载单个文件 (原 download_file)"""
        if not self.generated_files[file_type]:
            QMessageBox.warning(self, "警告", "请先生成标签文件")
            return

        filename = self.train_filename_lineedit.text() if file_type == 'train' else self.val_filename_lineedit.text()

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存标签文件", filename, "Text files (*.txt);;All files (*.*)"
        )

        if file_path:
            try:
                self.generator_service.save_file_content(file_path, self.generated_files[file_type])
                QMessageBox.information(self, "成功", f"文件已保存到：{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件失败：{str(e)}")

    def download_all_files(self):
        """下载所有文件 (原 download_all_files)"""
        if not self.generated_files['train'] or not self.generated_files['val']:
            QMessageBox.warning(self, "警告", "请先生成标签文件")
            return

        folder_path = QFileDialog.getExistingDirectory(self, "选择保存文件夹")

        if folder_path:
            try:
                train_filename = self.train_filename_lineedit.text()
                val_filename = self.val_filename_lineedit.text()

                # 保存训练集文件
                train_path = os.path.join(folder_path, train_filename)
                self.generator_service.save_file_content(train_path, self.generated_files['train'])

                # 保存验证集文件
                val_path = os.path.join(folder_path, val_filename)
                self.generator_service.save_file_content(val_path, self.generated_files['val'])

                QMessageBox.information(self, "成功", f"文件已保存到：\n{train_path}\n{val_path}")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件失败：{str(e)}")