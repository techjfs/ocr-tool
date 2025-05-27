import sys
import os
import subprocess
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QTextEdit,
                               QLineEdit, QSystemTrayIcon, QMenu, QMessageBox,
                               QDialog)
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon

from core.hotkey_manager import CrossPlatformHotkeyManager
from core.settings_manager import SettingsManager
from ui.capture_tool import CaptureTool
from ui.hover_tool import HoverTool
from ui.theme import default_stylesheet
from ui.settings_dialog import SettingsDialog

class MainWindow(QMainWindow):
    """OCR工具主窗口"""

    def __init__(self):
        super().__init__()
        self.tray_notified = False
        self.stylesheet = default_stylesheet

        self.capture_tool = CaptureTool()
        self.hover_tool = HoverTool()
        self.settings_manager = SettingsManager(use_file_storage=True)

        self.hotkey = self.settings_manager.get_value("capture_shortcuts", "alt+c")
        self.has_external_tool = bool(self.settings_manager.get_value("external_tool_exec_cmd", ""))

        # 设置界面
        self.setup_ui()

        # 设置热键管理器
        self.setup_hotkey_manager()

        # 设置系统托盘
        self.setup_tray_icon()

        # 设置状态栏提示
        QTimer.singleShot(1000, lambda: self.statusBar().showMessage(f"OCR工具已启动，可使用快捷键 {self.hotkey}"))

        # 连接信号
        self.connect_signals()

        # 更新UI配置
        self.update_ui_when_config_changed()

    def setup_ui(self):
        """初始化用户界面"""
        init_width, init_height = 960, 800
        self.setWindowTitle("OCR小工具")
        self.setGeometry(100, 100, init_width, init_height)
        self.setMinimumSize(init_width, init_height)

        # 居中显示窗口
        qr = self.frameGeometry()
        cp = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        # 创建中央控件
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 顶部标题栏
        title_widget = QWidget()
        title_widget.setStyleSheet(self.stylesheet.get_title_bar_style())
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(20, 12, 20, 12)

        title_label = QLabel("OCR 文字识别工具")
        title_label.setStyleSheet(self.stylesheet.get_title_label_style(16))

        # 状态指示标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet(self.stylesheet.get_status_label_style())

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.status_label)

        # 主要内容区域
        content_widget = QWidget()
        content_widget.setStyleSheet(self.stylesheet.get_content_background_style())
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # 配置文件信息卡片
        config_info = self.settings_manager.get_config_info()
        config_info_text = f"配置文件: {config_info['path']}\n版本: {config_info['version']}"
        if config_info.get('size'):
            config_info_text += f" | 大小: {config_info['size']} bytes"

        config_card = QWidget()
        config_card.setStyleSheet(self.stylesheet.get_card_style())
        config_layout = QVBoxLayout(config_card)
        config_layout.setContentsMargins(15, 12, 15, 12)

        config_path_label = QLabel(config_info_text)
        config_path_label.setWordWrap(True)
        config_path_label.setStyleSheet(self.stylesheet.get_info_label_style())
        config_layout.addWidget(config_path_label)

        # 功能按钮区域
        button_group = QWidget()
        button_group.setStyleSheet(self.stylesheet.get_card_style())
        button_group_layout = QVBoxLayout(button_group)
        button_group_layout.setContentsMargins(20, 20, 20, 20)
        button_group_layout.setSpacing(15)

        # 标题
        button_title = QLabel("功能操作")
        button_title.setStyleSheet(self.stylesheet.get_section_title_style(14))
        button_group_layout.addWidget(button_title)

        # 创建功能按钮
        self.screenshot_btn = QPushButton("📷 截屏识别")
        self.screenshot_btn.setStyleSheet(self.stylesheet.get_primary_button_style())
        self.screenshot_btn.clicked.connect(self.start_screenshot)

        self.hover_btn = QPushButton("🖱️ 启用悬停取词")
        self.hover_btn.setCheckable(True)
        self.hover_btn.setStyleSheet(self.stylesheet.get_secondary_button_style())
        self.hover_btn.clicked.connect(self.toggle_hover_mode)

        self.settings_button = QPushButton("⚙️ 设置")
        self.settings_button.setStyleSheet(self.stylesheet.get_secondary_button_style())
        self.settings_button.clicked.connect(self.open_settings)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addWidget(self.screenshot_btn)
        button_layout.addWidget(self.hover_btn)
        button_layout.addWidget(self.settings_button)
        button_layout.addStretch()

        button_group_layout.addLayout(button_layout)

        # 结果显示区域
        result_group = QWidget()
        result_group.setStyleSheet(self.stylesheet.get_card_style())
        result_layout = QVBoxLayout(result_group)
        result_layout.setContentsMargins(20, 20, 20, 20)
        result_layout.setSpacing(12)

        result_title = QLabel("识别结果")
        result_title.setStyleSheet(self.stylesheet.get_section_title_style(14))

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet(self.stylesheet.get_text_edit_style())

        result_layout.addWidget(result_title)
        result_layout.addWidget(self.result_text)

        # 外部工具区域
        tool_group = QWidget()
        tool_group.setStyleSheet(self.stylesheet.get_card_style())
        tool_layout = QVBoxLayout(tool_group)
        tool_layout.setContentsMargins(20, 20, 20, 20)
        tool_layout.setSpacing(12)

        tool_title = QLabel("外部工具集成")
        tool_title.setStyleSheet(self.stylesheet.get_section_title_style(14))

        self.tool_cmd = QLabel()
        cmd = self.settings_manager.get_value("external_tool_exec_cmd", "")
        if not cmd:
            self.tool_cmd.setText("在设置中配置外部工具后再使用OCR功能")
        else:
            self.tool_cmd.setText(cmd)

        self.tool_cmd.setStyleSheet(self.stylesheet.get_base_label_style())

        tool_layout.addWidget(tool_title)
        tool_layout.addWidget(self.tool_cmd)

        # 组装内容区域
        content_layout.addWidget(config_card)
        content_layout.addWidget(button_group)
        content_layout.addWidget(result_group, 1)
        content_layout.addWidget(tool_group)

        # 底部工具栏
        bottom_toolbar = QWidget()
        bottom_toolbar.setStyleSheet(self.stylesheet.get_bottom_toolbar_style())
        bottom_layout = QHBoxLayout(bottom_toolbar)
        bottom_layout.setContentsMargins(20, 12, 20, 12)

        minimize_btn = QPushButton("📥 最小化到托盘")
        minimize_btn.setStyleSheet(self.stylesheet.get_small_button_style())
        minimize_btn.clicked.connect(self.hide_window)

        bottom_layout.addStretch()
        bottom_layout.addWidget(minimize_btn)

        # 组装主布局
        main_layout.addWidget(title_widget)
        main_layout.addWidget(content_widget, 1)
        main_layout.addWidget(bottom_toolbar)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def setup_hotkey_manager(self):
        """设置全局热键管理器"""
        if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
            self.hotkey_manager.stop()

        self.hotkey_manager = CrossPlatformHotkeyManager(self.hotkey)
        self.hotkey_manager.hotkey_pressed.connect(self.start_screenshot)
        self.hotkey_manager.mouse_clicked.connect(self.start_hover)
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
            self.update_ui_when_config_changed()
            QMessageBox.information(self, "成功", "设置已保存并应用！")

    def update_ui_when_config_changed(self):
        """当配置变了，需要更新部分UI和状态"""
        self.screenshot_btn.setText(f'📷 截屏识别({self.settings_manager.get_value("capture_shortcuts", "alt+c")})')
        cmd = self.settings_manager.get_value("external_tool_exec_cmd", "")
        self.has_external_tool = bool(cmd)
        if not cmd:
            self.tool_cmd.setText("在设置中配置外部工具后再使用OCR功能")
        else:
            self.tool_cmd.setText(cmd)

    def connect_signals(self):
        """连接组件信号"""
        self.capture_tool.capture_completed.connect(self.update_ocr_result)
        self.hover_tool.word_found.connect(self.update_hover_result)
        self.hover_tool.status_changed.connect(self.update_status)

    def update_ocr_result(self, text_list):
        """更新OCR结果"""
        if not text_list:
            self.status_label.setText("未识别到文本")
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 12px;
                    color: {self.stylesheet.theme.WHITE};
                    background: {self.stylesheet.theme.DANGER};
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-weight: bold;
                }}
            """)
            self.result_text.setPlainText("未能识别到任何文本")
            return

        # 更新状态
        self.status_label.setText("识别完成")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                color: {self.stylesheet.theme.WHITE};
                background: {self.stylesheet.theme.SUCCESS};
                padding: 4px 12px;
                border-radius: 12px;
                font-weight: bold;
            }}
        """)

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
        if "成功" in status or "就绪" in status:
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 12px;
                    color: {self.stylesheet.theme.WHITE};
                    background: {self.stylesheet.theme.SUCCESS};
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-weight: bold;
                }}
            """)
        elif "失败" in status or "错误" in status:
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 12px;
                    color: {self.stylesheet.theme.WHITE};
                    background: {self.stylesheet.theme.DANGER};
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-weight: bold;
                }}
            """)
        else:
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 12px;
                    color: {self.stylesheet.theme.WHITE};
                    background: {self.stylesheet.theme.WARNING};
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-weight: bold;
                }}
            """)

        self.status_label.setText(status)

    def toggle_hover_mode(self, checked):
        """切换悬停取词模式"""
        if checked:
            self.status_label.setText("悬停取词模式已启用，按Alt+鼠标左键进行取词")
            self.statusBar().showMessage("悬停取词模式已启用")
        else:
            self.status_label.setText("就绪")
            self.statusBar().showMessage("悬停取词模式已禁用")

    def setup_hotkey(self):
        """设置全局快捷键"""
        new_hotkey = self.settings_manager.get_value("capture_shortcuts", "alt+c")
        self.hotkey = new_hotkey
        self.setup_hotkey_manager()

        # 更新托盘菜单
        hotkey_action = self.tray_icon.contextMenu().actions()[3]
        hotkey_action.setText(f"设置快捷键 ({self.hotkey})")

        self.statusBar().showMessage(f"已设置全局快捷键为: {self.hotkey}", 3000)

    def start_screenshot(self):
        """启动截图OCR功能"""
        if not self.has_external_tool:
            QMessageBox.warning(self, "警告", "请先在设置中配置外部工具命令")
            return

        self.hide()
        self.status_label.setText("请选择截图区域")
        QTimer.singleShot(300, self.capture_tool.start_capture)

    def start_hover(self):
        if not self.has_external_tool:
            QMessageBox.warning(self, "警告", "请先在设置中配置外部工具命令")
            return

        self.hover_tool.capture_at_cursor()

    def run_external_tool(self):
        """运行外部工具处理OCR结果"""
        text = self.result_text.toPlainText()
        cmd = self.settings_manager.get_value("external_tool_exec_cmd", "")
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
