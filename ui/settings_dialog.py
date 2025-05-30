from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QLineEdit, QFormLayout, QScrollArea,
                               QListWidget, QStackedWidget, QFileDialog,
                               QWidget, QMessageBox, QFrame)
from PySide6.QtCore import Qt, QSize
import subprocess
import os
from ui.theme import ThemeManager, ThemeType, create_stylesheet


class SectionWidget(QWidget):
    def __init__(self, title: str, description: str = "", stylesheet=None):
        super().__init__()
        self.stylesheet = stylesheet
        self.setStyleSheet(self.stylesheet.get_compact_card_style() if stylesheet else "")

        self._layout = QVBoxLayout()
        self._layout.setContentsMargins(12, 10, 12, 10)
        self._layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setStyleSheet(self.stylesheet.get_section_title_style(12))
        self._layout.addWidget(title_label)

        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet(self.stylesheet.get_info_label_style())
            self._layout.addWidget(desc_label)

            divider = QFrame()
            divider.setFrameShape(QFrame.Shape.HLine)
            divider.setStyleSheet(self.stylesheet.get_divider_style())
            self._layout.addWidget(divider)

        self.setLayout(self._layout)

    def addLayout(self, layout):
        self._layout.addLayout(layout)

    def addWidget(self, widget):
        self._layout.addWidget(widget)


class SettingsDialog(QDialog):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager

        # 根据设置管理器中的主题配置创建样式表
        current_theme = self.settings_manager.get_value("current_theme", "blue")
        theme_type = ThemeType(current_theme)
        self.stylesheet = create_stylesheet(theme_type)

        self.setWindowTitle("设置")
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self.setMinimumSize(680, 520)
        self.resize(720, 580)

        # 存储主题按钮的引用，用于状态管理
        self.theme_buttons = {}

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self.create_title_widget())
        main_layout.addWidget(self.create_content_widget(), 1)
        main_layout.addWidget(self.create_bottom_widget())

        self.category_list.setCurrentRow(0)

    def create_title_widget(self):
        widget = QWidget()
        widget.setStyleSheet(self.stylesheet.get_title_bar_style())
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(16, 8, 16, 8)

        title_label = QLabel("系统设置")
        title_label.setStyleSheet(self.stylesheet.get_title_label_style(16))
        status_label = QLabel("配置中心")
        status_label.setStyleSheet(self.stylesheet.get_status_label_style())

        layout.addWidget(title_label)
        layout.addWidget(status_label)
        layout.addStretch()
        return widget

    def create_content_widget(self):
        widget = QWidget()
        widget.setStyleSheet(self.stylesheet.get_content_background_style())
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        layout.addWidget(self.create_navigation_widget())
        layout.addWidget(self.create_settings_widget(), 1)
        return widget

    def create_navigation_widget(self):
        widget = QWidget()
        widget.setStyleSheet(self.stylesheet.get_compact_card_style())
        widget.setFixedWidth(140)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 8, 6, 8)

        nav_title = QLabel("设置分类")
        nav_title.setStyleSheet(self.stylesheet.get_section_title_style(12))
        layout.addWidget(nav_title)

        self.category_list = QListWidget()
        self.category_list.addItems(["🎨 界面设置", "⚙️ 系统设置", "🔧 高级设置"])
        self.category_list.setStyleSheet(self.stylesheet.get_nav_list_style())
        self.category_list.currentRowChanged.connect(self.on_category_changed)
        layout.addWidget(self.category_list)
        layout.addStretch()
        return widget

    def create_settings_widget(self):
        widget = QWidget()
        widget.setStyleSheet(self.stylesheet.get_card_style())
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.settings_stack = QStackedWidget()
        layout.addWidget(self.settings_stack)

        self.create_ui_settings_page()
        self.create_system_settings_page()
        self.create_advanced_settings_page()
        return widget

    def create_scrollable_page(self, title, icon, sections):
        page = QWidget()
        header = QLabel(f"{icon} {title}")
        header.setStyleSheet(self.stylesheet.get_section_title_style(14))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        for section in sections:
            layout.addWidget(section)
        layout.addStretch()
        scroll.setWidget(content)

        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(header)
        page_layout.addWidget(scroll)

        self.settings_stack.addWidget(page)

    def create_ui_settings_page(self):
        theme_section = SectionWidget("主题配色", "选择应用程序的视觉主题", self.stylesheet)
        theme_layout = QHBoxLayout()

        # 获取可用主题配置
        theme_configs = [
            ("蓝色主题", "#4A90E2", ThemeType.BLUE),
            ("红色主题", "#E74C3C", ThemeType.RED),
            ("绿色主题", "#27AE60", ThemeType.GREEN)
        ]

        # 创建主题按钮组
        for name, color, theme_type in theme_configs:
            btn = QPushButton(name)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    padding: 8px 16px;
                    border: 2px solid transparent;
                    border-radius: 6px;
                    font-weight: 500;
                    min-height: 20px;
                }}
                QPushButton:hover {{
                    border-color: rgba(255, 255, 255, 0.7);
                }}
                QPushButton:checked {{
                    border-color: white;
                    font-weight: 600;
                }}
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, t=theme_type: self.on_theme_changed(t))

            # 存储按钮引用
            self.theme_buttons[theme_type] = btn
            theme_layout.addWidget(btn)

        theme_layout.addStretch()
        theme_section.addLayout(theme_layout)

        # 主题预览区域
        preview_section = SectionWidget("主题预览", "预览当前选中的主题效果", self.stylesheet)
        self.create_theme_preview(preview_section)

        display_section = SectionWidget("显示选项", "调整界面显示相关设置", self.stylesheet)
        form = QFormLayout()

        # 界面字体大小设置
        self.font_size_input = QLineEdit()
        self.font_size_input.setStyleSheet(self.stylesheet.get_line_edit_style())
        form.addRow("界面字体大小:", self.font_size_input)

        # 窗口透明度设置
        self.opacity_input = QLineEdit()
        self.opacity_input.setStyleSheet(self.stylesheet.get_line_edit_style())
        form.addRow("窗口透明度:", self.opacity_input)

        display_section.addLayout(form)

        self.create_scrollable_page("界面设置", "🎨", [theme_section, preview_section, display_section])

    def create_theme_preview(self, parent_section):
        """创建主题预览区域"""
        preview_layout = QVBoxLayout()

        # 预览标题
        preview_title = QLabel("预览效果")
        preview_title.setStyleSheet(self.stylesheet.get_section_title_style(12))
        preview_layout.addWidget(preview_title)

        # 预览容器
        preview_container = QWidget()
        preview_container.setStyleSheet(self.stylesheet.get_card_style())
        preview_container.setFixedHeight(120)

        container_layout = QVBoxLayout(preview_container)
        container_layout.setContentsMargins(16, 12, 16, 12)

        # 预览按钮组
        button_layout = QHBoxLayout()

        primary_btn = QPushButton("主要按钮")
        primary_btn.setStyleSheet(self.stylesheet.get_primary_button_style())

        secondary_btn = QPushButton("次要按钮")
        secondary_btn.setStyleSheet(self.stylesheet.get_secondary_button_style())

        small_btn = QPushButton("小按钮")
        small_btn.setStyleSheet(self.stylesheet.get_small_button_style())

        button_layout.addWidget(primary_btn)
        button_layout.addWidget(secondary_btn)
        button_layout.addWidget(small_btn)
        button_layout.addStretch()

        # 预览输入框
        preview_input = QLineEdit("示例输入框")
        preview_input.setStyleSheet(self.stylesheet.get_line_edit_style())

        container_layout.addLayout(button_layout)
        container_layout.addWidget(preview_input)
        container_layout.addStretch()

        preview_layout.addWidget(preview_container)
        parent_section.addLayout(preview_layout)

        # 保存预览控件的引用，用于主题切换时更新
        self.preview_widgets = {
            'container': preview_container,
            'primary_btn': primary_btn,
            'secondary_btn': secondary_btn,
            'small_btn': small_btn,
            'input': preview_input
        }

    def on_theme_changed(self, theme_type: ThemeType):
        """主题切换处理"""
        # 更新按钮选中状态
        for btn_theme, btn in self.theme_buttons.items():
            btn.setChecked(btn_theme == theme_type)

        # 创建新的样式表
        self.stylesheet = create_stylesheet(theme_type)

        # 应用新主题到整个对话框
        self.apply_theme_to_dialog()

        # 更新预览区域
        self.update_theme_preview()

        # 保存主题设置（临时保存，等用户点击保存时正式生效）
        self.current_theme_type = theme_type

    def apply_theme_to_dialog(self):
        """将新主题应用到整个对话框"""
        # 重新应用样式到主要组件
        for widget in self.findChildren(QWidget):
            widget_class = widget.__class__.__name__

            # 根据控件类型应用相应样式
            if isinstance(widget, QPushButton):
                # 跳过主题按钮，它们有自定义样式
                if widget not in self.theme_buttons.values():
                    if hasattr(widget, 'property') and widget.property('button_type'):
                        button_type = widget.property('button_type')
                        if button_type == 'primary':
                            widget.setStyleSheet(self.stylesheet.get_primary_button_style())
                        elif button_type == 'secondary':
                            widget.setStyleSheet(self.stylesheet.get_secondary_button_style())
            elif isinstance(widget, QLineEdit):
                widget.setStyleSheet(self.stylesheet.get_line_edit_style())
            elif isinstance(widget, QListWidget):
                if widget == self.category_list:
                    widget.setStyleSheet(self.stylesheet.get_nav_list_style())

        # 重新应用主要区域样式
        self.update_main_areas_style()

    def update_main_areas_style(self):
        """更新主要区域的样式"""
        # 重新获取主要区域并应用样式
        title_widget = self.findChild(QWidget, "title_widget")
        if title_widget:
            title_widget.setStyleSheet(self.stylesheet.get_title_bar_style())

        content_widget = self.findChild(QWidget, "content_widget")
        if content_widget:
            content_widget.setStyleSheet(self.stylesheet.get_content_background_style())

    def update_theme_preview(self):
        """更新主题预览区域"""
        if hasattr(self, 'preview_widgets'):
            self.preview_widgets['container'].setStyleSheet(self.stylesheet.get_card_style())
            self.preview_widgets['primary_btn'].setStyleSheet(self.stylesheet.get_primary_button_style())
            self.preview_widgets['secondary_btn'].setStyleSheet(self.stylesheet.get_secondary_button_style())
            self.preview_widgets['small_btn'].setStyleSheet(self.stylesheet.get_small_button_style())
            self.preview_widgets['input'].setStyleSheet(self.stylesheet.get_line_edit_style())

    def create_system_settings_page(self):
        hotkey_section = SectionWidget("快捷键配置", "设置全局快捷键组合", self.stylesheet)
        self.hotkey_input = QLineEdit()
        self.hotkey_input.setPlaceholderText("例如: alt+c")
        form = QFormLayout()
        form.addRow("截图快捷键:", self.hotkey_input)
        hotkey_section.addLayout(form)

        tool_section = SectionWidget("外部工具集成", "配置外部图像处理工具", self.stylesheet)
        self.tool_path_label = QLabel("未选择工具")
        self.tool_path_label.setToolTip("")
        self.tool_path_label.setProperty("full_path", "")
        self.tool_param_input = QLineEdit('"{text}"')
        self.tool_param_input.textChanged.connect(self.update_check_tool_text)
        self.check_info_label = QLabel("命令预览将在此显示")

        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.open_file_dialog)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.tool_path_label, 1)
        path_layout.addWidget(browse_btn)
        tool_section.addLayout(path_layout)

        param_layout = QHBoxLayout()
        param_layout.addWidget(self.tool_param_input, 1)
        tool_section.addLayout(param_layout)

        preview_layout = QVBoxLayout()
        preview_layout.addWidget(self.check_info_label)
        test_btn = QPushButton("测试命令")
        test_btn.clicked.connect(self.check_tool_call)
        preview_layout.addWidget(test_btn)
        tool_section.addLayout(preview_layout)

        self.create_scrollable_page("系统设置", "⚙️", [hotkey_section, tool_section])

    def create_advanced_settings_page(self):
        dev_section = SectionWidget("开发中功能", "这些功能正在开发中，敬请期待", self.stylesheet)
        layout = QVBoxLayout()
        for f in ["🔄 自动更新检查", "📊 使用统计分析", "🗃️ 数据导入导出", "🔐 高级安全选项", "🌐 云同步设置"]:
            layout.addWidget(QLabel(f))
        dev_section.addLayout(layout)
        self.create_scrollable_page("高级设置", "🔧", [dev_section])

    def create_bottom_widget(self):
        widget = QWidget()
        widget.setFixedHeight(50)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(16, 10, 16, 10)

        layout.addWidget(QLabel("版本 1.0.0"))
        layout.addStretch()
        self.create_action_buttons(layout)
        return widget

    def create_action_buttons(self, layout):
        for text, callback in [("恢复默认", self.reset_to_default), ("取消", self.reject), ("保存设置", self.accept)]:
            btn = QPushButton(text)
            btn.setFixedSize(QSize(70, 28))
            btn.clicked.connect(callback)
            layout.addWidget(btn)

    def on_category_changed(self, index):
        self.settings_stack.setCurrentIndex(index)

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择外部工具", "", "可执行文件 (*.exe);;所有文件 (*.*)")
        if file_path:
            file_name = os.path.basename(file_path)
            self.tool_path_label.setText(file_name)
            self.tool_path_label.setToolTip(file_path)
            self.tool_path_label.setProperty("full_path", file_path)
            self.update_check_tool_text()

    def update_check_tool_text(self):
        tool_path = self.tool_path_label.property("full_path")
        tool_param = self.tool_param_input.text()
        if tool_path:
            self.check_info_label.setText(f'"{tool_path}" {tool_param}')
        else:
            self.check_info_label.setText("请先选择外部工具")

    def check_tool_call(self):
        cmd = self.check_info_label.text().replace("{text}", "hello")
        try:
            subprocess.Popen(cmd, shell=True)
            QMessageBox.information(self, "成功", "✅ 外部工具测试成功！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"❌ 命令执行失败:\n{str(e)}")

    def load_settings(self):
        """加载设置"""
        # 加载主题设置
        current_theme = self.settings_manager.get_value("current_theme", "blue")
        try:
            theme_type = ThemeType(current_theme)
            self.current_theme_type = theme_type
            # 设置对应主题按钮为选中状态
            if theme_type in self.theme_buttons:
                self.theme_buttons[theme_type].setChecked(True)
        except ValueError:
            # 如果主题值无效，使用默认蓝色主题
            self.current_theme_type = ThemeType.BLUE
            self.theme_buttons[ThemeType.BLUE].setChecked(True)

        # 加载显示设置
        font_size = self.settings_manager.get_value("font_size", "12")
        self.font_size_input.setText(str(font_size))

        opacity = self.settings_manager.get_value("window_opacity", "100")
        self.opacity_input.setText(str(opacity))

        # 加载外部工具设置
        cmd = self.settings_manager.get_value("external_tool_exec_cmd", "")
        if cmd:
            self.check_info_label.setText(cmd)
            if '"' in cmd:
                parts = cmd.split('"')
                if len(parts) >= 3:
                    tool_path = parts[1]
                    file_name = os.path.basename(tool_path)
                    self.tool_path_label.setText(file_name)
                    self.tool_path_label.setToolTip(tool_path)
                    self.tool_path_label.setProperty("full_path", tool_path)
                    self.tool_param_input.setText(f'"{parts[3].strip()}"')

        # 加载快捷键设置
        hotkey = self.settings_manager.get_value("capture_shortcuts", "alt+c")
        self.hotkey_input.setText(hotkey)

    def save_settings(self):
        """保存设置"""
        # 保存主题设置
        if hasattr(self, 'current_theme_type'):
            self.settings_manager.set_value("current_theme", self.current_theme_type.value)

        # 保存显示设置
        try:
            font_size = int(self.font_size_input.text())
            self.settings_manager.set_value("font_size", font_size)
        except ValueError:
            pass  # 忽略无效的字体大小值

        try:
            opacity = int(self.opacity_input.text())
            if 10 <= opacity <= 100:  # 限制透明度范围
                self.settings_manager.set_value("window_opacity", opacity)
        except ValueError:
            pass  # 忽略无效的透明度值

        # 保存外部工具设置
        cmd = self.check_info_label.text()
        if cmd != "请先选择外部工具":
            self.settings_manager.set_value("external_tool_exec_cmd", cmd)

        # 保存快捷键设置
        self.settings_manager.set_value("capture_shortcuts", self.hotkey_input.text())

        # 同步设置到文件
        self.settings_manager.sync()

    def reset_to_default(self):
        """恢复默认设置"""
        reply = QMessageBox.question(
            self, "确认操作",
            "⚠️ 确定要恢复默认设置吗？这将重置所有设置包括主题配置。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.settings_manager.reset_to_defaults()

            # 重置主题为默认（蓝色）
            self.on_theme_changed(ThemeType.BLUE)

            # 重新加载设置
            self.load_settings()

            QMessageBox.information(self, "完成", "✅ 已恢复默认设置！")

    def accept(self):
        """确认保存设置"""
        self.save_settings()

        # 通知父窗口主题已更改
        if self.parent() and hasattr(self.parent(), 'apply_theme'):
            if hasattr(self, 'current_theme_type'):
                self.parent().apply_theme(self.current_theme_type)

        # 设置快捷键管理器
        if self.parent() and hasattr(self.parent(), 'setup_hotkey_manager'):
            self.parent().setup_hotkey_manager()

        super().accept()
