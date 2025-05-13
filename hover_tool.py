from PySide6.QtCore import QObject, QPoint, Signal, QTimer, Qt, QRectF
from PySide6.QtGui import QGuiApplication, QCursor, QPen, QColor, QPainter
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsRectItem, QApplication
import jieba
import re
from ocr_engine import OCREngine


class HoverTool(QObject):
    """悬停取词工具类"""
    word_found = Signal(str)  # 找到单词时触发
    status_changed = Signal(str)  # 状态变化时触发
    capture_area_changed = Signal(QRectF)  # 捕获区域变化时触发

    def __init__(self):
        super().__init__()
        self.ocr_engine = OCREngine.get_instance()
        # 初始截图尺寸参数 - 较小的区域
        self.small_width = 160
        self.small_height = 60
        # 备用截图尺寸参数 - 稍大的区域
        self.medium_width = 240
        self.medium_height = 100
        # 最大截图尺寸 - 备用方案
        self.large_width = 300
        self.large_height = 120
        # 最小有效文本长度
        self.min_text_length = 1
        # DPI缩放比例
        self.dpi_scale = self._get_dpi_scale()
        # 视觉反馈
        self._setup_visual_feedback()
        # 置信度阈值 - 减少误判
        self.confidence_threshold = 0.75
        # 鼠标位置影响范围半径
        self.mouse_influence_radius = 30
        # 当前捕获区域
        self.current_capture_rect = None

    def _setup_visual_feedback(self):
        """设置视觉反馈组件"""
        # 创建场景和视图
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.view.setStyleSheet("background: transparent;")
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 创建矩形项
        self.rect_item = QGraphicsRectItem()
        pen = QPen(QColor(0, 120, 215, 180), 2)  # 半透明蓝色
        self.rect_item.setPen(pen)
        self.rect_item.setBrush(QColor(0, 120, 215, 40))  # 更透明的填充
        self.scene.addItem(self.rect_item)

        # 显示时间
        self.feedback_timer = QTimer()
        self.feedback_timer.setSingleShot(True)
        self.feedback_timer.timeout.connect(self.hide_visual_feedback)

    def show_visual_feedback(self, rect):
        """显示视觉反馈"""
        # 更新捕获区域
        self.current_capture_rect = rect
        self.capture_area_changed.emit(QRectF(rect[0], rect[1], rect[2], rect[3]))

        # 设置矩形
        self.rect_item.setRect(0, 0, rect[2], rect[3])

        # 设置视图位置和大小
        self.view.setGeometry(rect[0], rect[1], rect[2], rect[3])

        # 显示并启动定时器
        self.view.show()
        self.feedback_timer.start(800)  # 显示800ms

    def hide_visual_feedback(self):
        """隐藏视觉反馈"""
        self.view.hide()

    def _get_dpi_scale(self):
        """获取当前屏幕DPI缩放比例"""
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return 1.0
        return screen.devicePixelRatio()

    def _adjust_capture_size(self, width, height):
        """根据DPI调整截图尺寸"""
        return int(width * self.dpi_scale), int(height * self.dpi_scale)

    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'view') and self.view:
            self.view.hide()
            self.view.deleteLater()

    def __del__(self):
        """析构函数"""
        self.cleanup()

    def capture_at_cursor(self):
        """在光标位置捕获文字"""
        cursor_pos = QCursor().pos()
        self.status_changed.emit("正在识别中...")
        self.capture_text_at_position(cursor_pos)

    def _create_capture_region(self, pos, width, height):
        """创建截图区域"""
        x = pos.x() - width // 2
        y = pos.y() - height // 2
        return (x, y, width, height)

    def capture_text_at_position(self, pos):
        """在指定位置捕获文本，使用多级尺寸策略"""
        try:
            # 首先尝试使用小尺寸截图
            small_w, small_h = self._adjust_capture_size(self.small_width, self.small_height)
            small_rect = self._create_capture_region(pos, small_w, small_h)

            # 显示视觉反馈
            self.show_visual_feedback(small_rect)

            result = self._try_capture_with_size(pos, small_w, small_h)

            # 如果小尺寸截图成功找到文本，则直接返回
            if result and self._is_valid_result(result):
                text = self._process_result(result, pos, small_w, small_h)
                if text:
                    return

            # 如果小尺寸未找到有效文本，尝试中等尺寸
            medium_w, medium_h = self._adjust_capture_size(self.medium_width, self.medium_height)
            medium_rect = self._create_capture_region(pos, medium_w, medium_h)

            # 更新视觉反馈为中等尺寸
            self.show_visual_feedback(medium_rect)

            result = self._try_capture_with_size(pos, medium_w, medium_h)

            # 如果中等尺寸截图成功找到文本，则直接返回
            if result and self._is_valid_result(result):
                text = self._process_result(result, pos, medium_w, medium_h)
                if text:
                    return

            # 如果中等尺寸未找到有效文本，尝试大尺寸
            large_w, large_h = self._adjust_capture_size(self.large_width, self.large_height)
            large_rect = self._create_capture_region(pos, large_w, large_h)

            # 更新视觉反馈为大尺寸
            self.show_visual_feedback(large_rect)

            result = self._try_capture_with_size(pos, large_w, large_h)

            # 最后尝试大尺寸
            if result and self._is_valid_result(result):
                text = self._process_result(result, pos, large_w, large_h)
                if text:
                    return

            # 如果所有尺寸都未找到有效文本
            self.status_changed.emit("未能识别到文本")

        except Exception as e:
            self.status_changed.emit(f"取词失败: {str(e)}")

    def _is_valid_result(self, result):
        """判断OCR结果是否有效"""
        if not result:
            return False

        # 检查是否有至少一个有效文本区域
        for text, box, confidence in result:
            # 添加置信度检查，减少误判
            if len(text.strip()) >= self.min_text_length and confidence >= self.confidence_threshold:
                return True
        return False

    def _try_capture_with_size(self, pos, width, height):
        """尝试使用指定尺寸捕获图像并进行OCR"""
        screen = QGuiApplication.screenAt(pos)
        if not screen:
            return None

        # 计算截图区域
        x = pos.x() - width // 2
        y = pos.y() - height // 2

        # 截图
        screenshot = screen.grabWindow(0, x, y, width, height)
        if screenshot.isNull():
            return None

        # TODO: delete it
        import os
        debug_dir = "debug_captures"
        os.makedirs(debug_dir, exist_ok=True)
        screenshot_path = os.path.join(debug_dir, f"hover_capture_{width}x{height}.png")
        screenshot.save(screenshot_path)

        # 处理OCR
        img = screenshot.toImage()
        return self.ocr_engine.process_image(img)

    def _detect_language(self, text):
        """检测文本是否为英文"""
        # 检查是否包含英文字符（基本判断）
        english_pattern = re.compile(r'[a-zA-Z]')
        return bool(english_pattern.search(text))

    def _tokenize_text(self, text, box):
        """根据语言选择不同的分词方法"""
        # 检查文本中是否包含英文字符
        is_english = self._detect_language(text)
        contains_cjk = self._contains_cjk(text)

        # 如果文本既包含英文又包含中文，使用混合处理模式
        if is_english and contains_cjk:
            # 优先使用jieba分词，它能同时处理中英文混合文本
            words = []
            for tk in jieba.tokenize(text):
                word = tk[0]
                if word.strip() == '' or word in ['，', '。', '!', '?', ',', '.', ' ']:
                    continue
                start_idx = tk[1]
                end_idx = tk[2]
                words.append((word, start_idx, end_idx))

            # 如果jieba分词失败或没有得到有效结果，回退到空格分割
            if not words:
                return self._space_tokenize(text)
            return words

        # 纯英文文本，按空格分词
        elif is_english:
            return self._space_tokenize(text)

        # 纯中文文本，使用jieba分词
        else:
            words = []
            for tk in jieba.tokenize(text):
                word = tk[0]
                if word.strip() == '' or word in ['，', '。', '!', '?', ',', '.', ' ']:
                    continue
                start_idx = tk[1]
                end_idx = tk[2]
                words.append((word, start_idx, end_idx))
            return words

    def _space_tokenize(self, text):
        """使用空格分词，专门处理英文文本"""
        words = []
        # 查找所有连续的非空白字符序列
        word_matches = list(re.finditer(r'\S+', text))

        if word_matches:
            for match in word_matches:
                word = match.group()
                start = match.start()
                end = match.end()
                # 过滤掉单个标点符号
                if word.strip() and not (len(word) == 1 and word in ['，', '。', '!', '?', ',', '.', ';', ':', '"', "'"]):
                    words.append((word, start, end))

        return words

    def _contains_cjk(self, text):
        """检测文本是否包含中日韩字符"""
        # Unicode范围: CJK统一表意文字 (4E00-9FFF), CJK扩展 A (3400-4DBF),
        # 半角和全角表单 (FF00-FFEF), 中日韩符号和标点符号 (3000-303F)
        cjk_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\uff00-\uffef\u3000-\u303f]')
        return bool(cjk_pattern.search(text))

    def _process_result(self, result, pos, width, height):
        """处理OCR结果，提取文本"""
        # 计算相对于截图的鼠标位置
        relative_mouse_pos = QPoint(width // 2, height // 2)

        # 过滤低置信度的结果
        filtered_results = [(text, box, conf) for text, box, conf in result
                            if conf >= self.confidence_threshold and len(text.strip()) >= self.min_text_length]

        if not filtered_results:
            return None

        # 步骤1: 找出鼠标位置所在的文本框
        text_at_mouse = None
        for text, box, conf in filtered_results:
            # 计算文本框边界
            min_x = min(point[0] for point in box)
            max_x = max(point[0] for point in box)
            min_y = min(point[1] for point in box)
            max_y = max(point[1] for point in box)

            # 检查鼠标是否在文本框内部或靠近文本框边缘
            if (min_x - self.mouse_influence_radius <= relative_mouse_pos.x() <= max_x + self.mouse_influence_radius and
                    min_y - self.mouse_influence_radius <= relative_mouse_pos.y() <= max_y + self.mouse_influence_radius):
                text_at_mouse = (text, box, conf)
                break

        # 如果鼠标位置没有直接找到文本框，使用最近的文本框
        if not text_at_mouse:
            min_distance = float('inf')
            for text, box, conf in filtered_results:
                # 计算文本框中心点
                center_x = sum(point[0] for point in box) / 4
                center_y = sum(point[1] for point in box) / 4

                # 计算与鼠标的距离
                distance = ((center_x - relative_mouse_pos.x()) ** 2 +
                            (center_y - relative_mouse_pos.y()) ** 2) ** 0.5

                if distance < min_distance:
                    min_distance = distance
                    text_at_mouse = (text, box, conf)

        if not text_at_mouse:
            return None

        text, box, _ = text_at_mouse

        # 打印调试信息
        print(f"识别文本: '{text}'")

        # 计算文本框的边界信息
        x1 = min(point[0] for point in box)
        x2 = max(point[0] for point in box)
        y1 = min(point[1] for point in box)
        y2 = max(point[1] for point in box)
        box_width = x2 - x1
        box_height = y2 - y1

        text_length = len(text)
        if text_length == 0:
            return None

        # 计算每个字符的平均宽度
        avg_char_width = box_width / text_length

        # 调整文本和实际显示区域的对应关系
        # 处理OCR可能识别出括号等不在显示区域内的文本的情况
        actual_text_start = 0
        actual_text_end = text_length

        # 估算可见区域对应的文本下标 - 对应上面的例子，根据矩形区域计算"llo world by"对应的文本起始位置
        # 这一步是启发式的，我们尝试将OCR文本与实际可见区域进行对齐

        # 使用改进的分词方法
        word_positions = self._tokenize_text(text, box)

        print(f"word_positions:{word_positions}")

        # 如果没有找到有效单词（分词失败），返回整个文本
        if not word_positions:
            self.word_found.emit(text)
            self.status_changed.emit("识别完整文本，已复制到剪贴板")
            QGuiApplication.clipboard().setText(text)
            return text

        # 根据鼠标位置找到对应的单词
        mouse_x = relative_mouse_pos.x()
        mouse_y = relative_mouse_pos.y()
        selected_word = None
        min_word_distance = float('inf')

        # 计算鼠标到每个单词的距离
        for word, start, end in word_positions:
            # 计算单词在屏幕上的边界
            word_start_x = x1 + start * avg_char_width
            word_end_x = x1 + end * avg_char_width
            word_center_x = (word_start_x + word_end_x) / 2
            word_center_y = (y1 + y2) / 2

            # 计算鼠标到单词中心的二维欧几里得距离
            # 使用欧几里得距离可以更好地处理鼠标指向单词的情况
            distance = ((word_center_x - mouse_x) ** 2 + (word_center_y - mouse_y) ** 2) ** 0.5

            # 调试输出：显示每个单词的位置和距离
            print(f"单词: '{word}', 位置: ({word_start_x},{word_center_y}), 距离: {distance}")

            if distance < min_word_distance:
                min_word_distance = distance
                selected_word = word

        if selected_word:
            print(f"选中单词: '{selected_word}'")
            self.word_found.emit(selected_word)
            self.status_changed.emit("成功识别文本并复制到剪贴板")
            # 复制到剪贴板
            QGuiApplication.clipboard().setText(selected_word)
            return selected_word
        else:
            # 如果所有方法都失败，返回整个文本
            self.word_found.emit(text)
            self.status_changed.emit("未找到精确单词，已复制全部文本")
            QGuiApplication.clipboard().setText(text)
            return text