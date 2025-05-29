from rapidocr import RapidOCR
from util.utils import PathConfig

# engine = RapidOCR(params={
#     "Global.with_onnx": True,
#     "Global.lang_det": "ch_mobile",
#     "Global.lang_rec": "ch_mobile",
#     "Det.model_path": PathConfig.get_model_path("ch_PP-OCRv3_det_infer.onnx"),
#     "Cls.model_path": PathConfig.get_model_path("ch_ppocr_mobile_v2.0_cls_infer.onnx"),
#     "Rec.model_path": PathConfig.get_model_path(" ch_PP-OCRv4_rec_infer.onnx"),
#     "Global.font_path": PathConfig.models_dir / "FZYTK.TTF"
# })

engine = RapidOCR(params={
    "Global.with_onnx": True,
    "Global.lang_det": "en_mobile",
    "Global.lang_rec": "en_mobile",
    "Det.model_path": PathConfig.get_model_path("en_PP-OCRv3_det_infer.onnx", lang_type="en"),
    "Rec.model_path": PathConfig.get_model_path("en_PP-OCRv4_rec_infer.onnx", lang_type="en"),
    "Cls.model_path": PathConfig.get_model_path("ch_ppocr_mobile_v2.0_cls_infer.onnx"),
    "Global.font_path": PathConfig.models_dir / "FZYTK.TTF"
})

img_url = PathConfig.project_root / "ocr_result" / "ocr.png"
print(img_url)
result = engine(img_url)
print(result.txts)
print(result.boxes)
print(result.scores)