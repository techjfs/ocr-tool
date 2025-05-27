from PySide6.QtCore import Qt, QRect, Signal, QObject
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QImage, QGuiApplication
from PySide6.QtWidgets import QWidget
from core.ocr_engine import OCREngine


class ScreenshotWidget(QWidget):
    """截图选择窗口"""
    capture_finished = Signal(QImage)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("屏幕截图")
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 初始化截图区域
        self.start_point = None
        self.end_point = None
        self.selection_rect = QRect()
        self.dragging = False

        # 获取全屏截图
        self.screen = QGuiApplication.primaryScreen()
        self.full_screenshot = self.screen.grabWindow(0)

    def paintEvent(self, event):
        """绘制截图区域和遮罩"""
        painter = QPainter(self)

        # 绘制半透明背景
        painter.setPen(QPen(Qt.GlobalColor.blue, 2))
        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
        painter.drawRect(self.rect())

        # 绘制选择区域
        if not self.selection_rect.isNull():
            painter.setPen(QPen(Qt.GlobalColor.red, 2))
            painter.setBrush(QBrush(QColor(255, 0, 0, 30)))
            painter.drawRect(self.selection_rect)

            # 绘制区域尺寸信息
            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            size_text = f"{self.selection_rect.width()} × {self.selection_rect.height()}"
            painter.drawText(self.selection_rect.right() - 100,
                             self.selection_rect.bottom() + 20, size_text)

    def mousePressEvent(self, event):
        """鼠标按下开始截图"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.dragging = True

    def mouseMoveEvent(self, event):
        """鼠标移动更新截图区域"""
        if self.dragging:
            self.end_point = event.pos()
            self.selection_rect = QRect(self.start_point, self.end_point).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        """鼠标释放完成截图"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            if (self.selection_rect.width() > 5 and self.selection_rect.height() > 5):
                self.capture_selection()
            self.close()

    def capture_selection(self):
        """捕获选中的区域"""
        if self.selection_rect.isNull() or self.selection_rect.width() < 5 or self.selection_rect.height() < 5:
            return

        screenshot = self.full_screenshot.copy(
            self.selection_rect.x(),
            self.selection_rect.y(),
            self.selection_rect.width(),
            self.selection_rect.height()
        )

        # 发送截图完成信号
        self.capture_finished.emit(screenshot.toImage())

    def keyPressEvent(self, event):
        """按ESC取消截图"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()


class CaptureTool(QObject):
    """截图工具类，负责处理截图逻辑"""
    capture_completed = Signal(list)  # 截图完成后传递OCR结果

    def __init__(self):
        super().__init__()
        self.screenshot_widget = None
        self.ocr_engine = OCREngine.get_instance()

    def start_capture(self):
        """开始截图"""
        self.screenshot_widget = ScreenshotWidget()
        self.screenshot_widget.capture_finished.connect(self.process_captured_image)
        self.screenshot_widget.show()

    def process_captured_image(self, image):
        """处理截图并进行OCR识别"""
        if image.isNull():
            self.capture_completed.emit([])
            return

        # 将图像添加到剪贴板
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.clipboard().setImage(image)

        # 处理OCR
        text_results = self.ocr_engine.get_text_only(image)
        self.capture_completed.emit(text_results)