from rapidocr import RapidOCR
from util.utils import PathConfig
from rapidocr import EngineType, OCRVersion, RapidOCR, ModelType

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
    "Cls.model_path": PathConfig.get_model_path("ch_ppocr_mobile_v2.0_cls_infer.onnx"),
    "Det.ocr_version": OCRVersion.PPOCRV4,
    # "Det.model_type": ModelType.SERVER,
    # "Det.model_path": PathConfig.get_model_path("ch_PP-OCRv5_mobile_det.onnx"),
    "Rec.ocr_version": OCRVersion.PPOCRV4,
    # "Rec.model_type": ModelType.SERVER,
    # "Rec.model_path": PathConfig.get_model_path("ch_PP-OCRv5_rec_mobile_infer.onnx"),
    "Global.font_path": PathConfig.models_dir / "FZYTK.TTF"
})

images = [
    "ti.png",
    "guan.png",
    "chuangkou.png"
]


def ocr(img_url):
    print(img_url)
    result = engine(img_url)
    print(result.boxes)
    print(result.txts)
    print(result.scores)


# for image_name in images:
#     img_url = PathConfig.project_root / "ocr_error_images" / image_name
#     ocr(img_url)

ocr(PathConfig.project_root / "ocr_result" / "ocr.png")
