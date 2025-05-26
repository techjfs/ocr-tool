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
        main_layout.setContentsMargins(0, 0, 0, 0)  # 移除外边距以充分利用空间
        main_layout.setSpacing(0)

        # 创建顶部标题栏
        title_widget = QWidget()
        title_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 #4A90E2, stop:1 #357ABD);
                color: white;
                border-bottom: 2px solid #2E5BA8;
            }
        """)
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(20, 15, 20, 15)

        title_label = QLabel("系统设置")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                background: transparent;
                border: none;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # 主要内容区域
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #F8F9FA;
            }
        """)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #E3E8ED;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #4A90E2;
            }
        """)

        # 左侧分类列表 - 增加宽度并美化
        self.category_list = QListWidget()
        self.category_list.setFixedWidth(160)  # 增加宽度
        self.category_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #E3E8ED;
                border-radius: 8px;
                outline: none;
                padding: 8px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 12px 16px;
                margin: 2px 0;
                border-radius: 6px;
                color: #495057;
            }
            QListWidget::item:hover {
                background-color: #E8F4FD;
                color: #4A90E2;
            }
            QListWidget::item:selected {
                background-color: #4A90E2;
                color: white;
                font-weight: bold;
            }
        """)

        categories = ["界面设置", "系统设计", "高级设置"]
        self.category_list.addItems(categories)
        self.category_list.currentRowChanged.connect(self.on_category_changed)

        # 右侧设置页面区域
        self.settings_stack = QStackedWidget()
        self.settings_stack.setStyleSheet("""
            QStackedWidget {
                background-color: white;
                border: 1px solid #E3E8ED;
                border-radius: 8px;
                padding: 20px;
            }
        """)

        self.create_ui_settings_page()
        self.create_system_settings_page()
        self.create_advanced_settings_page()

        # 左右布局 - 优化比例
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(15, 15, 8, 15)
        left_layout.addWidget(self.category_list)
        left_layout.addStretch()  # 底部留白

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(8, 15, 15, 15)
        right_layout.addWidget(self.settings_stack)

        splitter.addWidget(left_container)
        splitter.addWidget(right_container)
        splitter.setStretchFactor(0, 0)  # 左侧固定
        splitter.setStretchFactor(1, 1)  # 右侧自适应

        # 底部按钮区域 - 重新设计
        button_container = QWidget()
        button_container.setStyleSheet("""
            QWidget {
                background-color: #F8F9FA;
                border-top: 1px solid #E3E8ED;
            }
        """)

        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(20, 15, 20, 15)
        button_layout.setSpacing(12)

        # 左侧添加版本信息或其他信息
        info_label = QLabel("版本 1.0.0")
        info_label.setStyleSheet("""
            QLabel {
                color: #6C757D;
                font-size: 12px;
                background: transparent;
            }
        """)
        button_layout.addWidget(info_label)
        button_layout.addStretch()

        # 按钮样式 - 蓝白色调
        self.reset_btn = QPushButton("恢复默认")
        self.cancel_btn = QPushButton("取消")
        self.save_btn = QPushButton("保存设置")

        # 统一按钮基础样式
        base_button_style = """
            QPushButton {
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
                border-radius: 6px;
                border: 2px solid transparent;
                min-width: 80px;
            }
            QPushButton:focus {
                outline: none;
            }
        """

        # 恢复默认按钮 - 次要按钮样式
        self.reset_btn.setStyleSheet(base_button_style + """
            QPushButton {
                background-color: white;
                color: #6C757D;
                border-color: #E3E8ED;
            }
            QPushButton:hover {
                background-color: #F8F9FA;
                border-color: #ADB5BD;
                color: #495057;
            }
            QPushButton:pressed {
                background-color: #E9ECEF;
            }
        """)

        # 取消按钮 - 次要按钮样式
        self.cancel_btn.setStyleSheet(base_button_style + """
            QPushButton {
                background-color: white;
                color: #495057;
                border-color: #CED4DA;
            }
            QPushButton:hover {
                background-color: #F8F9FA;
                border-color: #ADB5BD;
            }
            QPushButton:pressed {
                background-color: #E9ECEF;
            }
        """)

        # 保存按钮 - 主要按钮样式（蓝色）
        self.save_btn.setStyleSheet(base_button_style + """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                           stop:0 #4A90E2, stop:1 #357ABD);
                color: white;
                border-color: #357ABD;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                           stop:0 #5BA0F2, stop:1 #4A90E2);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                           stop:0 #357ABD, stop:1 #2E5BA8);
            }
        """)

        # 连接按钮信号
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.reset_btn.clicked.connect(self.reset_to_default)

        # 按钮从右到左排列：保存、取消、恢复默认
        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)

        # 组装主布局
        main_layout.addWidget(title_widget)
        main_layout.addWidget(splitter, 1)  # 主要内容区域占据大部分空间
        main_layout.addWidget(button_container)

        self.setLayout(main_layout)

        # 设置初始选择
        self.category_list.setCurrentRow(0)

        # 设置窗口最小尺寸以确保良好显示
        self.setMinimumSize(800, 600)

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
        self.setup_ui()

        # 设置热键管理器
        self.setup_hotkey_manager()

        # 设置系统托盘
        self.setup_tray_icon()

        # 设置状态栏提示
        QTimer.singleShot(1000, lambda: self.statusBar().showMessage(f"OCR工具已启动，可使用快捷键 {self.hotkey}"))

        # 连接信号
        self.connect_signals()

        # 有些UI的文本展示依赖配置，当配置改变后需要更新
        self.update_ui()

    def setup_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("OCR小工具")
        self.setGeometry(100, 100, 700, 500)
        self.setMinimumSize(600, 450)

        # 创建中央控件
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 顶部标题栏
        title_widget = QWidget()
        title_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 #4A90E2, stop:1 #357ABD);
                color: white;
                border-bottom: 2px solid #2E5BA8;
            }
        """)
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(20, 12, 20, 12)

        title_label = QLabel("OCR 文字识别工具")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: white;
                background: transparent;
                border: none;
            }
        """)

        # 状态指示标签（移到标题栏右侧）
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #E8F4FD;
                background: rgba(255, 255, 255, 0.2);
                padding: 4px 12px;
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
        """)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(self.status_label)

        # 主要内容区域
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #F8F9FA;
            }
        """)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # 配置文件信息卡片
        config_info = self.settings_manager.get_config_info()
        config_info_text = f"配置文件: {config_info['path']}\n版本: {config_info['version']}"
        if config_info.get('size'):
            config_info_text += f" | 大小: {config_info['size']} bytes"

        config_card = QWidget()
        config_card.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #E3E8ED;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        config_layout = QVBoxLayout(config_card)
        config_layout.setContentsMargins(15, 12, 15, 12)

        config_path_label = QLabel(config_info_text)
        config_path_label.setWordWrap(True)
        config_path_label.setStyleSheet("""
            QLabel {
                color: #6C757D;
                font-size: 11px;
                background: transparent;
                border: none;
                line-height: 1.4;
            }
        """)
        config_layout.addWidget(config_path_label)

        # 功能按钮区域
        button_group = QWidget()
        button_group.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #E3E8ED;
                border-radius: 8px;
            }
        """)
        button_group_layout = QVBoxLayout(button_group)
        button_group_layout.setContentsMargins(20, 20, 20, 20)
        button_group_layout.setSpacing(15)

        # 标题
        button_title = QLabel("功能操作")
        button_title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #495057;
                background: transparent;
                border: none;
                margin-bottom: 5px;
            }
        """)
        button_group_layout.addWidget(button_title)

        # 按钮样式定义
        primary_button_style = """
            QPushButton {
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 500;
                border-radius: 6px;
                border: 2px solid transparent;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                           stop:0 #4A90E2, stop:1 #357ABD);
                color: white;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                           stop:0 #5BA0F2, stop:1 #4A90E2);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                           stop:0 #357ABD, stop:1 #2E5BA8);
            }
            QPushButton:focus {
                outline: none;
            }
        """

        secondary_button_style = """
            QPushButton {
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 500;
                border-radius: 6px;
                background-color: white;
                color: #495057;
                border: 2px solid #CED4DA;
            }
            QPushButton:hover {
                background-color: #F8F9FA;
                border-color: #4A90E2;
                color: #4A90E2;
            }
            QPushButton:pressed {
                background-color: #E9ECEF;
            }
            QPushButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                           stop:0 #4A90E2, stop:1 #357ABD);
                color: white;
                border-color: #357ABD;
            }
            QPushButton:focus {
                outline: none;
            }
        """

        # 创建功能按钮
        self.screenshot_btn = QPushButton("📷 截屏识别")
        self.screenshot_btn.setStyleSheet(primary_button_style)
        self.screenshot_btn.clicked.connect(self.start_screenshot)

        self.hover_btn = QPushButton("🖱️ 启用悬停取词")
        self.hover_btn.setCheckable(True)
        self.hover_btn.setStyleSheet(secondary_button_style)
        self.hover_btn.clicked.connect(self.toggle_hover_mode)

        self.settings_button = QPushButton("⚙️ 设置")
        self.settings_button.setStyleSheet(secondary_button_style)
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
        result_group.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #E3E8ED;
                border-radius: 8px;
            }
        """)
        result_layout = QVBoxLayout(result_group)
        result_layout.setContentsMargins(20, 20, 20, 20)
        result_layout.setSpacing(12)

        result_title = QLabel("识别结果")
        result_title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #495057;
                background: transparent;
                border: none;
            }
        """)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E3E8ED;
                border-radius: 6px;
                padding: 12px;
                font-size: 13px;
                background-color: #FAFBFC;
                color: #495057;
                selection-background-color: #4A90E2;
            }
            QTextEdit:focus {
                border-color: #4A90E2;
                outline: none;
            }
        """)

        result_layout.addWidget(result_title)
        result_layout.addWidget(self.result_text)

        # 外部工具区域
        tool_group = QWidget()
        tool_group.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #E3E8ED;
                border-radius: 8px;
            }
        """)
        tool_layout = QVBoxLayout(tool_group)
        tool_layout.setContentsMargins(20, 20, 20, 20)
        tool_layout.setSpacing(12)

        tool_title = QLabel("外部工具集成")
        tool_title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #495057;
                background: transparent;
                border: none;
            }
        """)

        self.tool_cmd = QLineEdit()
        cmd_path = self.settings_manager.get_value("external_tool_exec_cmd", "")
        if not cmd_path:
            self.tool_cmd.setPlaceholderText("输入外部工具命令，使用{text}作为文本占位符")
        else:
            self.tool_cmd.setText(f'"{cmd_path}"' + ' "{text}"')

        self.tool_cmd.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 13px;
                border: 1px solid #CED4DA;
                border-radius: 6px;
                background-color: white;
                color: #495057;
            }
            QLineEdit:focus {
                border-color: #4A90E2;
                outline: none;
            }
            QLineEdit::placeholder {
                color: #ADB5BD;
            }
        """)

        self.run_tool_btn = QPushButton("🔧 检查外部工具调用")
        self.run_tool_btn.setStyleSheet(secondary_button_style)
        self.run_tool_btn.clicked.connect(self.check_external_tool_call)

        tool_layout.addWidget(tool_title)
        tool_layout.addWidget(self.tool_cmd)
        tool_layout.addWidget(self.run_tool_btn)

        # 组装内容区域
        content_layout.addWidget(config_card)
        content_layout.addWidget(button_group)
        content_layout.addWidget(result_group, 1)  # 结果区域占据剩余空间
        content_layout.addWidget(tool_group)

        # 底部工具栏
        bottom_toolbar = QWidget()
        bottom_toolbar.setStyleSheet("""
            QWidget {
                background-color: #F8F9FA;
                border-top: 1px solid #E3E8ED;
            }
        """)
        bottom_layout = QHBoxLayout(bottom_toolbar)
        bottom_layout.setContentsMargins(20, 12, 20, 12)

        minimize_btn = QPushButton("📥 最小化到托盘")
        minimize_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                font-size: 12px;
                border-radius: 4px;
                background-color: transparent;
                color: #6C757D;
                border: 1px solid transparent;
            }
            QPushButton:hover {
                background-color: #E9ECEF;
                color: #495057;
            }
            QPushButton:pressed {
                background-color: #DEE2E6;
            }
        """)
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
            self.update_ui()
            QMessageBox.information(self, "成功", "设置已保存并应用！")

    def update_ui(self):
        self.screenshot_btn.setText(f'截屏识别({self.settings_manager.get_value("capture_shortcuts", "alt+c")})')

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
