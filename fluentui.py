import sys
import webbrowser
import serial
import serial.tools.list_ports

from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QApplication, QLabel, QGroupBox, QGridLayout, QFrame,
    QHBoxLayout, QComboBox, QTextEdit, QLineEdit
)

from qfluentwidgets import (
    NavigationInterface, NavigationItemPosition, MessageBox,
    setTheme, Theme, FluentWindow, NavigationAvatarWidget,
    InfoBar, InfoBarPosition, PushButton, FluentIcon
)
from qfluentwidgets import FluentIcon as FIF

# ===================== 页面基类 =====================
class BaseInterface(QWidget):
    """所有页面的基类，页面内容完全自定义"""
    def __init__(self, parent=None):
        super().__init__(parent=parent)

# ===================== 首页界面 =====================
class HomeInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("homeInterface")
        layout = QVBoxLayout()
        self.setLayout(layout)
# ===================== 代码生成页面 =====================
class DataInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("dataInterface")
        # 空页面示例
        layout = QVBoxLayout()
        self.setLayout(layout)

# ===================== 串口终端界面 =====================
class SerialTerminalInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("serialTerminalInterface")
        layout = QVBoxLayout()

# ===================== 设置界面 =====================
class SettingInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("settingInterface")
        layout = QVBoxLayout()
        self.themeBtn = PushButton(
            "切换夜间", self, FluentIcon.BRUSH
        )
        self.themeBtn.setFixedWidth(120)
        self.themeBtn.clicked.connect(self.onThemeBtnClicked)
        layout.addWidget(self.themeBtn)
        layout.addStretch(1)
        self.setLayout(layout)

        # 监听主题变化
        mw = self.window()
        if hasattr(mw, "themeChanged"):
            mw.themeChanged.connect(self.updateThemeBtn)

    def onThemeBtnClicked(self):
        mw = self.window()
        if hasattr(mw, "toggleTheme"):
            mw.toggleTheme()

    def updateThemeBtn(self, theme):
        if theme == Theme.LIGHT:
            self.themeBtn.setText("切换夜间")
        else:
            self.themeBtn.setText("切换白天")
# ===================== 帮助与关于界面 =====================
class HelpInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("helpInterface")
        layout = QVBoxLayout()
        self.setLayout(layout)

class AboutInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("aboutInterface")
        layout = QVBoxLayout()
        self.setLayout(layout)

# ===================== 主窗口与导航 =====================
class MainWindow(FluentWindow):
    themeChanged = pyqtSignal(Theme)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MR_ToolBox")
        self.resize(1000, 700)
        self.setMinimumSize(800, 600)
        setTheme(Theme.LIGHT)
        self.theme = Theme.LIGHT

        self.page_registry = [
            (HomeInterface(self), FIF.HOME, "首页", NavigationItemPosition.TOP),
            (DataInterface(self), FIF.LIBRARY, "MRobot代码生成", NavigationItemPosition.SCROLL),
            (SerialTerminalInterface(self), FIF.COMMAND_PROMPT, "串口终端", NavigationItemPosition.SCROLL),
            (SettingInterface(self), FIF.SETTING, "设置", NavigationItemPosition.BOTTOM),
            (HelpInterface(self), FIF.HELP, "帮助", NavigationItemPosition.BOTTOM),
            (AboutInterface(self), FIF.INFO, "关于", NavigationItemPosition.BOTTOM),
        ]
        self.initNavigation()

        # 把切换主题按钮放到标题栏右侧
        self.themeBtn = PushButton("切换夜间", self, FluentIcon.BRUSH)
        self.themeBtn.setFixedWidth(120)
        self.themeBtn.clicked.connect(self.toggleTheme)
        self.addTitleBarWidget(self.themeBtn, align=Qt.AlignRight)

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

    def toggleTheme(self):
        if self.theme == Theme.LIGHT:
            setTheme(Theme.DARK)
            self.theme = Theme.DARK
            self.themeBtn.setText("切换白天")
        else:
            setTheme(Theme.LIGHT)
            self.theme = Theme.LIGHT
            self.themeBtn.setText("切换夜间")
        self.themeChanged.emit(self.theme)
        self.refreshStyle()

    def refreshStyle(self):
        def refresh(widget):
            widget.setStyleSheet(widget.styleSheet())
            for child in widget.findChildren(QWidget):
                refresh(child)
        refresh(self)

    def showUserInfo(self):
        MessageBox("用户信息", "当前登录用户：管理员", self).exec()
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