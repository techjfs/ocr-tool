from PySide6.QtCore import QObject, Signal
from pynput import keyboard
import ctypes


class HotkeyManager(QObject):
    """全局热键管理器"""
    hotkey_pressed = Signal()

    def __init__(self, hotkey='alt+c'):
        super().__init__()
        self.hotkey = hotkey
        self.listener = None
        self.current_keys = set()

        # 解析热键组合
        self.hotkey_parts = set()
        for part in hotkey.lower().split('+'):
            if part == 'ctrl':
                self.hotkey_parts.add(keyboard.Key.ctrl)
                self.hotkey_parts.add(keyboard.Key.ctrl_l)
                self.hotkey_parts.add(keyboard.Key.ctrl_r)
            elif part == 'alt':
                self.hotkey_parts.add(keyboard.Key.alt)
                self.hotkey_parts.add(keyboard.Key.alt_l)
                self.hotkey_parts.add(keyboard.Key.alt_r)
            elif part == 'shift':
                self.hotkey_parts.add(keyboard.Key.shift)
                self.hotkey_parts.add(keyboard.Key.shift_l)
                self.hotkey_parts.add(keyboard.Key.shift_r)
            else:  # 字母或数字
                self.hotkey_parts.add(part)

    def start_listening(self):
        """开始监听热键"""
        if self.listener is None or not self.listener.running:
            self.listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self.listener.daemon = True
            self.listener.start()
            print(f"Hotkey listener started for: {self.hotkey}")

    def stop_listening(self):
        """停止监听热键"""
        if self.listener and self.listener.running:
            self.listener.stop()
            self.listener = None
            print("Hotkey listener stopped")

    def _on_press(self, key):
        try:
            # 统一按键格式
            normalized_key = self._normalize_key(key)
            if normalized_key:
                self.current_keys.add(normalized_key)

            # 检查是否满足热键组合
            control_keys_matched = True
            for part in self.hotkey_parts:
                if isinstance(part, str):  # 非控制键（字母、数字）
                    if part not in self.current_keys:
                        control_keys_matched = False
                        break
                else:  # 控制键
                    # 如果是控制键，检查是否有任一变体在当前按下的键中
                    if part == keyboard.Key.ctrl or part == keyboard.Key.ctrl_l or part == keyboard.Key.ctrl_r:
                        if not (keyboard.Key.ctrl in self.current_keys or
                                keyboard.Key.ctrl_l in self.current_keys or
                                keyboard.Key.ctrl_r in self.current_keys):
                            control_keys_matched = False
                            break
                    elif part == keyboard.Key.alt or part == keyboard.Key.alt_l or part == keyboard.Key.alt_r:
                        if not (keyboard.Key.alt in self.current_keys or
                                keyboard.Key.alt_l in self.current_keys or
                                keyboard.Key.alt_r in self.current_keys):
                            control_keys_matched = False
                            break
                    elif part == keyboard.Key.shift or part == keyboard.Key.shift_l or part == keyboard.Key.shift_r:
                        if not (keyboard.Key.shift in self.current_keys or
                                keyboard.Key.shift_l in self.current_keys or
                                keyboard.Key.shift_r in self.current_keys):
                            control_keys_matched = False
                            break
                    elif part not in self.current_keys:
                        control_keys_matched = False
                        break

            if control_keys_matched:
                print("HOTKEY TRIGGERED")
                self.hotkey_pressed.emit()
        except Exception as e:
            print(f"Error in _on_press: {e}")

    def _on_release(self, key):
        try:
            # 统一按键格式后再移除
            normalized_key = self._normalize_key(key)
            if normalized_key:
                self.current_keys.discard(normalized_key)
        except Exception as e:
            print(f"Error in _on_release: {e}")

    def _normalize_key(self, key):
        """统一按键格式，处理字符键和特殊键"""
        try:
            if hasattr(key, 'char') and key.char is not None:
                return key.char.lower()
            else:
                return key
        except:
            return key


class WindowsMouseHook(QObject):
    """Windows专用的鼠标钩子，用于Alt+鼠标点击功能"""
    mouse_clicked = Signal()

    # Windows API 常量
    WH_MOUSE_LL = 14
    WM_LBUTTONDOWN = 0x0201
    VK_MENU = 0x12  # ALT键的虚拟键码

    def __init__(self):
        super().__init__()
        # 初始化Windows API
        self.user32 = ctypes.WinDLL('user32', use_last_error=True)
        self.kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

        # 定义必要的Windows API函数原型
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

        # 鼠标钩子回调函数类型
        self.MOUSEEVENTPROC = ctypes.WINFUNCTYPE(
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)
        )

        self.hooked = False
        self.mouse_hook = None
        self.mouse_proc = None
        self.alt_pressed = False

    def is_alt_pressed(self):
        """检查ALT键是否按下"""
        alt_state = self.user32.GetAsyncKeyState(self.VK_MENU)
        return (alt_state & 0x8000) != 0

    def install(self):
        """安装鼠标钩子"""

        # 创建鼠标钩子回调函数
        def low_level_mouse_proc(n_code, w_param, l_param):
            if n_code >= 0 and w_param == self.WM_LBUTTONDOWN and self.is_alt_pressed():
                # ALT键按下的情况下点击鼠标左键
                self.mouse_clicked.emit()

            # 调用下一个钩子
            return self.user32.CallNextHookEx(self.mouse_hook, n_code, w_param, l_param)

        # 创建回调函数类型
        self.mouse_proc = self.MOUSEEVENTPROC(low_level_mouse_proc)

        # 安装鼠标钩子
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

    def uninstall(self):
        """卸载鼠标钩子"""
        if self.hooked:
            self.user32.UnhookWindowsHookEx(self.mouse_hook)
            self.hooked = False