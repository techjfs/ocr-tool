import sys
import subprocess
import numpy as np
from PySide6.QtCore import Qt, QRect, QTimer, Signal, QObject, QThread
from PySide6.QtGui import QScreen, QPainter, QPen, QBrush, QColor, QFont, QImage, QPixmap, QGuiApplication, QIcon
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QPushButton, QTextEdit, QLineEdit, QLabel, QMessageBox,
                               QDialog, QHBoxLayout, QSystemTrayIcon, QMenu)
from pynput import keyboard
from paddleocr import PaddleOCR


def qimage_to_narry(qimage: QImage) -> np.ndarray:
    qimage = qimage.convertToFormat(QImage.Format.Format_RGB888)
    width, height = qimage.width(), qimage.height()
    img_np = np.ndarray((height, width, 3), buffer=qimage.constBits(),
                        strides=[qimage.bytesPerLine(), 3, 1], dtype=np.uint8)
    return img_np


# 简化的热键管理器
class HotkeyManager(QObject):
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
        if self.listener is None or not self.listener.running:
            self.listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self.listener.daemon = True
            self.listener.start()
            print(f"Hotkey listener started for: {self.hotkey}")

    def stop_listening(self):
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
            # 对控制键（如alt、ctrl等）进行特殊处理，只要有一个匹配即可
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


# 截图窗口，用户选择区域后会触发 OCR 处理
class ScreenshotWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OCR-Tool")
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.start_point = None
        self.end_point = None
        self.selection_rect = QRect()
        self.dragging = False
        self.main_window = None
        self.screen = QGuiApplication.primaryScreen()
        self.full_screenshot = self.screen.grabWindow(0)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(Qt.GlobalColor.blue, 2))
        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
        painter.drawRect(self.rect())
        if not self.selection_rect.isNull():
            painter.setPen(QPen(Qt.GlobalColor.red, 2))
            painter.setBrush(QBrush(QColor(255, 0, 0, 30)))
            painter.drawRect(self.selection_rect)
            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            size_text = f"{self.selection_rect.width()} × {self.selection_rect.height()}"
            painter.drawText(self.selection_rect.right() - 100,
                             self.selection_rect.bottom() + 20, size_text)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.dragging = True

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.end_point = event.pos()
            self.selection_rect = QRect(self.start_point, self.end_point).normalized()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            if (self.selection_rect.width() > 5 and self.selection_rect.height() > 5):
                self.capture_selection()
            self.close()

    def capture_selection(self):
        if self.selection_rect.isNull() or self.selection_rect.width() < 5 or self.selection_rect.height() < 5:
            return

        screenshot = self.full_screenshot.copy(
            self.selection_rect.x(),
            self.selection_rect.y(),
            self.selection_rect.width(),
            self.selection_rect.height()
        )

        QApplication.clipboard().setImage(screenshot.toImage())
        if self.main_window:
            self.main_window.process_ocr()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()


class HotkeySettingDialog(QDialog):
    def __init__(self, parent=None, current_hotkey="alt+c"):
        super().__init__(parent)
        self.setWindowTitle("设置全局快捷键")
        self.setFixedSize(300, 100)
        layout = QVBoxLayout()
        self.hotkey_input = QLineEdit(current_hotkey)
        self.hotkey_input.setPlaceholderText("例如: alt+c")
        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addWidget(QLabel("全局快捷键:"))
        layout.addWidget(self.hotkey_input)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_hotkey(self):
        return self.hotkey_input.text()


class OCRTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang='ch',
            det_model_dir="../_internal/models/det/",
            rec_model_dir="../_internal/models/rec/",
            cls_model_dir="../_internal/models/cls/"
        )
        self.hotkey = "alt+c"  # 默认快捷键
        self.tray_notified = False
        self.has_setting_external_tool = False
        self.setup_hotkey_manager()
        self.setup_tray_icon()
        self.init_ui()
        QTimer.singleShot(1000, lambda: self.statusBar().showMessage("OCR工具已启动，可使用快捷键 " + self.hotkey))

    def setup_hotkey_manager(self):
        if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
            self.hotkey_manager.stop_listening()
        self.hotkey_manager = HotkeyManager(self.hotkey)
        self.hotkey_manager.hotkey_pressed.connect(self.start_screenshot)
        self.hotkey_manager.start_listening()
        print(f"Hotkey manager setup with: {self.hotkey}")

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        # 尝试加载图标，如果失败则使用默认图标
        self.tray_icon.setIcon(QIcon("../_internal/ocr.png"))
        self.tray_icon.setToolTip("OCR小工具")
        tray_menu = QMenu()
        show_action = tray_menu.addAction("显示")
        show_action.triggered.connect(self.show)
        screenshot_action = tray_menu.addAction("截图OCR")
        screenshot_action.triggered.connect(self.start_screenshot)
        hotkey_action = tray_menu.addAction(f"设置快捷键 ({self.hotkey})")
        hotkey_action.triggered.connect(self.setup_hotkey)
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self.quit_application)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.activateWindow()

    def init_ui(self):
        self.setWindowTitle("OCR小工具")
        self.setGeometry(100, 100, 600, 400)
        central_widget = QWidget()
        layout = QVBoxLayout()

        # 添加状态指示标签
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold; color: green;")

        self.screenshot_btn = QPushButton("截屏识别", self)
        self.screenshot_btn.clicked.connect(self.start_screenshot)
        self.hotkey_btn = QPushButton(f"设置快捷键 ({self.hotkey})", self)
        self.hotkey_btn.clicked.connect(self.setup_hotkey)
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.tool_cmd = QLineEdit()
        self.tool_cmd.setPlaceholderText("输入外部工具命令，使用{text}作为文本占位符")
        self.run_tool_btn = QPushButton("检查可否正常调用外部工具")
        self.run_tool_btn.clicked.connect(self.check_external_tool_call)
        minimize_btn = QPushButton("最小化到托盘", self)
        minimize_btn.clicked.connect(self.hide_window)

        layout.addWidget(self.status_label)
        layout.addWidget(self.screenshot_btn)
        layout.addWidget(self.hotkey_btn)
        layout.addWidget(QLabel("识别结果:"))
        layout.addWidget(self.result_text)
        layout.addWidget(QLabel("外部工具命令:"))
        layout.addWidget(self.tool_cmd)
        layout.addWidget(self.run_tool_btn)
        layout.addWidget(minimize_btn)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        self.statusBar().showMessage(f"使用快捷键 {self.hotkey} 可以随时触发OCR")

    def setup_hotkey(self):
        dialog = HotkeySettingDialog(self, self.hotkey)
        if dialog.exec():
            new_hotkey = dialog.get_hotkey()
            self.hotkey = new_hotkey
            self.hotkey_btn.setText(f"设置快捷键 ({self.hotkey})")
            self.tray_icon.contextMenu().actions()[2].setText(f"设置快捷键 ({self.hotkey})")
            self.setup_hotkey_manager()
            self.statusBar().showMessage(f"已设置全局快捷键为: {self.hotkey}", 3000)
            QMessageBox.information(self, "成功", f"已设置全局快捷键为: {self.hotkey}")

    def start_screenshot(self):
        if not self.has_setting_external_tool:
            QMessageBox.warning(self, "错误", "请输入外部工具命令再进行OCR")
            self.show()
            return
        print("Starting screenshot")
        self.hide()
        QTimer.singleShot(300, self._delayed_screenshot)  # 增加延迟，确保窗口完全隐藏

    def _delayed_screenshot(self):
        print("Taking delayed screenshot")
        self.screenshot_widget = ScreenshotWidget()
        self.screenshot_widget.main_window = self
        self.screenshot_widget.show()

    def process_ocr(self):
        clipboard = QApplication.clipboard()
        image = clipboard.image()
        if image.isNull():
            QMessageBox.warning(self, "错误", "剪贴板中没有图像")
            self.show()
            return

        # 更新状态
        self.status_label.setText("正在识别中...")
        self.status_label.setStyleSheet("font-weight: bold; color: orange;")
        self.result_text.setPlainText("正在识别中...")

        # 转换为numpy数组
        img_np = qimage_to_narry(image)

        result = self.ocr.ocr(img_np)

        print(f"result: {result}")
        texts = []
        for line in result:
            if line:
                text, confidence = line[0][1]
                texts.append(text)
        print(f"texts: {texts}")
        self._update_ocr_result(texts)

    def _update_ocr_result(self, texts):
        # 更新状态
        self.status_label.setText("识别完成")
        self.status_label.setStyleSheet("font-weight: bold; color: green;")

        self.result_text.setPlainText('\n'.join(texts))
        self.run_external_tool()

    def check_external_tool_call(self):
        if self.run_external_tool():
            self.has_setting_external_tool = True
            QMessageBox.information(self, "成功", "外部工具命令设置成功")

    def run_external_tool(self):
        text = self.result_text.toPlainText()
        cmd = self.tool_cmd.text()
        if not cmd:
            QMessageBox.warning(self, "错误", "请输入外部工具命令")
            return False
        try:
            cmd = cmd.replace("{text}", text)
            subprocess.Popen(cmd, shell=True)
            self.statusBar().showMessage(f"已执行命令: {cmd}", 3000)
            return True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"执行失败: {str(e)}")
        return False

    def closeEvent(self, event):
        event.ignore()
        self.hide_window()

    def hide_window(self):
        if not self.tray_notified:
            self.tray_icon.showMessage("OCR小工具", "程序已最小化到托盘，可通过热键 " + self.hotkey + " 继续使用",
                                       QSystemTrayIcon.MessageIcon.Information, 2000)
            self.tray_notified = True
        self.hide()

    def quit_application(self):
        # 确保清理资源
        self.tray_notified = True
        if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
            self.hotkey_manager.stop_listening()

        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = OCRTool()
    window.show()
    sys.exit(app.exec())
