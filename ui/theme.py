"""
样式主题管理器
统一管理应用程序的所有样式和主题色彩
"""

from enum import Enum
from typing import Dict, Any


class ThemeType(Enum):
    """主题类型枚举"""
    BLUE = "blue"
    RED = "red"
    GREEN = "green"


class BaseTheme:
    """基础主题类"""

    def __init__(self):
        # 中性色（所有主题共用）
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

        # 状态色（所有主题共用）
        self.SUCCESS = "#28A745"
        self.WARNING = "#FFC107"
        self.DANGER = "#DC3545"
        self.INFO = "#17A2B8"

        # 背景色
        self.BACKGROUND = "#F5F7FA"
        self.CARD_BACKGROUND = "#FFFFFF"
        self.INPUT_BACKGROUND = "#FAFBFC"

        # 边框色
        self.BORDER_COLOR = "#E3E8ED"
        self.BORDER_HOVER = "#ADB5BD"


class BlueTheme(BaseTheme):
    """蓝色主题"""

    def __init__(self):
        super().__init__()
        self.PRIMARY = "#4A90E2"
        self.PRIMARY_DARK = "#357ABD"
        self.PRIMARY_DARKER = "#2E5BA8"
        self.PRIMARY_LIGHT = "#5BA0F2"
        self.PRIMARY_LIGHTER = "#E8F4FD"
        self.SECONDARY = "#6C757D"


class RedTheme(BaseTheme):
    """红色主题"""

    def __init__(self):
        super().__init__()
        self.PRIMARY = "#E74C3C"
        self.PRIMARY_DARK = "#C0392B"
        self.PRIMARY_DARKER = "#A93226"
        self.PRIMARY_LIGHT = "#EC7063"
        self.PRIMARY_LIGHTER = "#FADBD8"
        self.SECONDARY = "#95A5A6"


class GreenTheme(BaseTheme):
    """绿色主题"""

    def __init__(self):
        super().__init__()
        self.PRIMARY = "#27AE60"
        self.PRIMARY_DARK = "#239B56"
        self.PRIMARY_DARKER = "#1E8449"
        self.PRIMARY_LIGHT = "#58D68D"
        self.PRIMARY_LIGHTER = "#D5F4E6"
        self.SECONDARY = "#7F8C8D"


class ThemeManager:
    """主题管理器"""

    _themes = {
        ThemeType.BLUE: BlueTheme,
        ThemeType.RED: RedTheme,
        ThemeType.GREEN: GreenTheme,
    }

    @classmethod
    def get_theme(cls, theme_type: ThemeType = ThemeType.BLUE):
        """获取指定类型的主题"""
        return cls._themes[theme_type]()

    @classmethod
    def get_available_themes(cls) -> Dict[str, str]:
        """获取可用主题列表"""
        return {
            "蓝色": ThemeType.BLUE.value,
            "红色": ThemeType.RED.value,
            "绿色": ThemeType.GREEN.value,
        }


class StyleSheet:
    """样式表管理器"""

    def __init__(self, theme: BaseTheme = None):
        self.theme = theme or BlueTheme()

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
        """标题栏样式 - 更紧凑"""
        return f"""
            QWidget {{
                {self.get_gradient_background(self.theme.PRIMARY, self.theme.PRIMARY_DARK)}
                color: {self.theme.WHITE};
                border-bottom: 1px solid {self.theme.PRIMARY_DARKER};
                min-height: 50px;
                max-height: 50px;
            }}
        """

    def get_title_label_style(self, font_size: int = 16) -> str:
        """标题标签样式"""
        return f"""
            QLabel {{
                font-size: {font_size}px;
                font-weight: 600;
                color: {self.theme.WHITE};
                background: transparent;
                border: none;
                padding: 0;
            }}
        """

    def get_status_label_style(self) -> str:
        """状态标签样式 - 更小巧"""
        return f"""
            QLabel {{
                font-size: 11px;
                font-weight: 500;
                color: {self.theme.WHITE};
                background: rgba(255, 255, 255, 0.25);
                padding: 3px 10px;
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
        """

    def get_card_style(self) -> str:
        """卡片样式 - 增加阴影效果"""
        return f"""
            QWidget {{
                background-color: {self.theme.CARD_BACKGROUND};
                border: 1px solid {self.theme.BORDER_COLOR};
                border-radius: 10px;
                /* 模拟阴影效果 */
            }}
        """

    def get_compact_card_style(self) -> str:
        """紧凑卡片样式"""
        return f"""
            QWidget {{
                background-color: {self.theme.CARD_BACKGROUND};
                border: 1px solid {self.theme.BORDER_COLOR};
                border-radius: 8px;
                margin: 2px;
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
        """主要按钮样式 - 更紧凑"""
        return f"""
            QPushButton {{
                padding: 10px 18px;
                font-size: 13px;
                font-weight: 500;
                border-radius: 6px;
                border: none;
                {self.get_vertical_gradient_background(self.theme.PRIMARY_LIGHT, self.theme.PRIMARY)}
                color: {self.theme.WHITE};
                min-height: 20px;
            }}
            QPushButton:hover {{
                {self.get_vertical_gradient_background(self.theme.PRIMARY, self.theme.PRIMARY_DARK)}
            }}
            QPushButton:pressed {{
                {self.get_vertical_gradient_background(self.theme.PRIMARY_DARK, self.theme.PRIMARY_DARKER)}
            }}
            QPushButton:focus {{
                outline: none;
                border: 2px solid rgba(255, 255, 255, 0.5);
            }}
        """

    def get_secondary_button_style(self) -> str:
        """次要按钮样式 - 更紧凑"""
        return f"""
            QPushButton {{
                padding: 10px 18px;
                font-size: 13px;
                font-weight: 500;
                border-radius: 6px;
                background-color: {self.theme.WHITE};
                color: {self.theme.GRAY_700};
                border: 1px solid {self.theme.GRAY_400};
                min-height: 20px;
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
                border: 2px solid {self.theme.PRIMARY_LIGHT};
            }}
        """

    def get_small_button_style(self) -> str:
        """小按钮样式"""
        return f"""
            QPushButton {{
                padding: 6px 12px;
                font-size: 11px;
                border-radius: 4px;
                background-color: transparent;
                color: {self.theme.GRAY_600};
                border: 1px solid transparent;
                min-height: 16px;
            }}
            QPushButton:hover {{
                background-color: {self.theme.GRAY_200};
                color: {self.theme.GRAY_700};
            }}
            QPushButton:pressed {{
                background-color: {self.theme.GRAY_300};
            }}
        """

    def get_icon_button_style(self) -> str:
        """图标按钮样式"""
        return f"""
            QPushButton {{
                padding: 8px;
                border-radius: 6px;
                background-color: {self.theme.WHITE};
                border: 1px solid {self.theme.BORDER_COLOR};
                color: {self.theme.GRAY_600};
                min-width: 36px;
                min-height: 36px;
            }}
            QPushButton:hover {{
                background-color: {self.theme.PRIMARY_LIGHTER};
                border-color: {self.theme.PRIMARY};
                color: {self.theme.PRIMARY};
            }}
            QPushButton:pressed {{
                background-color: {self.theme.PRIMARY};
                color: {self.theme.WHITE};
            }}
        """

    def get_settings_button_style(self) -> str:
        """设置按钮样式"""
        base_style = """
            QPushButton {
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
                border-radius: 6px;
                border: 1px solid transparent;
                min-width: 70px;
                min-height: 20px;
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
        """输入框样式 - 更紧凑"""
        return f"""
            QLineEdit {{
                padding: 8px 12px;
                font-size: 13px;
                border: 1px solid {self.theme.GRAY_400};
                border-radius: 6px;
                background-color: {self.theme.WHITE};
                color: {self.theme.GRAY_700};
                min-height: 16px;
            }}
            QLineEdit:focus {{
                border-color: {self.theme.PRIMARY};
                background-color: {self.theme.PRIMARY_LIGHTER};
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
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                background-color: {self.theme.INPUT_BACKGROUND};
                color: {self.theme.GRAY_700};
                selection-background-color: {self.theme.PRIMARY_LIGHTER};
                selection-color: {self.theme.PRIMARY_DARK};
            }}
            QTextEdit:focus {{
                border-color: {self.theme.PRIMARY};
                background-color: {self.theme.WHITE};
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
                padding: 4px;
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 10px 14px;
                margin: 1px 0;
                border-radius: 5px;
                color: {self.theme.GRAY_700};
            }}
            QListWidget::item:hover {{
                background-color: {self.theme.PRIMARY_LIGHTER};
                color: {self.theme.PRIMARY};
            }}
            QListWidget::item:selected {{
                background-color: {self.theme.PRIMARY};
                color: {self.theme.WHITE};
                font-weight: 500;
            }}
        """

    def get_stacked_widget_style(self) -> str:
        """堆叠控件样式"""
        return f"""
            QStackedWidget {{
                background-color: {self.theme.WHITE};
                border: 1px solid {self.theme.BORDER_COLOR};
                border-radius: 8px;
                padding: 16px;
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
        """章节标题样式 - 更紧凑"""
        return f"""
            QLabel {{
                font-size: {font_size}px;
                font-weight: 600;
                color: {self.theme.GRAY_800};
                background: transparent;
                border: none;
                margin-bottom: 8px;
                padding: 4px 0;
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
                padding: 2px 0;
            }}
        """

    def get_base_label_style(self) -> str:
        """基础标签样式 - 更紧凑"""
        return f"""
            QLabel {{
                border: 1px solid {self.theme.GRAY_400};
                padding: 6px 10px;
                background-color: {self.theme.WHITE};
                color: {self.theme.GRAY_700};
                border-radius: 4px;
                font-size: 12px;
            }}
        """

    # 工具栏和底部样式
    def get_bottom_toolbar_style(self) -> str:
        """底部工具栏样式 - 更紧凑"""
        return f"""
            QWidget {{
                background-color: {self.theme.BACKGROUND};
                border-top: 1px solid {self.theme.BORDER_COLOR};
                min-height: 40px;
                max-height: 40px;
            }}
        """

    def get_version_label_style(self) -> str:
        """版本标签样式"""
        return f"""
            QLabel {{
                color: {self.theme.GRAY_600};
                font-size: 11px;
                background: transparent;
            }}
        """

    def get_divider_style(self) -> str:
        """分割线样式"""
        return f"""
            QFrame {{
                background-color: {self.theme.BORDER_COLOR};
                border: none;
                max-height: 1px;
                min-height: 1px;
            }}
        """


# 全局样式管理器实例
default_theme = BlueTheme()
default_stylesheet = StyleSheet(default_theme)

# 主题切换函数
def create_stylesheet(theme_type: ThemeType = ThemeType.BLUE) -> StyleSheet:
    """创建指定主题的样式表"""
    theme = ThemeManager.get_theme(theme_type)
    return StyleSheet(theme)