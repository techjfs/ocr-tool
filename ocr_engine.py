from paddleocr import PaddleOCR
import numpy as np
import re
from PySide6.QtGui import QImage
from utils import qimage_to_numpy


class OCREngine:
    """OCR引擎封装类，支持中英文自适应识别"""
    _instance = None

    @classmethod
    def get_instance(cls):
        """单例模式获取OCR引擎实例"""
        if cls._instance is None:
            cls._instance = OCREngine()
        return cls._instance

    def __init__(self):
        """初始化OCR引擎，准备中文和英文两种模型"""
        # 初始化中文OCR引擎
        self.ocr_ch = PaddleOCR(
            use_angle_cls=True,
            lang='ch',
            det_model_dir="./_internal/models/det/ch/",
            rec_model_dir="./_internal/models/rec/ch/",
            cls_model_dir="./_internal/models/cls/ch/"
        )

        self.ocr_en = PaddleOCR(
            use_angle_cls=True,
            lang='en',
            det_model_dir="./_internal/models/det/en/",
            rec_model_dir="./_internal/models/rec/en/"
        )

    def is_english_only(self, text_list):
        """判断文本是否只包含英文字符

        Args:
            text_list: 识别出的文本列表

        Returns:
            bool: 是否全为英文字符（含数字和标点）
        """
        if not text_list:
            return False

        # 将所有文本连接起来
        combined_text = ''.join([text for text, _, _ in text_list])

        # 去除数字、标点和空格后检查是否只包含英文字母
        # 使用正则表达式匹配非英文字符（包括中文和其他非ASCII字符）
        non_english_pattern = re.compile(r'[^a-zA-Z0-9\s.,!?;:\'\"()\[\]{}<>+=\-_*&^%$#@~`|/\\]')

        # 如果没有匹配到非英文字符，则表示文本只包含英文
        return not bool(non_english_pattern.search(combined_text))

    def process_image(self, image: QImage):
        """处理QImage图像并返回OCR结果，自动选择最佳语言模型"""
        if image.isNull():
            return []

        # 转换为numpy数组
        img_np = qimage_to_numpy(image)

        # 首先使用中文模型识别
        ch_result = self.ocr_ch.ocr(img_np, cls=True)

        # 提取中文识别结果
        ch_texts = []
        if ch_result and len(ch_result) > 0:
            for line in ch_result[0]:
                if line:
                    text, confidence = line[1]
                    box = line[0]
                    ch_texts.append((text, box, confidence))

        # 检查是否结果全是英文
        if self.is_english_only(ch_texts):
            # 使用英文模型重新识别
            en_result = self.ocr_en.ocr(img_np, cls=True)

            # 提取英文识别结果
            en_texts = []
            if en_result and len(en_result) > 0:
                for line in en_result[0]:
                    if line:
                        text, confidence = line[1]
                        box = line[0]
                        en_texts.append((text, box, confidence))

            print(f"使用英文模型识别结果: {en_texts}")
            return en_texts
        else:
            print(f"使用中文模型识别结果: {ch_texts}")
            return ch_texts

    def get_text_only(self, image: QImage):
        """只返回文本结果，不含位置信息"""
        results = self.process_image(image)
        return [text for text, _, _ in results]
