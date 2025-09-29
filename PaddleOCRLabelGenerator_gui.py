# import tkinter as tk
# from tkinter import ttk, filedialog, messagebox, scrolledtext
# import json
# import random
# import os
# from pathlib import Path
# import shutil
# import datetime

# class PaddleOCRLabelGenerator:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("PaddleOCR数据处理工具")
#         self.root.geometry("1000x700")
        
#         # 数据存储
#         self.json_data = None
#         self.generated_files = {'train': '', 'val': ''}
        
#         # 配置变量
#         self.train_ratio = tk.DoubleVar(value=0.8)
#         self.image_prefix = tk.StringVar(value="images/")
#         self.image_suffix = tk.StringVar(value=".jpg")
#         self.train_filename = tk.StringVar(value="train.txt")
#         self.val_filename = tk.StringVar(value="val.txt")
        
#         # 合并数据存储
#         self.merge_folders = []
        
#         self.setup_ui()
        
#     def setup_ui(self):
#         # 主框架
#         main_frame = ttk.Frame(self.root, padding="10")
#         main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
#         # 配置网格权重
#         self.root.columnconfigure(0, weight=1)
#         self.root.rowconfigure(0, weight=1)
#         main_frame.columnconfigure(0, weight=1)
        
#         # 标题
#         title_label = ttk.Label(main_frame, text="PaddleOCR数据处理工具", 
#                                font=("Arial", 16, "bold"))
#         title_label.grid(row=0, column=0, pady=(0, 20))
        
#         # 创建选项卡
#         self.setup_tabs(main_frame)
        
#         # 状态栏
#         self.status_var = tk.StringVar(value="就绪")
#         status_label = ttk.Label(main_frame, textvariable=self.status_var, 
#                                relief=tk.SUNKEN, anchor=tk.W)
#         status_label.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
#     def setup_tabs(self, parent):
#         """设置选项卡"""
#         self.notebook = ttk.Notebook(parent)
#         self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
#         parent.rowconfigure(1, weight=1)
        
#         # 创建两个选项卡
#         self.tab1 = ttk.Frame(self.notebook)
#         self.tab2 = ttk.Frame(self.notebook)
        
#         self.notebook.add(self.tab1, text="标签文件生成")
#         self.notebook.add(self.tab2, text="数据集合并")
        
#         # 设置选项卡内容
#         self.setup_tab1()
#         self.setup_tab2()
        
#     def setup_tab1(self):
#         """设置第一个选项卡：标签文件生成"""
#         # 配置选项卡内的网格
#         self.tab1.columnconfigure(0, weight=1)
        
#         # 文件上传区域
#         upload_frame = ttk.LabelFrame(self.tab1, text="文件上传", padding="10")
#         upload_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
#         upload_frame.columnconfigure(1, weight=1)
        
#         ttk.Label(upload_frame, text="JSON文件:").grid(row=0, column=0, sticky=tk.W)
#         self.file_path = tk.StringVar()
#         self.file_entry = ttk.Entry(upload_frame, textvariable=self.file_path, state="readonly")
#         self.file_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 10))
        
#         ttk.Button(upload_frame, text="选择文件", 
#                   command=self.select_file).grid(row=0, column=2)
        
#         self.file_info = ttk.Label(upload_frame, text="", foreground="green")
#         self.file_info.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
#         # 配置区域
#         config_frame = ttk.LabelFrame(self.tab1, text="生成配置", padding="10")
#         config_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
#         config_frame.columnconfigure(1, weight=1)
#         config_frame.columnconfigure(3, weight=1)
        
#         # 第一行配置
#         ttk.Label(config_frame, text="训练集比例:").grid(row=0, column=0, sticky=tk.W)
#         train_ratio_spin = ttk.Spinbox(config_frame, from_=0.1, to=0.9, increment=0.1,
#                                       textvariable=self.train_ratio, width=10)
#         train_ratio_spin.grid(row=0, column=1, sticky=tk.W, padx=(10, 20))
        
#         ttk.Label(config_frame, text="图片路径前缀:").grid(row=0, column=2, sticky=tk.W)
#         ttk.Entry(config_frame, textvariable=self.image_prefix, width=15).grid(row=0, column=3, sticky=tk.W, padx=(10, 0))
        
#         # 第二行配置
#         ttk.Label(config_frame, text="图片文件后缀:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
#         ttk.Entry(config_frame, textvariable=self.image_suffix, width=10).grid(row=1, column=1, sticky=tk.W, padx=(10, 20), pady=(10, 0))
        
#         # 第三行配置
#         ttk.Label(config_frame, text="训练集文件名:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
#         ttk.Entry(config_frame, textvariable=self.train_filename, width=15).grid(row=2, column=1, sticky=tk.W, padx=(10, 20), pady=(10, 0))
        
#         ttk.Label(config_frame, text="验证集文件名:").grid(row=2, column=2, sticky=tk.W, pady=(10, 0))
#         ttk.Entry(config_frame, textvariable=self.val_filename, width=15).grid(row=2, column=3, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        
#         # 生成按钮
#         button_frame = ttk.Frame(self.tab1)
#         button_frame.grid(row=2, column=0, pady=10)
        
#         self.generate_btn = ttk.Button(button_frame, text="生成标签文件", 
#                                       command=self.generate_label_files)
#         self.generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
#         ttk.Button(button_frame, text="下载所有文件", 
#                   command=self.download_all_files).pack(side=tk.LEFT)
        
#         # 预览区域
#         preview_frame = ttk.LabelFrame(self.tab1, text="文件预览", padding="10")
#         preview_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
#         preview_frame.columnconfigure(0, weight=1)
#         preview_frame.columnconfigure(1, weight=1)
#         preview_frame.rowconfigure(1, weight=1)
#         self.tab1.rowconfigure(3, weight=1)
        
#         # 训练集预览
#         train_frame = ttk.Frame(preview_frame)
#         train_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
#         train_frame.columnconfigure(0, weight=1)
#         train_frame.rowconfigure(1, weight=1)
        
#         train_header = ttk.Frame(train_frame)
#         train_header.grid(row=0, column=0, sticky=(tk.W, tk.E))
#         train_header.columnconfigure(0, weight=1)
        
#         ttk.Label(train_header, text="训练集预览", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W)
#         ttk.Button(train_header, text="下载", 
#                   command=lambda: self.download_file('train')).grid(row=0, column=1)
        
#         self.train_text = scrolledtext.ScrolledText(train_frame, height=15, font=("Consolas", 9))
#         self.train_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        
#         # 验证集预览
#         val_frame = ttk.Frame(preview_frame)
#         val_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
#         val_frame.columnconfigure(0, weight=1)
#         val_frame.rowconfigure(1, weight=1)
        
#         val_header = ttk.Frame(val_frame)
#         val_header.grid(row=0, column=0, sticky=(tk.W, tk.E))
#         val_header.columnconfigure(0, weight=1)
        
#         ttk.Label(val_header, text="验证集预览", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W)
#         ttk.Button(val_header, text="下载", 
#                   command=lambda: self.download_file('val')).grid(row=0, column=1)
        
#         self.val_text = scrolledtext.ScrolledText(val_frame, height=15, font=("Consolas", 9))
#         self.val_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        
#     def setup_tab2(self):
#         """设置第二个选项卡：数据集合并"""
#         # 配置选项卡内的网格
#         self.tab2.columnconfigure(0, weight=1)
        
#         # 文件夹选择区域
#         folder_frame = ttk.LabelFrame(self.tab2, text="选择数据集文件夹", padding="10")
#         folder_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
#         folder_frame.columnconfigure(0, weight=1)
        
#         # 文件夹列表
#         self.folder_listbox = tk.Listbox(folder_frame, height=8)
#         self.folder_listbox.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=(0, 10))
        
#         # 滚动条
#         scrollbar = ttk.Scrollbar(folder_frame, orient="vertical", command=self.folder_listbox.yview)
#         scrollbar.grid(row=0, column=3, sticky=(tk.N, tk.S))
#         self.folder_listbox.config(yscrollcommand=scrollbar.set)
        
#         # 按钮区域
#         folder_button_frame = ttk.Frame(folder_frame)
#         folder_button_frame.grid(row=1, column=0, columnspan=4, pady=(10, 0))
        
#         ttk.Button(folder_button_frame, text="添加文件夹", 
#                   command=self.add_folder).pack(side=tk.LEFT, padx=(0, 10))
#         ttk.Button(folder_button_frame, text="删除选中", 
#                   command=self.remove_folder).pack(side=tk.LEFT, padx=(0, 10))
#         ttk.Button(folder_button_frame, text="清空列表", 
#                   command=self.clear_folders).pack(side=tk.LEFT)
        
#         # 合并配置区域
#         merge_config_frame = ttk.LabelFrame(self.tab2, text="合并配置", padding="10")
#         merge_config_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
#         merge_config_frame.columnconfigure(1, weight=1)
        
#         # 输出目录
#         ttk.Label(merge_config_frame, text="输出目录:").grid(row=0, column=0, sticky=tk.W)
#         self.output_dir = tk.StringVar()
#         self.output_entry = ttk.Entry(merge_config_frame, textvariable=self.output_dir, state="readonly")
#         self.output_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 10))
#         ttk.Button(merge_config_frame, text="选择目录", 
#                   command=self.select_output_dir).grid(row=0, column=2)
        
#         # 合并选项
#         self.copy_images = tk.BooleanVar(value=True)
#         self.rename_duplicates = tk.BooleanVar(value=True)
#         self.create_summary = tk.BooleanVar(value=True)
        
#         ttk.Checkbutton(merge_config_frame, text="复制图片文件", 
#                        variable=self.copy_images).grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
#         ttk.Checkbutton(merge_config_frame, text="自动重命名重复文件", 
#                        variable=self.rename_duplicates).grid(row=1, column=1, sticky=tk.W, pady=(10, 0))
#         ttk.Checkbutton(merge_config_frame, text="生成合并摘要", 
#                        variable=self.create_summary).grid(row=1, column=2, sticky=tk.W, pady=(10, 0))
        
#         # 合并按钮
#         merge_button_frame = ttk.Frame(self.tab2)
#         merge_button_frame.grid(row=2, column=0, pady=10)
        
#         self.merge_btn = ttk.Button(merge_button_frame, text="开始合并", 
#                                    command=self.merge_datasets)
#         self.merge_btn.pack(side=tk.LEFT, padx=(0, 10))
        
#         ttk.Button(merge_button_frame, text="预览合并结果", 
#                   command=self.preview_merge).pack(side=tk.LEFT)
        
#         # 合并日志区域
#         log_frame = ttk.LabelFrame(self.tab2, text="合并日志", padding="10")
#         log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
#         log_frame.columnconfigure(0, weight=1)
#         log_frame.rowconfigure(0, weight=1)
#         self.tab2.rowconfigure(3, weight=1)
        
#         self.merge_log = scrolledtext.ScrolledText(log_frame, height=12, font=("Consolas", 9))
#         self.merge_log.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
#     def select_file(self):
#         file_path = filedialog.askopenfilename(
#             title="选择JSON文件",
#             filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
#         )
        
#         if file_path:
#             self.file_path.set(file_path)
#             self.load_json_file(file_path)
            
#     def load_json_file(self, file_path):
#         try:
#             with open(file_path, 'r', encoding='utf-8') as f:
#                 self.json_data = json.load(f)
                
#             if 'labels' not in self.json_data:
#                 messagebox.showerror("错误", "JSON文件中缺少'labels'字段")
#                 return
                
#             num_labels = len(self.json_data['labels'])
#             self.file_info.config(text=f"✓ 已加载 {num_labels} 个标签")
#             self.status_var.set(f"已加载JSON文件，包含 {num_labels} 个标签")
            
#         except Exception as e:
#             messagebox.showerror("错误", f"加载JSON文件失败：{str(e)}")
#             self.json_data = None
            
#     def generate_label_files(self):
#         if not self.json_data or 'labels' not in self.json_data:
#             messagebox.showwarning("警告", "请先加载有效的JSON文件")
#             return
            
#         try:
#             self.status_var.set("正在生成标签文件...")
#             self.root.update()
            
#             # 获取所有标签条目
#             label_entries = list(self.json_data['labels'].items())
            
#             # 随机打乱数据
#             random.shuffle(label_entries)
            
#             # 计算训练集大小
#             train_size = int(len(label_entries) * self.train_ratio.get())
            
#             # 分割训练集和验证集
#             train_entries = label_entries[:train_size]
#             val_entries = label_entries[train_size:]
            
#             # 生成训练集文件内容
#             train_lines = []
#             for i, (label_id, label_text) in enumerate(train_entries):
#                 image_filename = f"train_word_{i + 1}{self.image_suffix.get()}"
#                 line = f"{self.image_prefix.get()}{image_filename}\t{label_text}"
#                 train_lines.append(line)
            
#             # 生成验证集文件内容
#             val_lines = []
#             for i, (label_id, label_text) in enumerate(val_entries):
#                 image_filename = f"val_word_{i + 1}{self.image_suffix.get()}"
#                 line = f"{self.image_prefix.get()}{image_filename}\t{label_text}"
#                 val_lines.append(line)
            
#             # 存储生成的内容
#             self.generated_files['train'] = '\n'.join(train_lines)
#             self.generated_files['val'] = '\n'.join(val_lines)
            
#             # 更新预览
#             self.update_preview()
            
#             self.status_var.set(f"生成完成！训练集: {len(train_lines)} 条，验证集: {len(val_lines)} 条")
            
#         except Exception as e:
#             messagebox.showerror("错误", f"生成标签文件失败：{str(e)}")
#             self.status_var.set("生成失败")
            
#     def update_preview(self):
#         # 更新训练集预览
#         self.train_text.delete(1.0, tk.END)
#         self.train_text.insert(1.0, self.generated_files['train'])
        
#         # 更新验证集预览
#         self.val_text.delete(1.0, tk.END)
#         self.val_text.insert(1.0, self.generated_files['val'])
        
#     def download_file(self, file_type):
#         if not self.generated_files[file_type]:
#             messagebox.showwarning("警告", "请先生成标签文件")
#             return
            
#         filename = self.train_filename.get() if file_type == 'train' else self.val_filename.get()
        
#         file_path = filedialog.asksaveasfilename(
#             defaultextension=".txt",
#             initialvalue=filename,
#             filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
#         )
        
#         if file_path:
#             try:
#                 with open(file_path, 'w', encoding='utf-8') as f:
#                     f.write(self.generated_files[file_type])
#                 messagebox.showinfo("成功", f"文件已保存到：{file_path}")
#             except Exception as e:
#                 messagebox.showerror("错误", f"保存文件失败：{str(e)}")
                
#     def download_all_files(self):
#         if not self.generated_files['train'] or not self.generated_files['val']:
#             messagebox.showwarning("警告", "请先生成标签文件")
#             return
            
#         folder_path = filedialog.askdirectory(title="选择保存文件夹")
        
#         if folder_path:
#             try:
#                 # 保存训练集文件
#                 train_path = os.path.join(folder_path, self.train_filename.get())
#                 with open(train_path, 'w', encoding='utf-8') as f:
#                     f.write(self.generated_files['train'])
                    
#                 # 保存验证集文件
#                 val_path = os.path.join(folder_path, self.val_filename.get())
#                 with open(val_path, 'w', encoding='utf-8') as f:
#                     f.write(self.generated_files['val'])
                    
#                 messagebox.showinfo("成功", f"文件已保存到：\n{train_path}\n{val_path}")
                
#             except Exception as e:
#                 messagebox.showerror("错误", f"保存文件失败：{str(e)}")

#     # 数据集合并相关方法
#     def add_folder(self):
#         """添加数据集文件夹"""
#         folder_path = filedialog.askdirectory(title="选择数据集文件夹")
#         if folder_path:
#             # 检查文件夹结构
#             images_path = os.path.join(folder_path, "images")
#             if not os.path.exists(images_path):
#                 messagebox.showwarning("警告", f"文件夹中没有找到images目录：\n{folder_path}")
#                 return
                
#             # 查找标签文件
#             label_files = []
#             for file in os.listdir(folder_path):
#                 if file.endswith('.txt') and ('train' in file.lower() or 'val' in file.lower() or 'label' in file.lower()):
#                     label_files.append(file)
            
#             if not label_files:
#                 result = messagebox.askyesno("确认", f"在文件夹中未找到标签文件，是否仍要添加？\n{folder_path}")
#                 if not result:
#                     return
            
#             # 添加到列表
#             folder_info = {
#                 'path': folder_path,
#                 'name': os.path.basename(folder_path),
#                 'images_count': len([f for f in os.listdir(images_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]),
#                 'label_files': label_files
#             }
            
#             self.merge_folders.append(folder_info)
#             self.update_folder_list()
#             self.log_merge(f"已添加数据集：{folder_info['name']} (图片数量: {folder_info['images_count']})")
    
#     def remove_folder(self):
#         """删除选中的文件夹"""
#         selection = self.folder_listbox.curselection()
#         if not selection:
#             messagebox.showwarning("警告", "请先选择要删除的文件夹")
#             return
            
#         index = selection[0]
#         folder_name = self.merge_folders[index]['name']
#         del self.merge_folders[index]
#         self.update_folder_list()
#         self.log_merge(f"已删除数据集：{folder_name}")
    
#     def clear_folders(self):
#         """清空文件夹列表"""
#         if self.merge_folders:
#             result = messagebox.askyesno("确认", "确定要清空所有数据集吗？")
#             if result:
#                 self.merge_folders.clear()
#                 self.update_folder_list()
#                 self.log_merge("已清空所有数据集")
    
#     def update_folder_list(self):
#         """更新文件夹列表显示"""
#         self.folder_listbox.delete(0, tk.END)
#         for folder in self.merge_folders:
#             display_text = f"{folder['name']} (图片: {folder['images_count']}, 标签文件: {len(folder['label_files'])})"
#             self.folder_listbox.insert(tk.END, display_text)
    
#     def select_output_dir(self):
#         """选择输出目录"""
#         folder_path = filedialog.askdirectory(title="选择合并输出目录")
#         if folder_path:
#             self.output_dir.set(folder_path)
    
#     def log_merge(self, message):
#         """添加合并日志"""
#         self.merge_log.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n")
#         self.merge_log.see(tk.END)
#         self.root.update()
    
#     def preview_merge(self):
#         """预览合并结果"""
#         if not self.merge_folders:
#             messagebox.showwarning("警告", "请先添加数据集文件夹")
#             return
            
#         total_images = sum(folder['images_count'] for folder in self.merge_folders)
#         total_labels = sum(len(folder['label_files']) for folder in self.merge_folders)
        
#         preview_text = f"合并预览：\n"
#         preview_text += f"数据集数量：{len(self.merge_folders)}\n"
#         preview_text += f"总图片数量：{total_images}\n"
#         preview_text += f"总标签文件数：{total_labels}\n\n"
        
#         preview_text += "详细信息：\n"
#         for i, folder in enumerate(self.merge_folders, 1):
#             preview_text += f"{i}. {folder['name']}\n"
#             preview_text += f"   路径：{folder['path']}\n"
#             preview_text += f"   图片：{folder['images_count']} 张\n"
#             preview_text += f"   标签文件：{', '.join(folder['label_files']) if folder['label_files'] else '无'}\n\n"
        
#         messagebox.showinfo("合并预览", preview_text)
    
#     def merge_datasets(self):
#         """合并数据集"""
#         if not self.merge_folders:
#             messagebox.showwarning("警告", "请先添加数据集文件夹")
#             return
            
#         if not self.output_dir.get():
#             messagebox.showwarning("警告", "请选择输出目录")
#             return
            
#         try:
#             self.merge_btn.config(state="disabled")
#             self.status_var.set("正在合并数据集...")
            
#             output_path = Path(self.output_dir.get())
            
#             # 创建输出目录结构
#             merged_images_dir = output_path / "images"
#             merged_images_dir.mkdir(parents=True, exist_ok=True)
            
#             # 合并统计
#             merged_images = []
#             merged_labels = {}
#             duplicate_count = 0
#             # 文件名映射字典：原始文件名 -> 实际复制后的文件名
#             filename_mapping = {}
#             processed_labels_count = 0
            
#             self.log_merge("开始合并数据集...")
            
#             # 处理每个数据集
#             for folder_idx, folder in enumerate(self.merge_folders):
#                 self.log_merge(f"处理数据集 {folder_idx + 1}/{len(self.merge_folders)}: {folder['name']}")
                
#                 # 当前数据集的文件名映射
#                 current_mapping = {}
                
#                 # 复制图片文件
#                 if self.copy_images.get():
#                     images_src = Path(folder['path']) / "images"
#                     if images_src.exists():
#                         for image_file in images_src.iterdir():
#                             if image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
#                                 original_name = image_file.name
#                                 dest_name = original_name
#                                 dest_path = merged_images_dir / dest_name
                                
#                                 # 处理重复文件名
#                                 counter = 1
#                                 while dest_path.exists():
#                                     if self.rename_duplicates.get():
#                                         name_parts = original_name.rsplit('.', 1)
#                                         if len(name_parts) == 2:
#                                             dest_name = f"{name_parts[0]}_{counter}.{name_parts[1]}"
#                                         else:
#                                             dest_name = f"{original_name}_{counter}"
#                                         dest_path = merged_images_dir / dest_name
#                                         counter += 1
#                                         duplicate_count += 1
#                                     else:
#                                         # 如果不重命名重复文件，跳过这个文件
#                                         self.log_merge(f"跳过重复文件: {original_name}")
#                                         break
#                                 else:
#                                     # 复制文件
#                                     shutil.copy2(image_file, dest_path)
#                                     merged_images.append(dest_name)
#                                     # 记录文件名映射
#                                     current_mapping[original_name] = dest_name
                
#                 # 处理标签文件
#                 for label_file in folder['label_files']:
#                     label_path = Path(folder['path']) / label_file
#                     if label_path.exists():
#                         with open(label_path, 'r', encoding='utf-8') as f:
#                             lines = f.readlines()
                        
#                         self.log_merge(f"处理标签文件: {label_file}, 包含 {len(lines)} 行")
                        
#                         # 更新图片路径并合并标签
#                         for line_num, line in enumerate(lines, 1):
#                             line = line.strip()
#                             if line and '\t' in line:
#                                 parts = line.split('\t', 1)
#                                 if len(parts) == 2:
#                                     old_image_path, label_text = parts
#                                     # 提取图片文件名
#                                     image_name = os.path.basename(old_image_path)
                                    
#                                     # 方法1：直接映射查找
#                                     if image_name in current_mapping:
#                                         actual_image_name = current_mapping[image_name]
#                                         new_image_path = f"images/{actual_image_name}"
                                        
#                                         # 避免重复添加相同的标签
#                                         if new_image_path not in merged_labels:
#                                             merged_labels[new_image_path] = label_text
#                                             processed_labels_count += 1
#                                         else:
#                                             self.log_merge(f"跳过重复标签: {new_image_path}")
#                                     else:
#                                         # 方法2：模糊匹配 - 尝试匹配类似的文件名
#                                         matched_file = None
                                        
#                                         # 提取基础文件名（去除可能的前缀如train_word_, val_word_等）
#                                         base_name = image_name
#                                         for prefix in ['train_word_', 'val_word_', 'word_']:
#                                             if image_name.startswith(prefix):
#                                                 base_name = image_name[len(prefix):]
#                                                 break
                                        
#                                         # 在已复制的文件中查找匹配
#                                         for orig_name, mapped_name in current_mapping.items():
#                                             # 完全匹配
#                                             if orig_name == image_name:
#                                                 matched_file = mapped_name
#                                                 break
#                                             # 基础名称匹配
#                                             elif orig_name.endswith(base_name):
#                                                 matched_file = mapped_name
#                                                 break
#                                             # 反向匹配 - 原始文件名包含标签中的基础名称
#                                             elif base_name in orig_name:
#                                                 matched_file = mapped_name
#                                                 break
                                        
#                                         if matched_file:
#                                             new_image_path = f"images/{matched_file}"
#                                             if new_image_path not in merged_labels:
#                                                 merged_labels[new_image_path] = label_text
#                                                 processed_labels_count += 1
#                                                 self.log_merge(f"模糊匹配成功: {image_name} -> {matched_file}")
#                                             else:
#                                                 self.log_merge(f"跳过重复标签: {new_image_path}")
#                                         else:
#                                             # 方法3：如果还是找不到，尝试按索引匹配
#                                             # 假设标签文件是按顺序生成的，尝试按索引匹配
#                                             if 'word_' in image_name:
#                                                 try:
#                                                     # 提取数字索引
#                                                     import re
#                                                     match = re.search(r'word_(\d+)', image_name)
#                                                     if match:
#                                                         index = int(match.group(1)) - 1  # 转为0基索引
#                                                         if 0 <= index < len(merged_images):
#                                                             matched_file = merged_images[index]
#                                                             new_image_path = f"images/{matched_file}"
#                                                             if new_image_path not in merged_labels:
#                                                                 merged_labels[new_image_path] = label_text
#                                                                 processed_labels_count += 1
#                                                                 self.log_merge(f"索引匹配成功: {image_name} -> {matched_file}")
#                                                             else:
#                                                                 self.log_merge(f"跳过重复标签: {new_image_path}")
#                                                         else:
#                                                             self.log_merge(f"索引超出范围，跳过标签: {image_name}")
#                                                     else:
#                                                         self.log_merge(f"无法提取索引，跳过标签: {image_name}")
#                                                 except:
#                                                     self.log_merge(f"索引匹配失败，跳过标签: {image_name}")
#                                             else:
#                                                 self.log_merge(f"图片未找到，跳过标签: {image_name}")
#                             else:
#                                 if line.strip():  # 只对非空行报告格式错误
#                                     self.log_merge(f"标签格式错误(第{line_num}行): {line[:50]}...")
            
#             self.log_merge(f"图片复制完成，共复制 {len(merged_images)} 张图片")
#             self.log_merge(f"标签处理完成，共处理 {len(merged_labels)} 个标签")
            
#             # 如果没有匹配到任何标签，提供调试信息
#             if len(merged_labels) == 0 and len(merged_images) > 0:
#                 self.log_merge("❌ 没有匹配到任何标签！")
#                 self.log_merge("调试信息：")
#                 self.log_merge(f"复制的图片文件名示例: {merged_images[:5] if merged_images else '无'}")
                
#                 # 显示标签文件中的文件名示例
#                 for folder in self.merge_folders:
#                     for label_file in folder['label_files']:
#                         label_path = Path(folder['path']) / label_file
#                         if label_path.exists():
#                             with open(label_path, 'r', encoding='utf-8') as f:
#                                 lines = f.readlines()[:5]  # 只看前5行
#                             sample_names = []
#                             for line in lines:
#                                 if line.strip() and '\t' in line:
#                                     parts = line.split('\t', 1)
#                                     if len(parts) == 2:
#                                         sample_names.append(os.path.basename(parts[0]))
#                             if sample_names:
#                                 self.log_merge(f"标签文件 {label_file} 中的文件名示例: {sample_names}")
#                                 break
            
#             # 生成合并后的标签文件
#             self.log_merge("生成合并标签文件...")
            
#             # 随机打乱并分割数据
#             label_items = list(merged_labels.items())
#             random.shuffle(label_items)
            
#             train_size = int(len(label_items) * self.train_ratio.get())
#             train_items = label_items[:train_size]
#             val_items = label_items[train_size:]
            
#             # 写入训练集标签文件
#             train_file_path = output_path / self.train_filename.get()
#             with open(train_file_path, 'w', encoding='utf-8') as f:
#                 for image_path, label_text in train_items:
#                     f.write(f"{image_path}\t{label_text}\n")
            
#             # 写入验证集标签文件
#             val_file_path = output_path / self.val_filename.get()
#             with open(val_file_path, 'w', encoding='utf-8') as f:
#                 for image_path, label_text in val_items:
#                     f.write(f"{image_path}\t{label_text}\n")
            
#             # 生成合并摘要
#             if self.create_summary.get():
#                 summary_path = output_path / "merge_summary.txt"
#                 with open(summary_path, 'w', encoding='utf-8') as f:
#                     f.write("数据集合并摘要\n")
#                     f.write("=" * 50 + "\n\n")
#                     f.write(f"合并时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
#                     f.write(f"源数据集数量：{len(self.merge_folders)}\n")
#                     f.write(f"复制图片数量：{len(merged_images)}\n")
#                     f.write(f"有效标签数量：{len(merged_labels)}\n")
#                     f.write(f"重复文件处理数量：{duplicate_count}\n")
#                     f.write(f"训练集样本：{len(train_items)}\n")
#                     f.write(f"验证集样本：{len(val_items)}\n")
#                     f.write(f"训练集比例：{self.train_ratio.get():.1%}\n\n")
                    
#                     # 添加数据一致性检查
#                     f.write("数据一致性检查：\n")
#                     f.write(f"图片与标签匹配率：{len(merged_labels)}/{len(merged_images)} = {len(merged_labels)/max(len(merged_images), 1)*100:.1f}%\n")
#                     if len(merged_labels) != len(merged_images):
#                         f.write("⚠️ 警告：图片数量与标签数量不匹配！\n")
#                     f.write("\n")
                    
#                     f.write("源数据集详情：\n")
#                     for i, folder in enumerate(self.merge_folders, 1):
#                         f.write(f"{i}. {folder['name']}\n")
#                         f.write(f"   路径：{folder['path']}\n")
#                         f.write(f"   图片数：{folder['images_count']}\n")
#                         f.write(f"   标签文件：{', '.join(folder['label_files']) if folder['label_files'] else '无'}\n\n")
            
#             self.log_merge(f"合并完成！")
#             self.log_merge(f"输出目录：{output_path}")
#             self.log_merge(f"复制图片：{len(merged_images)} 张")
#             self.log_merge(f"有效标签：{len(merged_labels)} 个")
#             self.log_merge(f"训练集：{len(train_items)} 样本")
#             self.log_merge(f"验证集：{len(val_items)} 样本")
#             if duplicate_count > 0:
#                 self.log_merge(f"处理重复文件：{duplicate_count} 个")
            
#             # 数据一致性检查
#             if len(merged_labels) != len(merged_images):
#                 self.log_merge(f"⚠️ 警告：图片数量({len(merged_images)})与标签数量({len(merged_labels)})不匹配！")
            
#             self.status_var.set("合并完成")
#             messagebox.showinfo("成功", f"数据集合并完成！\n\n"
#                                       f"输出目录：{output_path}\n"
#                                       f"复制图片：{len(merged_images)} 张\n"
#                                       f"有效标签：{len(merged_labels)} 个\n"
#                                       f"训练集：{len(train_items)} 样本\n"
#                                       f"验证集：{len(val_items)} 样本\n"
#                                       f"匹配率：{len(merged_labels)/max(len(merged_images), 1)*100:.1f}%")
            
#         except Exception as e:
#             self.log_merge(f"合并失败：{str(e)}")
#             messagebox.showerror("错误", f"合并数据集失败：{str(e)}")
            
#         finally:
#             self.merge_btn.config(state="normal")

# def main():
#     root = tk.Tk()
#     app = PaddleOCRLabelGenerator(root)
    
#     # 设置图标（如果有的话）
#     try:
#         root.iconbitmap('icon.ico')  # 可选：添加应用图标
#     except:
#         pass
        
#     root.mainloop()

# if __name__ == "__main__":
#     main()
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import random
import os
from pathlib import Path
import shutil
import datetime

class PaddleOCRLabelGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("PaddleOCR数据集合并")
        self.root.geometry("1000x700")
        
        # 数据存储
        self.json_data = None
        self.generated_files = {'train': '', 'val': ''}
        
        # 配置变量
        self.train_ratio = tk.DoubleVar(value=0.8)
        self.image_prefix = tk.StringVar(value="images/")
        self.image_suffix = tk.StringVar(value=".jpg")
        self.train_filename = tk.StringVar(value="train.txt")
        self.val_filename = tk.StringVar(value="val.txt")
        
        # 合并数据存储
        self.merge_folders = []
        
        self.setup_ui()
        
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="PaddleOCR数据集合并", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # 创建选项卡
        self.setup_tabs(main_frame)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                               relief=tk.SUNKEN, anchor=tk.W)
        status_label.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def setup_tabs(self, parent):
        """设置选项卡"""
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        parent.rowconfigure(1, weight=1)
        
        # 创建两个选项卡
        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab1, text="标签文件生成")
        self.notebook.add(self.tab2, text="数据集合并")
        
        # 设置选项卡内容
        self.setup_tab1()
        self.setup_tab2()
        
    def setup_tab1(self):
        """设置第一个选项卡：标签文件生成"""
        # 配置选项卡内的网格
        self.tab1.columnconfigure(0, weight=1)
        
        # 文件上传区域
        upload_frame = ttk.LabelFrame(self.tab1, text="文件上传", padding="10")
        upload_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        upload_frame.columnconfigure(1, weight=1)
        
        ttk.Label(upload_frame, text="JSON文件:").grid(row=0, column=0, sticky=tk.W)
        self.file_path = tk.StringVar()
        self.file_entry = ttk.Entry(upload_frame, textvariable=self.file_path, state="readonly")
        self.file_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 10))
        
        ttk.Button(upload_frame, text="选择文件", 
                  command=self.select_file).grid(row=0, column=2)
        
        self.file_info = ttk.Label(upload_frame, text="", foreground="green")
        self.file_info.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # 配置区域
        config_frame = ttk.LabelFrame(self.tab1, text="生成配置", padding="10")
        config_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        config_frame.columnconfigure(3, weight=1)
        
        # 第一行配置
        ttk.Label(config_frame, text="训练集比例:").grid(row=0, column=0, sticky=tk.W)
        train_ratio_spin = ttk.Spinbox(config_frame, from_=0.1, to=0.9, increment=0.1,
                                      textvariable=self.train_ratio, width=10)
        train_ratio_spin.grid(row=0, column=1, sticky=tk.W, padx=(10, 20))
        
        ttk.Label(config_frame, text="图片路径前缀:").grid(row=0, column=2, sticky=tk.W)
        ttk.Entry(config_frame, textvariable=self.image_prefix, width=15).grid(row=0, column=3, sticky=tk.W, padx=(10, 0))
        
        # 第二行配置
        ttk.Label(config_frame, text="图片文件后缀:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        ttk.Entry(config_frame, textvariable=self.image_suffix, width=10).grid(row=1, column=1, sticky=tk.W, padx=(10, 20), pady=(10, 0))
        
        # 第三行配置
        ttk.Label(config_frame, text="训练集文件名:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        ttk.Entry(config_frame, textvariable=self.train_filename, width=15).grid(row=2, column=1, sticky=tk.W, padx=(10, 20), pady=(10, 0))
        
        ttk.Label(config_frame, text="验证集文件名:").grid(row=2, column=2, sticky=tk.W, pady=(10, 0))
        ttk.Entry(config_frame, textvariable=self.val_filename, width=15).grid(row=2, column=3, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        
        # 生成按钮
        button_frame = ttk.Frame(self.tab1)
        button_frame.grid(row=2, column=0, pady=10)
        
        self.generate_btn = ttk.Button(button_frame, text="生成标签文件", 
                                      command=self.generate_label_files)
        self.generate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="下载所有文件", 
                  command=self.download_all_files).pack(side=tk.LEFT)
        
        # 预览区域
        preview_frame = ttk.LabelFrame(self.tab1, text="文件预览", padding="10")
        preview_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.columnconfigure(1, weight=1)
        preview_frame.rowconfigure(1, weight=1)
        self.tab1.rowconfigure(3, weight=1)
        
        # 训练集预览
        train_frame = ttk.Frame(preview_frame)
        train_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        train_frame.columnconfigure(0, weight=1)
        train_frame.rowconfigure(1, weight=1)
        
        train_header = ttk.Frame(train_frame)
        train_header.grid(row=0, column=0, sticky=(tk.W, tk.E))
        train_header.columnconfigure(0, weight=1)
        
        ttk.Label(train_header, text="训练集预览", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W)
        ttk.Button(train_header, text="下载", 
                  command=lambda: self.download_file('train')).grid(row=0, column=1)
        
        self.train_text = scrolledtext.ScrolledText(train_frame, height=15, font=("Consolas", 9))
        self.train_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        
        # 验证集预览
        val_frame = ttk.Frame(preview_frame)
        val_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        val_frame.columnconfigure(0, weight=1)
        val_frame.rowconfigure(1, weight=1)
        
        val_header = ttk.Frame(val_frame)
        val_header.grid(row=0, column=0, sticky=(tk.W, tk.E))
        val_header.columnconfigure(0, weight=1)
        
        ttk.Label(val_header, text="验证集预览", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W)
        ttk.Button(val_header, text="下载", 
                  command=lambda: self.download_file('val')).grid(row=0, column=1)
        
        self.val_text = scrolledtext.ScrolledText(val_frame, height=15, font=("Consolas", 9))
        self.val_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        
    def setup_tab2(self):
        """设置第二个选项卡：数据集合并"""
        # 配置选项卡内的网格
        self.tab2.columnconfigure(0, weight=1)
        
        # 文件夹选择区域
        folder_frame = ttk.LabelFrame(self.tab2, text="选择数据集文件夹", padding="10")
        folder_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        folder_frame.columnconfigure(0, weight=1)
        
        # 文件夹列表
        self.folder_listbox = tk.Listbox(folder_frame, height=8)
        self.folder_listbox.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 滚动条
        scrollbar = ttk.Scrollbar(folder_frame, orient="vertical", command=self.folder_listbox.yview)
        scrollbar.grid(row=0, column=3, sticky=(tk.N, tk.S))
        self.folder_listbox.config(yscrollcommand=scrollbar.set)
        
        # 按钮区域
        folder_button_frame = ttk.Frame(folder_frame)
        folder_button_frame.grid(row=1, column=0, columnspan=4, pady=(10, 0))
        
        ttk.Button(folder_button_frame, text="添加文件夹", 
                  command=self.add_folder).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(folder_button_frame, text="删除选中", 
                  command=self.remove_folder).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(folder_button_frame, text="清空列表", 
                  command=self.clear_folders).pack(side=tk.LEFT)
        
        # 合并配置区域
        merge_config_frame = ttk.LabelFrame(self.tab2, text="合并配置", padding="10")
        merge_config_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        merge_config_frame.columnconfigure(1, weight=1)
        
        # 输出目录
        ttk.Label(merge_config_frame, text="输出目录:").grid(row=0, column=0, sticky=tk.W)
        self.output_dir = tk.StringVar()
        self.output_entry = ttk.Entry(merge_config_frame, textvariable=self.output_dir, state="readonly")
        self.output_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 10))
        ttk.Button(merge_config_frame, text="选择目录", 
                  command=self.select_output_dir).grid(row=0, column=2)
        
        # 合并选项
        self.copy_images = tk.BooleanVar(value=True)
        self.rename_duplicates = tk.BooleanVar(value=True)
        self.create_summary = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(merge_config_frame, text="复制图片文件", 
                       variable=self.copy_images).grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        ttk.Checkbutton(merge_config_frame, text="自动重命名重复文件", 
                       variable=self.rename_duplicates).grid(row=1, column=1, sticky=tk.W, pady=(10, 0))
        ttk.Checkbutton(merge_config_frame, text="生成合并摘要", 
                       variable=self.create_summary).grid(row=1, column=2, sticky=tk.W, pady=(10, 0))
        
        # 合并按钮
        merge_button_frame = ttk.Frame(self.tab2)
        merge_button_frame.grid(row=2, column=0, pady=10)
        
        self.merge_btn = ttk.Button(merge_button_frame, text="开始合并", 
                                   command=self.merge_datasets)
        self.merge_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(merge_button_frame, text="预览合并结果", 
                  command=self.preview_merge).pack(side=tk.LEFT)
        
        # 合并日志区域
        log_frame = ttk.LabelFrame(self.tab2, text="合并日志", padding="10")
        log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.tab2.rowconfigure(3, weight=1)
        
        self.merge_log = scrolledtext.ScrolledText(log_frame, height=12, font=("Consolas", 9))
        self.merge_log.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="选择JSON文件",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            self.file_path.set(file_path)
            self.load_json_file(file_path)
            
    def load_json_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.json_data = json.load(f)
                
            if 'labels' not in self.json_data:
                messagebox.showerror("错误", "JSON文件中缺少'labels'字段")
                return
                
            num_labels = len(self.json_data['labels'])
            # 检查是否有filenames字段
            has_filenames = 'filenames' in self.json_data
            self.file_info.config(text=f"✓ 已加载 {num_labels} 个标签 {'(包含文件名映射)' if has_filenames else '(无文件名映射)'}")
            self.status_var.set(f"已加载JSON文件，包含 {num_labels} 个标签")
            
        except Exception as e:
            messagebox.showerror("错误", f"加载JSON文件失败：{str(e)}")
            self.json_data = None
            
    def generate_label_files(self):
        if not self.json_data or 'labels' not in self.json_data:
            messagebox.showwarning("警告", "请先加载有效的JSON文件")
            return
            
        try:
            self.status_var.set("正在生成标签文件...")
            self.root.update()
            
            # 获取所有标签条目
            label_entries = list(self.json_data['labels'].items())
            
            # 检查是否有filenames字段
            has_filenames = 'filenames' in self.json_data
            
            # 随机打乱数据
            random.shuffle(label_entries)
            
            # 计算训练集大小
            train_size = int(len(label_entries) * self.train_ratio.get())
            
            # 分割训练集和验证集
            train_entries = label_entries[:train_size]
            val_entries = label_entries[train_size:]
            
            # 生成训练集文件内容
            train_lines = []
            for i, (label_id, label_text) in enumerate(train_entries):
                if has_filenames and label_id in self.json_data['filenames']:
                    # 使用实际的文件名
                    actual_filename = self.json_data['filenames'][label_id]
                    image_filename = actual_filename
                else:
                    # 使用默认的文件名格式
                    image_filename = f"{label_id}{self.image_suffix.get()}"
                
                line = f"{self.image_prefix.get()}{image_filename}\t{label_text}"
                train_lines.append(line)
            
            # 生成验证集文件内容
            val_lines = []
            for i, (label_id, label_text) in enumerate(val_entries):
                if has_filenames and label_id in self.json_data['filenames']:
                    # 使用实际的文件名
                    actual_filename = self.json_data['filenames'][label_id]
                    image_filename = actual_filename
                else:
                    # 使用默认的文件名格式
                    image_filename = f"{label_id}{self.image_suffix.get()}"
                
                line = f"{self.image_prefix.get()}{image_filename}\t{label_text}"
                val_lines.append(line)
            
            # 存储生成的内容
            self.generated_files['train'] = '\n'.join(train_lines)
            self.generated_files['val'] = '\n'.join(val_lines)
            
            # 更新预览
            self.update_preview()
            
            filename_type = "实际文件名" if has_filenames else "默认文件名"
            self.status_var.set(f"生成完成！训练集: {len(train_lines)} 条，验证集: {len(val_lines)} 条 (使用{filename_type})")
            
        except Exception as e:
            messagebox.showerror("错误", f"生成标签文件失败：{str(e)}")
            self.status_var.set("生成失败")
            
    def update_preview(self):
        # 更新训练集预览
        self.train_text.delete(1.0, tk.END)
        self.train_text.insert(1.0, self.generated_files['train'])
        
        # 更新验证集预览
        self.val_text.delete(1.0, tk.END)
        self.val_text.insert(1.0, self.generated_files['val'])
        
    def download_file(self, file_type):
        if not self.generated_files[file_type]:
            messagebox.showwarning("警告", "请先生成标签文件")
            return
            
        filename = self.train_filename.get() if file_type == 'train' else self.val_filename.get()
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialvalue=filename,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.generated_files[file_type])
                messagebox.showinfo("成功", f"文件已保存到：{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存文件失败：{str(e)}")
                
    def download_all_files(self):
        if not self.generated_files['train'] or not self.generated_files['val']:
            messagebox.showwarning("警告", "请先生成标签文件")
            return
            
        folder_path = filedialog.askdirectory(title="选择保存文件夹")
        
        if folder_path:
            try:
                # 保存训练集文件
                train_path = os.path.join(folder_path, self.train_filename.get())
                with open(train_path, 'w', encoding='utf-8') as f:
                    f.write(self.generated_files['train'])
                    
                # 保存验证集文件
                val_path = os.path.join(folder_path, self.val_filename.get())
                with open(val_path, 'w', encoding='utf-8') as f:
                    f.write(self.generated_files['val'])
                    
                messagebox.showinfo("成功", f"文件已保存到：\n{train_path}\n{val_path}")
                
            except Exception as e:
                messagebox.showerror("错误", f"保存文件失败：{str(e)}")

    # 数据集合并相关方法 (保持原有功能)
    def add_folder(self):
        """添加数据集文件夹"""
        folder_path = filedialog.askdirectory(title="选择数据集文件夹")
        if folder_path:
            # 检查文件夹结构
            images_path = os.path.join(folder_path, "images")
            if not os.path.exists(images_path):
                messagebox.showwarning("警告", f"文件夹中没有找到images目录：\n{folder_path}")
                return
                
            # 查找标签文件
            label_files = []
            for file in os.listdir(folder_path):
                if file.endswith('.txt') and ('train' in file.lower() or 'val' in file.lower() or 'label' in file.lower()):
                    label_files.append(file)
            
            if not label_files:
                result = messagebox.askyesno("确认", f"在文件夹中未找到标签文件，是否仍要添加？\n{folder_path}")
                if not result:
                    return
            
            # 添加到列表
            folder_info = {
                'path': folder_path,
                'name': os.path.basename(folder_path),
                'images_count': len([f for f in os.listdir(images_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]),
                'label_files': label_files
            }
            
            self.merge_folders.append(folder_info)
            self.update_folder_list()
            self.log_merge(f"已添加数据集：{folder_info['name']} (图片数量: {folder_info['images_count']})")
    
    def remove_folder(self):
        """删除选中的文件夹"""
        selection = self.folder_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的文件夹")
            return
            
        index = selection[0]
        folder_name = self.merge_folders[index]['name']
        del self.merge_folders[index]
        self.update_folder_list()
        self.log_merge(f"已删除数据集：{folder_name}")
    
    def clear_folders(self):
        """清空文件夹列表"""
        if self.merge_folders:
            result = messagebox.askyesno("确认", "确定要清空所有数据集吗？")
            if result:
                self.merge_folders.clear()
                self.update_folder_list()
                self.log_merge("已清空所有数据集")
    
    def update_folder_list(self):
        """更新文件夹列表显示"""
        self.folder_listbox.delete(0, tk.END)
        for folder in self.merge_folders:
            display_text = f"{folder['name']} (图片: {folder['images_count']}, 标签文件: {len(folder['label_files'])})"
            self.folder_listbox.insert(tk.END, display_text)
    
    def select_output_dir(self):
        """选择输出目录"""
        folder_path = filedialog.askdirectory(title="选择合并输出目录")
        if folder_path:
            self.output_dir.set(folder_path)
    
    def log_merge(self, message):
        """添加合并日志"""
        self.merge_log.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.merge_log.see(tk.END)
        self.root.update()
    
    def preview_merge(self):
        """预览合并结果"""
        if not self.merge_folders:
            messagebox.showwarning("警告", "请先添加数据集文件夹")
            return
            
        total_images = sum(folder['images_count'] for folder in self.merge_folders)
        total_labels = sum(len(folder['label_files']) for folder in self.merge_folders)
        
        preview_text = f"合并预览：\n"
        preview_text += f"数据集数量：{len(self.merge_folders)}\n"
        preview_text += f"总图片数量：{total_images}\n"
        preview_text += f"总标签文件数：{total_labels}\n\n"
        
        preview_text += "详细信息：\n"
        for i, folder in enumerate(self.merge_folders, 1):
            preview_text += f"{i}. {folder['name']}\n"
            preview_text += f"   路径：{folder['path']}\n"
            preview_text += f"   图片：{folder['images_count']} 张\n"
            preview_text += f"   标签文件：{', '.join(folder['label_files']) if folder['label_files'] else '无'}\n\n"
        
        messagebox.showinfo("合并预览", preview_text)
    
    def merge_datasets(self):
        """合并数据集"""
        if not self.merge_folders:
            messagebox.showwarning("警告", "请先添加数据集文件夹")
            return
            
        if not self.output_dir.get():
            messagebox.showwarning("警告", "请选择输出目录")
            return
            
        try:
            self.merge_btn.config(state="disabled")
            self.status_var.set("正在合并数据集...")
            
            output_path = Path(self.output_dir.get())
            
            # 创建输出目录结构
            merged_images_dir = output_path / "images"
            merged_images_dir.mkdir(parents=True, exist_ok=True)
            
            # 合并统计
            merged_images = []
            merged_labels = {}
            duplicate_count = 0
            # 文件名映射字典：原始文件名 -> 实际复制后的文件名
            filename_mapping = {}
            processed_labels_count = 0
            
            self.log_merge("开始合并数据集...")
            
            # 处理每个数据集
            for folder_idx, folder in enumerate(self.merge_folders):
                self.log_merge(f"处理数据集 {folder_idx + 1}/{len(self.merge_folders)}: {folder['name']}")
                
                # 当前数据集的文件名映射
                current_mapping = {}
                
                # 复制图片文件
                if self.copy_images.get():
                    images_src = Path(folder['path']) / "images"
                    if images_src.exists():
                        for image_file in images_src.iterdir():
                            if image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                                original_name = image_file.name
                                dest_name = original_name
                                dest_path = merged_images_dir / dest_name
                                
                                # 处理重复文件名
                                counter = 1
                                while dest_path.exists():
                                    if self.rename_duplicates.get():
                                        name_parts = original_name.rsplit('.', 1)
                                        if len(name_parts) == 2:
                                            dest_name = f"{name_parts[0]}_{counter}.{name_parts[1]}"
                                        else:
                                            dest_name = f"{original_name}_{counter}"
                                        dest_path = merged_images_dir / dest_name
                                        counter += 1
                                        duplicate_count += 1
                                    else:
                                        # 如果不重命名重复文件，跳过这个文件
                                        self.log_merge(f"跳过重复文件: {original_name}")
                                        break
                                else:
                                    # 复制文件
                                    shutil.copy2(image_file, dest_path)
                                    merged_images.append(dest_name)
                                    # 记录文件名映射
                                    current_mapping[original_name] = dest_name
                
                # 处理标签文件
                for label_file in folder['label_files']:
                    label_path = Path(folder['path']) / label_file
                    if label_path.exists():
                        with open(label_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                        
                        self.log_merge(f"处理标签文件: {label_file}, 包含 {len(lines)} 行")
                        
                        # 更新图片路径并合并标签
                        for line_num, line in enumerate(lines, 1):
                            line = line.strip()
                            if line and '\t' in line:
                                parts = line.split('\t', 1)
                                if len(parts) == 2:
                                    old_image_path, label_text = parts
                                    # 提取图片文件名
                                    image_name = os.path.basename(old_image_path)
                                    
                                    # 方法1：直接映射查找
                                    if image_name in current_mapping:
                                        actual_image_name = current_mapping[image_name]
                                        new_image_path = f"images/{actual_image_name}"
                                        
                                        # 避免重复添加相同的标签
                                        if new_image_path not in merged_labels:
                                            merged_labels[new_image_path] = label_text
                                            processed_labels_count += 1
                                        else:
                                            self.log_merge(f"跳过重复标签: {new_image_path}")
                                    else:
                                        # 方法2：模糊匹配 - 尝试匹配类似的文件名
                                        matched_file = None
                                        
                                        # 提取基础文件名（去除可能的前缀如train_word_, val_word_等）
                                        base_name = image_name
                                        for prefix in ['train_word_', 'val_word_', 'word_']:
                                            if image_name.startswith(prefix):
                                                base_name = image_name[len(prefix):]
                                                break
                                        
                                        # 在已复制的文件中查找匹配
                                        for orig_name, mapped_name in current_mapping.items():
                                            # 完全匹配
                                            if orig_name == image_name:
                                                matched_file = mapped_name
                                                break
                                            # 基础名称匹配
                                            elif orig_name.endswith(base_name):
                                                matched_file = mapped_name
                                                break
                                            # 反向匹配 - 原始文件名包含标签中的基础名称
                                            elif base_name in orig_name:
                                                matched_file = mapped_name
                                                break
                                        
                                        if matched_file:
                                            new_image_path = f"images/{matched_file}"
                                            if new_image_path not in merged_labels:
                                                merged_labels[new_image_path] = label_text
                                                processed_labels_count += 1
                                                self.log_merge(f"模糊匹配成功: {image_name} -> {matched_file}")
                                            else:
                                                self.log_merge(f"跳过重复标签: {new_image_path}")
                                        else:
                                            # 方法3：如果还是找不到，尝试按索引匹配
                                            # 假设标签文件是按顺序生成的，尝试按索引匹配
                                            if 'word_' in image_name:
                                                try:
                                                    # 提取数字索引
                                                    import re
                                                    match = re.search(r'word_(\d+)', image_name)
                                                    if match:
                                                        index = int(match.group(1)) - 1  # 转为0基索引
                                                        if 0 <= index < len(merged_images):
                                                            matched_file = merged_images[index]
                                                            new_image_path = f"images/{matched_file}"
                                                            if new_image_path not in merged_labels:
                                                                merged_labels[new_image_path] = label_text
                                                                processed_labels_count += 1
                                                                self.log_merge(f"索引匹配成功: {image_name} -> {matched_file}")
                                                            else:
                                                                self.log_merge(f"跳过重复标签: {new_image_path}")
                                                        else:
                                                            self.log_merge(f"索引超出范围，跳过标签: {image_name}")
                                                    else:
                                                        self.log_merge(f"无法提取索引，跳过标签: {image_name}")
                                                except:
                                                    self.log_merge(f"索引匹配失败，跳过标签: {image_name}")
                                            else:
                                                self.log_merge(f"图片未找到，跳过标签: {image_name}")
                            else:
                                if line.strip():  # 只对非空行报告格式错误
                                    self.log_merge(f"标签格式错误(第{line_num}行): {line[:50]}...")
            
            self.log_merge(f"图片复制完成，共复制 {len(merged_images)} 张图片")
            self.log_merge(f"标签处理完成，共处理 {len(merged_labels)} 个标签")
            
            # 如果没有匹配到任何标签，提供调试信息
            if len(merged_labels) == 0 and len(merged_images) > 0:
                self.log_merge("❌ 没有匹配到任何标签！")
                self.log_merge("调试信息：")
                self.log_merge(f"复制的图片文件名示例: {merged_images[:5] if merged_images else '无'}")
                
                # 显示标签文件中的文件名示例
                for folder in self.merge_folders:
                    for label_file in folder['label_files']:
                        label_path = Path(folder['path']) / label_file
                        if label_path.exists():
                            with open(label_path, 'r', encoding='utf-8') as f:
                                lines = f.readlines()[:5]  # 只看前5行
                            sample_names = []
                            for line in lines:
                                if line.strip() and '\t' in line:
                                    parts = line.split('\t', 1)
                                    if len(parts) == 2:
                                        sample_names.append(os.path.basename(parts[0]))
                            if sample_names:
                                self.log_merge(f"标签文件 {label_file} 中的文件名示例: {sample_names}")
                                break
            
            # 生成合并后的标签文件
            self.log_merge("生成合并标签文件...")
            
            # 随机打乱并分割数据
            label_items = list(merged_labels.items())
            random.shuffle(label_items)
            
            train_size = int(len(label_items) * self.train_ratio.get())
            train_items = label_items[:train_size]
            val_items = label_items[train_size:]
            
            # 写入训练集标签文件
            train_file_path = output_path / self.train_filename.get()
            with open(train_file_path, 'w', encoding='utf-8') as f:
                for image_path, label_text in train_items:
                    f.write(f"{image_path}\t{label_text}\n")
            
            # 写入验证集标签文件
            val_file_path = output_path / self.val_filename.get()
            with open(val_file_path, 'w', encoding='utf-8') as f:
                for image_path, label_text in val_items:
                    f.write(f"{image_path}\t{label_text}\n")
            
            # 生成合并摘要
            if self.create_summary.get():
                summary_path = output_path / "merge_summary.txt"
                with open(summary_path, 'w', encoding='utf-8') as f:
                    f.write("数据集合并摘要\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"合并时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"源数据集数量：{len(self.merge_folders)}\n")
                    f.write(f"复制图片数量：{len(merged_images)}\n")
                    f.write(f"有效标签数量：{len(merged_labels)}\n")
                    f.write(f"重复文件处理数量：{duplicate_count}\n")
                    f.write(f"训练集样本：{len(train_items)}\n")
                    f.write(f"验证集样本：{len(val_items)}\n")
                    f.write(f"训练集比例：{self.train_ratio.get():.1%}\n\n")
                    
                    # 添加数据一致性检查
                    f.write("数据一致性检查：\n")
                    f.write(f"图片与标签匹配率：{len(merged_labels)}/{len(merged_images)} = {len(merged_labels)/max(len(merged_images), 1)*100:.1f}%\n")
                    if len(merged_labels) != len(merged_images):
                        f.write("⚠️ 警告：图片数量与标签数量不匹配！\n")
                    f.write("\n")
                    
                    f.write("源数据集详情：\n")
                    for i, folder in enumerate(self.merge_folders, 1):
                        f.write(f"{i}. {folder['name']}\n")
                        f.write(f"   路径：{folder['path']}\n")
                        f.write(f"   图片数：{folder['images_count']}\n")
                        f.write(f"   标签文件：{', '.join(folder['label_files']) if folder['label_files'] else '无'}\n\n")
            
            self.log_merge(f"合并完成！")
            self.log_merge(f"输出目录：{output_path}")
            self.log_merge(f"复制图片：{len(merged_images)} 张")
            self.log_merge(f"有效标签：{len(merged_labels)} 个")
            self.log_merge(f"训练集：{len(train_items)} 样本")
            self.log_merge(f"验证集：{len(val_items)} 样本")
            if duplicate_count > 0:
                self.log_merge(f"处理重复文件：{duplicate_count} 个")
            
            # 数据一致性检查
            if len(merged_labels) != len(merged_images):
                self.log_merge(f"⚠️ 警告：图片数量({len(merged_images)})与标签数量({len(merged_labels)})不匹配！")
            
            self.status_var.set("合并完成")
            messagebox.showinfo("成功", f"数据集合并完成！\n\n"
                                      f"输出目录：{output_path}\n"
                                      f"复制图片：{len(merged_images)} 张\n"
                                      f"有效标签：{len(merged_labels)} 个\n"
                                      f"训练集：{len(train_items)} 样本\n"
                                      f"验证集：{len(val_items)} 样本\n"
                                      f"匹配率：{len(merged_labels)/max(len(merged_images), 1)*100:.1f}%")
            
        except Exception as e:
            self.log_merge(f"合并失败：{str(e)}")
            messagebox.showerror("错误", f"合并数据集失败：{str(e)}")
            
        finally:
            self.merge_btn.config(state="normal")

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
    main()