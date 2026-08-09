import os
import sys
from pathlib import Path


def runtime_working_directory() -> Path:
    """Return a writable runtime directory without modifying an app bundle."""
    if not getattr(sys, 'frozen', False):
        return Path(__file__).resolve().parent
    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / 'MRobot'
    if sys.platform == 'win32':
        return Path(os.environ.get('APPDATA', Path.home())) / 'MRobot'
    return Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share')) / 'MRobot'


runtime_dir = runtime_working_directory()
runtime_dir.mkdir(parents=True, exist_ok=True)
os.chdir(runtime_dir)

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
