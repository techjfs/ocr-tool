from paddlex import create_pipeline
from util.utils import PathConfig, qimage_to_numpy
from PySide6.QtGui import QImage

pipeline = create_pipeline(pipeline=str(PathConfig.project_root / "demos" / "OCR.yaml"), device="cpu")

output = pipeline.predict(
    input=qimage_to_numpy(QImage(PathConfig.project_root / "ocr_error_images" / "chuangkou.png"))
)
for res in output:
    print(res.json['res'])