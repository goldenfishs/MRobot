from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices

from qfluentwidgets import PrimaryPushSettingCard, FluentIcon
from qfluentwidgets import InfoBar, InfoBarPosition, SubtitleLabel

from .function_fit_interface import FunctionFitInterface
from app.tools.check_update import check_update

__version__ = "1.0.4"

class AboutInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("aboutInterface")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(20, 30, 20, 20)  # 添加边距

        title = SubtitleLabel("MRobot 帮助页面", self)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        # 添加空间隔
        layout.addSpacing(10)

        card = PrimaryPushSettingCard(
            text="检查更新",
            icon=FluentIcon.DOWNLOAD,
            title="更新",
            content=f"MRobot_Toolbox 当前版本：{__version__}",
        )
        card.clicked.connect(self.on_check_update_clicked)
        layout.addWidget(card)

    def on_check_update_clicked(self):
        try:
            latest = check_update(__version__)
            if latest:
                # 直接用浏览器打开下载链接
                QDesktopServices.openUrl(QUrl("https://github.com/goldenfishs/MRobot/releases/latest"))
                InfoBar.success(
                    title="发现新版本",
                    content=f"检测到新版本：{latest}，已为你打开下载页面。",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=5000
                )
            elif latest is None:
                InfoBar.info(
                    title="已是最新版本",
                    content="当前已是最新版本，无需更新。",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=3000
                )
        except Exception:
            InfoBar.error(
                title="检查更新失败",
                content="无法获取最新版本，请检查网络连接。",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=4000
            )