import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui.main_window import MainWindow


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
