from PySide6.QtCore import QObject, QPoint, Signal, QTimer, Qt, QRectF
from PySide6.QtGui import QGuiApplication, QCursor, QPen, QColor, QPainter
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsRectItem
import jieba
import re
import os
from core.ocr_engine import OCREngine


class CaptureConfig:
    """捕获配置类 - 优化版本"""
    # 多级截图尺寸配置 - 调整为更合适的尺寸
    SMALL_SIZE = (200, 80)  # 增大最小尺寸
    MEDIUM_SIZE = (300, 120)  # 保持中等尺寸
    LARGE_SIZE = (400, 160)  # 增大最大尺寸

    # 阈值配置
    MIN_TEXT_LENGTH = 1
    CONFIDENCE_THRESHOLD = 0.6  # 降低阈值，提高识别率
    MOUSE_INFLUENCE_RADIUS = 40  # 增大影响半径

    # 视觉反馈配置 - 优化颜色和持续时间
    FEEDBACK_DURATION = 1200  # 增加显示时间到1.2秒
    FEEDBACK_COLOR = QColor(255, 0, 0, 168)  # 改为红色边框，更明显
    FEEDBACK_FILL_COLOR = QColor(255, 0, 0, 24)  # 红色半透明填充

    # 新增: 调试模式配置
    DEBUG_MODE = True  # 启用调试输出
    SAVE_DEBUG_IMAGES = True  # 保存调试图片


class VisualFeedback:
    """视觉反馈管理器 - 修复版本"""

    def __init__(self):
        self.scene = None
        self.view = None
        self.rect_item = None
        self.timer = None
        self.is_showing = False
        self._setup_components()

    def _setup_components(self):
        """设置视觉反馈组件"""
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)

        # 修复1: 更明确的窗口标志设置
        self.view.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.X11BypassWindowManagerHint  # 确保在X11系统上正常显示
        )

        # 修复2: 先设置背景透明，但保留边框可见性
        self.view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.view.setStyleSheet("""
            QGraphicsView {
                background: transparent;
                border: none;
            }
        """)

        # 修复3: 禁用滚动条
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 修复4: 禁用交互，防止窗口抢夺焦点
        self.view.setInteractive(False)
        self.view.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # 修复5: 创建更明显的矩形项
        self.rect_item = QGraphicsRectItem()
        pen = QPen(CaptureConfig.FEEDBACK_COLOR, 3)  # 增加边框宽度
        pen.setStyle(Qt.PenStyle.SolidLine)
        self.rect_item.setPen(pen)

        # 设置半透明填充
        fill_color = QColor(CaptureConfig.FEEDBACK_FILL_COLOR)
        fill_color.setAlpha(60)  # 增加透明度
        self.rect_item.setBrush(fill_color)

        self.scene.addItem(self.rect_item)

        # 设置定时器
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._hide_feedback)

    def show(self, rect):
        """显示视觉反馈 - 修复版本"""
        if not self.view or not self.rect_item or not self.timer:
            print("视觉反馈组件未初始化")
            return

        x, y, width, height = rect
        print(f"准备显示反馈框: 位置({x}, {y}), 大小({width}x{height})")

        # 修复6: 确保尺寸合理
        if width <= 0 or height <= 0:
            print(f"警告: 反馈框尺寸无效: {width}x{height}")
            return

        # 修复7: 设置场景矩形
        self.scene.setSceneRect(0, 0, width, height)
        self.rect_item.setRect(0, 0, width, height)

        # 修复8: 设置视图几何形状
        self.view.setGeometry(x, y, width, height)
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.IgnoreAspectRatio)

        # 修复9: 确保窗口显示在最前面
        if not self.is_showing:
            self.view.show()
            self.is_showing = True

        # 强制刷新显示
        self.view.raise_()
        self.view.activateWindow()
        self.view.repaint()

        # 调试信息
        print(f"反馈框已显示: 可见={self.view.isVisible()}, 几何形状={self.view.geometry()}")

        # 启动隐藏定时器
        if self.timer.isActive():
            self.timer.stop()
        self.timer.start(CaptureConfig.FEEDBACK_DURATION)

    def _hide_feedback(self):
        """隐藏视觉反馈"""
        if self.view and self.is_showing:
            self.view.hide()
            self.is_showing = False
            print("反馈框已隐藏")

    def hide(self):
        """立即隐藏视觉反馈"""
        if self.timer and self.timer.isActive():
            self.timer.stop()
        self._hide_feedback()

    def cleanup(self):
        """清理资源"""
        if self.timer:
            self.timer.stop()
        if self.view:
            self.view.hide()
            self.view.deleteLater()
        self.timer = None
        self.view = None
        self.scene = None
        self.rect_item = None
        self.is_showing = False

class TextProcessor:
    """文本处理器"""

    @staticmethod
    def detect_language(text):
        """检测文本语言"""
        english_pattern = re.compile(r'[a-zA-Z]')
        cjk_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\uff00-\uffef\u3000-\u303f]')

        has_english = bool(english_pattern.search(text))
        has_cjk = bool(cjk_pattern.search(text))

        return has_english, has_cjk

    @staticmethod
    def tokenize_text(text):
        """根据语言选择不同的分词方法"""
        has_english, has_cjk = TextProcessor.detect_language(text)

        # 混合文本处理
        if has_english and has_cjk:
            return TextProcessor._jieba_tokenize(text)
        # 纯英文文本
        elif has_english:
            return TextProcessor._space_tokenize(text)
        # 纯中文文本
        else:
            return TextProcessor._jieba_tokenize(text)

    @staticmethod
    def _jieba_tokenize(text):
        """使用jieba分词"""
        words = []
        for word, start, end in jieba.tokenize(text):
            if word.strip() and word not in ['，', '。', '!', '?', ',', '.', ' ']:
                words.append((word, start, end))
        return words

    @staticmethod
    def _space_tokenize(text):
        """使用空格分词"""
        words = []
        word_matches = list(re.finditer(r'\S+', text))

        for match in word_matches:
            word = match.group()
            start = match.start()
            end = match.end()

            # 过滤单个标点符号
            if (word.strip() and
                    not (len(word) == 1 and word in ['，', '。', '!', '?', ',', '.', ';', ':', '"', "'"])):
                words.append((word, start, end))

        return words


# 在OCRProcessor类中添加调试方法
class OCRProcessor:
    """OCR处理器 - 修复版本"""

    def __init__(self):
        self.ocr_engine = OCREngine.get_instance()
        self.dpi_scale = self._get_dpi_scale()
        print(f"DPI缩放比例: {self.dpi_scale}")

    def _get_dpi_scale(self):
        """获取DPI缩放比例"""
        screen = QGuiApplication.primaryScreen()
        if screen:
            ratio = screen.devicePixelRatio()
            print(f"设备像素比: {ratio}")
            return ratio
        return 1.0

    def _adjust_capture_size(self, width, height):
        """根据DPI调整截图尺寸"""
        adjusted_width = int(width * self.dpi_scale)
        adjusted_height = int(height * self.dpi_scale)
        print(f"尺寸调整: {width}x{height} -> {adjusted_width}x{adjusted_height}")
        return adjusted_width, adjusted_height

    def capture_at_position(self, pos, width, height):
        """在指定位置捕获图像并进行OCR"""
        screen = QGuiApplication.screenAt(pos)
        if not screen:
            print("错误: 无法找到屏幕")
            return None

        # 计算截图区域
        x = pos.x() - width // 2
        y = pos.y() - height // 2

        print(f"截图区域: x={x}, y={y}, w={width}, h={height}")
        print(f"鼠标位置: ({pos.x()}, {pos.y()})")

        # 截图
        screenshot = screen.grabWindow(0, x, y, width, height)
        if screenshot.isNull():
            print("错误: 截图失败")
            return None

        print(f"截图成功: 尺寸={screenshot.width()}x{screenshot.height()}")

        # 调试保存
        self._save_debug_image(screenshot, width, height)

        # OCR处理
        img = screenshot.toImage()
        result = self.ocr_engine.process_image(img)
        print(f"OCR结果: {len(result) if result else 0} 个文本区域")

        return result

    def _save_debug_image(self, screenshot, width, height):
        """保存调试图片"""
        try:
            debug_dir = "debug_captures"
            os.makedirs(debug_dir, exist_ok=True)
            screenshot_path = os.path.join(debug_dir, f"hover_capture_{width}x{height}.png")
            success = screenshot.save(screenshot_path)
            print(f"调试图片保存: {screenshot_path} ({'成功' if success else '失败'})")
        except Exception as e:
            print(f"保存调试图片失败: {e}")


class WordSelector:
    """单词选择器"""

    @staticmethod
    def select_word_at_position(ocr_results, mouse_pos, capture_rect):
        """根据鼠标位置选择单词"""
        if not ocr_results:
            return None

        # 过滤低置信度结果
        filtered_results = [
            (text, box, conf) for text, box, conf in ocr_results
            if conf >= CaptureConfig.CONFIDENCE_THRESHOLD and
               len(text.strip()) >= CaptureConfig.MIN_TEXT_LENGTH
        ]

        if not filtered_results:
            return None

        # 计算真实的相对鼠标位置（考虑截图区域偏移）
        capture_x, capture_y, width, height = capture_rect
        relative_mouse_pos = QPoint(
            mouse_pos.x() - capture_x,  # 鼠标X坐标 - 截图左边界
            mouse_pos.y() - capture_y  # 鼠标Y坐标 - 截图上边界
        )

        # 调试输出
        print(f"鼠标全局位置: ({mouse_pos.x()}, {mouse_pos.y()})")
        print(f"截图区域: ({capture_x}, {capture_y}, {width}, {height})")
        print(f"相对鼠标位置: ({relative_mouse_pos.x()}, {relative_mouse_pos.y()})")

        # 找到鼠标位置对应的文本框
        target_text_box = WordSelector._find_text_box_at_mouse(
            filtered_results, relative_mouse_pos
        )

        if not target_text_box:
            return None

        text, box, _ = target_text_box
        print(f"选中文本框: '{text}', box: {box}")

        # 分词并选择单词
        selected_word = WordSelector._select_word_from_text(
            text, box, relative_mouse_pos
        )

        return selected_word or text

    @staticmethod
    def _find_text_box_at_mouse(filtered_results, mouse_pos):
        """找到鼠标位置对应的文本框"""
        # 添加调试输出
        print(f"寻找鼠标位置({mouse_pos.x()}, {mouse_pos.y()})对应的文本框:")
        for i, (text, box, conf) in enumerate(filtered_results):
            print(f"  {i}: '{text}' box:{box} conf:{conf:.3f}")

        # 首先检查鼠标是否在文本框内部
        candidates_inside = []
        for text, box, conf in filtered_results:
            min_x, max_x, min_y, max_y = box

            if (min_x <= mouse_pos.x() <= max_x and
                    min_y <= mouse_pos.y() <= max_y):
                candidates_inside.append((text, box, conf))
                print(f"  鼠标在文本框内: '{text}'")

        # 如果有文本框包含鼠标，选择置信度最高的
        if candidates_inside:
            best_candidate = max(candidates_inside, key=lambda x: x[2])  # 按置信度排序
            print(f"  选择置信度最高的内部候选: '{best_candidate[0]}' conf:{best_candidate[2]:.3f}")
            return best_candidate

        # 如果鼠标不在任何文本框内部，检查附近区域
        candidates_nearby = []
        radius = CaptureConfig.MOUSE_INFLUENCE_RADIUS

        for text, box, conf in filtered_results:
            min_x, max_x, min_y, max_y = box

            if (min_x - radius <= mouse_pos.x() <= max_x + radius and
                    min_y - radius <= mouse_pos.y() <= max_y + radius):
                # 计算到文本框边界的距离
                distance_to_box = WordSelector._calculate_distance_to_box(mouse_pos, box)
                candidates_nearby.append((text, box, conf, distance_to_box))
                print(f"  附近候选: '{text}' 距离:{distance_to_box:.1f} conf:{conf:.3f}")

        # 优先选择距离近且置信度高的候选
        if candidates_nearby:
            # 综合考虑距离和置信度，距离权重更高
            best_candidate = min(candidates_nearby,
                                 key=lambda x: x[3] * 2 - x[2])  # 距离*2 - 置信度
            result = (best_candidate[0], best_candidate[1], best_candidate[2])
            print(f"  选择最佳附近候选: '{result[0]}' 距离:{best_candidate[3]:.1f} conf:{result[2]:.3f}")
            return result

        # 最后兜底：选择最近的文本框
        min_distance = float('inf')
        closest_text_box = None

        for text, box, conf in filtered_results:
            distance = WordSelector._calculate_distance_to_box(mouse_pos, box)

            if distance < min_distance:
                min_distance = distance
                closest_text_box = (text, box, conf)

        if closest_text_box:
            print(f"  兜底选择最近候选: '{closest_text_box[0]}' 距离:{min_distance:.1f}")

        return closest_text_box

    @staticmethod
    def _calculate_distance_to_box(point, box):
        """计算点到矩形框的最短距离"""
        min_x, max_x, min_y, max_y = box
        x, y = point.x(), point.y()

        # 计算点到矩形的最短距离
        dx = max(min_x - x, 0, x - max_x)
        dy = max(min_y - y, 0, y - max_y)

        return (dx * dx + dy * dy) ** 0.5

    @staticmethod
    def _select_word_from_text(text, box, mouse_pos):
        """从文本中选择单词"""
        word_positions = TextProcessor.tokenize_text(text)

        if not word_positions:
            return text

        # 计算文本框信息
        x1, x2, y1, y2 = box
        box_width = x2 - x1
        text_length = len(text)

        if text_length == 0:
            return None

        avg_char_width = box_width / text_length
        mouse_x = mouse_pos.x()

        # 找到最接近鼠标位置的单词
        min_distance = float('inf')
        selected_word = None

        for word, start, end in word_positions:
            word_start_x = x1 + start * avg_char_width
            word_end_x = x1 + end * avg_char_width
            word_center_x = (word_start_x + word_end_x) / 2
            word_center_y = (y1 + y2) / 2

            distance = ((word_center_x - mouse_x) ** 2 +
                        (word_center_y - mouse_pos.y()) ** 2) ** 0.5

            if distance < min_distance:
                min_distance = distance
                selected_word = word

        return selected_word


class HoverTool(QObject):
    """悬停取词工具类"""
    word_found = Signal(str)
    status_changed = Signal(str)
    capture_area_changed = Signal(QRectF)

    def __init__(self):
        super().__init__()
        self.visual_feedback = VisualFeedback()
        self.ocr_processor = OCRProcessor()
        self.current_capture_rect = None

    def cleanup(self):
        """清理资源"""
        if self.visual_feedback:
            self.visual_feedback.cleanup()

    def __del__(self):
        """析构函数"""
        self.cleanup()

    def capture_at_cursor(self):
        """在光标位置捕获文字"""
        cursor_pos = QCursor().pos()
        self.status_changed.emit("正在识别中...")
        self.capture_text_at_position(cursor_pos)

    def capture_text_at_position(self, pos):
        """在指定位置捕获文本，使用多级尺寸策略"""
        try:
            print(f"\n=== 开始捕获文本，鼠标位置: ({pos.x()}, {pos.y()}) ===")

            # 按从小到大的顺序尝试不同尺寸
            size_configs = [
                CaptureConfig.SMALL_SIZE,
                CaptureConfig.MEDIUM_SIZE,
                CaptureConfig.LARGE_SIZE
            ]

            for i, (width, height) in enumerate(size_configs):
                print(f"\n--- 尝试尺寸 {i + 1}/{len(size_configs)}: {width}x{height} ---")

                # 调整尺寸并创建捕获区域
                adj_width, adj_height = self.ocr_processor._adjust_capture_size(width, height)
                capture_rect = self._create_capture_region(pos, adj_width, adj_height)

                print(f"调整后尺寸: {adj_width}x{adj_height}")
                print(f"捕获区域: {capture_rect}")

                # 显示视觉反馈 - 确保在OCR之前显示
                self._show_visual_feedback(capture_rect)

                # 强制处理事件，确保反馈框显示
                QGuiApplication.processEvents()

                # 尝试OCR识别
                ocr_result = self.ocr_processor.capture_at_position(pos, adj_width, adj_height)

                if self._is_valid_ocr_result(ocr_result):
                    print(f"OCR成功，找到 {len(ocr_result)} 个文本区域")

                    # 选择单词
                    selected_word = WordSelector.select_word_at_position(
                        ocr_result, pos, capture_rect
                    )

                    if selected_word:
                        self._handle_successful_recognition(selected_word)
                        return
                    else:
                        print("未能选择到有效单词")
                else:
                    print("OCR结果无效或不满足条件")

            # 所有尺寸都未成功
            print("=== 所有尺寸都未能成功识别 ===")
            self.status_changed.emit("未能识别到文本")

        except Exception as e:
            error_msg = f"取词失败: {str(e)}"
            print(f"异常: {error_msg}")
            self.status_changed.emit(error_msg)

    def _create_capture_region(self, pos, width, height):
        """创建截图区域"""
        x = pos.x() - width // 2
        y = pos.y() - height // 2
        return (x, y, width, height)

    def _show_visual_feedback(self, capture_rect):
        """显示视觉反馈 - 修复版本"""
        self.current_capture_rect = capture_rect

        # 发射区域变化信号
        x, y, width, height = capture_rect
        self.capture_area_changed.emit(QRectF(x, y, width, height))
        print(f"发射区域变化信号: QRectF({x}, {y}, {width}, {height})")

        # 显示视觉反馈
        print("准备显示视觉反馈...")
        self.visual_feedback.show(capture_rect)

        # 确保事件被处理
        QGuiApplication.processEvents()
        print("视觉反馈处理完成")

    def _is_valid_ocr_result(self, ocr_result):
        """判断OCR结果是否有效"""
        if not ocr_result:
            print("OCR结果为空")
            return False

        valid_count = 0
        for text, box, confidence in ocr_result:
            is_valid = (len(text.strip()) >= CaptureConfig.MIN_TEXT_LENGTH and
                       confidence >= CaptureConfig.CONFIDENCE_THRESHOLD)
            print(f"文本: '{text}', 置信度: {confidence:.3f}, 有效: {is_valid}")
            if is_valid:
                valid_count += 1

        print(f"有效文本区域数量: {valid_count}")
        return valid_count > 0

    def _handle_successful_recognition(self, word):
        """处理成功识别的结果"""
        print(f"成功识别单词: '{word}'")

        # 复制到剪贴板
        QGuiApplication.clipboard().setText(word)

        # 发射信号
        self.word_found.emit(word)
        self.status_changed.emit("成功识别文本并复制到剪贴板")