from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from contextlib import redirect_stdout
with redirect_stdout(None):
    from qfluentwidgets import NavigationItemPosition, FluentWindow, SplashScreen, setThemeColor, NavigationBarPushButton, toggleTheme, setTheme, Theme, NavigationAvatarWidget, NavigationToolButton ,NavigationPushButton, theme
    from qfluentwidgets import FluentIcon as FIF
    from qfluentwidgets import InfoBar, InfoBarPosition

from .home_interface import HomeInterface
from .serial_terminal_interface import SerialTerminalInterface
from .part_library_interface import PartLibraryInterface
from .data_interface import DataInterface
from .mini_tool_interface import MiniToolInterface
from .code_configuration_interface import CodeConfigurationInterface
from .finance_interface import FinanceInterface
from .about_interface import AboutInterface
import base64


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.initWindow()
        self.initInterface()
        self.initNavigation()

        # 后台检查更新（不弹窗，只显示通知）
        # self.check_updates_in_background()

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
        # self.dataInterface = DataInterface(self)
        self.miniToolInterface = MiniToolInterface(self)
        self.codeConfigurationInterface = CodeConfigurationInterface(self)
        self.financeInterface = FinanceInterface(self)


    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, self.tr('主页'))
        # self.addSubInterface(self.dataInterface, FIF.CODE, self.tr('代码生成'))
        self.addSubInterface(self.codeConfigurationInterface, FIF.CODE, self.tr('代码生成'))
        self.addSubInterface(self.serialTerminalInterface, FIF.COMMAND_PROMPT,self.tr('串口助手'))
        self.addSubInterface(self.partLibraryInterface, FIF.DOWNLOAD, self.tr('零件库'))
        self.addSubInterface(self.financeInterface, FIF.DOCUMENT, self.tr('财务做账'))
        self.addSubInterface(self.miniToolInterface, FIF.LIBRARY, self.tr('迷你工具箱'))
        self.addSubInterface(AboutInterface(self), FIF.INFO, self.tr('关于'), position=NavigationItemPosition.BOTTOM)



        self.themeBtn = NavigationPushButton(FIF.BRUSH, "切换主题", False, self.navigationInterface)
        self.themeBtn.clicked.connect(self._safe_toggle_theme)
        self.navigationInterface.addWidget(
            'themeButton',
            self.themeBtn,
            None,
            NavigationItemPosition.BOTTOM
        )
    
    def _safe_toggle_theme(self):
        """安全地切换主题，避免字典迭代异常"""
        def safe_toggle():
            try:
                import sys
                from io import StringIO
                
                # 捕获 stderr 以抑制库内的异常消息
                old_stderr = sys.stderr
                sys.stderr = StringIO()
                
                try:
                    # 获取当前主题
                    current_theme = theme()
                    # 根据当前主题切换到另一个
                    new_theme = Theme.LIGHT if current_theme == Theme.DARK else Theme.DARK
                    setTheme(new_theme, save=True, lazy=True)
                finally:
                    # 恢复 stderr
                    sys.stderr = old_stderr
                    
            except Exception as e:
                # 其他异常仍然打印，但忽略字典迭代异常
                error_msg = str(e)
                if "dictionary changed size during iteration" not in error_msg:
                    print(f"主题切换失败: {e}")
        
        # 在下一个事件循环中执行切换，让 Qt 完成当前事件处理
        QTimer.singleShot(50, safe_toggle)
    
    def check_updates_in_background(self):
        """后台检查更新"""
        try:
            # 后台更新检查已移至关于页面手动触发
            pass
        except Exception as e:
            print(f"初始化完成: {e}")

    # main_window.py 只需修改关闭事件
    def closeEvent(self, e):
        # if self.themeListener and self.themeListener.isRunning():
        #     self.themeListener.terminate()
        #     self.themeListener.deleteLater()
        super().closeEvent(e)
