import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                               QListWidget, QStackedWidget, QFormLayout, QLabel,
                               QPushButton, QComboBox, QCheckBox, QSpinBox,
                               QSlider, QColorDialog, QFileDialog, QGroupBox,
                               QMessageBox, QSplitter)
from PySide6.QtCore import Qt


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.settings_data = {}  # 存储所有设置
        self.default_settings = {}  # 存储默认设置
        self.initUI()
        self.load_default_settings()

    def initUI(self):
        # 主布局
        main_layout = QVBoxLayout()

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧分类列表
        self.category_list = QListWidget()
        self.category_list.setFixedWidth(200)
        self.category_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                background-color: #f8f9fa;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #e9ecef;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e9ecef;
            }
        """)

        # 添加分类项目
        categories = ["界面设置", "主题设置", "系统设置", "文件设置", "高级设置"]
        self.category_list.addItems(categories)
        self.category_list.currentRowChanged.connect(self.on_category_changed)

        # 右侧设置内容区域
        self.settings_stack = QStackedWidget()

        # 创建各个设置页面
        self.create_ui_settings_page()
        self.create_theme_settings_page()
        self.create_system_settings_page()
        self.create_file_settings_page()
        self.create_advanced_settings_page()

        # 将左右两部分添加到分割器
        splitter.addWidget(self.category_list)
        splitter.addWidget(self.settings_stack)
        splitter.setStretchFactor(1, 1)  # 右侧可拉伸

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
        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn.clicked.connect(self.cancel_settings)
        self.reset_btn.clicked.connect(self.reset_to_default)

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.reset_btn)

        # 组装主布局
        main_layout.addWidget(splitter)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.setWindowTitle("应用程序设置")
        self.setGeometry(200, 200, 800, 600)

        # 默认选择第一个分类
        self.category_list.setCurrentRow(0)

    def create_ui_settings_page(self):
        """创建界面设置页面"""
        page = QWidget()
        layout = QVBoxLayout()

        # 基础界面设置
        basic_group = QGroupBox("基础界面设置")
        basic_layout = QFormLayout()

        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文", "English", "繁體中文", "日本語"])
        basic_layout.addRow("界面语言:", self.language_combo)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(12)
        basic_layout.addRow("字体大小:", self.font_size_spin)

        self.window_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.window_opacity_slider.setRange(50, 100)
        self.window_opacity_slider.setValue(100)
        self.opacity_label = QLabel("100%")
        self.window_opacity_slider.valueChanged.connect(lambda v: self.opacity_label.setText(f"{v}%"))
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(self.window_opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        basic_layout.addRow("窗口透明度:", opacity_layout)

        self.always_on_top_check = QCheckBox("窗口置顶")
        basic_layout.addRow("窗口行为:", self.always_on_top_check)

        basic_group.setLayout(basic_layout)

        # 布局设置
        layout_group = QGroupBox("布局设置")
        layout_layout = QFormLayout()

        self.toolbar_visible_check = QCheckBox("显示工具栏")
        self.toolbar_visible_check.setChecked(True)
        layout_layout.addRow("工具栏:", self.toolbar_visible_check)

        self.statusbar_visible_check = QCheckBox("显示状态栏")
        self.statusbar_visible_check.setChecked(True)
        layout_layout.addRow("状态栏:", self.statusbar_visible_check)

        layout_group.setLayout(layout_layout)

        layout.addWidget(basic_group)
        layout.addWidget(layout_group)
        layout.addStretch()

        page.setLayout(layout)
        self.settings_stack.addWidget(page)

    def create_theme_settings_page(self):
        """创建主题设置页面"""
        page = QWidget()
        layout = QVBoxLayout()

        # 主题选择
        theme_group = QGroupBox("主题选择")
        theme_layout = QFormLayout()

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色主题", "深色主题", "系统跟随", "自定义"])
        theme_layout.addRow("主题模式:", self.theme_combo)

        # 颜色设置
        self.primary_color_btn = QPushButton("选择主色调")
        self.primary_color_btn.setStyleSheet("background-color: #007bff; color: white;")
        self.primary_color_btn.clicked.connect(lambda: self.choose_color(self.primary_color_btn))
        theme_layout.addRow("主色调:", self.primary_color_btn)

        self.accent_color_btn = QPushButton("选择强调色")
        self.accent_color_btn.setStyleSheet("background-color: #28a745; color: white;")
        self.accent_color_btn.clicked.connect(lambda: self.choose_color(self.accent_color_btn))
        theme_layout.addRow("强调色:", self.accent_color_btn)

        theme_group.setLayout(theme_layout)

        # 字体设置
        font_group = QGroupBox("字体设置")
        font_layout = QFormLayout()

        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems(["Microsoft YaHei", "SimSun", "Arial", "Times New Roman"])
        font_layout.addRow("字体族:", self.font_family_combo)

        self.ui_font_size_spin = QSpinBox()
        self.ui_font_size_spin.setRange(8, 18)
        self.ui_font_size_spin.setValue(9)
        font_layout.addRow("界面字体大小:", self.ui_font_size_spin)

        font_group.setLayout(font_layout)

        layout.addWidget(theme_group)
        layout.addWidget(font_group)
        layout.addStretch()

        page.setLayout(layout)
        self.settings_stack.addWidget(page)

    def create_system_settings_page(self):
        """创建系统设置页面"""
        page = QWidget()
        layout = QVBoxLayout()

        # 启动设置
        startup_group = QGroupBox("启动设置")
        startup_layout = QFormLayout()

        self.auto_start_check = QCheckBox("开机自启动")
        startup_layout.addRow("启动行为:", self.auto_start_check)

        self.minimize_to_tray_check = QCheckBox("最小化到系统托盘")
        startup_layout.addRow("最小化行为:", self.minimize_to_tray_check)

        self.remember_window_check = QCheckBox("记住窗口位置和大小")
        self.remember_window_check.setChecked(True)
        startup_layout.addRow("窗口状态:", self.remember_window_check)

        startup_group.setLayout(startup_layout)

        # 性能设置
        performance_group = QGroupBox("性能设置")
        performance_layout = QFormLayout()

        self.hardware_acceleration_check = QCheckBox("启用硬件加速")
        self.hardware_acceleration_check.setChecked(True)
        performance_layout.addRow("图形渲染:", self.hardware_acceleration_check)

        self.animation_check = QCheckBox("启用动画效果")
        self.animation_check.setChecked(True)
        performance_layout.addRow("动画效果:", self.animation_check)

        performance_group.setLayout(performance_layout)

        layout.addWidget(startup_group)
        layout.addWidget(performance_group)
        layout.addStretch()

        page.setLayout(layout)
        self.settings_stack.addWidget(page)

    def create_file_settings_page(self):
        """创建文件设置页面"""
        page = QWidget()
        layout = QVBoxLayout()

        # 默认路径设置
        path_group = QGroupBox("默认路径设置")
        path_layout = QFormLayout()

        # 默认下载路径
        self.download_path_label = QLabel("未设置")
        self.download_path_btn = QPushButton("选择下载路径")
        self.download_path_btn.clicked.connect(lambda: self.choose_folder(self.download_path_label))
        path_layout.addRow("下载路径:", self.download_path_btn)
        path_layout.addRow("", self.download_path_label)

        # 默认保存路径
        self.save_path_label = QLabel("未设置")
        self.save_path_btn = QPushButton("选择保存路径")
        self.save_path_btn.clicked.connect(lambda: self.choose_folder(self.save_path_label))
        path_layout.addRow("保存路径:", self.save_path_btn)
        path_layout.addRow("", self.save_path_label)

        path_group.setLayout(path_layout)

        # 文件处理设置
        file_group = QGroupBox("文件处理设置")
        file_layout = QFormLayout()

        self.auto_backup_check = QCheckBox("自动备份文件")
        file_layout.addRow("备份选项:", self.auto_backup_check)

        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setRange(1, 60)
        self.backup_interval_spin.setValue(10)
        self.backup_interval_spin.setSuffix(" 分钟")
        file_layout.addRow("备份间隔:", self.backup_interval_spin)

        self.max_backup_files_spin = QSpinBox()
        self.max_backup_files_spin.setRange(1, 100)
        self.max_backup_files_spin.setValue(5)
        file_layout.addRow("最大备份数:", self.max_backup_files_spin)

        file_group.setLayout(file_layout)

        layout.addWidget(path_group)
        layout.addWidget(file_group)
        layout.addStretch()

        page.setLayout(layout)
        self.settings_stack.addWidget(page)

    def create_advanced_settings_page(self):
        """创建高级设置页面"""
        page = QWidget()
        layout = QVBoxLayout()

        # 调试设置
        debug_group = QGroupBox("调试设置")
        debug_layout = QFormLayout()

        self.debug_mode_check = QCheckBox("启用调试模式")
        debug_layout.addRow("调试选项:", self.debug_mode_check)

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["ERROR", "WARNING", "INFO", "DEBUG"])
        self.log_level_combo.setCurrentText("INFO")
        debug_layout.addRow("日志级别:", self.log_level_combo)

        debug_group.setLayout(debug_layout)

        # 实验性功能
        experimental_group = QGroupBox("实验性功能")
        experimental_layout = QFormLayout()

        self.beta_features_check = QCheckBox("启用测试功能")
        experimental_layout.addRow("测试功能:", self.beta_features_check)

        self.plugin_support_check = QCheckBox("启用插件支持")
        experimental_layout.addRow("插件系统:", self.plugin_support_check)

        experimental_group.setLayout(experimental_layout)

        # 配置导入导出
        config_group = QGroupBox("配置管理")
        config_layout = QVBoxLayout()

        config_buttons_layout = QHBoxLayout()
        self.export_config_btn = QPushButton("导出配置")
        self.import_config_btn = QPushButton("导入配置")
        self.export_config_btn.clicked.connect(self.export_config)
        self.import_config_btn.clicked.connect(self.import_config)

        config_buttons_layout.addWidget(self.export_config_btn)
        config_buttons_layout.addWidget(self.import_config_btn)
        config_buttons_layout.addStretch()

        config_layout.addLayout(config_buttons_layout)
        config_group.setLayout(config_layout)

        layout.addWidget(debug_group)
        layout.addWidget(experimental_group)
        layout.addWidget(config_group)
        layout.addStretch()

        page.setLayout(layout)
        self.settings_stack.addWidget(page)

    def on_category_changed(self, index):
        """分类选择改变时的处理"""
        self.settings_stack.setCurrentIndex(index)

    def choose_color(self, button):
        """选择颜色"""
        color = QColorDialog.getColor(Qt.GlobalColor.blue, self)
        if color.isValid():
            button.setStyleSheet(f"background-color: {color.name()}; color: white;")

    def choose_folder(self, label):
        """选择文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            label.setText(folder)
            label.setToolTip(folder)

    def load_default_settings(self):
        """加载默认设置"""
        self.default_settings = {
            # 界面设置
            'language': 0,
            'font_size': 12,
            'window_opacity': 100,
            'always_on_top': False,
            'toolbar_visible': True,
            'statusbar_visible': True,

            # 主题设置
            'theme_mode': 0,
            'font_family': 0,
            'ui_font_size': 9,

            # 系统设置
            'auto_start': False,
            'minimize_to_tray': False,
            'remember_window': True,
            'hardware_acceleration': True,
            'animation': True,

            # 文件设置
            'auto_backup': False,
            'backup_interval': 10,
            'max_backup_files': 5,

            # 高级设置
            'debug_mode': False,
            'log_level': 2,  # INFO
            'beta_features': False,
            'plugin_support': False,
        }

        # 应用默认设置
        self.apply_settings(self.default_settings)

    def get_current_settings(self):
        """获取当前设置"""
        return {
            # 界面设置
            'language': self.language_combo.currentIndex(),
            'font_size': self.font_size_spin.value(),
            'window_opacity': self.window_opacity_slider.value(),
            'always_on_top': self.always_on_top_check.isChecked(),
            'toolbar_visible': self.toolbar_visible_check.isChecked(),
            'statusbar_visible': self.statusbar_visible_check.isChecked(),

            # 主题设置
            'theme_mode': self.theme_combo.currentIndex(),
            'font_family': self.font_family_combo.currentIndex(),
            'ui_font_size': self.ui_font_size_spin.value(),

            # 系统设置
            'auto_start': self.auto_start_check.isChecked(),
            'minimize_to_tray': self.minimize_to_tray_check.isChecked(),
            'remember_window': self.remember_window_check.isChecked(),
            'hardware_acceleration': self.hardware_acceleration_check.isChecked(),
            'animation': self.animation_check.isChecked(),

            # 文件设置
            'auto_backup': self.auto_backup_check.isChecked(),
            'backup_interval': self.backup_interval_spin.value(),
            'max_backup_files': self.max_backup_files_spin.value(),

            # 高级设置
            'debug_mode': self.debug_mode_check.isChecked(),
            'log_level': self.log_level_combo.currentIndex(),
            'beta_features': self.beta_features_check.isChecked(),
            'plugin_support': self.plugin_support_check.isChecked(),
        }

    def apply_settings(self, settings):
        """应用设置到界面"""
        # 界面设置
        self.language_combo.setCurrentIndex(settings.get('language', 0))
        self.font_size_spin.setValue(settings.get('font_size', 12))
        self.window_opacity_slider.setValue(settings.get('window_opacity', 100))
        self.always_on_top_check.setChecked(settings.get('always_on_top', False))
        self.toolbar_visible_check.setChecked(settings.get('toolbar_visible', True))
        self.statusbar_visible_check.setChecked(settings.get('statusbar_visible', True))

        # 主题设置
        self.theme_combo.setCurrentIndex(settings.get('theme_mode', 0))
        self.font_family_combo.setCurrentIndex(settings.get('font_family', 0))
        self.ui_font_size_spin.setValue(settings.get('ui_font_size', 9))

        # 系统设置
        self.auto_start_check.setChecked(settings.get('auto_start', False))
        self.minimize_to_tray_check.setChecked(settings.get('minimize_to_tray', False))
        self.remember_window_check.setChecked(settings.get('remember_window', True))
        self.hardware_acceleration_check.setChecked(settings.get('hardware_acceleration', True))
        self.animation_check.setChecked(settings.get('animation', True))

        # 文件设置
        self.auto_backup_check.setChecked(settings.get('auto_backup', False))
        self.backup_interval_spin.setValue(settings.get('backup_interval', 10))
        self.max_backup_files_spin.setValue(settings.get('max_backup_files', 5))

        # 高级设置
        self.debug_mode_check.setChecked(settings.get('debug_mode', False))
        self.log_level_combo.setCurrentIndex(settings.get('log_level', 2))
        self.beta_features_check.setChecked(settings.get('beta_features', False))
        self.plugin_support_check.setChecked(settings.get('plugin_support', False))

    def save_settings(self):
        """保存设置"""
        self.settings_data = self.get_current_settings()
        QMessageBox.information(self, "设置", "设置已保存！")
        print("保存的设置:", self.settings_data)

    def cancel_settings(self):
        """取消设置"""
        if self.settings_data:
            self.apply_settings(self.settings_data)
        else:
            self.apply_settings(self.default_settings)
        QMessageBox.information(self, "设置", "已取消更改！")

    def reset_to_default(self):
        """恢复默认设置"""
        reply = QMessageBox.question(self, "确认", "确定要恢复到默认设置吗？这将丢失所有自定义设置。",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.apply_settings(self.default_settings)
            QMessageBox.information(self, "设置", "已恢复到默认设置！")

    def export_config(self):
        """导出配置"""
        file_path, _ = QFileDialog.getSaveFileName(self, "导出配置", "config.txt", "文本文件 (*.txt)")
        if file_path:
            try:
                current_settings = self.get_current_settings()
                with open(file_path, 'w', encoding='utf-8') as f:
                    for key, value in current_settings.items():
                        f.write(f"{key}={value}\n")
                QMessageBox.information(self, "导出", f"配置已导出到: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"导出失败: {str(e)}")

    def import_config(self):
        """导入配置"""
        file_path, _ = QFileDialog.getOpenFileName(self, "导入配置", "", "文本文件 (*.txt)")
        if file_path:
            try:
                settings = {}
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line:
                            key, value = line.split('=', 1)
                            # 简单的类型转换
                            if value.lower() in ['true', 'false']:
                                settings[key] = value.lower() == 'true'
                            elif value.isdigit():
                                settings[key] = int(value)
                            else:
                                settings[key] = value

                self.apply_settings(settings)
                QMessageBox.information(self, "导入", "配置导入成功！")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"导入失败: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    settings_window = SettingsPage()
    settings_window.show()

    sys.exit(app.exec())