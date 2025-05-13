from paddleocr import PaddleOCR
import numpy as np
from PySide6.QtGui import QImage
from utils import qimage_to_numpy


class OCREngine:
    """OCR引擎封装类"""
    _instance = None

    @classmethod
    def get_instance(cls):
        """单例模式获取OCR引擎实例"""
        if cls._instance is None:
            cls._instance = OCREngine()
        return cls._instance

    def __init__(self):
        """初始化OCR引擎"""
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang='ch',
            det_model_dir="./_internal/models/det/",
            rec_model_dir="./_internal/models/rec/",
            cls_model_dir="./_internal/models/cls/"
        )

    def process_image(self, image: QImage):
        """处理QImage图像并返回OCR结果"""
        if image.isNull():
            return []

        # 转换为numpy数组
        img_np = qimage_to_numpy(image)

        # 执行OCR识别
        result = self.ocr.ocr(img_np, cls=True)

        # 提取文本
        texts = []
        if result and len(result) > 0:
            for line in result[0]:
                if line:
                    text, confidence = line[1]
                    box = line[0]
                    texts.append((text, box, confidence))

        return texts

    def get_text_only(self, image: QImage):
        """只返回文本结果，不含位置信息"""
        results = self.process_image(image)
        return [text for text, _, _ in results]