import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageDraw, ImageFont, ImageTk
import os
import io
import json
import random
import re

class DimensionGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("工程尺寸标注生成")
        self.root.geometry("1000x850")
        self.root.resizable(True, True)
        
        # 当前预览图像
        self.current_image = None
        self.preview_photo = None
        
        self.setup_ui()
        self.update_preview()  # 初始预览
    
    def setup_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(9, weight=1)
        
        # 生成模式选择
        mode_frame = ttk.LabelFrame(main_frame, text="生成模式", padding="10")
        mode_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.mode_var = tk.StringVar(value="single")
        ttk.Radiobutton(mode_frame, text="单个生成", variable=self.mode_var, 
                       value="single", command=self.on_mode_change).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(mode_frame, text="批量生成", variable=self.mode_var, 
                       value="batch", command=self.on_mode_change).pack(side=tk.LEFT)
        
        # 参数输入区域
        params_frame = ttk.LabelFrame(main_frame, text="参数设置", padding="10")
        params_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 单个模式的参数
        self.single_frame = ttk.Frame(params_frame)
        self.single_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 主尺寸
        ttk.Label(self.single_frame, text="主尺寸:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.main_value_var = tk.StringVar(value="⌀5.00")
        self.main_value_entry = ttk.Entry(self.single_frame, textvariable=self.main_value_var, width=15)
        self.main_value_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 20))
        self.main_value_var.trace('w', self.on_param_change)
        
        # 上公差
        ttk.Label(self.single_frame, text="上公差:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.tol_upper_var = tk.StringVar(value="0.05")
        self.tol_upper_entry = ttk.Entry(self.single_frame, textvariable=self.tol_upper_var, width=10)
        self.tol_upper_entry.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(0, 20))
        self.tol_upper_var.trace('w', self.on_param_change)
        
        # 下公差
        ttk.Label(self.single_frame, text="下公差:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.tol_lower_var = tk.StringVar(value="-0.10")
        self.tol_lower_entry = ttk.Entry(self.single_frame, textvariable=self.tol_lower_var, width=10)
        self.tol_lower_entry.grid(row=0, column=5, sticky=(tk.W, tk.E))
        self.tol_lower_var.trace('w', self.on_param_change)
        
        # 批量模式的参数
        self.batch_frame = ttk.Frame(params_frame)
        
        # 主尺寸区间
        ttk.Label(self.batch_frame, text="主尺寸范围:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        # 主尺寸前缀
        ttk.Label(self.batch_frame, text="前缀:").grid(row=0, column=1, sticky=tk.W, padx=(0, 5))
        self.main_prefix_var = tk.StringVar(value="⌀")
        self.main_prefix_entry = ttk.Entry(self.batch_frame, textvariable=self.main_prefix_var, width=5)
        self.main_prefix_entry.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Label(self.batch_frame, text="从:").grid(row=0, column=3, sticky=tk.W, padx=(0, 5))
        self.main_min_var = tk.DoubleVar(value=1.0)
        self.main_min_spinbox = ttk.Spinbox(self.batch_frame, from_=0.1, to=1000, 
                                           textvariable=self.main_min_var, width=8, increment=0.1)
        self.main_min_spinbox.grid(row=0, column=4, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Label(self.batch_frame, text="到:").grid(row=0, column=5, sticky=tk.W, padx=(0, 5))
        self.main_max_var = tk.DoubleVar(value=10.0)
        self.main_max_spinbox = ttk.Spinbox(self.batch_frame, from_=0.1, to=1000, 
                                           textvariable=self.main_max_var, width=8, increment=0.1)
        self.main_max_spinbox.grid(row=0, column=6, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 上公差区间
        ttk.Label(self.batch_frame, text="上公差范围:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Label(self.batch_frame, text="从:").grid(row=1, column=1, sticky=tk.W, padx=(0, 5))
        self.upper_min_var = tk.DoubleVar(value=0.01)
        self.upper_min_spinbox = ttk.Spinbox(self.batch_frame, from_=-1.0, to=1.0, 
                                            textvariable=self.upper_min_var, width=8, increment=0.01)
        self.upper_min_spinbox.grid(row=1, column=2, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Label(self.batch_frame, text="到:").grid(row=1, column=3, sticky=tk.W, padx=(0, 5))
        self.upper_max_var = tk.DoubleVar(value=0.10)
        self.upper_max_spinbox = ttk.Spinbox(self.batch_frame, from_=-1.0, to=1.0, 
                                            textvariable=self.upper_max_var, width=8, increment=0.01)
        self.upper_max_spinbox.grid(row=1, column=4, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 下公差区间
        ttk.Label(self.batch_frame, text="下公差范围:").grid(row=1, column=5, sticky=tk.W, padx=(0, 5))
        ttk.Label(self.batch_frame, text="从:").grid(row=1, column=6, sticky=tk.W, padx=(0, 5))
        self.lower_min_var = tk.DoubleVar(value=-0.10)
        self.lower_min_spinbox = ttk.Spinbox(self.batch_frame, from_=-1.0, to=1.0, 
                                            textvariable=self.lower_min_var, width=8, increment=0.01)
        self.lower_min_spinbox.grid(row=1, column=7, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Label(self.batch_frame, text="到:").grid(row=2, column=6, sticky=tk.W, padx=(0, 5))
        self.lower_max_var = tk.DoubleVar(value=-0.01)
        self.lower_max_spinbox = ttk.Spinbox(self.batch_frame, from_=-1.0, to=1.0, 
                                            textvariable=self.lower_max_var, width=8, increment=0.01)
        self.lower_max_spinbox.grid(row=2, column=7, sticky=(tk.W, tk.E), padx=(0, 5))
        
        # 批量生成数量
        ttk.Label(self.batch_frame, text="生成数量:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        self.batch_count_var = tk.IntVar(value=50)
        self.batch_count_spinbox = ttk.Spinbox(self.batch_frame, from_=1, to=1000, 
                                              textvariable=self.batch_count_var, width=8)
        self.batch_count_spinbox.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        # 配置params_frame的列权重
        for i in range(8):
            params_frame.columnconfigure(i, weight=1)
        
        # 尺寸设置
        size_frame = ttk.LabelFrame(main_frame, text="图像尺寸", padding="10")
        size_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 宽度
        ttk.Label(size_frame, text="宽度:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.width_var = tk.IntVar(value=134)
        self.width_spinbox = ttk.Spinbox(size_frame, from_=50, to=500, textvariable=self.width_var, width=10)
        self.width_spinbox.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 20))
        self.width_var.trace('w', self.on_param_change)
        
        # 高度
        ttk.Label(size_frame, text="高度:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.height_var = tk.IntVar(value=40)
        self.height_spinbox = ttk.Spinbox(size_frame, from_=20, to=200, textvariable=self.height_var, width=10)
        self.height_spinbox.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(0, 20))
        self.height_var.trace('w', self.on_param_change)
        
        # 字体设置
        font_frame = ttk.LabelFrame(main_frame, text="字体设置", padding="10")
        font_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 主字体大小
        ttk.Label(font_frame, text="主字体大小:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.font_main_size_var = tk.IntVar(value=28)
        self.font_main_spinbox = ttk.Spinbox(font_frame, from_=10, to=50, textvariable=self.font_main_size_var, width=10)
        self.font_main_spinbox.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 20))
        self.font_main_size_var.trace('w', self.on_param_change)
        
        # 公差字体大小
        ttk.Label(font_frame, text="公差字体大小:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.font_tol_size_var = tk.IntVar(value=16)
        self.font_tol_spinbox = ttk.Spinbox(font_frame, from_=8, to=30, textvariable=self.font_tol_size_var, width=10)
        self.font_tol_spinbox.grid(row=0, column=3, sticky=(tk.W, tk.E))
        self.font_tol_size_var.trace('w', self.on_param_change)
        
        # 位置调整区域
        position_frame = ttk.LabelFrame(main_frame, text="位置调整 (像素)", padding="10")
        position_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 主尺寸位置
        ttk.Label(position_frame, text="主尺寸 X:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.main_x_var = tk.IntVar(value=5)
        self.main_x_spinbox = ttk.Spinbox(position_frame, from_=-50, to=200, textvariable=self.main_x_var, width=8)
        self.main_x_spinbox.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        self.main_x_var.trace('w', self.on_param_change)
        
        ttk.Label(position_frame, text="Y:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.main_y_var = tk.StringVar(value="4")
        self.main_y_entry = ttk.Entry(position_frame, textvariable=self.main_y_var, width=8)
        self.main_y_entry.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(0, 20))
        self.main_y_var.trace('w', self.on_param_change)
        
        # 上公差位置
        ttk.Label(position_frame, text="上公差 X:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        self.upper_x_var = tk.StringVar(value="98")
        self.upper_x_entry = ttk.Entry(position_frame, textvariable=self.upper_x_var, width=8)
        self.upper_x_entry.grid(row=0, column=5, sticky=(tk.W, tk.E), padx=(0, 10))
        self.upper_x_var.trace('w', self.on_param_change)
        
        ttk.Label(position_frame, text="Y:").grid(row=0, column=6, sticky=tk.W, padx=(0, 5))
        self.upper_y_var = tk.IntVar(value=2)
        self.upper_y_spinbox = ttk.Spinbox(position_frame, from_=-20, to=100, textvariable=self.upper_y_var, width=8)
        self.upper_y_spinbox.grid(row=0, column=7, sticky=(tk.W, tk.E))
        self.upper_y_var.trace('w', self.on_param_change)
        
        # 下公差位置
        ttk.Label(position_frame, text="下公差 X:").grid(row=1, column=4, sticky=tk.W, padx=(0, 5))
        self.lower_x_var = tk.StringVar(value="90")
        self.lower_x_entry = ttk.Entry(position_frame, textvariable=self.lower_x_var, width=8)
        self.lower_x_entry.grid(row=1, column=5, sticky=(tk.W, tk.E), padx=(0, 10))
        self.lower_x_var.trace('w', self.on_param_change)
        
        ttk.Label(position_frame, text="Y:").grid(row=1, column=6, sticky=tk.W, padx=(0, 5))
        self.lower_y_var = tk.StringVar(value="17")
        self.lower_y_entry = ttk.Entry(position_frame, textvariable=self.lower_y_var, width=8)
        self.lower_y_entry.grid(row=1, column=7, sticky=(tk.W, tk.E))
        self.lower_y_var.trace('w', self.on_param_change)
        
        # 快捷输入按钮
        shortcut_frame = ttk.LabelFrame(main_frame, text="快捷输入", padding="10")
        shortcut_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        symbols = [
            ("⌀", "直径"),
            ("Φ", "直径(希腊字母)"),
            ("∅", "空集/直径"),
            ("□", "正方形"), 
            ("±", "正负"),
            ("°", "度数"),
        ]
        
        for symbol, desc in symbols:
            btn = ttk.Button(shortcut_frame, text=f"{symbol} {desc}", 
                           command=lambda s=symbol: self.insert_symbol(s))
            btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 预设位置按钮
        preset_frame = ttk.LabelFrame(main_frame, text="位置预设", padding="10")
        preset_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(preset_frame, text="标准布局", command=self.preset_standard).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(preset_frame, text="紧凑布局", command=self.preset_compact).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(preset_frame, text="左对齐", command=self.preset_left_align).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(preset_frame, text="居中布局", command=self.preset_center).pack(side=tk.LEFT, padx=(0, 5))
        
        # 操作按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.save_button = ttk.Button(button_frame, text="保存图像", command=self.save_image)
        self.save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.batch_button = ttk.Button(button_frame, text="批量生成", command=self.batch_generate)
        
        ttk.Button(button_frame, text="重置参数", command=self.reset_params).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="复制到剪贴板", command=self.copy_to_clipboard).pack(side=tk.LEFT)
        
        # 预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="实时预览", padding="10")
        preview_frame.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        # 创建画布用于显示预览
        self.canvas = tk.Canvas(preview_frame, bg="white", width=400, height=200)
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 添加滚动条
        v_scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.canvas.yview)
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.canvas.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.canvas.xview)
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        self.canvas.configure(xscrollcommand=h_scrollbar.set)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 初始化模式
        self.on_mode_change()
    
    def on_mode_change(self):
        """切换生成模式"""
        mode = self.mode_var.get()
        if mode == "single":
            self.single_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
            self.batch_frame.grid_remove()
            self.save_button.pack(side=tk.LEFT, padx=(0, 10))
            self.batch_button.pack_forget()
        else:
            self.single_frame.grid_remove()
            self.batch_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
            self.save_button.pack_forget()
            self.batch_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.status_var.set(f"切换到{'单个' if mode == 'single' else '批量'}生成模式")
    
    def generate_random_values(self):
        """生成随机的尺寸值"""
        # 主尺寸值
        main_val = random.uniform(self.main_min_var.get(), self.main_max_var.get())
        main_text = f"{self.main_prefix_var.get()}{main_val:.2f}"
        
        # 上公差
        upper_tol = random.uniform(self.upper_min_var.get(), self.upper_max_var.get())
        upper_text = f"{upper_tol:+.2f}" if upper_tol >= 0 else f"{upper_tol:.2f}"
        
        # 下公差
        lower_tol = random.uniform(self.lower_min_var.get(), self.lower_max_var.get())
        lower_text = f"{lower_tol:+.2f}" if lower_tol >= 0 else f"{lower_tol:.2f}"
        
        return main_text, upper_text, lower_text
    
    def batch_generate(self):
        """批量生成图像"""
        try:
            # 选择保存目录
            output_dir = filedialog.askdirectory(title="选择批量输出目录")
            if not output_dir:
                return
            
            # 创建images子目录
            images_dir = os.path.join(output_dir, "images")
            if not os.path.exists(images_dir):
                os.makedirs(images_dir)
            
            count = self.batch_count_var.get()
            labels_data = {
                "num-samples": count,
                "labels": {},
                "sizes": {}
            }
            
            self.status_var.set("开始批量生成...")
            
            for i in range(count):
                # 生成ID
                img_id = f"{i:09d}"
                filename = f"{img_id}.jpg"
                # 图片保存在images子目录中
                filepath = os.path.join(images_dir, filename)
                
                # 生成随机参数
                main_text, upper_text, lower_text = self.generate_random_values()
                
                # 生成图像
                img = self.generate_dimension_image_with_params(main_text, upper_text, lower_text)
                
                if img:
                    # 保存为JPEG格式
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img)
                    rgb_img.save(filepath, 'JPEG', quality=95)
                    
                    # 组合完整的标签格式：主尺寸 +上公差/-下公差
                    # 处理上公差格式
                    if upper_text.startswith('+') or upper_text.startswith('-'):
                        formatted_upper = upper_text
                    else:
                        formatted_upper = '+' + upper_text
                    
                    # 处理下公差格式（确保有负号）
                    if lower_text.startswith('-'):
                        formatted_lower = lower_text
                    elif lower_text.startswith('+'):
                        formatted_lower = lower_text
                    else:
                        formatted_lower = '-' + lower_text
                    
                    # 组合完整标签：主尺寸 +上公差/下公差
                    complete_label = f"{main_text} {formatted_upper}/{formatted_lower}"
                    
                    # 记录到labels
                    labels_data["labels"][img_id] = complete_label
                    labels_data["sizes"][img_id] = [img.width, img.height]
                
                # 更新进度
                progress = (i + 1) / count * 100
                self.status_var.set(f"批量生成进度: {progress:.1f}% ({i+1}/{count})")
                self.root.update_idletasks()
            
            # JSON文件保存在主目录中（与images目录同级）
            json_path = os.path.join(output_dir, "labels.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(labels_data, f, indent=2, ensure_ascii=False)
            
            self.status_var.set(f"批量生成完成! 共生成 {count} 个文件")
            messagebox.showinfo("完成", f"批量生成完成!\n"
                                       f"图像文件: {count} 个 (保存在images/目录)\n"
                                       f"JSON文件: labels.json\n"
                                       f"保存位置: {output_dir}")
                                       
        except Exception as e:
            self.status_var.set(f"批量生成失败: {str(e)}")
            messagebox.showerror("错误", f"批量生成失败: {str(e)}")
    
    def parse_position_value(self, value, dimension, text_size, is_x=True):
        """解析位置值，支持数字和关键词"""
        try:
            if isinstance(value, str):
                value = value.strip().lower()
                if value == "center":
                    if is_x:
                        return (self.width_var.get() - text_size) // 2
                    else:
                        return (self.height_var.get() - text_size) // 2
                elif value == "right":
                    return self.width_var.get() - text_size - 5
                elif value == "bottom":
                    return self.height_var.get() - text_size - 2
                else:
                    return int(float(value))
            else:
                return int(value)
        except:
            return 0
    
    def load_unicode_font(self, size):
        """改进的字体加载函数"""
        font_candidates = [
            ("C:/Windows/Fonts/segoeui.ttf", "Segoe UI"),
            ("C:/Windows/Fonts/arial.ttf", "Arial"),
            ("C:/Windows/Fonts/calibri.ttf", "Calibri"),
            ("C:/Windows/Fonts/consola.ttf", "Consolas"),
            ("C:/Windows/Fonts/tahoma.ttf", "Tahoma"),
            ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "DejaVu Sans"),
            ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "Liberation Sans"),
            ("/System/Library/Fonts/Arial.ttf", "Arial"),
            ("arial.ttf", "Arial"),
        ]
        
        for font_path, name in font_candidates:
            try:
                font = ImageFont.truetype(font_path, size)
                if self._test_font_unicode_support(font):
                    return font
            except (OSError, IOError):
                continue
        
        return ImageFont.load_default()
    
    def _test_font_unicode_support(self, font):
        """测试字体是否支持Unicode字符"""
        try:
            test_img = Image.new("RGB", (50, 50), "white")
            test_draw = ImageDraw.Draw(test_img)
            
            test_chars = ["⌀", "±", "°"]
            for char in test_chars:
                try:
                    bbox = test_draw.textbbox((0, 0), char, font=font)
                    if bbox[2] - bbox[0] == 0:
                        return False
                except:
                    return False
            return True
        except:
            return False
    
    def get_text_size(self, draw, text, font):
        """使用最新PIL API获取文本尺寸"""
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            try:
                return draw.textsize(text, font=font)
            except:
                return (len(text) * font.size // 2, font.size)
    
    def insert_symbol(self, symbol):
        """插入特殊符号到主尺寸输入框"""
        if self.mode_var.get() == "single":
            current_pos = self.main_value_entry.index(tk.INSERT)
            current_text = self.main_value_var.get()
            new_text = current_text[:current_pos] + symbol + current_text[current_pos:]
            self.main_value_var.set(new_text)
            self.main_value_entry.icursor(current_pos + 1)
            self.main_value_entry.focus()
        else:
            # 批量模式下插入到前缀
            current_text = self.main_prefix_var.get()
            self.main_prefix_var.set(current_text + symbol)
    
    def preset_standard(self):
        """标准布局预设"""
        self.main_x_var.set(5)
        self.main_y_var.set("center")
        self.upper_x_var.set("right")
        self.upper_y_var.set(2)
        self.lower_x_var.set("right")
        self.lower_y_var.set("bottom")
        self.status_var.set("已应用标准布局")
    
    def preset_compact(self):
        """紧凑布局预设"""
        self.main_x_var.set(2)
        self.main_y_var.set("center")
        self.upper_x_var.set("right")
        self.upper_y_var.set(0)
        self.lower_x_var.set("right")
        self.lower_y_var.set("bottom")
        self.status_var.set("已应用紧凑布局")
    
    def preset_left_align(self):
        """左对齐预设"""
        self.main_x_var.set(5)
        self.main_y_var.set("center")
        self.upper_x_var.set(60)
        self.upper_y_var.set(2)
        self.lower_x_var.set(60)
        self.lower_y_var.set("bottom")
        self.status_var.set("已应用左对齐布局")
    
    def preset_center(self):
        """居中布局预设"""
        self.main_x_var.set("center")
        self.main_y_var.set("center")
        self.upper_x_var.set("right")
        self.upper_y_var.set(2)
        self.lower_x_var.set("right")
        self.lower_y_var.set("bottom")
        self.status_var.set("已应用居中布局")
    
    def on_param_change(self, *args):
        """参数变化时更新预览"""
        if self.mode_var.get() == "single":
            self.root.after_idle(self.update_preview)
    
    def generate_dimension_image_with_params(self, main_value, tol_upper, tol_lower):
        """使用指定参数生成尺寸标注图像"""
        try:
            width = self.width_var.get()
            height = self.height_var.get()
            font_main_size = self.font_main_size_var.get()
            font_tol_size = self.font_tol_size_var.get()
            
            # 创建白底图像
            img = Image.new("RGB", (width, height), "white")
            draw = ImageDraw.Draw(img)
            
            # 加载字体
            font_main = self.load_unicode_font(font_main_size)
            font_tol = self.load_unicode_font(font_tol_size)
            
            # 使用最新API获取文本尺寸
            main_w, main_h = self.get_text_size(draw, main_value, font_main)
            tol_upper_w, tol_upper_h = self.get_text_size(draw, tol_upper, font_tol)
            tol_lower_w, tol_lower_h = self.get_text_size(draw, tol_lower, font_tol)
            
            # 计算实际位置
            main_x = self.parse_position_value(self.main_x_var.get(), width, main_w, True)
            main_y = self.parse_position_value(self.main_y_var.get(), height, main_h, False)
            
            upper_x = self.parse_position_value(self.upper_x_var.get(), width, tol_upper_w, True)
            upper_y = self.parse_position_value(self.upper_y_var.get(), height, tol_upper_h, False)
            
            lower_x = self.parse_position_value(self.lower_x_var.get(), width, tol_lower_w, True)
            lower_y = self.parse_position_value(self.lower_y_var.get(), height, tol_lower_h, False)
            
            # 绘制文本
            draw.text((main_x, main_y), main_value, font=font_main, fill="black")
            draw.text((upper_x, upper_y), tol_upper, font=font_tol, fill="black")
            draw.text((lower_x, lower_y), tol_lower, font=font_tol, fill="black")
            
            return img
            
        except Exception as e:
            print(f"生成图像时出错: {str(e)}")
            return None
    
    def generate_dimension_image(self):
        """生成尺寸标注图像 - 单个模式使用"""
        if self.mode_var.get() == "single":
            main_value = self.main_value_var.get()
            tol_upper = self.tol_upper_var.get()
            tol_lower = self.tol_lower_var.get()
            return self.generate_dimension_image_with_params(main_value, tol_upper, tol_lower)
        else:
            # 批量模式下生成预览用的随机值
            main_text, upper_text, lower_text = self.generate_random_values()
            return self.generate_dimension_image_with_params(main_text, upper_text, lower_text)
    
    def update_preview(self):
        """更新预览图像"""
        try:
            self.current_image = self.generate_dimension_image()
            if self.current_image:
                # 创建放大版本用于预览
                preview_scale = 3
                preview_img = self.current_image.resize(
                    (self.current_image.width * preview_scale, 
                     self.current_image.height * preview_scale), 
                    Image.NEAREST
                )
                
                # 转换为Tkinter可用的格式
                self.preview_photo = ImageTk.PhotoImage(preview_img)
                
                # 清除画布并显示新图像
                self.canvas.delete("all")
                self.canvas.create_image(10, 10, anchor=tk.NW, image=self.preview_photo)
                
                # 更新滚动区域
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))
                
                # 显示当前使用的字体信息
                font_info = f"实际尺寸: {self.current_image.width}×{self.current_image.height}px"
                mode_info = "单个模式" if self.mode_var.get() == "single" else "批量模式预览"
                self.status_var.set(f"预览已更新 - {mode_info} - {font_info}")
        except Exception as e:
            self.status_var.set(f"预览更新失败: {str(e)}")
    
    def save_image(self):
        """保存图像到文件"""
        if not self.current_image:
            messagebox.showwarning("警告", "没有可保存的图像")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存尺寸标注图像",
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("BMP files", "*.bmp"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                # 对于JPEG格式，需要转换为RGB模式
                if file_path.lower().endswith(('.jpg', '.jpeg')):
                    rgb_img = Image.new('RGB', self.current_image.size, (255, 255, 255))
                    rgb_img.paste(self.current_image, mask=self.current_image.split()[-1] if self.current_image.mode == 'RGBA' else None)
                    rgb_img.save(file_path, 'JPEG', quality=95)
                else:
                    self.current_image.save(file_path)
                    
                self.status_var.set(f"图像已保存到: {file_path}")
                messagebox.showinfo("成功", f"图像已成功保存到:\n{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存图像时出错: {str(e)}")
    
    def copy_to_clipboard(self):
        """复制图像到剪贴板"""
        if not self.current_image:
            messagebox.showwarning("警告", "没有可复制的图像")
            return
        
        try:
            # 优先尝试使用win32clipboard
            import win32clipboard
            import io
            
            output = io.BytesIO()
            self.current_image.save(output, format='BMP')
            bmp_data = output.getvalue()[14:]  # 跳过BMP文件头
            
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data)
            win32clipboard.CloseClipboard()
            
            self.status_var.set("图像已复制到剪贴板")
            messagebox.showinfo("成功", "图像已成功复制到剪贴板！")
            
        except ImportError:
            # 备选方案
            try:
                import tempfile
                import subprocess
                import platform
                
                # 保存到临时文件
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    self.current_image.save(tmp.name)
                    temp_path = tmp.name
                
                if platform.system() == 'Windows':
                    # Windows PowerShell命令
                    cmd = f'powershell.exe -command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Clipboard]::SetImage([System.Drawing.Image]::FromFile(\'{temp_path}\'))"'
                    subprocess.run(cmd, shell=True, check=True)
                    os.unlink(temp_path)
                    
                    self.status_var.set("图像已复制到剪贴板")
                    messagebox.showinfo("成功", "图像已成功复制到剪贴板！")
                else:
                    self.status_var.set(f"图像已保存到临时文件: {temp_path}")
                    messagebox.showinfo("提示", 
                        f"无法直接复制到剪贴板。\n图像已保存到临时文件:\n{temp_path}")
                        
            except Exception as e:
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    self.current_image.save(tmp.name)
                    temp_path = tmp.name
                
                self.status_var.set(f"图像已保存到临时文件: {temp_path}")
                messagebox.showinfo("提示", 
                    f"无法直接复制到剪贴板。\n图像已保存到临时文件:\n{temp_path}")
                    
        except Exception as e:
            messagebox.showerror("错误", f"复制到剪贴板时出错: {str(e)}")
    
    def reset_params(self):
        """重置参数到默认值"""
        # 单个模式参数
        self.main_value_var.set("⌀5.00")
        self.tol_upper_var.set("0.05")
        self.tol_lower_var.set("-0.10")
        
        # 批量模式参数
        self.main_prefix_var.set("⌀")
        self.main_min_var.set(1.0)
        self.main_max_var.set(10.0)
        self.upper_min_var.set(0.01)
        self.upper_max_var.set(0.10)
        self.lower_min_var.set(-0.10)
        self.lower_max_var.set(-0.01)
        self.batch_count_var.set(50)
        
        # 通用参数
        self.width_var.set(134)
        self.height_var.set(40)
        self.font_main_size_var.set(28)
        self.font_tol_size_var.set(16)
        
        # 重置位置参数
        self.main_x_var.set(5)
        self.main_y_var.set("4")
        self.upper_x_var.set("96")
        self.upper_y_var.set(2)
        self.lower_x_var.set("90")
        self.lower_y_var.set("17")
        
        self.status_var.set("参数已重置")


def generate_dimension_image_standalone(output_path,
                                       main_value="⌀5.00",
                                       tol_upper="0.05",
                                       tol_lower="-0.10",
                                       width=134,
                                       height=40,
                                       font_main_size=28,
                                       font_tol_size=16):
    """
    独立的尺寸标注生成函数，使用最新API，与GUI代码兼容
    """
    def load_font_with_unicode_support(size):
        font_candidates = [
            ("C:/Windows/Fonts/segoeui.ttf", "Segoe UI"),
            ("C:/Windows/Fonts/arial.ttf", "Arial"),
            ("C:/Windows/Fonts/calibri.ttf", "Calibri"),
            ("C:/Windows/Fonts/consola.ttf", "Consolas"),
            ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "DejaVu Sans"),
            ("/System/Library/Fonts/Arial.ttf", "Arial"),
            ("arial.ttf", "Arial"),
            ("DejaVuSans.ttf", "DejaVu Sans"),
        ]
        
        for font_path, name in font_candidates:
            try:
                return ImageFont.truetype(font_path, size)
            except (OSError, IOError):
                continue
        return ImageFont.load_default()
    
    def get_text_size_standalone(draw, text, font):
        """获取文本尺寸的兼容方法"""
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            try:
                return draw.textsize(text, font=font)
            except:
                return (len(text) * font.size // 2, font.size)
    
    # 创建白底图像
    new_img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(new_img)
    
    # 加载字体
    font_main = load_font_with_unicode_support(font_main_size)
    font_tol = load_font_with_unicode_support(font_tol_size)
    
    # 主尺寸文本居左垂直居中
    main_w, main_h = get_text_size_standalone(draw, main_value, font_main)
    draw.text((0, height // 2 - main_h // 2), main_value, font=font_main, fill="black")
    
    # 上下公差文本靠右对齐
    tol_upper_w, tol_upper_h = get_text_size_standalone(draw, tol_upper, font_tol)
    tol_lower_w, tol_lower_h = get_text_size_standalone(draw, tol_lower, font_tol)
    
    draw.text((width - tol_upper_w, 0), tol_upper, font=font_tol, fill="black")
    draw.text((width - tol_lower_w, height - tol_lower_h), tol_lower, font=font_tol, fill="black")
    
    # 保存结果
    new_img.save(output_path)
    return output_path


def batch_generate_standalone(output_dir, count=50, 
                             main_prefix="⌀", main_range=(1.0, 10.0),
                             upper_range=(0.01, 0.10), lower_range=(-0.10, -0.01),
                             width=134, height=40):
    """
    独立的批量生成函数
    """
    # 创建主输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 创建images子目录
    images_dir = os.path.join(output_dir, "images")
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    
    labels_data = {
        "num-samples": count,
        "labels": {},
        "sizes": {}
    }
    
    for i in range(count):
        # 生成ID和文件名
        img_id = f"{i:09d}"
        filename = f"A{img_id}.jpg"
        # 图片保存在images子目录中
        filepath = os.path.join(images_dir, filename)
        
        # 生成随机参数
        main_val = random.uniform(main_range[0], main_range[1])
        main_text = f"{main_prefix}{main_val:.2f}"
        
        upper_tol = random.uniform(upper_range[0], upper_range[1])
        upper_text = f"{upper_tol:+.2f}" if upper_tol >= 0 else f"{upper_tol:.2f}"
        
        lower_tol = random.uniform(lower_range[0], lower_range[1])
        lower_text = f"{lower_tol:+.2f}" if lower_tol >= 0 else f"{lower_tol:.2f}"
        
        # 生成并保存图像
        generate_dimension_image_standalone(
            filepath, main_text, upper_text, lower_text, width, height
        )
        
        # 组合完整的标签格式：主尺寸 +上公差/下公差
        # 处理上公差格式
        if upper_text.startswith('+') or upper_text.startswith('-'):
            formatted_upper = upper_text
        else:
            formatted_upper = '+' + upper_text
        
        # 处理下公差格式（确保有负号）
        if lower_text.startswith('-'):
            formatted_lower = lower_text
        elif lower_text.startswith('+'):
            formatted_lower = lower_text
        else:
            formatted_lower = '-' + lower_text
        
        # 组合完整标签：主尺寸 +上公差/下公差
        complete_label = f"{main_text} {formatted_upper}/{formatted_lower}"
        
        # 记录标签
        labels_data["labels"][img_id] = complete_label
        labels_data["sizes"][img_id] = [width, height]
        
        print(f"生成进度: {i+1}/{count}")
    
    # JSON文件保存在主目录中（与images目录同级）
    json_path = os.path.join(output_dir, "labels.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(labels_data, f, indent=2, ensure_ascii=False)
    
    print(f"批量生成完成!")
    print(f"图像目录: {images_dir}")
    print(f"JSON文件: {json_path}")
    return json_path


def main():
    """主函数 - 启动GUI应用"""
    root = tk.Tk()
    app = DimensionGeneratorGUI(root)
    root.mainloop()


# 使用示例和测试
if __name__ == "__main__":
    print("工程尺寸标注生成器 - 批量版")
    print("=" * 60)
    print("新增功能:")
    print("✓ 批量生成模式")
    print("✓ 数值区间设置")
    print("✓ 0000开头的JPG文件命名")
    print("✓ 自动生成labels.json文件")
    print("✓ 支持单个和批量两种模式")
    print("=" * 60)
    
    # 基本示例 - 独立函数使用
    try:
        # 单个生成示例
        generate_dimension_image_standalone(
            "example_batch.jpg",
            main_value="⌀5.00",
            tol_upper="+0.05", 
            tol_lower="-0.10"
        )
        print("✓ 单个示例图像生成成功: example_batch.jpg")
        
        # 批量生成示例（少量）
        output_test_dir = "test_batch_output"
        batch_generate_standalone(output_test_dir, count=5)
        print(f"✓ 批量示例生成成功:")
        print(f"  - 图像目录: {output_test_dir}/images/")
        print(f"  - JSON文件: {output_test_dir}/labels.json")
        
    except Exception as e:
        print(f"✗ 示例生成失败: {e}")
    
    print("\n启动GUI界面...")
    # 启动GUI
    main()