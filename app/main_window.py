from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from contextlib import redirect_stdout
with redirect_stdout(None):
    from qfluentwidgets import NavigationItemPosition, FluentWindow, SplashScreen, setThemeColor, NavigationBarPushButton, toggleTheme, setTheme, Theme, NavigationAvatarWidget, NavigationToolButton ,NavigationPushButton
    from qfluentwidgets import FluentIcon as FIF
    from qfluentwidgets import InfoBar, InfoBarPosition

from .home_interface import HomeInterface
from .serial_terminal_interface import SerialTerminalInterface
from .part_library_interface import PartLibraryInterface
from .data_interface import DataInterface
from .mini_tool_interface import MiniToolInterface
from .about_interface import AboutInterface
import base64


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.initWindow()
        self.initInterface()
        self.initNavigation()

        # 检查更新
        # checkUpdate(self, flag=True)
        # checkAnnouncement(self) # 检查公告

    def initWindow(self):
        self.setMicaEffectEnabled(False)
        setThemeColor('#f18cb9', lazy=True)
        setTheme(Theme.AUTO, lazy=True)

        self.resize(960, 640)
        self.setWindowIcon(QIcon('./assets/logo/M2.ico'))
        self.setWindowTitle("MRobot Toolbox")


        desktop = QApplication.desktop().availableGeometry() # 获取可用屏幕大小
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

        self.show()
        QApplication.processEvents()

    def initInterface(self):
        self.homeInterface = HomeInterface(self)
        self.serialTerminalInterface = SerialTerminalInterface(self)
        self.partLibraryInterface = PartLibraryInterface(self)
        self.dataInterface = DataInterface(self)
        self.miniToolInterface = MiniToolInterface(self)


    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, self.tr('主页'))
        self.addSubInterface(self.dataInterface, FIF.CODE, self.tr('代码生成'))
        self.addSubInterface(self.serialTerminalInterface, FIF.COMMAND_PROMPT,self.tr('串口助手'))
        self.addSubInterface(self.partLibraryInterface, FIF.DOWNLOAD, self.tr('零件库'))
        self.addSubInterface(self.miniToolInterface, FIF.LIBRARY, self.tr('迷你工具箱'))
        self.addSubInterface(AboutInterface(self), FIF.INFO, self.tr('关于'), position=NavigationItemPosition.BOTTOM)


        # self.navigationInterface.addWidget(
        #     'startGameButton',
        #     NavigationBarPushButton(FIF.PLAY, '启动游戏', isSelectable=False),
        #     self.startGame,
        #     NavigationItemPosition.BOTTOM)

        # self.navigationInterface.addWidget(
        #     'themeButton',
        #     NavigationBarPushButton(FIF.BRUSH, '主题', isSelectable=False),
        #     lambda: toggleTheme(lazy=True),
        #     NavigationItemPosition.BOTTOM)

        self.themeBtn = NavigationPushButton(FIF.BRUSH, "切换主题", False, self.navigationInterface)
        self.themeBtn.clicked.connect(lambda: toggleTheme(lazy=True))
        self.navigationInterface.addWidget(
            'themeButton',
            self.themeBtn,
            None,
            NavigationItemPosition.BOTTOM
        )

        # self.navigationInterface.addWidget(
        #     'avatar',
        #     NavigationBarPushButton(FIF.HEART, '赞赏', isSelectable=False),
        #     lambda: MessageBoxSupport(
        #         '支持作者🥰',
        #         '此程序为免费开源项目，如果你付了钱请立刻退款\n如果喜欢本项目，可以微信赞赏送作者一杯咖啡☕\n您的支持就是作者开发和维护项目的动力🚀',
        #         './assets/app/images/sponsor.jpg',
        #         self
        #     ).exec(),
        #     NavigationItemPosition.BOTTOM
        # )

        # self.addSubInterface(self.settingInterface, FIF.SETTING, self.tr('设置'), position=NavigationItemPosition.BOTTOM)

        # self.splashScreen.finish() # 结束启动画面
        # self.themeListener = checkThemeChange(self)

        # if not cfg.get_value(base64.b64decode("YXV0b191cGRhdGU=").decode("utf-8")):
        #     disclaimer(self)


    # main_window.py 只需修改关闭事件
    def closeEvent(self, e):
        # if self.themeListener and self.themeListener.isRunning():
        #     self.themeListener.terminate()
        #     self.themeListener.deleteLater()
        super().closeEvent(e)
