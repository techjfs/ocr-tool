"""
跨平台热键管理器
支持 Windows 和 macOS 平台的全局热键监听和 Alt+鼠标点击功能
"""

import platform
import threading
from abc import ABC, abstractmethod
from typing import Set, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import QObject, Signal
from pynput import keyboard


class ModifierKey(Enum):
    """修饰键枚举"""
    CTRL = "ctrl"
    ALT = "alt"
    SHIFT = "shift"
    CMD = "cmd"  # macOS Command键


@dataclass
class HotkeyCombo:
    """热键组合数据类"""
    modifiers: Set[ModifierKey]
    key: str

    @classmethod
    def parse(cls, hotkey_str: str) -> 'HotkeyCombo':
        """解析热键字符串，如 'ctrl+alt+c' """
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


class PlatformHandler(ABC):
    """平台特定处理器抽象基类"""

    @abstractmethod
    def start_hotkey_listener(self, combo: HotkeyCombo, callback: Callable):
        """开始热键监听"""
        pass

    @abstractmethod
    def stop_hotkey_listener(self):
        """停止热键监听"""
        pass

    @abstractmethod
    def start_mouse_hook(self, callback: Callable):
        """开始鼠标钩子监听（Alt+点击）"""
        pass

    @abstractmethod
    def stop_mouse_hook(self):
        """停止鼠标钩子监听"""
        pass


class WindowsHandler(PlatformHandler):
    """Windows平台处理器"""

    def __init__(self):
        self.listener = None
        self.mouse_hook = None
        self.current_keys = set()
        self._setup_mouse_hook()

    def _setup_mouse_hook(self):
        """设置Windows鼠标钩子 - 基于原版本的简化实现"""
        try:
            import ctypes

            self.user32 = ctypes.WinDLL('user32', use_last_error=True)
            self.kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

            # Windows API常量
            self.WH_MOUSE_LL = 14
            self.WM_LBUTTONDOWN = 0x0201
            self.VK_MENU = 0x12  # ALT键

            # 鼠标钩子回调函数类型 - 保持和原版本一致
            self.MOUSEEVENTPROC = ctypes.WINFUNCTYPE(
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_void_p)
            )

            # API函数原型 - 简化版本
            self.user32.SetWindowsHookExA.argtypes = [
                ctypes.c_int,
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_uint
            ]
            self.user32.SetWindowsHookExA.restype = ctypes.c_void_p

            self.user32.CallNextHookEx.argtypes = [
                ctypes.c_void_p,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_void_p
            ]
            self.user32.CallNextHookEx.restype = ctypes.c_int

            self.user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
            self.user32.UnhookWindowsHookEx.restype = ctypes.c_int

            self.user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
            self.user32.GetAsyncKeyState.restype = ctypes.c_short

            self.kernel32.GetModuleHandleA.argtypes = [ctypes.c_char_p]
            self.kernel32.GetModuleHandleA.restype = ctypes.c_void_p

            self.hooked = False
            self.mouse_hook = None
            self.mouse_proc = None

        except ImportError as e:
            print(f"Warning: Windows-specific libraries not available: {e}")
            self.user32 = None

    def start_hotkey_listener(self, combo: HotkeyCombo, callback: Callable):
        """启动热键监听"""
        def on_press(key):
            try:
                normalized_key = self._normalize_key(key)
                if normalized_key:
                    self.current_keys.add(normalized_key)

                if self._is_combo_pressed(combo):
                    callback()
            except Exception as e:
                print(f"Error in hotkey press: {e}")

        def on_release(key):
            try:
                normalized_key = self._normalize_key(key)
                if normalized_key:
                    self.current_keys.discard(normalized_key)
            except Exception as e:
                print(f"Error in hotkey release: {e}")

        self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.listener.daemon = True
        self.listener.start()

    def stop_hotkey_listener(self):
        """停止热键监听"""
        if self.listener:
            self.listener.stop()
            self.listener = None

    def start_mouse_hook(self, callback: Callable):
        """启动鼠标钩子 - 基于原版本的实现"""
        if not self.user32:
            return False

        # 创建鼠标钩子回调函数 - 和原版本保持一致
        def low_level_mouse_proc(n_code, w_param, l_param):
            if n_code >= 0 and w_param == self.WM_LBUTTONDOWN and self._is_alt_pressed():
                # ALT键按下的情况下点击鼠标左键
                callback()

            # 调用下一个钩子
            return self.user32.CallNextHookEx(self.mouse_hook, n_code, w_param, l_param)

        # 创建回调函数类型
        self.mouse_proc = self.MOUSEEVENTPROC(low_level_mouse_proc)

        # 安装鼠标钩子 - 和原版本完全一致
        self.mouse_hook = self.user32.SetWindowsHookExA(
            self.WH_MOUSE_LL,
            self.mouse_proc,
            self.kernel32.GetModuleHandleA(None),
            0
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

    def _normalize_key(self, key) -> Optional[str]:
        """标准化按键"""
        try:
            if hasattr(key, 'char') and key.char:
                return key.char.lower()
            elif hasattr(key, 'name'):
                return key.name.lower()
            else:
                return str(key).split('.')[-1].lower()
        except:
            return None

    def _is_combo_pressed(self, combo: HotkeyCombo) -> bool:
        """检查热键组合是否被按下"""
        # 检查修饰键
        for modifier in combo.modifiers:
            if not self._is_modifier_pressed(modifier):
                return False

        # 检查主键
        if combo.key not in self.current_keys:
            return False

        return True

    def _is_modifier_pressed(self, modifier: ModifierKey) -> bool:
        """检查修饰键是否按下"""
        modifier_map = {
            ModifierKey.CTRL: ['ctrl', 'ctrl_l', 'ctrl_r'],
            ModifierKey.ALT: ['alt', 'alt_l', 'alt_r'],
            ModifierKey.SHIFT: ['shift', 'shift_l', 'shift_r'],
            ModifierKey.CMD: ['cmd', 'cmd_l', 'cmd_r']  # Windows上通常是Win键
        }

        keys_to_check = modifier_map.get(modifier, [])
        return any(key in self.current_keys for key in keys_to_check)

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
        self.current_keys = set()
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

    def start_hotkey_listener(self, combo: HotkeyCombo, callback: Callable):
        """启动热键监听（macOS版本）"""
        def on_press(key):
            try:
                normalized_key = self._normalize_key(key)
                if normalized_key:
                    self.current_keys.add(normalized_key)

                if self._is_combo_pressed(combo):
                    callback()
            except Exception as e:
                print(f"Error in hotkey press: {e}")

        def on_release(key):
            try:
                normalized_key = self._normalize_key(key)
                if normalized_key:
                    self.current_keys.discard(normalized_key)
            except Exception as e:
                print(f"Error in hotkey release: {e}")

        self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.listener.daemon = True
        self.listener.start()

    def stop_hotkey_listener(self):
        """停止热键监听"""
        if self.listener:
            self.listener.stop()
            self.listener = None

    def start_mouse_hook(self, callback: Callable):
        """启动鼠标监听（macOS版本）"""
        if not self.Cocoa or not self.Quartz:
            print("Warning: Mouse hook not available on this system")
            return False

        def mouse_handler(proxy, event_type, event, refcon):
            try:
                if event_type == self.Quartz.kCGEventLeftMouseDown:
                    # 检查Option键（Alt键）是否按下
                    flags = self.Quartz.CGEventGetFlags(event)
                    if flags & self.Quartz.kCGEventFlagMaskAlternate:
                        callback()
            except Exception as e:
                print(f"Error in mouse handler: {e}")
            return event

        # 创建事件监听器
        self.mouse_monitor = self.Quartz.CGEventTapCreate(
            self.Quartz.kCGSessionEventTap,
            self.Quartz.kCGHeadInsertEventTap,
            self.Quartz.kCGEventTapOptionDefault,
            1 << self.Quartz.kCGEventLeftMouseDown,
            mouse_handler,
            None
        )

        if self.mouse_monitor:
            run_loop_source = self.Quartz.CFMachPortCreateRunLoopSource(
                None, self.mouse_monitor, 0
            )
            self.Quartz.CFRunLoopAddSource(
                self.Quartz.CFRunLoopGetCurrent(),
                run_loop_source,
                self.Quartz.kCFRunLoopDefaultMode
            )
            self.Quartz.CGEventTapEnable(self.mouse_monitor, True)
            return True

        return False

    def stop_mouse_hook(self):
        """停止鼠标监听"""
        if self.mouse_monitor:
            self.Quartz.CGEventTapEnable(self.mouse_monitor, False)
            self.mouse_monitor = None

    def _normalize_key(self, key) -> Optional[str]:
        """标准化按键（macOS版本）"""
        try:
            if hasattr(key, 'char') and key.char:
                return key.char.lower()
            elif hasattr(key, 'name'):
                # macOS特殊键映射
                name = key.name.lower()
                if name == 'cmd':
                    return 'cmd'
                return name
            else:
                return str(key).split('.')[-1].lower()
        except:
            return None

    def _is_combo_pressed(self, combo: HotkeyCombo) -> bool:
        """检查热键组合是否被按下（macOS版本）"""
        for modifier in combo.modifiers:
            if not self._is_modifier_pressed(modifier):
                return False

        if combo.key not in self.current_keys:
            return False

        return True

    def _is_modifier_pressed(self, modifier: ModifierKey) -> bool:
        """检查修饰键是否按下（macOS版本）"""
        modifier_map = {
            ModifierKey.CTRL: ['ctrl', 'ctrl_l', 'ctrl_r'],
            ModifierKey.ALT: ['alt', 'alt_l', 'alt_r', 'option'],
            ModifierKey.SHIFT: ['shift', 'shift_l', 'shift_r'],
            ModifierKey.CMD: ['cmd', 'cmd_l', 'cmd_r']
        }

        keys_to_check = modifier_map.get(modifier, [])
        return any(key in self.current_keys for key in keys_to_check)


class HotkeyManagerFactory:
    """热键管理器工厂类"""

    @staticmethod
    def create_handler() -> PlatformHandler:
        """根据当前平台创建对应的处理器"""
        system = platform.system().lower()

        if system == 'windows':
            return WindowsHandler()
        elif system == 'darwin':  # macOS
            return MacOSHandler()
        else:
            # 对于Linux等其他平台，使用基础实现
            print(f"Warning: Platform {system} not fully supported, using basic implementation")
            return WindowsHandler()  # 降级使用Windows处理器


class CrossPlatformHotkeyManager(QObject):
    """跨平台热键管理器主类"""

    hotkey_pressed = Signal()
    mouse_clicked = Signal()

    def __init__(self, hotkey: str = 'alt+c'):
        super().__init__()
        self.hotkey_combo = HotkeyCombo.parse(hotkey)
        self.handler = HotkeyManagerFactory.create_handler()
        self._running = False

        print(f"Initialized for platform: {platform.system()}")
        print(f"Hotkey combination: {hotkey}")

    def start(self, enable_mouse_hook: bool = True):
        """启动热键和鼠标监听

        Args:
            enable_mouse_hook: 是否启用鼠标钩子（默认True）
        """
        if self._running:
            return

        try:
            # 启动热键监听
            self.handler.start_hotkey_listener(
                self.hotkey_combo,
                self._on_hotkey_pressed
            )
            print("Hotkey listener started successfully")

            # 启动鼠标钩子监听（可选）
            if enable_mouse_hook:
                success = self.handler.start_mouse_hook(self._on_mouse_clicked)
                if success:
                    print("Mouse hook started successfully")
                else:
                    print("Mouse hook could not be started (this is optional)")
            else:
                print("Mouse hook disabled by user")

            self._running = True
            print("Hotkey manager started")

        except Exception as e:
            print(f"Error starting hotkey manager: {e}")

    def start_hotkey_only(self):
        """只启动热键监听，不启动鼠标钩子"""
        self.start(enable_mouse_hook=False)

    def stop(self):
        """停止热键和鼠标监听"""
        if not self._running:
            return

        try:
            self.handler.stop_hotkey_listener()
            self.handler.stop_mouse_hook()
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
            print(f"Hotkey changed to: {new_hotkey}")

            if was_running:
                self.start()

        except ValueError as e:
            print(f"Invalid hotkey format: {e}")

    def _on_hotkey_pressed(self):
        """热键按下回调"""
        print(f"Hotkey triggered: {self.hotkey_combo}")
        self.hotkey_pressed.emit()

    def _on_mouse_clicked(self):
        """Alt+鼠标点击回调"""
        print("Alt+Mouse click detected")
        self.mouse_clicked.emit()

    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._running

    def get_platform_info(self) -> Dict[str, Any]:
        """获取平台信息"""
        return {
            'platform': platform.system(),
            'handler_type': type(self.handler).__name__,
            'hotkey': str(self.hotkey_combo),
            'running': self._running
        }


# 使用示例
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # 创建热键管理器
    manager = CrossPlatformHotkeyManager('alt+c')

    # 连接信号
    manager.hotkey_pressed.connect(lambda: print("🔥 Hotkey activated!"))
    manager.mouse_clicked.connect(lambda: print("🖱️ Alt+Click detected!"))

    # 启动管理器
    manager.start()

    print("Hotkey manager is running. Press Alt+c or Alt+Click to test.")
    print("Platform info:", manager.get_platform_info())

    try:
        sys.exit(app.exec())
    finally:
        manager.stop()