import re
from PySide6.QtGui import QImage
from util.utils import PathConfig, qimage_to_numpy
from rapidocr import EngineType, OCRVersion, RapidOCR, ModelType, LangDet, LangRec

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
        self.default_ocr = RapidOCR(params={
            "Cls.model_path": PathConfig.get_model_path("ch_ppocr_mobile_v2.0_cls_infer.onnx"),
            "Det.ocr_version": OCRVersion.PPOCRV4,
            # "Det.model_type": ModelType.SERVER,
            "Det.model_path": PathConfig.get_model_path("ch_PP-OCRv4_det_infer.onnx"),
            "Rec.ocr_version": OCRVersion.PPOCRV4,
            # "Rec.model_type": ModelType.SERVER,
            "Rec.model_path": PathConfig.get_model_path("ch_PP-OCRv4_rec_infer.onnx"),
            "Global.font_path": PathConfig.models_dir / "FZYTK.TTF"
        })
        self.en_ocr = RapidOCR(params={
            "Det.lang_type": LangDet.EN,
            "Rec.lang_type": LangRec.EN,
            "Det.model_path": PathConfig.get_model_path("en_PP-OCRv3_det_infer.onnx", lang_type="en"),
            "Rec.model_path": PathConfig.get_model_path("en_PP-OCRv4_rec_infer.onnx", lang_type="en"),
            "Cls.model_path": PathConfig.get_model_path("ch_ppocr_mobile_v2.0_cls_infer.onnx"),
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

        ch_result = self.default_ocr(screenshot_path)

        ch_texts = self.process_ocr_result(ch_result)

        if self.is_english_only(ch_texts):
            en_result = self.en_ocr(screenshot_path)
            en_texts = self.process_ocr_result(en_result)
            print(f"使用英文模型识别结果: {en_texts}")
            return en_texts

        print(f"使用中文模型识别结果: {ch_texts}")
        return ch_texts

    def process_ocr_result(self, result):
        if not result:
            return []
        texts = []
        for i, txt in enumerate(result.txts):
            print(txt, result.boxes[i])
            x_list = [x[0] for x in result.boxes[i]]
            y_list = [x[1] for x in result.boxes[i]]
            min_x, max_x, min_y, max_y = min(x_list), max(x_list), min(y_list), max(y_list)
            texts.append((txt, [min_x, max_x, min_y, max_y], result.scores[i]))
        return texts

    def get_text_only(self, image: QImage):
        """只返回文本结果，不含位置信息"""
        results = self.process_image(image)
        return [text for text, _, _ in results]
