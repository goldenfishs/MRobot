import os
import sys
# 将当前工作目录设置为程序所在的目录，确保无论从哪里执行，其工作目录都正确设置为程序本身的位置，避免路径错误。
os.chdir(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False)else os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from app.main_window import MainWindow



# 启用 DPI 缩放
QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling) # 启用高 DPI 缩放
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps) # 使用高 DPI 图标

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings) # 避免创建原生窗口小部件的兄弟窗口

    w = MainWindow()

    sys.exit(app.exec_()) # 启动应用程序并进入主事件循环
    # 注意：在 PyQt5 中，exec_() 是一个阻塞调用，直到应用程序退出。
