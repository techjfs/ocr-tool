import sys
import os
import subprocess
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QTextEdit,
                               QLineEdit, QSystemTrayIcon, QMenu, QMessageBox,
                               QDialog, QFormLayout)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QGuiApplication

from hotkey_manager import CrossPlatformHotkeyManager
from settings_manager import SettingsManager
from capture_tool import CaptureTool
from hover_tool import HoverTool


class HotkeySettingDialog(QDialog):
    """设置全局快捷键对话框"""

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

class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("应用设置")
        self.setModal(True)
        self.resize(400, 300)

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout()

        # 创建表单布局
        form_layout = QFormLayout()

        # 用户名设置
        self.username_edit = QLineEdit()
        form_layout.addRow("用户名:", self.username_edit)

        # 自动保存间隔
        self.autosave_spinbox = QSpinBox()
        self.autosave_spinbox.setRange(1, 60)
        self.autosave_spinbox.setSuffix(" 分钟")
        form_layout.addRow("自动保存间隔:", self.autosave_spinbox)

        # 启用通知
        self.notification_checkbox = QCheckBox()
        form_layout.addRow("启用通知:", self.notification_checkbox)

        # 主题选择
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色", "深色", "系统默认"])
        form_layout.addRow("主题:", self.theme_combo)

        # 语言选择
        self.language_combo = QComboBox()
        self.language_combo.addItems(["中文", "English", "日本語"])
        form_layout.addRow("语言:", self.language_combo)

        layout.addLayout(form_layout)

        # 字体和颜色设置
        font_color_layout = QHBoxLayout()

        self.font_button = QPushButton("选择字体")
        self.font_button.clicked.connect(self.choose_font)
        font_color_layout.addWidget(self.font_button)

        self.color_button = QPushButton("选择颜色")
        self.color_button.clicked.connect(self.choose_color)
        font_color_layout.addWidget(self.color_button)

        layout.addLayout(font_color_layout)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.RestoreDefaults
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self.restore_defaults)

        layout.addWidget(button_box)

        self.setLayout(layout)

        # 用于存储选择的字体和颜色
        self.selected_font = None
        self.selected_color = None

    def load_settings(self):
        """从设置中加载当前值"""
        self.username_edit.setText(self.settings_manager.get_value("username", ""))
        self.autosave_spinbox.setValue(int(self.settings_manager.get_value("autosave_interval", 5)))
        self.notification_checkbox.setChecked(
            self.settings_manager.get_value("enable_notifications", True, type=bool)
        )
        self.theme_combo.setCurrentText(self.settings_manager.get_value("theme", "浅色"))
        self.language_combo.setCurrentText(self.settings_manager.get_value("language", "中文"))

        # 加载字体设置
        font_family = self.settings_manager.get_value("font_family", "Arial")
        font_size = int(self.settings_manager.get_value("font_size", 12))
        self.selected_font = QFont(font_family, font_size)

        # 加载颜色设置
        color_name = self.settings_manager.get_value("color", "#000000")
        self.selected_color = QColor(color_name)

    def choose_font(self):
        """选择字体"""
        ok, font = QFontDialog.getFont(self.selected_font or QFont(), self)
        if ok:
            self.selected_font = font
            self.font_button.setText(f"字体: {font.family()}, {font.pointSize()}pt")

    def choose_color(self):
        """选择颜色"""
        color = QColorDialog.getColor(self.selected_color or QColor(), self)
        if color.isValid():
            self.selected_color = color
            # 更新按钮背景色以显示选择的颜色
            self.color_button.setStyleSheet(f"background-color: {color.name()}")

    def restore_defaults(self):
        """恢复默认设置"""
        reply = QMessageBox.question(
            self, "确认", "确定要恢复默认设置吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.username_edit.setText("")
            self.autosave_spinbox.setValue(5)
            self.notification_checkbox.setChecked(True)
            self.theme_combo.setCurrentText("浅色")
            self.language_combo.setCurrentText("中文")
            self.selected_font = QFont("Arial", 12)
            self.selected_color = QColor("#000000")
            self.font_button.setText("选择字体")
            self.color_button.setStyleSheet("")

    def accept(self):
        """保存设置"""
        self.save_settings()
        super().accept()

    def save_settings(self):
        """保存所有设置"""
        self.settings_manager.set_value("username", self.username_edit.text())
        self.settings_manager.set_value("autosave_interval", self.autosave_spinbox.value())
        self.settings_manager.set_value("enable_notifications", self.notification_checkbox.isChecked())
        self.settings_manager.set_value("theme", self.theme_combo.currentText())
        self.settings_manager.set_value("language", self.language_combo.currentText())

        if self.selected_font:
            self.settings_manager.set_value("font_family", self.selected_font.family())
            self.settings_manager.set_value("font_size", self.selected_font.pointSize())

        if self.selected_color:
            self.settings_manager.set_value("color", self.selected_color.name())

        # 强制同步到磁盘
        self.settings_manager.sync()

class MainWindow(QMainWindow):
    """OCR工具主窗口"""

    def __init__(self):
        super().__init__()
        self.hotkey = "alt+c"  # 默认快捷键
        self.tray_notified = False
        self.has_external_tool = False

        self.capture_tool = CaptureTool()
        self.hover_tool = HoverTool()

        self.settings_manager = SettingsManager(use_file_storage=True)

        # 设置界面
        self.init_ui()

        # 设置热键管理器
        self.setup_hotkey_manager()

        # 设置系统托盘
        self.setup_tray_icon()

        # 设置状态栏提示
        QTimer.singleShot(1000, lambda: self.statusBar().showMessage(f"OCR工具已启动，可使用快捷键 {self.hotkey}"))

        # 连接信号
        self.connect_signals()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("OCR小工具")
        self.setGeometry(100, 100, 600, 400)

        # 创建中央控件和布局
        central_widget = QWidget()
        layout = QVBoxLayout()

        # 显示配置文件信息
        config_info = self.settings_manager.get_config_info()
        config_info_text = f"配置文件: {config_info['path']}\n版本: {config_info['version']}"
        if config_info.get('size'):
            config_info_text += f" | 大小: {config_info['size']} bytes"

        config_path_label = QLabel(config_info_text)
        config_path_label.setWordWrap(True)
        config_path_label.setStyleSheet("color: #666; font-size: 10px; margin-bottom: 10px;")
        layout.addWidget(config_path_label)

        # 状态指示标签
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold; color: green;")

        # 创建功能按钮
        self.screenshot_btn = QPushButton("截屏识别", self)
        self.screenshot_btn.clicked.connect(self.start_screenshot)

        self.hover_btn = QPushButton("启用悬停取词", self)
        self.hover_btn.setCheckable(True)
        self.hover_btn.clicked.connect(self.toggle_hover_mode)

        self.hotkey_btn = QPushButton(f"设置快捷键 ({self.hotkey})", self)
        self.hotkey_btn.clicked.connect(self.setup_hotkey)

        self.settings_button = QPushButton("设置", self)
        self.settings_button.clicked.connect(self.open_settings)

        # 结果显示区域
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)

        # 外部工具命令输入
        self.tool_cmd = QLineEdit()
        self.tool_cmd.setPlaceholderText("输入外部工具命令，使用{text}作为文本占位符")

        self.run_tool_btn = QPushButton("检查可否正常调用外部工具")
        self.run_tool_btn.clicked.connect(self.check_external_tool_call)

        # 最小化按钮
        minimize_btn = QPushButton("最小化到托盘", self)
        minimize_btn.clicked.connect(self.hide_window)

        # 添加组件到布局
        layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.screenshot_btn)
        button_layout.addWidget(self.hover_btn)
        button_layout.addWidget(self.hotkey_btn)
        layout.addLayout(button_layout)

        layout.addWidget(QLabel("识别结果:"))
        layout.addWidget(self.result_text)
        layout.addWidget(QLabel("外部工具命令:"))
        layout.addWidget(self.tool_cmd)
        layout.addWidget(self.run_tool_btn)
        layout.addWidget(minimize_btn)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def setup_hotkey_manager(self):
        """设置全局热键管理器"""
        if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
            self.hotkey_manager.stop()

        self.hotkey_manager = CrossPlatformHotkeyManager(self.hotkey)
        self.hotkey_manager.hotkey_pressed.connect(self.start_screenshot)
        self.hotkey_manager.mouse_clicked.connect(self.hover_tool.capture_at_cursor)
        self.hotkey_manager.start()

    def setup_tray_icon(self):
        """设置系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self)

        # 尝试加载图标
        icon_path = os.path.join("_internal", "ocr.png")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            print(f"Warning: Icon file not found at {icon_path}")
            # 使用应用默认图标
            self.tray_icon.setIcon(QIcon.fromTheme("edit-find"))

        self.tray_icon.setToolTip("OCR小工具")

        # 创建托盘菜单
        tray_menu = QMenu()
        show_action = tray_menu.addAction("显示")
        show_action.triggered.connect(self.show)

        screenshot_action = tray_menu.addAction("截图OCR")
        screenshot_action.triggered.connect(self.start_screenshot)

        hover_action = tray_menu.addAction("悬停取词")
        hover_action.triggered.connect(self.hover_tool.capture_at_cursor)

        hotkey_action = tray_menu.addAction(f"设置快捷键 ({self.hotkey})")
        hotkey_action.triggered.connect(self.setup_hotkey)

        tray_menu.addSeparator()

        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self.quit_application)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def open_settings(self):
        """打开设置对话框"""
        dialog = SettingsDialog(self.settings_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.apply_settings()
            QMessageBox.information(self, "成功", "设置已保存并应用！")

    def apply_settings(self):
        pass

    def connect_signals(self):
        """连接组件信号"""
        # 截图工具信号
        self.capture_tool.capture_completed.connect(self.update_ocr_result)

        # 悬停工具信号
        self.hover_tool.word_found.connect(self.update_hover_result)
        self.hover_tool.status_changed.connect(self.update_status)

    def update_ocr_result(self, text_list):
        """更新OCR结果"""
        if not text_list:
            self.status_label.setText("未识别到文本")
            self.status_label.setStyleSheet("font-weight: bold; color: red;")
            self.result_text.setPlainText("未能识别到任何文本")
            return

        # 更新状态
        self.status_label.setText("识别完成")
        self.status_label.setStyleSheet("font-weight: bold; color: green;")

        # 更新结果
        self.result_text.setPlainText('\n'.join(text_list))

        # 运行外部工具
        if self.has_external_tool:
            self.run_external_tool()

    def update_hover_result(self, word):
        """更新悬停取词结果"""
        self.result_text.setPlainText(word)

        # 运行外部工具
        if self.has_external_tool:
            self.run_external_tool()

    def update_status(self, status):
        """更新状态信息"""
        self.status_label.setText(status)
        if "成功" in status or "就绪" in status:
            self.status_label.setStyleSheet("font-weight: bold; color: green;")
        elif "失败" in status or "错误" in status:
            self.status_label.setStyleSheet("font-weight: bold; color: red;")
        else:
            self.status_label.setStyleSheet("font-weight: bold; color: orange;")

    def toggle_hover_mode(self, checked):
        """切换悬停取词模式"""
        if checked:
            # 启用悬停取词模式
            self.status_label.setText("悬停取词模式已启用，按Alt+鼠标左键进行取词")
            self.statusBar().showMessage("悬停取词模式已启用")

        else:
            # 禁用悬停取词模式
            self.status_label.setText("就绪")
            self.statusBar().showMessage("悬停取词模式已禁用")

    def setup_hotkey(self):
        """设置全局快捷键"""
        dialog = HotkeySettingDialog(self, self.hotkey)
        if dialog.exec():
            new_hotkey = dialog.get_hotkey()
            self.hotkey = new_hotkey
            self.hotkey_btn.setText(f"设置快捷键 ({self.hotkey})")
            self.setup_hotkey_manager()

            # 更新托盘菜单
            hotkey_action = self.tray_icon.contextMenu().actions()[3]  # 索引3是热键设置菜单项
            hotkey_action.setText(f"设置快捷键 ({self.hotkey})")

            self.statusBar().showMessage(f"已设置全局快捷键为: {self.hotkey}", 3000)
            QMessageBox.information(self, "成功", f"已设置全局快捷键为: {self.hotkey}")

    def start_screenshot(self):
        """启动截图OCR功能"""
        if not self.has_external_tool and not self.check_external_tool_call():
            return

        self.hide()
        self.status_label.setText("请选择截图区域")
        QTimer.singleShot(300, self.capture_tool.start_capture)

    def check_external_tool_call(self):
        """检查外部工具调用"""
        cmd = self.tool_cmd.text()
        if not cmd:
            QMessageBox.warning(self, "错误", "请输入外部工具命令")
            return False

        try:
            # 测试替换
            test_command = cmd.replace("{text}", "hello")
            subprocess.Popen(test_command, shell=True)
            self.statusBar().showMessage(f"测试命令: {test_command}", 3000)

            self.has_external_tool = True
            QMessageBox.information(self, "成功", "外部工具命令设置成功")
            return True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"命令格式错误: {str(e)}")
            return False

    def run_external_tool(self):
        """运行外部工具处理OCR结果"""
        import subprocess

        text = self.result_text.toPlainText()
        cmd = self.tool_cmd.text()

        try:
            cmd = cmd.replace("{text}", text)
            subprocess.Popen(cmd, shell=True)
            self.statusBar().showMessage(f"已执行命令: {cmd}", 3000)
            return True
        except Exception as e:
            self.statusBar().showMessage(f"执行命令失败: {str(e)}", 3000)
            return False

    def tray_icon_activated(self, reason):
        """系统托盘图标激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.activateWindow()

    def closeEvent(self, event):
        """窗口关闭事件"""
        event.ignore()
        self.hide_window()

    def hide_window(self):
        """隐藏窗口到系统托盘"""
        if not self.tray_notified:
            self.tray_icon.showMessage(
                "OCR小工具",
                f"程序已最小化到托盘，可通过热键 {self.hotkey} 继续使用",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            self.tray_notified = True
        self.hide()

    def quit_application(self):
        """退出应用程序"""
        self.tray_notified = True

        # 确保清理资源
        if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
            self.hotkey_manager.stop()

        QApplication.quit()


def main():
    """主函数"""
    # 确保只有一个实例运行
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # 设置应用图标
    icon_path = os.path.join("_internal", "ocr.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()