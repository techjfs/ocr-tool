"""
样式主题管理器
统一管理应用程序的所有样式和主题色彩
"""


class Theme:
    """主题色彩配置"""

    def __init__(self):
        # 主题色配置
        self.PRIMARY = "#4A90E2"
        self.PRIMARY_DARK = "#357ABD"
        self.PRIMARY_DARKER = "#2E5BA8"
        self.PRIMARY_LIGHT = "#5BA0F2"
        self.PRIMARY_LIGHTER = "#E8F4FD"

        # 辅助色
        self.SECONDARY = "#6C757D"
        self.SUCCESS = "#28A745"
        self.WARNING = "#FFC107"
        self.DANGER = "#DC3545"
        self.INFO = "#17A2B8"

        # 中性色
        self.WHITE = "#FFFFFF"
        self.LIGHT_GRAY = "#F8F9FA"
        self.GRAY_100 = "#F8F9FA"
        self.GRAY_200 = "#E9ECEF"
        self.GRAY_300 = "#DEE2E6"
        self.GRAY_400 = "#CED4DA"
        self.GRAY_500 = "#ADB5BD"
        self.GRAY_600 = "#6C757D"
        self.GRAY_700 = "#495057"
        self.GRAY_800 = "#343A40"
        self.GRAY_900 = "#212529"

        # 边框色
        self.BORDER_COLOR = "#E3E8ED"
        self.BORDER_HOVER = "#ADB5BD"

        # 背景色
        self.BACKGROUND = "#F8F9FA"
        self.CARD_BACKGROUND = "#FFFFFF"
        self.INPUT_BACKGROUND = "#FAFBFC"


class StyleSheet:
    """样式表管理器"""

    def __init__(self, theme: Theme = None):
        self.theme = theme or Theme()

    def get_gradient_background(self, start_color: str, end_color: str) -> str:
        """获取渐变背景样式"""
        return f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                       stop:0 {start_color}, stop:1 {end_color});
        """

    def get_vertical_gradient_background(self, start_color: str, end_color: str) -> str:
        """获取垂直渐变背景样式"""
        return f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                       stop:0 {start_color}, stop:1 {end_color});
        """

    # 通用组件样式
    def get_title_bar_style(self) -> str:
        """标题栏样式"""
        return f"""
            QWidget {{
                {self.get_gradient_background(self.theme.PRIMARY, self.theme.PRIMARY_DARK)}
                color: {self.theme.WHITE};
                border-bottom: 2px solid {self.theme.PRIMARY_DARKER};
            }}
        """

    def get_title_label_style(self, font_size: int = 16) -> str:
        """标题标签样式"""
        return f"""
            QLabel {{
                font-size: {font_size}px;
                font-weight: bold;
                color: {self.theme.WHITE};
                background: transparent;
                border: none;
            }}
        """

    def get_status_label_style(self) -> str:
        """状态标签样式"""
        return f"""
            QLabel {{
                font-size: 12px;
                color: {self.theme.PRIMARY_LIGHTER};
                background: rgba(255, 255, 255, 0.2);
                padding: 4px 12px;
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
        """

    def get_card_style(self) -> str:
        """卡片样式"""
        return f"""
            QWidget {{
                background-color: {self.theme.CARD_BACKGROUND};
                border: 1px solid {self.theme.BORDER_COLOR};
                border-radius: 8px;
            }}
        """

    def get_content_background_style(self) -> str:
        """内容区域背景样式"""
        return f"""
            QWidget {{
                background-color: {self.theme.BACKGROUND};
            }}
        """

    # 按钮样式
    def get_primary_button_style(self) -> str:
        """主要按钮样式"""
        return f"""
            QPushButton {{
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 500;
                border-radius: 6px;
                border: 2px solid transparent;
                {self.get_vertical_gradient_background(self.theme.PRIMARY, self.theme.PRIMARY_DARK)}
                color: {self.theme.WHITE};
            }}
            QPushButton:hover {{
                {self.get_vertical_gradient_background(self.theme.PRIMARY_LIGHT, self.theme.PRIMARY)}
            }}
            QPushButton:pressed {{
                {self.get_vertical_gradient_background(self.theme.PRIMARY_DARK, self.theme.PRIMARY_DARKER)}
            }}
            QPushButton:focus {{
                outline: none;
            }}
        """

    def get_secondary_button_style(self) -> str:
        """次要按钮样式"""
        return f"""
            QPushButton {{
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 500;
                border-radius: 6px;
                background-color: {self.theme.WHITE};
                color: {self.theme.GRAY_700};
                border: 2px solid {self.theme.GRAY_400};
            }}
            QPushButton:hover {{
                background-color: {self.theme.GRAY_100};
                border-color: {self.theme.PRIMARY};
                color: {self.theme.PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {self.theme.GRAY_200};
            }}
            QPushButton:checked {{
                {self.get_vertical_gradient_background(self.theme.PRIMARY, self.theme.PRIMARY_DARK)}
                color: {self.theme.WHITE};
                border-color: {self.theme.PRIMARY_DARK};
            }}
            QPushButton:focus {{
                outline: none;
            }}
        """

    def get_small_button_style(self) -> str:
        """小按钮样式"""
        return f"""
            QPushButton {{
                padding: 8px 16px;
                font-size: 12px;
                border-radius: 4px;
                background-color: transparent;
                color: {self.theme.GRAY_600};
                border: 1px solid transparent;
            }}
            QPushButton:hover {{
                background-color: {self.theme.GRAY_200};
                color: {self.theme.GRAY_700};
            }}
            QPushButton:pressed {{
                background-color: {self.theme.GRAY_300};
            }}
        """

    def get_settings_button_style(self) -> str:
        """设置按钮样式"""
        base_style = """
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

        return {
            'reset': base_style + f"""
                QPushButton {{
                    background-color: {self.theme.WHITE};
                    color: {self.theme.GRAY_600};
                    border-color: {self.theme.BORDER_COLOR};
                }}
                QPushButton:hover {{
                    background-color: {self.theme.GRAY_100};
                    border-color: {self.theme.BORDER_HOVER};
                    color: {self.theme.GRAY_700};
                }}
                QPushButton:pressed {{
                    background-color: {self.theme.GRAY_200};
                }}
            """,
            'cancel': base_style + f"""
                QPushButton {{
                    background-color: {self.theme.WHITE};
                    color: {self.theme.GRAY_700};
                    border-color: {self.theme.GRAY_400};
                }}
                QPushButton:hover {{
                    background-color: {self.theme.GRAY_100};
                    border-color: {self.theme.BORDER_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {self.theme.GRAY_200};
                }}
            """,
            'save': base_style + f"""
                QPushButton {{
                    {self.get_vertical_gradient_background(self.theme.PRIMARY, self.theme.PRIMARY_DARK)}
                    color: {self.theme.WHITE};
                    border-color: {self.theme.PRIMARY_DARK};
                }}
                QPushButton:hover {{
                    {self.get_vertical_gradient_background(self.theme.PRIMARY_LIGHT, self.theme.PRIMARY)}
                }}
                QPushButton:pressed {{
                    {self.get_vertical_gradient_background(self.theme.PRIMARY_DARK, self.theme.PRIMARY_DARKER)}
                }}
            """
        }

    # 输入控件样式
    def get_line_edit_style(self) -> str:
        """输入框样式"""
        return f"""
            QLineEdit {{
                padding: 10px;
                font-size: 13px;
                border: 1px solid {self.theme.GRAY_400};
                border-radius: 6px;
                background-color: {self.theme.WHITE};
                color: {self.theme.GRAY_700};
            }}
            QLineEdit:focus {{
                border-color: {self.theme.PRIMARY};
                outline: none;
            }}
            QLineEdit::placeholder {{
                color: {self.theme.GRAY_500};
            }}
        """

    def get_text_edit_style(self) -> str:
        """文本编辑器样式"""
        return f"""
            QTextEdit {{
                border: 1px solid {self.theme.BORDER_COLOR};
                border-radius: 6px;
                padding: 12px;
                font-size: 13px;
                background-color: {self.theme.INPUT_BACKGROUND};
                color: {self.theme.GRAY_700};
                selection-background-color: {self.theme.PRIMARY};
            }}
            QTextEdit:focus {{
                border-color: {self.theme.PRIMARY};
                outline: none;
            }}
        """

    # 列表和容器样式
    def get_list_widget_style(self) -> str:
        """列表控件样式"""
        return f"""
            QListWidget {{
                background-color: {self.theme.WHITE};
                border: 1px solid {self.theme.BORDER_COLOR};
                border-radius: 8px;
                outline: none;
                padding: 8px;
                font-size: 14px;
            }}
            QListWidget::item {{
                padding: 12px 16px;
                margin: 2px 0;
                border-radius: 6px;
                color: {self.theme.GRAY_700};
            }}
            QListWidget::item:hover {{
                background-color: {self.theme.PRIMARY_LIGHTER};
                color: {self.theme.PRIMARY};
            }}
            QListWidget::item:selected {{
                background-color: {self.theme.PRIMARY};
                color: {self.theme.WHITE};
                font-weight: bold;
            }}
        """

    def get_stacked_widget_style(self) -> str:
        """堆叠控件样式"""
        return f"""
            QStackedWidget {{
                background-color: {self.theme.WHITE};
                border: 1px solid {self.theme.BORDER_COLOR};
                border-radius: 8px;
                padding: 20px;
            }}
        """

    def get_splitter_style(self) -> str:
        """分割器样式"""
        return f"""
            QSplitter::handle {{
                background-color: {self.theme.BORDER_COLOR};
                width: 2px;
            }}
            QSplitter::handle:hover {{
                background-color: {self.theme.PRIMARY};
            }}
        """

    # 标签样式
    def get_section_title_style(self, font_size: int = 14) -> str:
        """章节标题样式"""
        return f"""
            QLabel {{
                font-size: {font_size}px;
                font-weight: bold;
                color: {self.theme.GRAY_700};
                background: transparent;
                border: none;
                margin-bottom: 5px;
            }}
        """

    def get_info_label_style(self) -> str:
        """信息标签样式"""
        return f"""
            QLabel {{
                color: {self.theme.GRAY_600};
                font-size: 11px;
                background: transparent;
                border: none;
                line-height: 1.4;
            }}
        """

    def get_file_path_label_style(self) -> str:
        """文件路径标签样式"""
        return f"""
            QLabel {{
                border: 1px solid {self.theme.GRAY_400};
                padding: 5px;
                background-color: {self.theme.WHITE};
                color: {self.theme.GRAY_700};
                border-radius: 4px;
            }}
        """

    # 工具栏和底部样式
    def get_bottom_toolbar_style(self) -> str:
        """底部工具栏样式"""
        return f"""
            QWidget {{
                background-color: {self.theme.BACKGROUND};
                border-top: 1px solid {self.theme.BORDER_COLOR};
            }}
        """

    def get_version_label_style(self) -> str:
        """版本标签样式"""
        return f"""
            QLabel {{
                color: {self.theme.GRAY_600};
                font-size: 12px;
                background: transparent;
            }}
        """


# 全局样式管理器实例
default_theme = Theme()
default_stylesheet = StyleSheet(default_theme)