import cv2
import numpy as np
import os
from pathlib import Path
import argparse

def process_image_to_black_white(image_path, output_path=None, threshold=127):
    """
    将图像处理为纯黑白图像
    
    Args:
        image_path: 输入图像路径
        output_path: 输出图像路径，如果为None则覆盖原图
        threshold: 二值化阈值，默认127
    """
    # 读取图像
    img = cv2.imread(str(image_path))
    if img is None:
        print(f"无法读取图像: {image_path}")
        return False
    
    # 转换为灰度图
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    
    # 二值化处理 - 确保只有纯黑和纯白
    _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    
    # 如果需要反转（文字变黑，背景变白）
    # binary = cv2.bitwise_not(binary)
    
    # 保存图像
    if output_path is None:
        output_path = image_path
    
    success = cv2.imwrite(str(output_path), binary)
    if success:
        print(f"处理完成: {output_path}")
        return True
    else:
        print(f"保存失败: {output_path}")
        return False

def process_directory(input_dir, output_dir=None, threshold=127, file_extensions=None):
    """
    批量处理目录中的所有图像
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录，如果为None则覆盖原图
        threshold: 二值化阈值
        file_extensions: 支持的文件扩展名
    """
    if file_extensions is None:
        file_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"输入目录不存在: {input_dir}")
        return
    
    print(f"正在扫描目录: {input_path}")
    
    # 创建输出目录
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = input_path
    
    # 处理所有图像文件
    processed_count = 0
    found_files = []
    
    for file_path in input_path.rglob('*'):
        if file_path.is_file():
            found_files.append(file_path)
            print(f"找到文件: {file_path}")
            
            if file_path.suffix.lower() in file_extensions:
                # 构建输出路径
                relative_path = file_path.relative_to(input_path)
                if output_dir:
                    out_file = output_path / relative_path
                    out_file.parent.mkdir(parents=True, exist_ok=True)
                else:
                    out_file = file_path
                
                # 处理图像
                if process_image_to_black_white(file_path, out_file, threshold):
                    processed_count += 1
            else:
                print(f"跳过非图像文件: {file_path}")
    
    if not found_files:
        print("目录中没有找到任何文件!")
        # 列出所有子目录
        subdirs = [d for d in input_path.iterdir() if d.is_dir()]
        if subdirs:
            print("找到的子目录:")
            for subdir in subdirs:
                print(f"  - {subdir.name}")
        
    print(f"共找到 {len(found_files)} 个文件，处理了 {processed_count} 个图像文件")

def enhance_text_clarity(image_path, output_path=None):
    """
    增强文字清晰度的专门处理
    """
    img = cv2.imread(str(image_path))
    if img is None:
        return False
    
    # 转换为灰度
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 高斯模糊去噪
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # 自适应阈值处理 - 对不均匀光照更友好
    adaptive_thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    # 形态学操作 - 去除噪点
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
    
    # 保存
    if output_path is None:
        output_path = image_path
    
    return cv2.imwrite(str(output_path), cleaned)

def batch_process_text_renderer_output(base_dir):
    """
    专门处理text_renderer输出的图像
    """
    base_path = Path(base_dir)
    
    # 查找所有输出子目录
    for subdir in base_path.iterdir():
        if subdir.is_dir():
            print(f"处理目录: {subdir.name}")
            
            # 为每个配置目录创建处理后的版本
            processed_dir = subdir.parent / f"{subdir.name}_processed"
            
            # 处理该目录下的所有图像
            process_directory(
                input_dir=subdir,
                output_dir=processed_dir,
                threshold=127  # 可以根据实际效果调整
            )

def main():
    parser = argparse.ArgumentParser(description='图像后处理工具')
    parser.add_argument('--input', '-i', required=True, help='输入路径（文件或目录）')
    parser.add_argument('--output', '-o', help='输出路径（可选）')
    parser.add_argument('--threshold', '-t', type=int, default=225, help='二值化阈值 (0-255)')
    parser.add_argument('--enhance', action='store_true', help='使用增强清晰度模式')
    parser.add_argument('--batch', action='store_true', help='批量处理text_renderer输出')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if args.batch:
        # 批量处理模式
        batch_process_text_renderer_output(args.input)
    elif input_path.is_file():
        # 单文件处理
        if args.enhance:
            enhance_text_clarity(input_path, args.output)
        else:
            process_image_to_black_white(input_path, args.output, args.threshold)
    elif input_path.is_dir():
        # 目录处理
        process_directory(args.input, args.output, args.threshold)
    else:
        print(f"输入路径不存在: {args.input}")

if __name__ == "__main__":
    main()

# 使用示例：
"""
# 处理单个图像
python postprocess.py -i image.jpg -o image_bw.jpg

# 处理整个目录
python postprocess.py -i ./my_output -o ./my_output_processed

# 批量处理text_renderer的输出（推荐）
python postprocess.py -i ./my_output --batch

# 使用增强模式
python postprocess.py -i ./my_output --enhance --batch

# 调整阈值
python postprocess.py -i ./my_output --batch -t 100
"""