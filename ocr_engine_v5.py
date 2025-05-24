import json

from paddleocr import PaddleOCR
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
        self.ocr = PaddleOCR(
            use_doc_unwarping=True,
            use_textline_orientation=False,
            use_doc_orientation_classify=False,
            device="CPU",
            text_detection_model_name="PP-OCRv5_server_det",
            text_detection_model_dir="./_internal/official_models/PP-OCRv5_server_det/",
            text_recognition_model_name="PP-OCRv5_server_rec",
            text_recognition_model_dir="./_internal/official_models/PP-OCRv5_server_rec/"
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
        image.save("ocr_result/ocr.png")

        result = self.ocr.predict("ocr_result/ocr.png")

        texts = []
        for res in result:
            res.print()
            res.save_to_json("ocr_result")
            with open("ocr_result/ocr_res.json", "r", encoding='utf-8') as f:
                json_data = json.loads(f.read())
                for i, text in enumerate(json_data.get("rec_texts")):
                    texts.append((text, json_data.get("rec_scores")[i]))
        return texts


    def get_text_only(self, image: QImage):
        """只返回文本结果，不含位置信息"""
        results = self.process_image(image)
        return [text for text, _ in results]
