import json
import random
import os
from typing import Dict, List, Tuple, Any


class GenerationResult:
    """标签生成结果的数据结构"""

    def __init__(self, train_content: str, val_content: str, train_count: int, val_count: int, used_filenames: bool):
        self.train_content = train_content
        self.val_content = val_content
        self.train_count = train_count
        self.val_count = val_count
        self.used_filenames = used_filenames


class LabelGeneratorService:
    """
    纯业务逻辑服务类，负责从 JSON 数据中生成 PaddleOCR 标签文件内容。
    不包含任何 UI 代码。
    """

    def __init__(self):
        pass

    def load_json_data(self, file_path: str) -> Tuple[Dict, bool]:
        """
        加载并验证 JSON 文件。
        返回 (json_data, has_filenames_field)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            if 'labels' not in json_data:
                raise ValueError("JSON文件中缺少'labels'字段")

            has_filenames = 'filenames' in json_data
            return json_data, has_filenames

        except Exception as e:
            raise Exception(f"加载JSON文件失败：{str(e)}")

    def generate_labels(
            self,
            json_data: Dict[str, Any],
            train_ratio: float,
            image_prefix: str,
            image_suffix: str
    ) -> GenerationResult:
        """
        根据配置和 JSON 数据生成训练集和验证集标签内容。
        原 generate_label_files 方法的核心逻辑。
        """
        if 'labels' not in json_data:
            raise ValueError("JSON数据结构无效，缺少'labels'字段。")

        # 获取所有标签条目 (label_id, label_text)
        label_entries = list(json_data['labels'].items())

        # 检查是否有filenames字段
        has_filenames = 'filenames' in json_data

        # 随机打乱数据
        random.shuffle(label_entries)

        # 计算训练集大小
        train_size = int(len(label_entries) * train_ratio)

        # 分割训练集和验证集
        train_entries = label_entries[:train_size]
        val_entries = label_entries[train_size:]

        # 生成训练集文件内容
        train_lines = []
        for label_id, label_text in train_entries:
            image_filename = self._get_image_filename(label_id, json_data, image_suffix, has_filenames)
            line = f"{image_prefix}{image_filename}\t{label_text}"
            train_lines.append(line)

        # 生成验证集文件内容
        val_lines = []
        for label_id, label_text in val_entries:
            image_filename = self._get_image_filename(label_id, json_data, image_suffix, has_filenames)
            line = f"{image_prefix}{image_filename}\t{label_text}"
            val_lines.append(line)

        return GenerationResult(
            train_content='\n'.join(train_lines),
            val_content='\n'.join(val_lines),
            train_count=len(train_lines),
            val_count=len(val_lines),
            used_filenames=has_filenames
        )

    def _get_image_filename(self, label_id: str, json_data: Dict[str, Any], image_suffix: str,
                            has_filenames: bool) -> str:
        """根据配置获取图片文件名"""
        if has_filenames and label_id in json_data['filenames']:
            return json_data['filenames'][label_id]
        else:
            return f"{label_id}{image_suffix}"

    def save_file_content(self, file_path: str, content: str):
        """将内容保存到指定文件路径"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise Exception(f"保存文件失败：{str(e)}")