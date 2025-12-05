from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QListWidget,
    QPushButton, QLineEdit, QCheckBox, QLabel, QFileDialog,
    QPlainTextEdit, QMessageBox, QSpacerItem, QSizePolicy
)

# 导入核心业务逻辑服务
from app.core.dataset_merge import DatasetMergeService, FolderInfo


# ------------------------------------------------
# 信号处理器 (如果需要跨线程处理，这是必要的，这里简化为同步调用)
# ------------------------------------------------

class DataMergeTab(QWidget):
    """
    第一个标签页：数据集合并 (PyQT5 View)
    """

    # 假设有一个共享的 train_ratio_getter 用于获取训练集比例 (来自主窗口或另一个标签页)
    def __init__(self, train_ratio_getter, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 依赖注入/引用
        self.merge_service = DatasetMergeService()
        self.train_ratio_getter = train_ratio_getter

        # 状态数据 (替代 tk.StringVar/BooleanVar)
        self.merge_folders: List[FolderInfo] = []

        self.setup_ui()
        self._connect_signals()

    def setup_ui(self):
        # ... (UI 布局代码与我之前提供的 PyQT5 实现相同，省略重复部分) ...
        main_layout = QVBoxLayout(self)

        # 1. 文件夹选择区域
        main_layout.addWidget(QLabel("选择数据集目录文件夹:"))
        self.list_widget = QListWidget()
        main_layout.addWidget(self.list_widget)

        # 1.1 列表操作按钮区域
        list_btn_layout = QHBoxLayout()
        self.add_folder_btn = QPushButton("添加文件夹")
        self.remove_btn = QPushButton("删除选中")
        self.clear_list_btn = QPushButton("清空列表")
        list_btn_layout.addWidget(self.add_folder_btn)
        list_btn_layout.addWidget(self.remove_btn)
        list_btn_layout.addWidget(self.clear_list_btn)
        list_btn_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        main_layout.addLayout(list_btn_layout)

        # 2. 合并配置区域
        merge_config_group = QGroupBox("合并配置")
        config_layout = QVBoxLayout(merge_config_group)

        # 2.1 输出目录行
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出目录:"))
        self.output_lineedit = QLineEdit()
        self.select_dir_btn = QPushButton("选择目录")
        output_layout.addWidget(self.output_lineedit)
        output_layout.addWidget(self.select_dir_btn)
        config_layout.addLayout(output_layout)

        # 2.2 选项复选框行
        checkbox_layout = QHBoxLayout()
        self.copy_images_cb = QCheckBox("复制图片文件")
        self.rename_files_cb = QCheckBox("自动重命名重复文件")
        self.create_summary_cb = QCheckBox("生成合并摘要")  # 对应原代码的 create_summary

        self.copy_images_cb.setChecked(True)
        self.create_summary_cb.setChecked(True)

        checkbox_layout.addWidget(self.copy_images_cb)
        checkbox_layout.addWidget(self.rename_files_cb)
        checkbox_layout.addWidget(self.create_summary_cb)
        checkbox_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        config_layout.addLayout(checkbox_layout)

        main_layout.addWidget(merge_config_group)

        # 3. 操作按钮区域
        action_btn_layout = QHBoxLayout()
        action_btn_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.start_merge_btn = QPushButton("开始合并")
        self.preview_btn = QPushButton("预览合并结果")
        action_btn_layout.addWidget(self.start_merge_btn)
        action_btn_layout.addWidget(self.preview_btn)
        main_layout.addLayout(action_btn_layout)

        # 4. 合并日志区域
        main_layout.addWidget(QLabel("合并日志"))
        self.log_area = QPlainTextEdit()
        self.log_area.setReadOnly(True)
        main_layout.addWidget(self.log_area)

        # 5. 底部状态栏/说明
        main_layout.addWidget(QLabel("致谢"))

    def _connect_signals(self):
        """连接所有按钮的点击事件到相应的方法"""
        self.add_folder_btn.clicked.connect(self.add_folder)
        self.remove_btn.clicked.connect(self.remove_selected)
        self.clear_list_btn.clicked.connect(self.clear_folders)
        self.select_dir_btn.clicked.connect(self.select_output_directory)
        self.start_merge_btn.clicked.connect(self.handle_start_merge)
        self.preview_btn.clicked.connect(self.handle_preview_merge)

    # ------------------------------------------------
    # UI 辅助方法 (更新列表显示)
    # ------------------------------------------------
    def update_folder_list_display(self):
        """更新文件夹列表显示 (原 update_folder_list)"""
        self.list_widget.clear()
        for folder in self.merge_folders:
            display_text = f"{folder.name} (图片: {folder.images_count}, 标签文件: {len(folder.label_files)})"
            self.list_widget.addItem(display_text)

    def log_message(self, message):
        """添加日志，并滚动到底部 (替代 log_merge 的 UI 部分)"""
        self.log_area.appendPlainText(message)
        # QPlainTextEdit 自动滚动到底部

    # ------------------------------------------------
    # UI 交互方法 (调用核心逻辑)
    # ------------------------------------------------

    def select_output_directory(self):
        """选择输出目录 (原 select_output_dir)"""
        directory = QFileDialog.getExistingDirectory(self, "选择合并输出目录", self.output_lineedit.text())
        if directory:
            self.output_lineedit.setText(directory)
            self.log_message(f"输出目录设置为: {directory}")

    def add_folder(self):
        """添加数据集文件夹 (原 add_folder)"""
        folder_path = QFileDialog.getExistingDirectory(self, "选择数据集文件夹", "")
        if folder_path:
            try:
                # 调用核心逻辑服务来检查和获取数据
                folder_info = self.merge_service.get_folder_info(folder_path)

                # 检查标签文件缺失 (如果核心逻辑没有抛出异常，则提示 UI)
                if not folder_info.label_files:
                    reply = QMessageBox.question(self, '确认',
                                                 f"在文件夹中未找到标签文件，是否仍要添加？\n{folder_path}",
                                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if reply == QMessageBox.No:
                        return

                self.merge_folders.append(folder_info)
                self.update_folder_list_display()
                self.log_message(f"已添加数据集：{folder_info.name} (图片数量: {folder_info.images_count})")

            except FileNotFoundError as e:
                QMessageBox.warning(self, "警告", str(e))
            except Exception as e:
                QMessageBox.critical(self, "错误", f"处理文件夹时发生错误: {e}")

    def remove_selected(self):
        """删除选中的文件夹 (原 remove_folder)"""
        selected_rows = self.list_widget.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "警告", "请先选择要删除的文件夹")
            return

        # 从后往前删除，避免索引混乱
        selected_rows.sort(key=lambda x: x.row(), reverse=True)

        for index in selected_rows:
            row = index.row()
            folder_name = self.merge_folders[row].name
            del self.merge_folders[row]
            self.list_widget.takeItem(row)  # 从 UI 中删除
            self.log_message(f"已删除选中数据集：{folder_name}")

    def clear_folders(self):
        """清空文件夹列表 (原 clear_folders)"""
        if self.merge_folders:
            reply = QMessageBox.question(self, '确认', "确定要清空所有数据集吗？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.merge_folders.clear()
                self.list_widget.clear()
                self.log_message("已清空所有数据集")

    def handle_preview_merge(self):
        """预览合并结果 (原 preview_merge)"""
        if not self.merge_folders:
            QMessageBox.warning(self, "警告", "请先添加数据集文件夹")
            return

        total_images = sum(folder.images_count for folder in self.merge_folders)
        total_labels = sum(len(folder.label_files) for folder in self.merge_folders)

        preview_text = f"合并预览：\n"
        preview_text += f"数据集数量：{len(self.merge_folders)}\n"
        preview_text += f"总图片数量：{total_images}\n"
        preview_text += f"总标签文件数：{total_labels}\n\n"

        preview_text += "详细信息：\n"
        for i, folder in enumerate(self.merge_folders, 1):
            preview_text += f"{i}. {folder.name}\n"
            preview_text += f"   路径：{folder.path}\n"
            preview_text += f"   图片：{folder.images_count} 张\n"
            preview_text += f"   标签文件：{', '.join(folder.label_files) if folder.label_files else '无'}\n\n"

        QMessageBox.information(self, "合并预览", preview_text)
        self.log_message("已显示合并预览。")

    def handle_start_merge(self):
        """处理开始合并按钮的点击事件 (原 merge_datasets)"""

        output_dir = self.output_lineedit.text().strip()
        if not self.merge_folders or not output_dir:
            msg = ""
            if not self.merge_folders: msg += "请添加数据集文件夹。\n"
            if not output_dir: msg += "请选择输出目录。\n"
            QMessageBox.warning(self, "警告", msg.strip())
            return

        self.log_message("\n--- 开始合并进程 ---")
        self.start_merge_btn.setEnabled(False)  # 禁用按钮，避免重复点击

        try:
            # 1. 收集参数
            copy_images = self.copy_images_cb.isChecked()
            rename_duplicates = self.rename_files_cb.isChecked()
            create_summary = self.create_summary_cb.isChecked()
            train_ratio = self.train_ratio_getter()  # 从主应用获取共享的训练集比例

            # 2. 调用核心业务逻辑服务
            success, stats = self.merge_service.merge_datasets(
                folders=self.merge_folders,
                output_dir=output_dir,
                copy_images=copy_images,
                rename_duplicates=rename_duplicates,
                train_ratio=train_ratio,
                create_summary=create_summary,
                log_func=self.log_message  # 传入日志回调函数
            )

            # 3. 根据结果更新 UI
            if success:
                self.log_message("✅ 合并完成！")

                # 构建成功信息
                success_msg = (
                    f"数据集合并完成！\n\n"
                    f"输出目录：{output_dir}\n"
                    f"复制图片：{stats.merged_images_count} 张\n"
                    f"有效标签：{stats.valid_labels_count} 个\n"
                    f"训练集：{stats.train_size} 样本\n"
                    f"验证集：{stats.val_size} 样本\n"
                    f"匹配率：{stats.match_rate:.1f}%"
                )
                QMessageBox.information(self, "成功", success_msg)
            else:
                self.log_message("❌ 合并失败，请查看日志。")
                QMessageBox.critical(self, "错误", "数据集合并失败，请查看日志详情。")

        except Exception as e:
            self.log_message(f"❌ 发生未知错误: {str(e)}")
            QMessageBox.critical(self, "致命错误", f"合并过程中发生错误: {e}")

        finally:
            self.start_merge_btn.setEnabled(True)  # 恢复按钮

# ... (main_window.py 中需要添加一个 train_ratio_getter 才能完整运行)