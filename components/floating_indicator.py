from PySide6.QtWidgets import QWidget, QLabel, QApplication
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, Signal, QByteArray
from PySide6.QtGui import QCursor, QFont
import math


class FloatingIndicator(QWidget):
    """增强版浮动指示器 - 支持鼠标跟随和动画效果"""

    # 信号定义
    position_updated = Signal(int, int)  # 位置更新信号
    visibility_changed = Signal(bool)  # 可见性变化信号

    # 定义信号用于线程安全操作
    show_at_cursor_signal = Signal(str, bool)
    start_following_signal = Signal()
    stop_following_signal = Signal()
    hide_animated_signal = Signal(bool)

    def __init__(self):
        super().__init__()

        # 窗口基本设置
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus  # 不接受焦点，避免干扰其他窗口
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)  # 显示时不激活窗口

        # 设置固定大小
        self.setFixedSize(200, 50)

        # 创建标签
        self.label = QLabel("🔥 Ready", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setGeometry(0, 0, 200, 50)

        # 设置样式
        self._setup_styles()

        # 连接信号到实际的实现方法
        self.show_at_cursor_signal.connect(self.show_at_cursor_impl)
        self.start_following_signal.connect(self.start_mouse_following_impl)
        self.stop_following_signal.connect(self.stop_mouse_following_impl)
        self.hide_animated_signal.connect(self.hide_animated_impl)

        # 鼠标跟随相关属性
        self.mouse_following = False
        self.follow_offset_x = 40  # 相对鼠标的X偏移
        self.follow_offset_y = 60  # 相对鼠标的Y偏移
        self.smooth_follow = True  # 是否启用平滑跟随
        self.follow_speed = 0.15  # 跟随速度 (0-1之间，越大越快)

        # 位置相关
        self.target_x = 0
        self.target_y = 0
        self.current_x = 0
        self.current_y = 0

        # 定时器设置
        self.mouse_timer = QTimer(self)
        self.mouse_timer.timeout.connect(self._update_mouse_position)
        self.mouse_timer.setInterval(16)  # 约60fps

        self.smooth_timer = QTimer(self)
        self.smooth_timer.timeout.connect(self._smooth_follow_update)
        self.smooth_timer.setInterval(16)  # 约60fps

        # 动画相关
        self.fade_animation = None
        self.move_animation = None
        self._setup_animations()

        # 屏幕边界检测
        self.screen_margin = 10  # 距离屏幕边缘的最小距离

        print("Enhanced FloatingIndicator initialized")

    def _setup_styles(self):
        """设置样式"""
        self.label.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 107, 129, 220), 
                    stop:0.5 rgba(255, 154, 158, 200),
                    stop:1 rgba(255, 182, 193, 180));
                color: white; 
                border-radius: 25px; 
                font-weight: bold;
                font-size: 13px; 
                padding: 10px 16px;
                border: 2px solid rgba(255, 255, 255, 100);
            }
        """)

        # 设置字体
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        font.setBold(True)
        self.label.setFont(font)

    def _setup_animations(self):
        """设置动画效果"""
        # 淡入淡出动画
        self.fade_animation = QPropertyAnimation(self, QByteArray(b"windowOpacity"))
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # 移动动画
        self.move_animation = QPropertyAnimation(self, QByteArray(b"geometry"))
        self.move_animation.setDuration(200)
        self.move_animation.setEasingCurve(QEasingCurve.Type.OutQuart)

    def show_at_cursor(self, text="🔥 Ready", follow_mouse=False):
        """线程安全的显示方法"""
        # 使用信号确保在主线程中执行
        self.show_at_cursor_signal.emit(text, follow_mouse)

    def show_at_cursor_impl(self, text="🔥 Ready", follow_mouse=False):
        """在鼠标位置显示指示器

        Args:
            text: 显示的文本
            follow_mouse: 是否跟随鼠标移动
        """
        self.label.setText(text)

        # 设置跟随参数
        self.mouse_following = follow_mouse

        # 获取鼠标位置并应用偏移量
        cursor_pos = QCursor.pos()

        display_x = cursor_pos.x() + self.follow_offset_x
        display_y = cursor_pos.y() + self.follow_offset_y

        self._update_position(display_x, display_y)

        # 显示窗口
        if not self.isVisible():
            self.setWindowOpacity(0)
            self.show()
            self._fade_in()
            self.visibility_changed.emit(True)

        # 开始鼠标跟随
        if follow_mouse:
            self.start_mouse_following()

        print(f"FloatingIndicator shown at cursor with text: {text}, follow_mouse: {follow_mouse}")

    def start_mouse_following(self):
        """线程安全的开始跟随"""
        self.start_following_signal.emit()

    def start_mouse_following_impl(self):
        """开始鼠标跟随"""
        if not self.mouse_following:
            self.mouse_following = True

        if not self.mouse_timer.isActive():
            self.mouse_timer.start()

        if self.smooth_follow and not self.smooth_timer.isActive():
            self.smooth_timer.start()

        print("Mouse following started")

    def stop_mouse_following(self):
        """线程安全的停止跟随"""
        self.stop_following_signal.emit()

    def stop_mouse_following_impl(self):
        """停止鼠标跟随"""
        self.mouse_following = False

        if self.mouse_timer.isActive():
            self.mouse_timer.stop()

        if self.smooth_timer.isActive():
            self.smooth_timer.stop()

        print("Mouse following stopped")

    def _update_mouse_position(self):
        """更新鼠标位置"""
        if not self.mouse_following or not self.isVisible():
            return

        cursor_pos = QCursor.pos()
        self.target_x = cursor_pos.x() + self.follow_offset_x
        self.target_y = cursor_pos.y() + self.follow_offset_y

        # 屏幕边界检测
        self.target_x, self.target_y = self._clamp_to_screen(self.target_x, self.target_y)

        if not self.smooth_follow:
            # 直接跟随
            self._update_position(self.target_x, self.target_y)

    def _smooth_follow_update(self):
        """平滑跟随更新"""
        if not self.mouse_following or not self.isVisible():
            return

        # 计算当前位置到目标位置的距离
        dx = self.target_x - self.current_x
        dy = self.target_y - self.current_y
        distance = math.sqrt(dx * dx + dy * dy)

        # 如果距离很小，直接移动到目标位置
        if distance < 1:
            self.current_x = self.target_x
            self.current_y = self.target_y
        else:
            # 平滑插值
            self.current_x += dx * self.follow_speed
            self.current_y += dy * self.follow_speed

        # 更新位置
        self.move(int(self.current_x), int(self.current_y))
        self.position_updated.emit(int(self.current_x), int(self.current_y))

    def _update_position(self, x, y):
        """更新位置"""
        # 屏幕边界检测
        x, y = self._clamp_to_screen(x, y)

        self.current_x = x
        self.current_y = y
        self.target_x = x
        self.target_y = y

        self.move(x, y)
        self.position_updated.emit(x, y)

    def _clamp_to_screen(self, x, y):
        """将位置限制在屏幕范围内"""
        try:
            screen = QApplication.primaryScreen()
            if screen:
                screen_rect = screen.availableGeometry()

                # 限制X坐标
                x = max(screen_rect.left() + self.screen_margin,
                        min(x, screen_rect.right() - self.width() - self.screen_margin))

                # 限制Y坐标
                y = max(screen_rect.top() + self.screen_margin,
                        min(y, screen_rect.bottom() - self.height() - self.screen_margin))

        except Exception as e:
            print(f"Screen clamping error: {e}")

        return x, y

    def _fade_in(self):
        """淡入动画"""
        if self.fade_animation:
            self.fade_animation.stop()
            self.fade_animation.setStartValue(0)
            self.fade_animation.setEndValue(1)
            self.fade_animation.start()

    def _fade_out(self):
        """淡出动画"""
        if self.fade_animation:
            self.fade_animation.stop()
            self.fade_animation.setStartValue(self.windowOpacity())
            self.fade_animation.setEndValue(0)
            self.fade_animation.finished.connect(self._on_fade_out_finished)
            self.fade_animation.start()

    def _on_fade_out_finished(self):
        """淡出完成后隐藏窗口"""
        self.hide()
        self.fade_animation.finished.disconnect()

    def hide_animated(self, stop_following=True):
        """线程安全的隐藏"""
        self.hide_animated_signal.emit(stop_following)

    def hide_animated_impl(self, stop_following=True):
        """带动画的隐藏"""
        if stop_following:
            self.stop_mouse_following()

        if self.isVisible():
            self._fade_out()
            self.visibility_changed.emit(False)
            print("FloatingIndicator hiding with animation")

    def hide(self):
        """立即隐藏"""
        self.stop_mouse_following()
        super().hide()
        self.visibility_changed.emit(False)
        print("FloatingIndicator hidden immediately")

    def update_text(self, text):
        """更新显示文本"""
        self.label.setText(text)
        print(f"FloatingIndicator text updated: {text}")

    def set_follow_speed(self, speed):
        """设置跟随速度 (0-1之间)"""
        self.follow_speed = max(0.01, min(1.0, speed))
        print(f"Follow speed set to: {self.follow_speed}")

    def set_smooth_follow(self, enabled):
        """设置是否启用平滑跟随"""
        self.smooth_follow = enabled
        if enabled and self.mouse_following and not self.smooth_timer.isActive():
            self.smooth_timer.start()
        elif not enabled and self.smooth_timer.isActive():
            self.smooth_timer.stop()

        print(f"Smooth follow {'enabled' if enabled else 'disabled'}")

    def set_offset(self, offset_x, offset_y):
        """设置鼠标偏移量"""
        self.follow_offset_x = offset_x
        self.follow_offset_y = offset_y
        print(f"Offset set to: ({offset_x}, {offset_y})")

    def get_status(self):
        """获取当前状态信息"""
        return {
            'visible': self.isVisible(),
            'mouse_following': self.mouse_following,
            'smooth_follow': self.smooth_follow,
            'follow_speed': self.follow_speed,
            'position': (self.x(), self.y()),
            'target_position': (self.target_x, self.target_y),
            'offset': (self.follow_offset_x, self.follow_offset_y),
            'text': self.label.text()
        }

    def closeEvent(self, event):
        """关闭事件"""
        self.stop_mouse_following()
        super().closeEvent(event)
