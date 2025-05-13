from PySide6.QtCore import QObject, QPoint, Signal, QTimer
from PySide6.QtGui import QGuiApplication, QCursor
import jieba
from ocr_engine import OCREngine
from utils import qimage_to_numpy


class HoverTool(QObject):
    """悬停取词工具类"""
    word_found = Signal(str)  # 找到单词时触发
    status_changed = Signal(str)  # 状态变化时触发

    def __init__(self):
        super().__init__()
        self.ocr_engine = OCREngine.get_instance()

    def capture_at_cursor(self):
        """在光标位置捕获文字"""
        cursor_pos = QCursor().pos()
        self.status_changed.emit("正在识别中...")
        self.capture_text_at_position(cursor_pos)

    def capture_text_at_position(self, pos):
        """在指定位置捕获文本"""
        try:
            # 捕获光标附近较大区域的截图
            screen = QGuiApplication.screenAt(pos)
            if not screen:
                self.status_changed.emit("无法获取屏幕截图")
                return

            # 获取截图区域
            capture_width, capture_height = 400, 200
            x = pos.x() - capture_width // 2
            y = pos.y() - capture_height // 2

            # 截图
            screenshot = screen.grabWindow(0, x, y, capture_width, capture_height)
            if screenshot.isNull():
                self.status_changed.emit("截图为空")
                return

            # TODO: delete
            screenshot_path = "hover_capture_initial.png"
            screenshot.save(screenshot_path)

            # 处理OCR
            img = screenshot.toImage()
            result = self.ocr_engine.process_image(img)

            if not result:
                self.status_changed.emit("未识别到文本")
                return

            # 计算相对于截图的鼠标位置
            relative_mouse_pos = QPoint(capture_width // 2, capture_height // 2)

            # 找到距离鼠标最近的文本区域
            closest_text = None
            min_distance = float('inf')

            for text, box, _ in result:
                # 计算文本框中心点
                center_x = sum(point[0] for point in box) / 4
                center_y = sum(point[1] for point in box) / 4

                # 计算与鼠标的距离
                distance = ((center_x - relative_mouse_pos.x()) ** 2 +
                            (center_y - relative_mouse_pos.y()) ** 2) ** 0.5

                if distance < min_distance:
                    min_distance = distance
                    closest_text = (text, box)

            if not closest_text:
                self.status_changed.emit("未在鼠标位置找到文本")
                return

            text, box = closest_text

            # 计算每个字符的平均宽度
            x1 = min(point[0] for point in box)
            x2 = max(point[0] for point in box)
            box_width = x2 - x1
            text_length = len(text)

            if text_length == 0:
                self.status_changed.emit("文本为空")
                return

            avg_char_width = box_width / text_length

            # 使用jieba分词
            tokenized = list(jieba.tokenize(text))
            word_positions = []
            for tk in tokenized:
                word = tk[0]
                if word.strip() == '' or word in ['，', '。', '!', '?', ',', '.', ' ']:
                    continue
                start_idx = tk[1]
                end_idx = tk[2]
                word_positions.append((word, start_idx, end_idx))

            # 根据鼠标位置找到对应的单词
            mouse_x = relative_mouse_pos.x()
            selected_word = None
            min_word_distance = float('inf')

            for word, start, end in word_positions:
                word_start_x = x1 + start * avg_char_width
                word_end_x = x1 + end * avg_char_width

                if word_start_x <= mouse_x <= word_end_x:
                    word_center = (word_start_x + word_end_x) / 2
                    distance = abs(mouse_x - word_center)

                    if distance < min_word_distance:
                        min_word_distance = distance
                        selected_word = word

            if selected_word:
                self.word_found.emit(selected_word)
                self.status_changed.emit("成功识别文本并复制到剪贴板")
                # 复制到剪贴板
                QGuiApplication.clipboard().setText(selected_word)
            else:
                self.status_changed.emit("未找到精确单词")

        except Exception as e:
            self.status_changed.emit(f"取词失败: {str(e)}")