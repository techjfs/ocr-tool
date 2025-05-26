import numpy as np
from PySide6.QtGui import QImage
from pathlib import Path

class PathConfig:
    project_root = Path(__file__).resolve().parent.parent
    models_dir = project_root / "_internal" / "official_models"

    @staticmethod
    def get_model_path(model_name):
        return str(PathConfig.models_dir / model_name)

    @staticmethod
    def get_config_path():
        return str(PathConfig.project_root / "config.json")

def qimage_to_numpy(qimage: QImage) -> np.ndarray:
    """将QImage转换为numpy数组"""
    qimage = qimage.convertToFormat(QImage.Format.Format_RGB888)
    width, height = qimage.width(), qimage.height()
    img_np = np.ndarray((height, width, 3), buffer=qimage.constBits(),
                      strides=[qimage.bytesPerLine(), 3, 1], dtype=np.uint8)
    return img_np
