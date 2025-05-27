from rapidocr import RapidOCR
from util.utils import PathConfig

engine = RapidOCR(params={
    "Global.lang_det": "ch_mobile",
    "Global.lang_rec": "ch_mobile",
    "Global.with_onnx": True,
})

img_url = PathConfig.project_root / "debug_captures" / "hover_capture_160x60.png"
print(img_url)
result = engine(img_url)
print(result.txts)
print(result.boxes)
print(result.scores)

result.vis("vis_result.jpg")