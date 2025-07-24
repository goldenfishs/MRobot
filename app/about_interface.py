from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt
from qfluentwidgets import PrimaryPushSettingCard, FluentIcon
from qfluentwidgets import InfoBar, InfoBarPosition

from .function_fit_interface import FunctionFitInterface
from app.tools.check_update import check_update

__version__ = "1.0.0"

class AboutInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("aboutInterface")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        card = PrimaryPushSettingCard(
            text="检查更新",
            icon=FluentIcon.DOWNLOAD,
            title="关于",
            content=f"MRobot_Toolbox 当前版本：{__version__}",
        )
        card.clicked.connect(self.on_check_update_clicked)
        layout.addWidget(card)

    def on_check_update_clicked(self):
        latest = check_update(__version__)
        if latest:
            InfoBar.success(
                title="发现新版本",
                content=f"检测到新版本：{latest}，请前往官网或仓库下载更新。",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=5000
            )
        else:
            InfoBar.info(
                title="已是最新版本",
                content="当前已是最新版本，无需更新。",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )