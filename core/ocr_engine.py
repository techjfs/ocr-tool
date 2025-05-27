import json

from rapidocr import RapidOCR
import re
import json
from PySide6.QtGui import QImage
from util.utils import PathConfig


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
        self.ocr = RapidOCR(params={
            "Global.with_onnx": True,
            "Global.lang_det": "ch_mobile",
            "Global.lang_rec": "ch_mobile",
            "Det.model_path": PathConfig.get_model_path("ch_PP-OCRv4_det_infer.onnx"),
            "Cls.model_path": PathConfig.get_model_path("ch_ppocr_mobile_v2.0_cls_infer.onnx"),
            "Rec.model_path": PathConfig.get_model_path("ch_PP-OCRv4_rec_infer.onnx"),
            "Global.font_path": PathConfig.models_dir / "FZYTK.TTF"
        })

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

        import os
        ocr_dir = PathConfig.get_ocr_result_path()
        os.makedirs(ocr_dir, exist_ok=True)
        screenshot_path = os.path.join(ocr_dir, "ocr.png")
        image.save(screenshot_path)

        result = self.ocr(screenshot_path)

        texts = []
        for i, txt in enumerate(result.txts):
            texts.append((txt, result.boxes[i], result.scores[i]))
        return texts

    def get_text_only(self, image: QImage):
        """只返回文本结果，不含位置信息"""
        results = self.process_image(image)
        return [text for text, _, _ in results]
