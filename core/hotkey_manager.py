import platform
from abc import ABC, abstractmethod
from typing import Set, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from pynput import keyboard
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
                               QLineEdit, QTextEdit, QCheckBox, QGroupBox, QWidget, QGraphicsDropShadowEffect)
from PySide6.QtCore import (Qt, QTimer, QPropertyAnimation, QObject, Signal, QByteArray, QThread)
from PySide6.QtGui import (QPainter, QPen, QColor, QCursor, QFont)
import sys
import signal


class ModifierKey(Enum):
    """修饰键枚举"""
    CTRL = "ctrl"
    ALT = "alt"
    SHIFT = "shift"
    CMD = "cmd"


@dataclass
class HotkeyCombo:
    """热键组合数据类"""
    modifiers: Set[ModifierKey]
    key: str

    @classmethod
    def parse(cls, hotkey_str: str) -> 'HotkeyCombo':
        """解析热键字符串"""
        parts = [part.strip().lower() for part in hotkey_str.split('+')]
        modifiers = set()
        key = None

        for part in parts:
            if part in ['ctrl', 'control']:
                modifiers.add(ModifierKey.CTRL)
            elif part in ['alt', 'option']:
                modifiers.add(ModifierKey.ALT)
            elif part in ['shift']:
                modifiers.add(ModifierKey.SHIFT)
            elif part in ['cmd', 'command', 'meta']:
                modifiers.add(ModifierKey.CMD)
            else:
                key = part

        if not key:
            raise ValueError(f"Invalid hotkey format: {hotkey_str}")

        return cls(modifiers=modifiers, key=key)


class HotkeyState(Enum):
    """热键状态枚举"""
    IDLE = "idle"  # 空闲状态
    MODIFIERS_READY = "ready"  # 修饰键已按下，等待主键
    ACTIVATED = "activated"  # 热键已激活
    ERROR = "error"  # 错误状态


class KeyboardState:
    """键盘状态管理器 - 统一管理按键状态"""

    def __init__(self):
        self.pressed_keys: Set[str] = set()
        self._state_callbacks = []

    def add_key(self, key: str):
        """添加按下的键"""
        self.pressed_keys.add(key)
        self._notify_state_change()

    def remove_key(self, key: str):
        """移除释放的键"""
        self.pressed_keys.discard(key)
        self._notify_state_change()

    def clear(self):
        """清空所有按键状态"""
        self.pressed_keys.clear()
        self._notify_state_change()

    def is_modifier_pressed(self, modifier: ModifierKey) -> bool:
        """检查修饰键是否按下"""
        modifier_map = {
            ModifierKey.CTRL: ['ctrl', 'ctrl_l', 'ctrl_r'],
            ModifierKey.ALT: ['alt', 'alt_l', 'alt_r'],
            ModifierKey.SHIFT: ['shift', 'shift_l', 'shift_r'],
            ModifierKey.CMD: ['cmd', 'cmd_l', 'cmd_r']
        }

        keys_to_check = modifier_map.get(modifier, [])
        return any(self.is_key_pressed(key) for key in keys_to_check)

    def are_modifiers_pressed(self, modifiers: Set[ModifierKey]) -> bool:
        """检查多个修饰键是否都按下"""
        return all(self.is_modifier_pressed(modifier) for modifier in modifiers)

    def is_key_pressed(self, key: str) -> bool:
        """检查特定键是否按下"""
        return key in self.pressed_keys

    def add_state_callback(self, callback: Callable):
        """添加状态变化回调"""
        self._state_callbacks.append(callback)

    def _notify_state_change(self):
        """通知状态变化"""
        for callback in self._state_callbacks:
            callback(self.pressed_keys.copy())


class HotkeyStateMachine:
    """热键状态机 - 管理热键激活逻辑和状态转换"""

    def __init__(self, combo: HotkeyCombo):
        self.combo = combo
        self.current_state = HotkeyState.IDLE
        self._state_callbacks: Dict[HotkeyState, list] = {
            state: [] for state in HotkeyState
        }

    def update_state(self, keyboard_state: KeyboardState):
        """根据键盘状态更新热键状态"""
        old_state = self.current_state
        new_state = self._calculate_new_state(keyboard_state)

        if old_state != new_state:
            self.current_state = new_state
            self._notify_state_change(old_state, new_state)

    def _calculate_new_state(self, keyboard_state: KeyboardState) -> HotkeyState:
        """计算新的热键状态"""
        modifiers_pressed = keyboard_state.are_modifiers_pressed(self.combo.modifiers)
        main_key_pressed = keyboard_state.is_key_pressed(self.combo.key)

        if modifiers_pressed and main_key_pressed:
            return HotkeyState.ACTIVATED
        elif modifiers_pressed:
            return HotkeyState.MODIFIERS_READY
        else:
            return HotkeyState.IDLE

    def add_state_callback(self, state: HotkeyState, callback: Callable):
        """添加特定状态的回调"""
        self._state_callbacks[state].append(callback)

    def _notify_state_change(self, old_state: HotkeyState, new_state: HotkeyState):
        """通知状态变化"""
        # 调用新状态的回调
        for callback in self._state_callbacks[new_state]:
            callback(old_state, new_state)


class FeedbackManager(QObject):
    """反馈管理器 - 统一管理所有用户反馈"""

    # 定义信号
    show_idle_signal = Signal()
    show_activated_signal = Signal(str)
    show_error_signal = Signal(str)

    def __init__(self):
        super().__init__()  # 调用父类构造函数

        self.floating_indicator = FloatingIndicator()
        self.screen_overlay = ScreenOverlay()
        self.sound_feedback = SoundFeedback()

        self._current_feedback_state = None

        # 连接信号到槽函数（确保在主线程中）
        self.show_idle_signal.connect(self._show_idle_state)
        self.show_activated_signal.connect(self._show_activated_state)
        self.show_error_signal.connect(self._show_error_state)

    def show_ready_state(self):
        """显示准备状态反馈"""
        if self._current_feedback_state != "ready":
            self.floating_indicator.show_at_cursor("🔥 Ready")
            self.screen_overlay.show_overlay()
            self.sound_feedback.play_activate_sound()
            self._current_feedback_state = "ready"

    def show_activated_state(self, message: str = "Activated!"):
        self.show_activated_signal.emit(message)

    def _show_activated_state(self, message: str = "Activated!"):
        """显示激活状态反馈"""
        self.floating_indicator.show_at_cursor(f"✅ {message}")
        self.sound_feedback.play_capture_sound()
        self._current_feedback_state = "activated"

        QTimer.singleShot(3000, self.show_idle_signal.emit)

    def show_error_state(self, message: str = "Error"):
        self.show_error_signal.emit(message)

    def _show_error_state(self, message: str = "Error"):
        """显示错误状态反馈"""
        self.floating_indicator.show_at_cursor(f"❌ {message}")
        self._current_feedback_state = "error"

        QTimer.singleShot(3000, self.show_idle_signal.emit)

    def show_idle_state(self):
        self.show_idle_signal.emit()

    def _show_idle_state(self):
        """显示空闲状态（隐藏所有反馈）"""
        if self._current_feedback_state in ["ready", "activated", "error"]:
            self.floating_indicator.hide_animated()
            self.screen_overlay.hide_overlay()
            self._current_feedback_state = "idle"


class PlatformHandler(ABC):
    """平台处理器抽象基类 - 只负责底层平台相关功能"""

    @abstractmethod
    def start_keyboard_listener(self, on_key_press: Callable, on_key_release: Callable):
        """开始键盘监听"""
        pass

    @abstractmethod
    def stop_keyboard_listener(self):
        """停止键盘监听"""
        pass

    @abstractmethod
    def start_mouse_hook(self, callback: Callable):
        """开始鼠标钩子监听"""
        pass

    @abstractmethod
    def stop_mouse_hook(self):
        """停止鼠标钩子监听"""
        pass

    @abstractmethod
    def normalize_key(self, key) -> Optional[str]:
        """标准化按键名称"""
        pass


class WindowsHandler(PlatformHandler):
    """Windows平台处理器 - 简化为只处理平台相关功能"""

    def __init__(self):
        self.listener = None
        self.mouse_hook = None
        self._setup_mouse_hook()

    def _setup_mouse_hook(self):
        """设置Windows鼠标钩子"""
        try:
            import ctypes
            self.user32 = ctypes.WinDLL('user32', use_last_error=True)
            self.kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

            # Windows API常量和设置
            self.WH_MOUSE_LL = 14
            self.WM_LBUTTONDOWN = 0x0201
            self.VK_MENU = 0x12

            self.MOUSEEVENTPROC = ctypes.WINFUNCTYPE(
                ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)
            )

            # API函数设置
            self.user32.SetWindowsHookExA.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
            self.user32.SetWindowsHookExA.restype = ctypes.c_void_p
            self.user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
            self.user32.CallNextHookEx.restype = ctypes.c_int
            self.user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
            self.user32.UnhookWindowsHookEx.restype = ctypes.c_int
            self.user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
            self.user32.GetAsyncKeyState.restype = ctypes.c_short
            self.kernel32.GetModuleHandleA.argtypes = [ctypes.c_char_p]
            self.kernel32.GetModuleHandleA.restype = ctypes.c_void_p

            self.hooked = False
            self.mouse_proc = None

        except ImportError as e:
            print(f"Warning: Windows-specific libraries not available: {e}")
            self.user32 = None

    def start_keyboard_listener(self, on_key_press: Callable, on_key_release: Callable):
        """启动键盘监听"""

        def press_handler(key):
            try:
                normalized_key = self.normalize_key(key)
                if normalized_key:
                    on_key_press(normalized_key)
            except Exception as e:
                print(f"Error in key press: {e}")

        def release_handler(key):
            try:
                normalized_key = self.normalize_key(key)
                if normalized_key:
                    on_key_release(normalized_key)
            except Exception as e:
                print(f"Error in key release: {e}")

        self.listener = keyboard.Listener(on_press=press_handler, on_release=release_handler)
        self.listener.daemon = True
        self.listener.start()

    def stop_keyboard_listener(self):
        """停止键盘监听"""
        if self.listener:
            self.listener.stop()
            self.listener = None

    def start_mouse_hook(self, callback: Callable):
        """启动鼠标钩子"""
        if not self.user32:
            return False

        def low_level_mouse_proc(n_code, w_param, l_param):
            if n_code >= 0 and w_param == self.WM_LBUTTONDOWN and self._is_alt_pressed():
                callback()
            return self.user32.CallNextHookEx(self.mouse_hook, n_code, w_param, l_param)

        self.mouse_proc = self.MOUSEEVENTPROC(low_level_mouse_proc)
        self.mouse_hook = self.user32.SetWindowsHookExA(
            self.WH_MOUSE_LL, self.mouse_proc,
            self.kernel32.GetModuleHandleA(None), 0
        )

        if self.mouse_hook:
            self.hooked = True
            return True
        return False

    def stop_mouse_hook(self):
        """停止鼠标钩子"""
        if self.hooked and self.mouse_hook:
            self.user32.UnhookWindowsHookEx(self.mouse_hook)
            self.hooked = False
            self.mouse_hook = None

    def normalize_key(self, key) -> Optional[str]:
        """标准化按键名称"""
        try:
            if hasattr(key, 'char') and key.char:
                return key.char.lower()
            elif hasattr(key, 'name'):
                return key.name.lower()
            else:
                return str(key).split('.')[-1].lower()
        except:
            return None

    def _is_alt_pressed(self) -> bool:
        """检查Alt键是否按下"""
        try:
            return (self.user32.GetAsyncKeyState(self.VK_MENU) & 0x8000) != 0
        except:
            return False


class MacOSHandler(PlatformHandler):
    """macOS平台处理器"""

    def __init__(self):
        self.listener = None
        self.mouse_monitor = None
        self._setup_cocoa()

    def _setup_cocoa(self):
        """设置macOS Cocoa框架"""
        try:
            import Cocoa
            import Quartz
            self.Cocoa = Cocoa
            self.Quartz = Quartz
        except ImportError:
            print("Warning: macOS-specific libraries not available")
            self.Cocoa = None
            self.Quartz = None

    def start_keyboard_listener(self, on_key_press: Callable, on_key_release: Callable):
        """启动键盘监听"""

        def press_handler(key):
            try:
                normalized_key = self.normalize_key(key)
                if normalized_key:
                    on_key_press(normalized_key)
            except Exception as e:
                print(f"Error in key press: {e}")

        def release_handler(key):
            try:
                normalized_key = self.normalize_key(key)
                if normalized_key:
                    on_key_release(normalized_key)
            except Exception as e:
                print(f"Error in key release: {e}")

        self.listener = keyboard.Listener(on_press=press_handler, on_release=release_handler)
        self.listener.daemon = True
        self.listener.start()

    def stop_keyboard_listener(self):
        """停止键盘监听"""
        if self.listener:
            self.listener.stop()
            self.listener = None

    def start_mouse_hook(self, callback: Callable):
        """启动鼠标监听（macOS版本）"""
        if not self.Cocoa or not self.Quartz:
            return False

        def mouse_handler(proxy, event_type, event, refcon):
            try:
                if event_type == self.Quartz.kCGEventLeftMouseDown:
                    flags = self.Quartz.CGEventGetFlags(event)
                    if flags & self.Quartz.kCGEventFlagMaskAlternate:
                        callback()
            except Exception as e:
                print(f"Error in mouse handler: {e}")
            return event

        self.mouse_monitor = self.Quartz.CGEventTapCreate(
            self.Quartz.kCGSessionEventTap,
            self.Quartz.kCGHeadInsertEventTap,
            self.Quartz.kCGEventTapOptionDefault,
            1 << self.Quartz.kCGEventLeftMouseDown,
            mouse_handler, None
        )

        if self.mouse_monitor:
            run_loop_source = self.Quartz.CFMachPortCreateRunLoopSource(None, self.mouse_monitor, 0)
            self.Quartz.CFRunLoopAddSource(
                self.Quartz.CFRunLoopGetCurrent(), run_loop_source, self.Quartz.kCFRunLoopDefaultMode
            )
            self.Quartz.CGEventTapEnable(self.mouse_monitor, True)
            return True
        return False

    def stop_mouse_hook(self):
        """停止鼠标监听"""
        if self.mouse_monitor:
            self.Quartz.CGEventTapEnable(self.mouse_monitor, False)
            self.mouse_monitor = None

    def normalize_key(self, key) -> Optional[str]:
        """标准化按键名称（macOS版本）"""
        try:
            if hasattr(key, 'char') and key.char:
                return key.char.lower()
            elif hasattr(key, 'name'):
                name = key.name.lower()
                if name == 'cmd':
                    return 'cmd'
                return name
            else:
                return str(key).split('.')[-1].lower()
        except:
            return None


class CrossPlatformHotkeyManager(QObject):
    """重构后的跨平台热键管理器 - 清晰的架构"""

    # 信号定义
    hotkey_activated = Signal()
    mouse_clicked = Signal()
    state_changed = Signal(str)  # 状态变化信号

    def __init__(self, hotkey: str = 'alt+c'):
        super().__init__()

        # 核心组件
        self.hotkey_combo = HotkeyCombo.parse(hotkey)
        self.keyboard_state = KeyboardState()
        self.state_machine = HotkeyStateMachine(self.hotkey_combo)
        self.feedback_manager = FeedbackManager()
        self.platform_handler = self._create_platform_handler()

        self._running = False
        self._setup_connections()

        print(f"Initialized for platform: {platform.system()}")
        print(f"Hotkey combination: {hotkey}")

    def _create_platform_handler(self) -> PlatformHandler:
        """创建平台处理器"""
        system = platform.system().lower()

        if system == 'windows':
            return WindowsHandler()
        elif system == 'darwin':
            return MacOSHandler()
        else:
            print(f"Warning: Platform {system} not fully supported, using Windows handler")
            return WindowsHandler()

    def _setup_connections(self):
        """设置组件间的连接"""
        # 键盘状态变化时更新状态机
        self.keyboard_state.add_state_callback(lambda keys: self.state_machine.update_state(self.keyboard_state))

        # 状态机状态变化时更新反馈和发送信号
        self.state_machine.add_state_callback(HotkeyState.MODIFIERS_READY, self._on_modifiers_ready)
        self.state_machine.add_state_callback(HotkeyState.ACTIVATED, self._on_hotkey_activated)
        self.state_machine.add_state_callback(HotkeyState.IDLE, self._on_state_idle)

    def start(self, enable_mouse_hook: bool = True):
        """启动热键和鼠标监听"""
        if self._running:
            return

        try:
            # 启动键盘监听
            self.platform_handler.start_keyboard_listener(
                self._on_key_press,
                self._on_key_release
            )
            print("Keyboard listener started successfully")

            # 启动鼠标钩子监听（可选）
            if enable_mouse_hook:
                success = self.platform_handler.start_mouse_hook(self._on_mouse_clicked)
                if success:
                    print("Mouse hook started successfully")
                else:
                    print("Mouse hook could not be started")
            else:
                print("Mouse hook disabled")

            self._running = True
            print("Hotkey manager started")

        except Exception as e:
            print(f"Error starting hotkey manager: {e}")
            self.feedback_manager.show_error_state(f"Start failed: {e}")

    def stop(self):
        """停止热键和鼠标监听"""
        if not self._running:
            return

        try:
            self.platform_handler.stop_keyboard_listener()
            self.platform_handler.stop_mouse_hook()
            self.keyboard_state.clear()
            self.feedback_manager.show_idle_state()
            self._running = False
            print("Hotkey manager stopped")

        except Exception as e:
            print(f"Error stopping hotkey manager: {e}")

    def change_hotkey(self, new_hotkey: str):
        """更改热键组合"""
        was_running = self._running

        if was_running:
            self.stop()

        try:
            self.hotkey_combo = HotkeyCombo.parse(new_hotkey)
            self.state_machine = HotkeyStateMachine(self.hotkey_combo)
            self._setup_connections()
            print(f"Hotkey changed to: {new_hotkey}")

            if was_running:
                self.start()

        except ValueError as e:
            print(f"Invalid hotkey format: {e}")
            self.feedback_manager.show_error_state(f"Invalid hotkey: {e}")

    def _on_key_press(self, key: str):
        """按键按下处理"""
        self.keyboard_state.add_key(key)

    def _on_key_release(self, key: str):
        """按键释放处理"""
        self.keyboard_state.remove_key(key)

    def _on_modifiers_ready(self, old_state: HotkeyState, new_state: HotkeyState):
        """修饰键准备状态处理"""
        print("Modifiers ready - showing feedback")
        self.feedback_manager.show_ready_state()
        self.state_changed.emit("ready")

    def _on_hotkey_activated(self, old_state: HotkeyState, new_state: HotkeyState):
        """热键激活处理"""
        print(f"Hotkey activated: {self.hotkey_combo}")
        self.feedback_manager.show_activated_state("Hotkey Activated!")
        self.state_changed.emit("activated")
        self.hotkey_activated.emit()

    def _on_state_idle(self, old_state: HotkeyState, new_state: HotkeyState):
        """空闲状态处理"""
        if old_state != HotkeyState.IDLE:
            self.feedback_manager.show_idle_state()
            self.state_changed.emit("idle")

    def _on_mouse_clicked(self):
        """Alt+鼠标点击处理"""
        print("Alt+Mouse click detected")
        self.feedback_manager.show_activated_state("Alt+Click!")
        self.mouse_clicked.emit()

    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._running

    def get_current_state(self) -> str:
        """获取当前状态"""
        return self.state_machine.current_state.value

    def get_platform_info(self) -> Dict[str, Any]:
        """获取平台信息"""
        return {
            'platform': platform.system(),
            'handler_type': type(self.platform_handler).__name__,
            'hotkey': str(self.hotkey_combo),
            'current_state': self.get_current_state(),
            'running': self._running
        }


# 保持原有的UI组件类（简化版本）
class FloatingIndicator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setFixedSize(200, 50)

        self.label = QLabel("🔥 Ready", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 107, 129, 200), stop:1 rgba(255, 154, 158, 200));
                color: white; border-radius: 20px; font-weight: bold;
                font-size: 12px; padding: 8px 16px;
            }
        """)
        self.label.setGeometry(0, 0, 120, 40)

    def show_at_cursor(self, text="TEST"):
        self.label.setText(text)
        cursor_pos = QCursor.pos()
        self.move(cursor_pos.x(), cursor_pos.y())
        self.show()

    def hide_animated(self):
        self.hide()

class ScreenOverlay(QWidget):
    """全屏遮罩"""

    # 如果需要跨线程控制，添加信号
    show_overlay_signal = Signal()
    hide_overlay_signal = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        # 在初始化时创建timer
        self.update_timer = QTimer(self)  # 指定parent
        self.update_timer.timeout.connect(self.update)

        # 如果需要跨线程控制
        self.show_overlay_signal.connect(self._show_overlay)
        self.hide_overlay_signal.connect(self._hide_overlay)

    def show_overlay(self):
        # 检查是否在主线程
        if QThread.currentThread() != QApplication.instance().thread():
            self.show_overlay_signal.emit()
            return
        self._show_overlay()

    def _show_overlay(self):
        self.show()
        self.update_timer.start(16)  # 约60fps

    def hide_overlay(self):
        # 检查是否在主线程
        if QThread.currentThread() != QApplication.instance().thread():
            self.hide_overlay_signal.emit()
            return
        self._hide_overlay()

    def _hide_overlay(self):
        self.update_timer.stop()
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 30))
        cursor_pos = self.mapFromGlobal(QCursor.pos())
        painter.setPen(QPen(QColor(255, 255, 255, 150), 1, Qt.PenStyle.DashLine))
        painter.drawLine(cursor_pos.x(), 0, cursor_pos.x(), self.height())
        painter.drawLine(0, cursor_pos.y(), self.width(), cursor_pos.y())


class SoundFeedback:
    """声音反馈"""

    def __init__(self):
        self.activate_sound = None
        self.capture_sound = None

    def play_activate_sound(self):
        pass  # 实现音效播放

    def play_capture_sound(self):
        pass  # 实现音效播放


# 使用示例
# 使用示例和主函数
if __name__ == "__main__":
    class HotkeyTestWindow(QMainWindow):
        """热键测试主窗口"""

        def __init__(self):
            super().__init__()
            self.hotkey_manager = None
            self.init_ui()
            self.setup_hotkey_manager()

        def init_ui(self):
            """初始化UI界面"""
            self.setWindowTitle("热键管理器测试程序")
            self.setGeometry(100, 100, 500, 600)

            # 创建中央窗口部件
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)

            # 标题
            title_label = QLabel("🔥 跨平台热键管理器")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            title_label.setStyleSheet("color: #FF6B81; margin: 10px;")
            layout.addWidget(title_label)

            # 热键配置组
            hotkey_group = QGroupBox("热键配置")
            hotkey_layout = QVBoxLayout(hotkey_group)

            # 热键输入
            hotkey_input_layout = QHBoxLayout()
            hotkey_input_layout.addWidget(QLabel("热键组合:"))
            self.hotkey_input = QLineEdit("alt+c")
            self.hotkey_input.setPlaceholderText("例如: ctrl+shift+c, alt+x")
            hotkey_input_layout.addWidget(self.hotkey_input)

            self.change_hotkey_btn = QPushButton("更改热键")
            self.change_hotkey_btn.clicked.connect(self.change_hotkey)
            hotkey_input_layout.addWidget(self.change_hotkey_btn)

            hotkey_layout.addLayout(hotkey_input_layout)

            # 鼠标钩子选项
            self.mouse_hook_checkbox = QCheckBox("启用 Alt+鼠标点击检测")
            self.mouse_hook_checkbox.setChecked(True)
            hotkey_layout.addWidget(self.mouse_hook_checkbox)

            layout.addWidget(hotkey_group)

            # 控制按钮组
            control_group = QGroupBox("控制")
            control_layout = QHBoxLayout(control_group)

            self.start_btn = QPushButton("启动监听")
            self.start_btn.clicked.connect(self.start_monitoring)
            self.start_btn.setStyleSheet(
                "QPushButton { background-color: #4CAF50; color: white; padding: 8px; border-radius: 4px; }")
            control_layout.addWidget(self.start_btn)

            self.stop_btn = QPushButton("停止监听")
            self.stop_btn.clicked.connect(self.stop_monitoring)
            self.stop_btn.setEnabled(False)
            self.stop_btn.setStyleSheet(
                "QPushButton { background-color: #f44336; color: white; padding: 8px; border-radius: 4px; }")
            control_layout.addWidget(self.stop_btn)

            self.test_btn = QPushButton("测试反馈")
            self.test_btn.clicked.connect(self.test_feedback)
            self.test_btn.setStyleSheet(
                "QPushButton { background-color: #2196F3; color: white; padding: 8px; border-radius: 4px; }")
            control_layout.addWidget(self.test_btn)

            layout.addWidget(control_group)

            # 状态显示组
            status_group = QGroupBox("状态信息")
            status_layout = QVBoxLayout(status_group)

            self.status_label = QLabel("状态: 未启动")
            self.status_label.setStyleSheet("font-weight: bold; color: #666;")
            status_layout.addWidget(self.status_label)

            self.platform_label = QLabel("平台信息: 加载中...")
            self.platform_label.setStyleSheet("color: #888;")
            status_layout.addWidget(self.platform_label)

            layout.addWidget(status_group)

            # 事件日志组
            log_group = QGroupBox("事件日志")
            log_layout = QVBoxLayout(log_group)

            self.log_text = QTextEdit()
            self.log_text.setMaximumHeight(200)
            self.log_text.setStyleSheet("font-family: Consolas, monospace; font-size: 10px;")
            log_layout.addWidget(self.log_text)

            clear_log_btn = QPushButton("清空日志")
            clear_log_btn.clicked.connect(self.clear_log)
            log_layout.addWidget(clear_log_btn)

            layout.addWidget(log_group)

            # 使用说明
            help_group = QGroupBox("使用说明")
            help_layout = QVBoxLayout(help_group)

            help_text = QLabel("""
            • 支持的修饰键: ctrl, alt, shift, cmd(macOS)
            • 热键格式: modifier+key (例如: alt+c, ctrl+shift+x)
            • 按下修饰键会显示准备状态反馈
            • 完整按下热键组合会触发激活事件
            • Alt+鼠标左键点击也会触发事件（可选）
            """)
            help_text.setWordWrap(True)
            help_text.setStyleSheet("color: #666; font-size: 11px;")
            help_layout.addWidget(help_text)

            layout.addWidget(help_group)

        def setup_hotkey_manager(self):
            """设置热键管理器"""
            try:
                self.hotkey_manager = CrossPlatformHotkeyManager('alt+c')

                # 连接信号
                self.hotkey_manager.hotkey_activated.connect(self.on_hotkey_activated)
                self.hotkey_manager.mouse_clicked.connect(self.on_mouse_clicked)
                self.hotkey_manager.state_changed.connect(self.on_state_changed)

                # 更新平台信息
                platform_info = self.hotkey_manager.get_platform_info()
                self.platform_label.setText(
                    f"平台: {platform_info['platform']} | "
                    f"处理器: {platform_info['handler_type']} | "
                    f"当前热键: {platform_info['hotkey']}"
                )

                self.log_message("热键管理器初始化成功")

            except Exception as e:
                self.log_message(f"初始化失败: {e}", "ERROR")

        def start_monitoring(self):
            """启动监听"""
            if self.hotkey_manager:
                try:
                    enable_mouse = self.mouse_hook_checkbox.isChecked()
                    self.hotkey_manager.start(enable_mouse_hook=enable_mouse)

                    self.start_btn.setEnabled(False)
                    self.stop_btn.setEnabled(True)
                    self.status_label.setText("状态: 监听中")
                    self.status_label.setStyleSheet("font-weight: bold; color: #4CAF50;")

                    mouse_status = "启用" if enable_mouse else "禁用"
                    self.log_message(f"开始监听热键，鼠标钩子: {mouse_status}")

                except Exception as e:
                    self.log_message(f"启动监听失败: {e}", "ERROR")

        def stop_monitoring(self):
            """停止监听"""
            if self.hotkey_manager:
                try:
                    self.hotkey_manager.stop()

                    self.start_btn.setEnabled(True)
                    self.stop_btn.setEnabled(False)
                    self.status_label.setText("状态: 已停止")
                    self.status_label.setStyleSheet("font-weight: bold; color: #f44336;")

                    self.log_message("停止监听热键")

                except Exception as e:
                    self.log_message(f"停止监听失败: {e}", "ERROR")

        def change_hotkey(self):
            """更改热键"""
            new_hotkey = self.hotkey_input.text().strip()
            if not new_hotkey:
                self.log_message("热键不能为空", "ERROR")
                return

            if self.hotkey_manager:
                try:
                    self.hotkey_manager.change_hotkey(new_hotkey)
                    self.log_message(f"热键已更改为: {new_hotkey}")

                    # 更新平台信息显示
                    platform_info = self.hotkey_manager.get_platform_info()
                    self.platform_label.setText(
                        f"平台: {platform_info['platform']} | "
                        f"处理器: {platform_info['handler_type']} | "
                        f"当前热键: {platform_info['hotkey']}"
                    )

                except Exception as e:
                    self.log_message(f"更改热键失败: {e}", "ERROR")

        def test_feedback(self):
            """测试反馈效果"""
            if self.hotkey_manager:
                self.hotkey_manager.feedback_manager.show_activated_state("测试反馈效果!")
                self.log_message("测试反馈效果")

        def on_hotkey_activated(self):
            """热键激活回调"""
            self.log_message("🔥 热键被激活!", "SUCCESS")

        def on_mouse_clicked(self):
            """鼠标点击回调"""
            self.log_message("🖱️ Alt+鼠标点击检测到!", "SUCCESS")

        def on_state_changed(self, state):
            """状态变化回调"""
            state_map = {
                "idle": "空闲",
                "ready": "准备就绪",
                "activated": "已激活",
                "error": "错误"
            }
            chinese_state = state_map.get(state, state)
            self.log_message(f"状态变化: {chinese_state}")

        def log_message(self, message, level="INFO"):
            """记录日志消息"""
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")

            # 根据级别设置颜色
            color_map = {
                "INFO": "#333",
                "SUCCESS": "#4CAF50",
                "ERROR": "#f44336",
                "WARNING": "#FF9800"
            }
            color = color_map.get(level, "#333")

            # 添加到日志
            log_entry = f'<span style="color: {color};">[{timestamp}] {message}</span>'
            self.log_text.append(log_entry)

            # 自动滚动到底部
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

        def clear_log(self):
            """清空日志"""
            self.log_text.clear()
            self.log_message("日志已清空")

        def closeEvent(self, event):
            """窗口关闭事件"""
            if self.hotkey_manager and self.hotkey_manager.is_running():
                self.hotkey_manager.stop()
            event.accept()


    # 主函数
    def main():
        """主函数 - 启动热键管理器测试应用"""
        print("=" * 50)
        print("🔥 跨平台热键管理器测试程序")
        print("=" * 50)

        app = QApplication(sys.argv)

        # 设置应用程序信息
        app.setApplicationName("Hotkey Manager")
        app.setApplicationVersion("1.0")
        app.setOrganizationName("CrossPlatform Solutions")

        # 创建主窗口
        window = HotkeyTestWindow()
        window.show()

        # 设置优雅退出
        def signal_handler(signum, frame):
            print("\n正在优雅退出...")
            if window.hotkey_manager and window.hotkey_manager.is_running():
                window.hotkey_manager.stop()
            app.quit()

        signal.signal(signal.SIGINT, signal_handler)

        # 启动事件循环
        print("应用程序已启动，请在GUI中进行操作")
        print("按 Ctrl+C 可以优雅退出程序")

        try:
            exit_code = app.exec()
            print("应用程序正常退出")
            return exit_code
        except KeyboardInterrupt:
            print("\n程序被用户中断")
            return 0
        except Exception as e:
            print(f"程序异常退出: {e}")
            return 1


    # 简单使用示例
    def simple_example():
        """简单使用示例 - 无GUI版本"""
        print("🔥 简单热键管理器示例")
        print("按 Alt+C 触发热键，Alt+鼠标左键也会触发")
        print("按 Ctrl+C 退出程序")

        # 创建QApplication (即使无GUI也需要)
        app = QApplication(sys.argv)

        # 创建热键管理器
        manager = CrossPlatformHotkeyManager('alt+c')

        # 连接信号
        def on_hotkey():
            print("🔥 热键被激活!")

        def on_mouse():
            print("🖱️ Alt+鼠标点击!")

        def on_state_change(state):
            print(f"状态变化: {state}")

        manager.hotkey_activated.connect(on_hotkey)
        manager.mouse_clicked.connect(on_mouse)
        manager.state_changed.connect(on_state_change)

        # 启动监听
        manager.start()

        # 设置退出处理
        def signal_handler(signum, frame):
            print("\n正在退出...")
            manager.stop()
            app.quit()

        signal.signal(signal.SIGINT, signal_handler)

        # 运行
        try:
            app.exec()
        except KeyboardInterrupt:
            manager.stop()


    # 程序入口点
    # simple_example()
    main()
