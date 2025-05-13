
import numpy as np
from PySide6.QtGui import QImage

def qimage_to_numpy(qimage: QImage) -> np.ndarray:
    """将QImage转换为numpy数组"""
    qimage = qimage.convertToFormat(QImage.Format.Format_RGB888)
    width, height = qimage.width(), qimage.height()
    img_np = np.ndarray((height, width, 3), buffer=qimage.constBits(),
                      strides=[qimage.bytesPerLine(), 3, 1], dtype=np.uint8)
    return img_np