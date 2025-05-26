import sys
import os
import subprocess
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QTextEdit,
                               QLineEdit, QSystemTrayIcon, QMenu, QMessageBox, QFormLayout,
                               QDialog, QSplitter, QListWidget, QStackedWidget, QFileDialog)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon

from hotkey_manager import CrossPlatformHotkeyManager
from settings_manager import SettingsManager
from capture_tool import CaptureTool
from hover_tool import HoverTool


class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("设置")
        self.setModal(True)
        self.resize(400, 300)

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        main_layout = QVBoxLayout()

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.category_list = QListWidget()
        self.category_list.setFixedWidth(100)
        categories = ["界面设置", "系统设计", "高级设置"]
        self.category_list.addItems(categories)
        self.category_list.currentRowChanged.connect(self.on_category_changed)

        self.settings_stack = QStackedWidget()

        self.create_ui_settings_page()
        self.create_system_settings_page()
        self.create_advanced_settings_page()

        splitter.addWidget(self.category_list)
        splitter.addWidget(self.settings_stack)
        splitter.setStretchFactor(1, 1)

        # 底部按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # 添加弹性空间，使按钮靠右

        self.save_btn = QPushButton("保存设置")
        self.cancel_btn = QPushButton("取消设置")
        self.reset_btn = QPushButton("恢复默认")

        # 设置按钮样式
        button_style = """
            QPushButton {
                padding: 8px 16px;
                font-size: 14px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """

        self.save_btn.setStyleSheet(
            button_style + "QPushButton { background-color: #28a745; color: white; border-color: #28a745; }")
        self.cancel_btn.setStyleSheet(button_style)
        self.reset_btn.setStyleSheet(
            button_style + "QPushButton { background-color: #dc3545; color: white; border-color: #dc3545; }")

        # 连接按钮信号
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.reset_btn.clicked.connect(self.reset_to_default)

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.reset_btn)

        main_layout.addWidget(splitter)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        self.category_list.setCurrentRow(0)

    def accept(self, /) -> None:
        self.save_settings()
        self.parent().setup_hotkey()
        super().accept()

    def on_category_changed(self, index):
        self.settings_stack.setCurrentIndex(index)

    def create_ui_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        todo_label = QLabel("待完善")
        layout.addWidget(todo_label)

        page.setLayout(layout)
        self.settings_stack.addWidget(page)

    def create_system_settings_page(self):
        page = QWidget()
        form_layout = QFormLayout()

        self.hotkey_input = QLineEdit("")
        self.hotkey_input.setPlaceholderText("例如: alt+c")

        form_layout.addRow("设置快捷键:", self.hotkey_input)

        self.file_path_label = QLabel("未选择文件")
        self.file_path_label.setStyleSheet("border: 1px solid gray; padding: 5px;")
        self.file_path_label.setMinimumHeight(30)

        # 创建打开文件对话框的按钮
        self.open_file_btn = QPushButton("选择文件")
        self.open_file_btn.clicked.connect(self.open_file_dialog)

        # 将按钮和标签添加到表单布局
        form_layout.addRow("选择文件:", self.open_file_btn)
        form_layout.addRow("文件路径:", self.file_path_label)


        page.setLayout(form_layout)
        self.settings_stack.addWidget(page)

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文件",
            "",
            "所有文件 (*);;可执行文件 (*.exe)"
        )
        if file_path:
            self.file_path_label.setText(file_path)
            self.file_path_label.setToolTip(file_path)

    def create_advanced_settings_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        todo_label = QLabel("待完善")
        layout.addWidget(todo_label)

        page.setLayout(layout)
        self.settings_stack.addWidget(page)

    def load_settings(self):
        """从设置中加载当前值"""
        self.file_path_label.setText(self.settings_manager.get_value("external_tool_exec_cmd", ""))
        self.hotkey_input.setText(self.settings_manager.get_value("capture_shortcuts", "alt+c"))

    def save_settings(self):
        """保存所有设置"""
        self.settings_manager.set_value("external_tool_exec_cmd", self.file_path_label.text())
        self.settings_manager.set_value("capture_shortcuts", self.hotkey_input.text())
        # 强制同步到磁盘
        self.settings_manager.sync()

    def reset_to_default(self):
        """恢复默认设置"""
        reply = QMessageBox.question(self, "确认", "确定要恢复到默认设置吗？这将丢失所有自定义设置。",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.settings_manager.reset_to_defaults()
            self.load_settings()
            QMessageBox.information(self, "设置", "已恢复到默认设置！")


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


        self.settings_button = QPushButton("设置", self)
        self.settings_button.clicked.connect(self.open_settings)

        # 结果显示区域
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)

        # 外部工具命令输入
        self.tool_cmd = QLineEdit()
        cmd_path = self.settings_manager.get_value("external_tool_exec_cmd", "")
        if not cmd_path:
            self.tool_cmd.setPlaceholderText("输入外部工具命令，使用{text}作为文本占位符")
        else:
            self.tool_cmd.setText(f'"{cmd_path}"' +  ' "{text}"')

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
        button_layout.addWidget(self.settings_button)
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
            QMessageBox.information(self, "成功", "设置已保存并应用！")

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
        new_hotkey = self.settings_manager.get_value("capture_shortcuts", "alt+c")
        self.hotkey = new_hotkey
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
