import os
import subprocess
import logging
from typing import List
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QSystemTrayIcon, QMenu, QMessageBox, QDialog,
)
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QIcon

from core.hotkey_manager import CrossPlatformHotkeyManager
from core.settings_manager import SettingsManager
from ui.capture_tool import CaptureTool
from ui.hover_tool import HoverTool
from ui.theme import default_stylesheet
from ui.settings_dialog import SettingsDialog
from ui.status_label import StatusLabel


class MainWindow(QMainWindow):
    """OCR工具主窗口

    主要功能:
    - 截屏OCR识别
    - 悬停取词
    - 外部工具集成
    - 系统托盘支持
    """

    # 信号定义
    window_hidden = Signal()
    window_shown = Signal()

    def __init__(self):
        super().__init__()
        self.logger = self._setup_logger()
        self.tray_notified = False

        # 初始化核心组件
        self._init_components()

        # 设置界面
        self._setup_ui()

        # 设置功能模块
        self._setup_modules()

        # 延迟初始化状态栏消息
        QTimer.singleShot(1000, self._show_startup_message)

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _init_components(self):
        """初始化核心组件"""
        try:
            self.stylesheet = default_stylesheet
            self.capture_tool = CaptureTool()
            self.hover_tool = HoverTool()
            self.settings_manager = SettingsManager(use_file_storage=True)

            # 获取配置
            self.hotkey = self.settings_manager.get_value("capture_shortcuts", "alt+c")
            self.has_external_tool = bool(
                self.settings_manager.get_value("external_tool_exec_cmd", "")
            )

            self.logger.info("核心组件初始化完成")
        except Exception as e:
            self.logger.error(f"核心组件初始化失败: {e}")
            raise

    def _setup_ui(self):
        """初始化用户界面"""
        # 窗口基本设置
        self._setup_window_properties()

        # 创建主界面
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 添加各个组件
        main_layout.addWidget(self._create_title_bar())
        main_layout.addWidget(self._create_content_area(), 1)
        main_layout.addWidget(self._create_bottom_bar())

        self.setCentralWidget(central_widget)
        self.logger.info("UI界面创建完成")

    def _setup_window_properties(self):
        """设置窗口属性"""
        self.setWindowTitle("OCR 文字识别工具")
        init_w, init_h = 720, 680
        self.setMinimumSize(init_w, init_h)
        self.resize(init_w, init_h)

        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        # 居中显示
        self._center_window()

    def _center_window(self):
        """窗口居中显示"""
        frame_geometry = self.frameGeometry()
        screen_center = QApplication.primaryScreen().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())

    def _setup_modules(self):
        """设置功能模块"""
        self.setup_hotkey_manager()
        self._setup_system_tray()
        self._connect_signals()
        self._update_ui_config()

    def _show_startup_message(self):
        """显示启动消息"""
        self.statusBar().showMessage(f"OCR工具已启动，可使用快捷键 {self.hotkey}")

    def _create_title_bar(self) -> QWidget:
        """创建标题栏"""
        title_widget = QWidget()
        title_widget.setStyleSheet(self.stylesheet.get_title_bar_style())

        layout = QHBoxLayout(title_widget)
        layout.setContentsMargins(24, 8, 24, 8)

        # 左侧：标题和图标
        title_container = self._create_title_container()

        # 右侧：状态和快捷键信息
        info_container = self._create_info_container()

        layout.addWidget(title_container)
        layout.addStretch()
        layout.addWidget(info_container)

        return title_widget

    def _create_title_container(self) -> QWidget:
        """创建标题容器"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 应用图标
        icon_label = QLabel("🔍")
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                color: {self.stylesheet.theme.WHITE};
                background: transparent;
            }}
        """)

        # 标题
        title_label = QLabel("OCR 文字识别工具")
        title_label.setStyleSheet(self.stylesheet.get_title_label_style(18))

        layout.addWidget(icon_label)
        layout.addWidget(title_label)

        return container

    def _create_info_container(self) -> QWidget:
        """创建信息容器"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 快捷键提示
        self.hotkey_label = QLabel(f"快捷键: {self.hotkey}")
        self.hotkey_label.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                color: rgba(255, 255, 255, 0.8);
                background: transparent;
                font-weight: normal;
            }}
        """)

        # 状态指示器
        self.status_label = StatusLabel()

        layout.addWidget(self.hotkey_label)
        layout.addWidget(self.status_label)

        return container

    def _create_content_area(self) -> QWidget:
        """创建内容区域"""
        content_widget = QWidget()
        content_widget.setStyleSheet(self.stylesheet.get_content_background_style())

        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 添加各个面板
        layout.addWidget(self._create_config_info_card())
        layout.addWidget(self._create_action_panel())
        layout.addWidget(self._create_result_panel(), 1)
        layout.addWidget(self._create_tool_integration_panel())

        return content_widget

    def _create_config_info_card(self) -> QWidget:
        """创建配置信息卡片"""
        card = QWidget()
        card.setStyleSheet(self.stylesheet.get_compact_card_style())

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        config_info = self.settings_manager.get_config_info()

        # 主要信息
        main_info = QLabel(f"📁 配置文件: {os.path.basename(config_info['path'])}")
        main_info.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                font-weight: 500;
                color: {self.stylesheet.theme.GRAY_700};
                background: transparent;
            }}
        """)

        # 详细信息
        detail_text = f"版本: {config_info['version']}"
        if config_info.get('size'):
            detail_text += f" | 大小: {config_info['size']} bytes"

        detail_info = QLabel(detail_text)
        detail_info.setStyleSheet(self.stylesheet.get_info_label_style())
        detail_info.setWordWrap(True)

        layout.addWidget(main_info)
        layout.addWidget(detail_info)

        return card

    def _create_action_panel(self) -> QWidget:
        """创建操作面板"""
        panel = QWidget()
        panel.setStyleSheet(self.stylesheet.get_card_style())

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # 面板标题
        title = QLabel("🎯 功能操作")
        title.setStyleSheet(self.stylesheet.get_section_title_style(14))

        # 创建按钮
        button_container = self._create_action_buttons()

        layout.addWidget(title)
        layout.addWidget(button_container)

        return panel

    def _create_action_buttons(self) -> QWidget:
        """创建操作按钮"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setSpacing(10)

        # 截屏识别按钮
        self.screenshot_btn = QPushButton("📷 截屏识别")
        self.screenshot_btn.setStyleSheet(self.stylesheet.get_primary_button_style())
        self.screenshot_btn.clicked.connect(self.start_screenshot)

        # 悬停取词按钮
        self.hover_btn = QPushButton("🖱️ 悬停取词")
        self.hover_btn.setCheckable(True)
        self.hover_btn.setStyleSheet(self.stylesheet.get_secondary_button_style())
        self.hover_btn.clicked.connect(self.toggle_hover_mode)

        # 设置按钮
        self.settings_button = QPushButton("⚙️ 设置")
        self.settings_button.setStyleSheet(self.stylesheet.get_secondary_button_style())
        self.settings_button.clicked.connect(self.open_settings)

        layout.addWidget(self.screenshot_btn, 2)
        layout.addWidget(self.hover_btn, 1)
        layout.addWidget(self.settings_button, 1)

        return container

    def _create_result_panel(self) -> QWidget:
        """创建结果显示面板"""
        panel = QWidget()
        panel.setStyleSheet(self.stylesheet.get_card_style())
        panel.setMaximumHeight(120)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # 头部（标题和操作按钮）
        header = self._create_result_header()

        # 结果输入框
        self.result_text = QLineEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet(self.stylesheet.get_line_edit_style())
        self.result_text.setPlaceholderText("识别结果将显示在这里...")
        self.result_text.setFixedHeight(36)

        layout.addWidget(header)
        layout.addWidget(self.result_text)

        return panel

    def _create_result_header(self) -> QWidget:
        """创建结果面板头部"""
        header = QWidget()

        # 移除QWidget的所有默认样式
        header.setStyleSheet("""
            QWidget {
                border: none;
                margin: 0;
                padding: 0;
                background: transparent;
            }
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 标题
        title = QLabel("📝 识别结果")
        # 确保标题样式不包含边框
        base_style = self.stylesheet.get_section_title_style(14)
        title_style = f"{base_style}; border: none; margin: 0;"
        title.setStyleSheet(title_style)

        # 操作按钮
        button_container = self._create_result_buttons()
        # 也检查按钮容器的样式
        if hasattr(button_container, 'setStyleSheet'):
            button_container.setStyleSheet("border: none; margin: 0; padding: 0;")

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(button_container)

        return header

    def _create_result_buttons(self) -> QWidget:
        """创建结果操作按钮"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 复制按钮
        self.copy_btn = QPushButton("📋 复制")
        self.copy_btn.setStyleSheet(self.stylesheet.get_small_button_style())
        self.copy_btn.clicked.connect(self.copy_result)

        # 清空按钮
        self.clear_btn = QPushButton("🗑️ 清空")
        self.clear_btn.setStyleSheet(self.stylesheet.get_small_button_style())
        self.clear_btn.clicked.connect(self.clear_result)

        layout.addWidget(self.copy_btn)
        layout.addWidget(self.clear_btn)

        return container

    def _create_tool_integration_panel(self) -> QWidget:
        """创建外部工具集成面板"""
        panel = QWidget()
        panel.setStyleSheet(self.stylesheet.get_compact_card_style())

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # 标题
        title = QLabel("🔧 外部工具集成")
        title.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: 600;
                color: {self.stylesheet.theme.GRAY_700};
                background: transparent;
            }}
        """)

        # 工具命令显示
        self.tool_cmd = QLabel()
        self._update_tool_cmd_display()

        layout.addWidget(title)
        layout.addWidget(self.tool_cmd)

        return panel

    def _create_bottom_bar(self) -> QWidget:
        """创建底部工具栏"""
        toolbar = QWidget()
        toolbar.setStyleSheet(self.stylesheet.get_bottom_toolbar_style())

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(20, 8, 20, 8)

        # 版本信息
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet(self.stylesheet.get_version_label_style())

        # 最小化按钮
        minimize_btn = QPushButton("📥 最小化到托盘")
        minimize_btn.setStyleSheet(self.stylesheet.get_small_button_style())
        minimize_btn.clicked.connect(self.hide_window)

        layout.addWidget(version_label)
        layout.addStretch()
        layout.addWidget(minimize_btn)

        return toolbar

    def _update_tool_cmd_display(self):
        """更新外部工具命令显示"""
        cmd = self.settings_manager.get_value("external_tool_exec_cmd", "")
        self.tool_cmd.setWordWrap(True)

        if not cmd:
            self.tool_cmd.setText("⚠️ 在设置中配置外部工具后再使用OCR功能")
            self.tool_cmd.setStyleSheet(f"""
                QLabel {{
                    color: {self.stylesheet.theme.WARNING};
                    font-size: 11px;
                    background: transparent;
                    padding: 4px 8px;
                    border: 1px dashed {self.stylesheet.theme.WARNING};
                    border-radius: 4px;
                }}
            """)
        else:
            self.tool_cmd.setText(f"✅ {cmd}")
            self.tool_cmd.setStyleSheet(f"""
                QLabel {{
                    color: {self.stylesheet.theme.SUCCESS};
                    font-size: 11px;
                    background: rgba(40, 167, 69, 0.1);
                    padding: 4px 8px;
                    border: 1px solid rgba(40, 167, 69, 0.3);
                    border-radius: 4px;
                }}
            """)

    def setup_hotkey_manager(self):
        """设置全局热键管理器"""
        try:
            if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
                self.hotkey_manager.stop()

            self.hotkey_manager = CrossPlatformHotkeyManager(self.hotkey)
            self.hotkey_manager.hotkey_activated.connect(self.start_screenshot)
            self.hotkey_manager.mouse_clicked.connect(self.start_hover)
            self.hotkey_manager.start()

            self.logger.info(f"热键管理器已启动，快捷键: {self.hotkey}")
        except Exception as e:
            self.logger.error(f"热键管理器设置失败: {e}")

    def _setup_system_tray(self):
        """设置系统托盘图标"""
        try:
            self.tray_icon = QSystemTrayIcon(self)

            # 设置图标
            self._setup_tray_icon()

            # 设置菜单
            self._setup_tray_menu()

            # 连接信号
            self.tray_icon.activated.connect(self._on_tray_activated)
            self.tray_icon.show()

            self.logger.info("系统托盘设置完成")
        except Exception as e:
            self.logger.error(f"系统托盘设置失败: {e}")

    def _setup_tray_icon(self):
        """设置托盘图标"""
        icon_path = os.path.join("_internal", "ocr.png")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.logger.warning(f"图标文件未找到: {icon_path}")
            self.tray_icon.setIcon(QIcon.fromTheme("edit-find"))

        self.tray_icon.setToolTip("OCR小工具")

    def _setup_tray_menu(self):
        """设置托盘菜单"""
        tray_menu = QMenu()

        # 创建菜单项
        actions = [
            ("显示", self.show),
            ("截图OCR", self.start_screenshot),
            ("悬停取词", lambda: self.hover_tool.capture_at_cursor()),
            None,  # 分隔符
            ("退出", self.quit_application)
        ]

        for action_data in actions:
            if action_data is None:
                tray_menu.addSeparator()
            else:
                name, callback = action_data
                action = tray_menu.addAction(name)
                action.triggered.connect(callback)

        self.tray_icon.setContextMenu(tray_menu)

    def _connect_signals(self):
        """连接组件信号"""
        try:
            self.capture_tool.capture_completed.connect(self.update_ocr_result)
            self.hover_tool.word_found.connect(self.update_hover_result)
            self.hover_tool.status_changed.connect(self._update_status)
            self.logger.info("信号连接完成")
        except Exception as e:
            self.logger.error(f"信号连接失败: {e}")

    def _update_ui_config(self):
        """更新UI配置"""
        try:
            # 更新快捷键显示
            new_hotkey = self.settings_manager.get_value("capture_shortcuts", "alt+c")
            self.hotkey = new_hotkey
            self.hotkey_label.setText(f"快捷键: {new_hotkey}")
            self.screenshot_btn.setText(f'📷 截屏识别 ({new_hotkey})')

            # 更新外部工具状态
            cmd = self.settings_manager.get_value("external_tool_exec_cmd", "")
            self.has_external_tool = bool(cmd)
            self._update_tool_cmd_display()

            self.logger.info("UI配置更新完成")
        except Exception as e:
            self.logger.error(f"UI配置更新失败: {e}")

    def _update_status(self, status_text: str):
        """更新状态信息"""
        self.status_label.update_status(status_text)

    def _on_tray_activated(self, reason):
        """系统托盘图标激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.activateWindow()

    def _validate_external_tool(self) -> bool:
        """验证外部工具是否配置"""
        if not self.has_external_tool:
            QMessageBox.warning(self, "警告", "请先在设置中配置外部工具命令")
            return False
        return True

    # 公共方法
    def open_settings(self):
        """打开设置对话框"""
        try:
            dialog = SettingsDialog(self.settings_manager, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._update_ui_config()
                self.setup_hotkey_manager()  # 重新设置热键
                QMessageBox.information(self, "成功", "设置已保存并应用！")
                self.logger.info("设置已更新")
        except Exception as e:
            self.logger.error(f"打开设置对话框失败: {e}")
            QMessageBox.critical(self, "错误", f"打开设置失败: {str(e)}")

    def start_screenshot(self):
        """启动截图OCR功能"""
        if not self._validate_external_tool():
            return

        try:
            self.hide()
            self._update_status("请选择截图区域")
            QTimer.singleShot(300, self.capture_tool.start_capture)
            self.logger.info("启动截图OCR")
        except Exception as e:
            self.logger.error(f"启动截图OCR失败: {e}")
            self._update_status("启动截图失败")

    def start_hover(self):
        """启动悬停取词功能"""
        if not self._validate_external_tool():
            return

        try:
            self.hover_tool.capture_at_cursor()
            self.logger.info("启动悬停取词")
        except Exception as e:
            self.logger.error(f"启动悬停取词失败: {e}")

    def toggle_hover_mode(self, checked: bool):
        """切换悬停取词模式"""
        try:
            if checked:
                self._update_status("悬停取词已启用")
                self.statusBar().showMessage("悬停取词模式已启用，按Alt+鼠标左键进行取词")
            else:
                self._update_status("就绪")
                self.statusBar().showMessage("悬停取词模式已禁用")

            self.logger.info(f"悬停取词模式: {'启用' if checked else '禁用'}")
        except Exception as e:
            self.logger.error(f"切换悬停取词模式失败: {e}")

    def update_ocr_result(self, text_list: List[str]):
        """更新OCR结果"""
        try:
            if not text_list:
                self._update_status("未识别到文本")
                self.result_text.setText("未能识别到任何文本")
                return

            # 更新结果
            result_text = '\n'.join(text_list)
            self.result_text.setText(result_text)
            self._update_status("识别完成")

            # 运行外部工具
            if self.has_external_tool:
                self._run_external_tool()

            self.logger.info(f"OCR识别完成，识别到 {len(text_list)} 行文本")
        except Exception as e:
            self.logger.error(f"更新OCR结果失败: {e}")
            self._update_status("结果更新失败")

    def update_hover_result(self, word: str):
        """更新悬停取词结果"""
        try:
            self.result_text.setText(word)

            # 运行外部工具
            if self.has_external_tool:
                self._run_external_tool()

            self.logger.info(f"悬停取词完成: {word}")
        except Exception as e:
            self.logger.error(f"更新悬停取词结果失败: {e}")

    def copy_result(self):
        """复制结果到剪贴板"""
        try:
            text = self.result_text.text()
            if text:
                clipboard = QApplication.clipboard()
                clipboard.setText(text)
                self.statusBar().showMessage("结果已复制到剪贴板", 2000)
                self.logger.info("结果已复制到剪贴板")
            else:
                self.statusBar().showMessage("没有可复制的内容", 2000)
        except Exception as e:
            self.logger.error(f"复制结果失败: {e}")
            self.statusBar().showMessage("复制失败", 2000)

    def clear_result(self):
        """清空结果"""
        try:
            self.result_text.clear()
            self.statusBar().showMessage("结果已清空", 2000)
            self.logger.info("结果已清空")
        except Exception as e:
            self.logger.error(f"清空结果失败: {e}")

    def _run_external_tool(self) -> bool:
        """运行外部工具处理OCR结果"""
        try:
            text = self.result_text.text()
            cmd = self.settings_manager.get_value("external_tool_exec_cmd", "")

            if not cmd or not text:
                return False

            # 替换文本占位符
            formatted_cmd = cmd.replace("{text}", text)

            # 执行命令
            subprocess.Popen(formatted_cmd, shell=True)
            self.statusBar().showMessage(f"已执行命令: {formatted_cmd}", 3000)
            self.logger.info(f"外部工具执行成功: {formatted_cmd}")
            return True

        except Exception as e:
            error_msg = f"执行命令失败: {str(e)}"
            self.statusBar().showMessage(error_msg, 3000)
            self.logger.error(f"外部工具执行失败: {e}")
            return False

    def hide_window(self):
        """隐藏窗口到系统托盘"""
        try:
            if not self.tray_notified:
                self.tray_icon.showMessage(
                    "OCR小工具",
                    f"程序已最小化到托盘，可通过热键 {self.hotkey} 继续使用",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
                self.tray_notified = True

            self.hide()
            self.window_hidden.emit()
            self.logger.info("窗口已隐藏到托盘")
        except Exception as e:
            self.logger.error(f"隐藏窗口失败: {e}")

    def show(self):
        """显示窗口"""
        try:
            super().show()
            self.activateWindow()
            self.raise_()
            self.window_shown.emit()
            self.logger.info("窗口已显示")
        except Exception as e:
            self.logger.error(f"显示窗口失败: {e}")

    def quit_application(self):
        """安全退出应用程序"""
        try:
            self.logger.info("开始退出应用程序")
            self.tray_notified = True

            # 清理资源
            self._cleanup_resources()

            # 退出应用
            QApplication.quit()
            self.logger.info("应用程序已安全退出")
        except Exception as e:
            self.logger.error(f"退出应用程序时出错: {e}")
            # 强制退出
            QApplication.quit()

    def _cleanup_resources(self):
        """清理应用资源"""
        try:
            # 停止热键管理器
            if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
                self.hotkey_manager.stop()
                self.logger.info("热键管理器已停止")

            # 隐藏托盘图标
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.hide()
                self.logger.info("托盘图标已隐藏")

            # 清理其他资源
            if hasattr(self, 'capture_tool') and self.capture_tool:
                # 如果capture_tool有cleanup方法
                if hasattr(self.capture_tool, 'cleanup'):
                    self.capture_tool.cleanup()

            if hasattr(self, 'hover_tool') and self.hover_tool:
                # 如果hover_tool有cleanup方法
                if hasattr(self.hover_tool, 'cleanup'):
                    self.hover_tool.cleanup()

        except Exception as e:
            self.logger.error(f"清理资源时出错: {e}")

    # 事件处理方法
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        try:
            # 阻止直接关闭，改为隐藏到托盘
            event.ignore()
            self.hide_window()
        except Exception as e:
            self.logger.error(f"处理关闭事件失败: {e}")
            event.accept()  # 如果出错，允许正常关闭

    def changeEvent(self, event):
        """窗口状态改变事件处理"""
        try:
            if event.type() == event.Type.WindowStateChange:
                # 如果窗口被最小化，隐藏到托盘
                if self.isMinimized():
                    QTimer.singleShot(100, self.hide_window)
                    event.ignore()
                    return

            super().changeEvent(event)
        except Exception as e:
            self.logger.error(f"处理窗口状态改变事件失败: {e}")
            super().changeEvent(event)

    def keyPressEvent(self, event):
        """键盘按键事件处理"""
        try:
            # ESC键隐藏窗口
            if event.key() == Qt.Key.Key_Escape:
                self.hide_window()
                event.accept()
                return

            super().keyPressEvent(event)
        except Exception as e:
            self.logger.error(f"处理按键事件失败: {e}")
            super().keyPressEvent(event)
