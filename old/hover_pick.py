import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QSystemTrayIcon, QMenu
from PySide6.QtCore import Qt, QPoint, QEvent, Signal, QObject, QTimer
from PySide6.QtGui import QGuiApplication, QCursor, QMouseEvent, QIcon, QImage
import ctypes
from paddleocr import PaddleOCR
import numpy as np
import jieba

# Windows API 常量
WH_MOUSE_LL = 14
WM_LBUTTONDOWN = 0x0201
VK_MENU = 0x12  # ALT键的虚拟键码

# 全局变量
alt_pressed = False
mouse_hook = None
mouse_callback = None

# 获取Windows函数
user32 = ctypes.WinDLL('user32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# 定义必要的Windows API函数原型
user32.SetWindowsHookExA.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
user32.SetWindowsHookExA.restype = ctypes.c_void_p

user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
user32.CallNextHookEx.restype = ctypes.c_int

user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]
user32.UnhookWindowsHookEx.restype = ctypes.c_int

user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = ctypes.c_short

kernel32.GetModuleHandleA.argtypes = [ctypes.c_char_p]
kernel32.GetModuleHandleA.restype = ctypes.c_void_p

# 鼠标钩子回调函数类型
MOUSEEVENTPROC = ctypes.WINFUNCTYPE(
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)
)


def qimage_to_narry(qimage: QImage) -> np.ndarray:
    qimage = qimage.convertToFormat(QImage.Format.Format_RGB888)
    width, height = qimage.width(), qimage.height()
    img_np = np.ndarray((height, width, 3), buffer=qimage.constBits(),
                        strides=[qimage.bytesPerLine(), 3, 1], dtype=np.uint8)
    return img_np


class MouseHook:
    def __init__(self, callback):
        self.callback = callback
        self.hooked = False
        self.mouse_hook = None
        self.mouse_proc = None

    def install(self):
        # 创建鼠标钩子回调函数
        def low_level_mouse_proc(n_code, w_param, l_param):
            global alt_pressed

            if n_code >= 0 and w_param == WM_LBUTTONDOWN and alt_pressed:
                # ALT键按下的情况下点击鼠标左键
                self.callback()

            # 调用下一个钩子
            return user32.CallNextHookEx(self.mouse_hook, n_code, w_param, l_param)

        # 创建回调函数类型
        self.mouse_proc = MOUSEEVENTPROC(low_level_mouse_proc)

        # 安装鼠标钩子
        self.mouse_hook = user32.SetWindowsHookExA(
            WH_MOUSE_LL,
            self.mouse_proc,
            kernel32.GetModuleHandleA(None),
            0
        )

        if self.mouse_hook:
            self.hooked = True
            return True
        return False

    def uninstall(self):
        if self.hooked:
            user32.UnhookWindowsHookEx(self.mouse_hook)
            self.hooked = False


class KeyboardMonitor(QObject):
    alt_key_pressed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_alt_key)
        self.timer.start(50)  # 每50毫秒检查一次

    def check_alt_key(self):
        global alt_pressed
        # 检查ALT键状态
        alt_state = user32.GetAsyncKeyState(VK_MENU)
        is_pressed = (alt_state & 0x8000) != 0

        # 状态改变时发出信号
        if is_pressed != alt_pressed:
            alt_pressed = is_pressed
            self.alt_key_pressed.emit(is_pressed)


class WordPickerWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 设置窗口标题和大小
        self.setWindowTitle("悬停取词工具")
        self.setGeometry(100, 100, 400, 200)

        # 创建中央控件和布局
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        # 创建标签用于显示取词结果
        self.status_label = QLabel("悬停取词工具已启动，按Alt+鼠标左键进行取词")
        layout.addWidget(self.status_label)

        self.result_label = QLabel("取词结果将显示在这里")
        self.result_label.setStyleSheet("font-size: 16pt; background-color: #f0f0f0; padding: 10px;")
        layout.addWidget(self.result_label)

        self.setCentralWidget(central_widget)

        # 初始化OCR引擎
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang='ch',
            det_model_dir="../_internal/models/det/",
            rec_model_dir="../_internal/models/rec/",
            cls_model_dir="../_internal/models/cls/"
        )

        # 创建系统托盘图标
        self.create_tray_icon()

        # 初始化键盘监视器
        self.keyboard_monitor = KeyboardMonitor()
        self.keyboard_monitor.alt_key_pressed.connect(self.on_alt_key_state_changed)

        # 初始化鼠标钩子
        self.mouse_hook = MouseHook(self.on_alt_mouse_click)
        if not self.mouse_hook.install():
            self.status_label.setText("安装鼠标钩子失败!")

    def create_tray_icon(self):
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("../_internal/ocr.png"))

        # 创建托盘菜单
        tray_menu = QMenu()
        show_action = tray_menu.addAction("显示")
        show_action.triggered.connect(self.show)
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(QApplication.quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def on_alt_key_state_changed(self, is_pressed):
        if is_pressed:
            self.status_label.setText("Alt键已按下，点击鼠标左键进行取词")
        else:
            self.status_label.setText("悬停取词工具已启动，按Alt+鼠标左键进行取词")

    def on_alt_mouse_click(self):
        # 获取鼠标当前位置
        cursor_pos = QCursor().pos()
        # 在主线程中执行截图和OCR
        QApplication.instance().postEvent(self, QMouseEvent(
            QEvent.Type.MouseButtonPress,
            QPoint(0, 0),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.AltModifier
        ))
        self.capture_text_at_position(cursor_pos)

    def capture_text_at_position(self, pos):
        """捕获指定位置的文本"""
        try:
            # 首先截取较大区域用于OCR分析
            screen = QGuiApplication.screenAt(pos)
            if screen:
                # 获取一个较大的屏幕截图区域
                initial_width, initial_height = 400, 200
                x, y = pos.x() - initial_width // 2, pos.y() - initial_height // 2

                screenshot = screen.grabWindow(0, x, y, initial_width, initial_height)
                screenshot_path = "hover_capture_initial.png"
                screenshot.save(screenshot_path)

                # 使用OCR识别文本和位置
                img = np.array(qimage_to_narry(screenshot.toImage()))
                result = self.ocr.ocr(img, cls=True)

                if result and result[0]:
                    closest_text = None
                    min_distance = float('inf')
                    relative_mouse_pos = QPoint(initial_width // 2, initial_height // 2)

                    for line in result[0]:
                        box = line[0]
                        text = line[1][0]
                        center_x = sum(point[0] for point in box) / 4
                        center_y = sum(point[1] for point in box) / 4
                        distance = ((center_x - relative_mouse_pos.x()) ** 2 +
                                    (center_y - relative_mouse_pos.y()) ** 2) ** 0.5

                        if distance < min_distance:
                            min_distance = distance
                            closest_text = (text, box)

                    if closest_text:
                        text, box = closest_text
                        x1 = box[0][0]
                        x2 = box[1][0]
                        box_width = x2 - x1
                        text_length = len(text)

                        if text_length == 0:
                            self.result_label.setText("文本为空")
                            return

                        avg_char_width = box_width / text_length

                        # 使用jieba分词并获取单词位置
                        tokenized = list(jieba.tokenize(text))
                        word_positions = []
                        for tk in tokenized:
                            word = tk[0]
                            if word.strip() == '' or word in ['，', '。', '!', '?', ',', '.', ' ']:
                                continue
                            start_idx = tk[1]
                            end_idx = tk[2]
                            word_positions.append((word, start_idx, end_idx))

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
                            self.result_label.setText(selected_word)
                            clipboard = QApplication.clipboard()
                            clipboard.setText(selected_word)
                            self.status_label.setText("成功识别文本并复制到剪贴板")
                        else:
                            self.result_label.setText("未找到精确单词")
                    else:
                        self.result_label.setText("未在鼠标位置找到文本")
                else:
                    self.result_label.setText("OCR未识别到任何文本")
            else:
                self.result_label.setText("无法获取屏幕截图")
        except Exception as e:
            self.result_label.setText(f"取词失败: {str(e)}")

    def closeEvent(self, event):
        # 卸载鼠标钩子
        if hasattr(self, 'mouse_hook'):
            self.mouse_hook.uninstall()

        # 正常关闭窗口
        super().closeEvent(event)


# 运行应用
if __name__ == "__main__":
    # 确保只有一个实例运行
    app = QApplication(sys.argv)

    # 确保应用程序有一个图标
    app.setWindowIcon(QIcon("../_internal/ocr.png"))

    window = WordPickerWindow()
    window.show()
    sys.exit(app.exec())