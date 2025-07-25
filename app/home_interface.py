from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from qfluentwidgets import SubtitleLabel, BodyLabel, HorizontalSeparator, ImageLabel, FluentLabelBase, TitleLabel
import sys
import os

def resource_path(relative_path):
    """获取资源文件的绝对路径，兼容打包和开发环境"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的临时目录
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class HomeInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("homeInterface")

        # 外层居中布局
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        outer_layout.addStretch()

        # 内容布局
        content_layout = QVBoxLayout()
        content_layout.setSpacing(24)
        content_layout.setContentsMargins(48, 48, 48, 48)

        # Logo
        logo = ImageLabel(resource_path('assets/logo/MRobot.png'))
        logo.scaledToHeight(80)
        content_layout.addWidget(logo, alignment=Qt.AlignHCenter) # 居中对齐

        content_layout.addSpacing(8)
        content_layout.addStretch()

        # 主标题
        title = TitleLabel("MRobot Toolbox")
        title.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title)

        # 副标题
        subtitle = BodyLabel("现代化，多功能机器人开发工具箱")
        subtitle.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(subtitle)

        # 欢迎语
        welcome = BodyLabel("欢迎使用 MRobot Toolbox！一站式支持代码生成、硬件管理、串口调试与零件库下载。")
        welcome.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(welcome)

        content_layout.addSpacing(16)
        content_layout.addStretch()

        # 加到主布局
        outer_layout.addLayout(content_layout)
        outer_layout.addStretch()

        # 版权信息置底
        copyright_label = BodyLabel("© 2025 MRobot | Powered by QUT RM&RCer")
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setStyleSheet("font-size: 13px;")
        outer_layout.addWidget(copyright_label)
        outer_layout.addSpacing(18)