"""
设置对话框模块
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QLineEdit, QFormLayout, QSplitter,
                               QListWidget, QStackedWidget, QFileDialog,
                               QWidget, QMessageBox)
from PySide6.QtCore import Qt

from ui.theme import default_stylesheet


class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.stylesheet = default_stylesheet

        self.setWindowTitle("设置")
        self.setModal(True)
        self.resize(400, 300)

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """设置用户界面"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建顶部标题栏
        title_widget = self.create_title_widget()

        # 主要内容区域
        content_widget = self.create_content_widget()

        # 底部按钮区域
        button_container = self.create_button_container()

        # 组装主布局
        main_layout.addWidget(title_widget)
        main_layout.addWidget(content_widget, 1)
        main_layout.addWidget(button_container)

        self.setLayout(main_layout)

        # 设置初始选择
        self.category_list.setCurrentRow(0)

        # 设置窗口最小尺寸
        self.setMinimumSize(800, 600)

    def create_title_widget(self) -> QWidget:
        """创建标题栏控件"""
        title_widget = QWidget()
        title_widget.setStyleSheet(self.stylesheet.get_title_bar_style())

        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(20, 15, 20, 15)

        title_label = QLabel("系统设置")
        title_label.setStyleSheet(self.stylesheet.get_title_label_style(18))

        title_layout.addWidget(title_label)
        title_layout.addStretch()

        return title_widget

    def create_content_widget(self) -> QWidget:
        """创建内容区域控件"""
        content_widget = QWidget()
        content_widget.setStyleSheet(self.stylesheet.get_content_background_style())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet(self.stylesheet.get_splitter_style())

        # 左侧分类列表
        left_container = self.create_left_container()

        # 右侧设置页面区域
        right_container = self.create_right_container()

        splitter.addWidget(left_container)
        splitter.addWidget(right_container)
        splitter.setStretchFactor(0, 0)  # 左侧固定
        splitter.setStretchFactor(1, 1)  # 右侧自适应

        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(splitter)

        return content_widget

    def create_left_container(self) -> QWidget:
        """创建左侧容器"""
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(15, 15, 8, 15)

        self.category_list = QListWidget()
        self.category_list.setFixedWidth(160)
        self.category_list.setStyleSheet(self.stylesheet.get_list_widget_style())

        categories = ["界面设置", "系统设计", "高级设置"]
        self.category_list.addItems(categories)
        self.category_list.currentRowChanged.connect(self.on_category_changed)

        left_layout.addWidget(self.category_list)
        left_layout.addStretch()

        return left_container

    def create_right_container(self) -> QWidget:
        """创建右侧容器"""
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(8, 15, 15, 15)

        self.settings_stack = QStackedWidget()
        self.settings_stack.setStyleSheet(self.stylesheet.get_stacked_widget_style())

        self.create_ui_settings_page()
        self.create_system_settings_page()
        self.create_advanced_settings_page()

        right_layout.addWidget(self.settings_stack)

        return right_container

    def create_button_container(self) -> QWidget:
        """创建按钮容器"""
        button_container = QWidget()
        button_container.setStyleSheet(self.stylesheet.get_bottom_toolbar_style())

        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(20, 15, 20, 15)
        button_layout.setSpacing(12)

        # 版本信息
        info_label = QLabel("版本 1.0.0")
        info_label.setStyleSheet(self.stylesheet.get_version_label_style())

        button_layout.addWidget(info_label)
        button_layout.addStretch()

        # 创建按钮
        self.create_buttons(button_layout)

        return button_container

    def create_buttons(self, layout: QHBoxLayout):
        """创建按钮"""
        button_styles = self.stylesheet.get_settings_button_style()

        self.reset_btn = QPushButton("恢复默认")
        self.cancel_btn = QPushButton("取消")
        self.save_btn = QPushButton("保存设置")

        self.reset_btn.setStyleSheet(button_styles['reset'])
        self.cancel_btn.setStyleSheet(button_styles['cancel'])
        self.save_btn.setStyleSheet(button_styles['save'])

        # 连接信号
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.reset_btn.clicked.connect(self.reset_to_default)

        layout.addWidget(self.reset_btn)
        layout.addWidget(self.cancel_btn)
        layout.addWidget(self.save_btn)

    def create_ui_settings_page(self):
        """创建界面设置页面"""
        page = QWidget()
        layout = QVBoxLayout()

        todo_label = QLabel("待完善")
        todo_label.setStyleSheet(self.stylesheet.get_section_title_style())
        layout.addWidget(todo_label)

        page.setLayout(layout)
        self.settings_stack.addWidget(page)

    def create_system_settings_page(self):
        """创建系统设置页面"""
        page = QWidget()
        form_layout = QFormLayout()

        # 快捷键设置
        self.hotkey_input = QLineEdit("")
        self.hotkey_input.setPlaceholderText("例如: alt+c")
        self.hotkey_input.setStyleSheet(self.stylesheet.get_line_edit_style())
        form_layout.addRow("设置快捷键:", self.hotkey_input)

        # 文件选择
        self.file_path_label = QLabel("未选择文件")
        self.file_path_label.setStyleSheet(self.stylesheet.get_file_path_label_style())
        self.file_path_label.setMinimumHeight(30)

        self.open_file_btn = QPushButton("选择文件")
        self.open_file_btn.setStyleSheet(self.stylesheet.get_secondary_button_style())
        self.open_file_btn.clicked.connect(self.open_file_dialog)

        form_layout.addRow("选择文件:", self.open_file_btn)
        form_layout.addRow("文件路径:", self.file_path_label)

        page.setLayout(form_layout)
        self.settings_stack.addWidget(page)

    def create_advanced_settings_page(self):
        """创建高级设置页面"""
        page = QWidget()
        layout = QVBoxLayout()

        todo_label = QLabel("待完善")
        todo_label.setStyleSheet(self.stylesheet.get_section_title_style())
        layout.addWidget(todo_label)

        page.setLayout(layout)
        self.settings_stack.addWidget(page)

    def on_category_changed(self, index):
        """分类改变事件"""
        self.settings_stack.setCurrentIndex(index)

    def open_file_dialog(self):
        """打开文件对话框"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文件",
            "",
            "所有文件 (*);;可执行文件 (*.exe)"
        )
        if file_path:
            self.file_path_label.setText(file_path)
            self.file_path_label.setToolTip(file_path)

    def load_settings(self):
        """从设置中加载当前值"""
        self.file_path_label.setText(
            self.settings_manager.get_value("external_tool_exec_cmd", "")
        )
        self.hotkey_input.setText(
            self.settings_manager.get_value("capture_shortcuts", "alt+c")
        )

    def save_settings(self):
        """保存所有设置"""
        self.settings_manager.set_value(
            "external_tool_exec_cmd",
            self.file_path_label.text()
        )
        self.settings_manager.set_value(
            "capture_shortcuts",
            self.hotkey_input.text()
        )
        # 强制同步到磁盘
        self.settings_manager.sync()

    def reset_to_default(self):
        """恢复默认设置"""
        reply = QMessageBox.question(
            self,
            "确认",
            "确定要恢复到默认设置吗？这将丢失所有自定义设置。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.settings_manager.reset_to_defaults()
            self.load_settings()
            QMessageBox.information(self, "设置", "已恢复到默认设置！")

    def accept(self):
        """接受设置"""
        self.save_settings()
        if self.parent():
            self.parent().setup_hotkey()
        super().accept()