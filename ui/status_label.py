from PySide6.QtWidgets import QLabel
from ui.theme import default_stylesheet


class StatusLabel(QLabel):
    """自定义状态标签组件"""

    def __init__(self, text: str = "就绪", parent=None):
        super().__init__(text, parent)
        self.theme = default_stylesheet.theme
        self.set_ready_style()

    def set_ready_style(self):
        """设置就绪状态样式"""
        self.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                font-weight: 500;
                color: {self.theme.WHITE};
                background: {self.theme.PRIMARY};
                padding: 3px 10px;
                border-radius: 10px;
                border: 1px solid rgba(0, 123, 255, 0.3);
            }}
        """)

    def set_success_style(self):
        """设置成功状态样式"""
        self.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                font-weight: 500;
                color: {self.theme.WHITE};
                background: {self.theme.SUCCESS};
                padding: 3px 10px;
                border-radius: 10px;
                border: 1px solid rgba(40, 167, 69, 0.3);
            }}
        """)

    def set_error_style(self):
        """设置错误状态样式"""
        self.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                font-weight: 500;
                color: {self.theme.WHITE};
                background: {self.theme.DANGER};
                padding: 3px 10px;
                border-radius: 10px;
                border: 1px solid rgba(220, 53, 69, 0.3);
            }}
        """)

    def set_warning_style(self):
        """设置警告状态样式"""
        self.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                font-weight: 500;
                color: {self.theme.WHITE};
                background: {self.theme.WARNING};
                padding: 3px 10px;
                border-radius: 10px;
                border: 1px solid rgba(255, 193, 7, 0.3);
            }}
        """)

    def set_info_style(self):
        """设置信息状态样式"""
        self.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                font-weight: 500;
                color: {self.theme.WHITE};
                background: {self.theme.INFO};
                padding: 3px 10px;
                border-radius: 10px;
                border: 1px solid rgba(23, 162, 184, 0.3);
            }}
        """)

    def update_status(self, status_text: str):
        """根据状态文本自动设置样式"""
        self.setText(status_text)

        if "成功" in status_text or "就绪" in status_text or "完成" in status_text:
            self.set_success_style()
        elif "失败" in status_text or "错误" in status_text:
            self.set_error_style()
        elif "警告" in status_text:
            self.set_warning_style()
        elif "启用" in status_text or "处理中" in status_text:
            self.set_info_style()
        else:
            self.set_ready_style()
