import cv2
import numpy as np
import os
import random
from pathlib import Path
from tqdm import tqdm
from sklearn.model_selection import train_test_split

def rotate_image_with_padding(image, angle, bg_color=(255, 255, 255)):
    """
    带自适应画布和背景填充的旋转
    """
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    
    # 获取旋转矩阵
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    
    # 计算新画布尺寸防止裁剪
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))
    M[0, 2] += (new_w - w) / 2
    M[1, 2] += (new_h - h) / 2

    # 执行旋转，使用纯白色填充边缘
    rotated = cv2.warpAffine(image, M, (new_w, new_h), 
                             flags=cv2.INTER_CUBIC, 
                             borderMode=cv2.BORDER_CONSTANT, 
                             borderValue=bg_color)
    return rotated

def build_ocr_cls_dataset(src_dir, dst_dir, train_ratio=0.8):
    # 1. 定义配置
    # 格式：ID: (角度, 文件夹名/标签名)
    angle_configs = {
        0: (0, "0_degree"),
        1: (45, "45_degree"),
        2: (90, "90_degree"),
        3: (180, "180_degree"),
        4: (270, "270_degree"),
        5: (315, "315_degree")
    }

    src_root = Path(src_dir)
    dst_root = Path(dst_dir)
    img_save_dir = dst_root / "images"
    
    # 创建目录
    for cfg in angle_configs.values():
        (img_save_dir / cfg[1]).mkdir(parents=True, exist_ok=True)

    # 2. 收集源文件
    image_paths = list(src_root.rglob("*.jpg")) + list(src_root.rglob("*.png"))
    print(f"找到源图片: {len(image_paths)} 张")

    all_samples = [] # 用于存储 (文件相对路径, 类别ID)

    # 3. 处理旋转
    for img_p in tqdm(image_paths, desc="旋转处理中"):
        img = cv2.imread(str(img_p))
        if img is None: continue

        for class_id, (base_angle, label_name) in angle_configs.items():
            # 增加上下5度的随机浮动
            jitter = random.uniform(-5, 5)
            final_angle = base_angle + jitter
            
            # 执行旋转
            rotated = rotate_image_with_padding(img, final_angle)
            
            # 生成新文件名和路径
            # 格式：原名_rot_角度_随机数.jpg
            new_name = f"{img_p.stem}_r{base_angle}_{random.randint(1000,9999)}.jpg"
            relative_path = Path("images") / label_name / new_name
            save_path = dst_root / relative_path
            
            cv2.imwrite(str(save_path), rotated)
            
            # 记录数据 (使用 / 作为路径分隔符，兼容Linux/Windows训练)
            all_samples.append(f"{relative_path.as_posix()} {class_id}")

    # 4. 生成 label.txt (字典文件)
    with open(dst_root / "label.txt", "w", encoding="utf-8") as f:
        for class_id, (angle, label_name) in angle_configs.items():
            f.write(f"{class_id} {label_name}\n")

    # 5. 划分训练集和验证集并生成 txt
    train_data, val_data = train_test_split(all_samples, test_size=1-train_ratio, shuffle=True)

    with open(dst_root / "train.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(train_data))

    with open(dst_root / "val.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(val_data))

    print(f"\n✅ 数据集构建完成!")
    print(f"总样本数: {len(all_samples)}")
    print(f"训练集: {len(train_data)}")
    print(f"验证集: {len(val_data)}")
    print(f"输出目录: {dst_root.absolute()}")

if __name__ == "__main__":
    # 使用方法：
    # src_dir: text_renderer 生成的 output 文件夹
    # dst_dir: 你想要存放分类数据集的目标文件夹
    build_ocr_cls_dataset(
        src_dir="./my_output/engineering_math_data", 
        dst_dir="./cls_dataset/2"
    )