import sys
import webbrowser
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication, QLabel, QGroupBox, QGridLayout, QFrame, QHBoxLayout
from PyQt5.QtGui import QPixmap, QFont
from qfluentwidgets import (
    NavigationInterface, NavigationItemPosition, MessageBox,
    setTheme, Theme, FluentWindow, NavigationAvatarWidget,
    SubtitleLabel, setFont, InfoBar, InfoBarPosition, PushButton
)
from qfluentwidgets import FluentIcon as FIF

# ===================== 页面基类 =====================
class BaseInterface(QWidget):
    """所有页面的基类，便于统一扩展"""
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent=parent)
        self.setObjectName(f'{self.__class__.__name__}')
        self._mainLayout = QVBoxLayout(self)
        if title:
            self.titleLabel = SubtitleLabel(title, self)
            setFont(self.titleLabel, 24)
            self._mainLayout.addWidget(self.titleLabel, 0, Qt.AlignmentFlag.AlignCenter)
        self._mainLayout.addStretch(1)
        self.setLayout(self._mainLayout)

# ===================== 首页界面 =====================
class HomeInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # 顶部Logo
        iconLabel = QLabel(self)
        iconPixmap = QPixmap('img/MRobot.png').scaled(
            180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        iconLabel.setPixmap(iconPixmap)
        iconLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 标题
        titleLabel = QLabel("MRobot 智能R助手", self)
        titleLabel.setFont(QFont("微软雅黑", 28, QFont.Bold))
        titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titleLabel.setStyleSheet("color: #1976d2; margin-top: 12px;")

        # 副标题
        subtitle = QLabel("高效 · 智能 · 便捷\n让R语言开发更简单", self)
        subtitle.setFont(QFont("微软雅黑", 16))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #555; margin-bottom: 18px;")

        # 三个主按钮
        btnGen = PushButton('代码生成', self, FIF.LIBRARY)
        btnGen.setFixedSize(180, 48)
        btnGen.setFont(QFont("微软雅黑", 15))
        btnGen.clicked.connect(self.showInfoBar)

        btnHelp = PushButton('帮助文档', self, FIF.HELP)
        btnHelp.setFixedSize(180, 48)
        btnHelp.setFont(QFont("微软雅黑", 15))
        btnHelp.clicked.connect(self.showHelp)

        btnAbout = PushButton('关于我们', self, FIF.INFO)
        btnAbout.setFixedSize(180, 48)
        btnAbout.setFont(QFont("微软雅黑", 15))
        btnAbout.clicked.connect(self.showAbout)

        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(36)
        btnLayout.addStretch(1)
        btnLayout.addWidget(btnGen)
        btnLayout.addWidget(btnHelp)
        btnLayout.addWidget(btnAbout)
        btnLayout.addStretch(1)

        # 卡片式欢迎信息
        card = QFrame(self)
        card.setStyleSheet("""
            QFrame {
                background: #f8fbfd;
                border-radius: 18px;
                border: 1.5px solid #d6eaf8;
                padding: 24px 32px 18px 32px;
            }
        """)
        cardLayout = QVBoxLayout(card)
        cardLayout.setSpacing(10)
        cardLayout.addWidget(titleLabel)
        cardLayout.addWidget(subtitle)
        cardLayout.addLayout(btnLayout)

        # 主布局
        layout = QVBoxLayout()
        layout.setSpacing(24)
        layout.setContentsMargins(0, 32, 0, 0)
        layout.addWidget(iconLabel, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(card, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch(1)

        # 清空原有内容并设置新布局
        QWidget().setLayout(self._mainLayout)
        self.setLayout(layout)

    def showInfoBar(self):
        InfoBar.success(
            title="提示",
            content="代码生成功能即将上线，敬请期待！",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=2000
        )

    def showHelp(self):
        webbrowser.open("https://github.com/lvzucheng/MRobot")

    def showAbout(self):
        MessageBox("关于我们", "MRobot 由 lvzucheng 开发，致力于高效智能的R代码辅助。", self).exec()
# ===================== 代码生成页面 =====================
class DataInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__('代码生成', parent)

# ===================== 实用工具页面 =====================
# ...existing code...

class DownloadTool(BaseInterface):
    def __init__(self, parent=None):
        super().__init__('实用工具', parent)

        # 主体水平布局
        main_layout = QHBoxLayout()
        main_layout.setSpacing(32)
        main_layout.setContentsMargins(32, 0, 32, 0)  # 顶部和底部间距减小

        # 区域1：常用小工具
        tools = [
            ("Geek Uninstaller", "https://geekuninstaller.com/download", FIF.DELETE),
            ("Neat Download Manager", "https://www.neatdownloadmanager.com/index.php/en/", FIF.DOWNLOAD),
            ("Everything", "https://www.voidtools.com/zh-cn/downloads/", FIF.SEARCH),
            ("Bandizip", "https://www.bandisoft.com/bandizip/", FIF.ZIP_FOLDER),
            ("PotPlayer", "https://potplayer.daum.net/", FIF.VIDEO),
            ("Typora", "https://typora.io/", FIF.EDIT),
            ("Git", "https://git-scm.com/download/win", FIF.CODE),
            ("Python", "https://www.python.org/downloads/", FIF.CODE),
        ]
        tools_card = QGroupBox("常用小工具", self)
        tools_card.setFont(QFont("微软雅黑", 15, QFont.Bold))
        tools_card.setStyleSheet("""
            QGroupBox { border: 1.5px solid #d6eaf8; border-radius: 12px; background: #f8fbfd; margin-top: 0px; }
            QGroupBox:title { color: #222; left: 18px; top: -10px; background: transparent; padding: 0 8px; }
        """)
        tools_grid = QGridLayout()
        tools_grid.setSpacing(18)
        tools_grid.setContentsMargins(18, 18, 18, 18)
        for idx, (name, url, icon) in enumerate(tools):
            btn = PushButton(name, self, icon)
            btn.setFont(QFont("微软雅黑", 14))
            btn.setMinimumHeight(44)
            btn.clicked.connect(self._make_open_url(url))
            row, col = divmod(idx, 2)
            tools_grid.addWidget(btn, row, col)
        tools_card.setLayout(tools_grid)
        main_layout.addWidget(tools_card, 1)

        # 区域2：开发/设计软件
        dev_tools = [
            ("STM32CubeMX", "https://www.st.com/zh/development-tools/stm32cubemx.html", FIF.SETTING),
            ("Keil MDK", "https://www.keil.com/download/product/", FIF.CODE),
            ("Visual Studio Code", "https://code.visualstudio.com/", FIF.CODE),
            ("CLion", "https://www.jetbrains.com/clion/download/", FIF.CODE),
            ("MATLAB", "https://www.mathworks.com/downloads/", FIF.CODE),
            ("SolidWorks", "https://www.solidworks.com/sw/support/downloads.htm", FIF.LAYOUT),
            ("Altium Designer", "https://www.altium.com/zh/altium-designer/downloads", FIF.LAYOUT),
            ("原神", "https://download-porter.hoyoverse.com/download-porter/2025/03/27/GenshinImpact_install_202503072011.exe?trace_key=GenshinImpact_install_ua_679d0b4e9b10", FIF.GAME),
        ]
        dev_card = QGroupBox("开发/设计软件", self)
        dev_card.setFont(QFont("微软雅黑", 15, QFont.Bold))
        dev_card.setStyleSheet("""
            QGroupBox { border: 1.5px solid #d6eaf8; border-radius: 12px; background: #f8fbfd; margin-top: 0px; }
            QGroupBox:title { color: #222; left: 18px; top: -10px; background: transparent; padding: 0 8px; }
        """)
        dev_grid = QGridLayout()
        dev_grid.setSpacing(18)
        dev_grid.setContentsMargins(18, 18, 18, 18)
        for idx, (name, url, icon) in enumerate(dev_tools):
            btn = PushButton(name, self, icon)
            btn.setFont(QFont("微软雅黑", 14))
            btn.setMinimumHeight(44)
            btn.clicked.connect(self._make_open_url(url))
            row, col = divmod(idx, 2)
            dev_grid.addWidget(btn, row, col)
        dev_card.setLayout(dev_grid)
        main_layout.addWidget(dev_card, 1)

        # 添加到主布局，靠上显示
        self._mainLayout.insertLayout(1, main_layout)

    def _make_open_url(self, url):
        # 返回一个只带url参数的槽，避免lambda闭包问题
        return lambda checked=False, link=url: webbrowser.open(link)
# ...existing code...
# ===================== 其它页面 =====================
class SettingInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__('设置页面', parent)

class HelpInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__('帮助页面', parent)

class AboutInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__('关于页面', parent)

# ===================== 主窗口与导航 =====================
class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MR_ToolBox")
        self.resize(1000, 700)
        self.setMinimumSize(800, 600)
        setTheme(Theme.LIGHT)

        self.page_registry = [
            (HomeInterface(self), FIF.HOME, "首页", NavigationItemPosition.TOP),
            (DataInterface(self), FIF.LIBRARY, "MRobot代码生成", NavigationItemPosition.SCROLL),
            (DownloadTool(self), FIF.DOWNLOAD, "实用工具", NavigationItemPosition.SCROLL),
            (SettingInterface(self), FIF.SETTING, "设置", NavigationItemPosition.BOTTOM),
            (HelpInterface(self), FIF.HELP, "帮助", NavigationItemPosition.BOTTOM),
            (AboutInterface(self), FIF.INFO, "关于", NavigationItemPosition.BOTTOM),
        ]
        self.initNavigation()

    def initNavigation(self):
        for page, icon, name, position in self.page_registry:
            self.addSubInterface(page, icon, name, position)
        self.navigationInterface.addSeparator()
        avatar = NavigationAvatarWidget('用户', ':/qfluentwidgets/images/avatar.png')
        self.navigationInterface.addWidget(
            routeKey='avatar',
            widget=avatar,
            onClick=self.showUserInfo,
            position=NavigationItemPosition.BOTTOM
        )

    def showUserInfo(self):
        content = "当前登录用户: 管理员\n邮箱: admin@example.com"
        MessageBox("用户信息", content, self).exec()

# ===================== 程序入口 =====================
def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()