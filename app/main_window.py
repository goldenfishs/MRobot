from PyQt5.QtCore import QSettings, Qt, QSize, QTimer, QRect
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from contextlib import redirect_stdout
with redirect_stdout(None):
    from qfluentwidgets import NavigationItemPosition, FluentWindow, SplashScreen, setThemeColor, NavigationBarPushButton, toggleTheme, setTheme, Theme, NavigationAvatarWidget, NavigationToolButton ,NavigationPushButton, theme
    from qfluentwidgets import FluentIcon as FIF
    from qfluentwidgets import InfoBar, InfoBarPosition

from .home_interface import HomeInterface, resource_path
from .serial_terminal_interface import SerialTerminalInterface
from .part_library_interface import PartLibraryInterface
from .data_interface import DataInterface
from .mini_tool_interface import MiniToolInterface
from .code_configuration_interface import CodeConfigurationInterface
from .finance_interface import FinanceInterface
from .mech_design_interface import MechDesignInterface
from .about_interface import AboutInterface
from .feature_flags import is_ai_beta_enabled, set_ai_beta_enabled
from .tools.update_check_thread import UpdateCheckThread
from . import __version__
import base64
import sys
import os


class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self._navigation_ready = False
        self.initWindow()
        self.initInterface()
        self.initNavigation()
        self._navigation_ready = True

        QTimer.singleShot(2500, self.check_updates_in_background)

    def initWindow(self):
        setThemeColor('#f18cb9', lazy=True)
        setTheme(Theme.AUTO, lazy=True)
        self._enable_native_window_effect()

        self.resize(960, 640)
        self.setWindowIcon(QIcon(resource_path('assets/logo/M2.ico')))
        self.setWindowTitle("MRobot Toolbox")


        desktop = QApplication.desktop().availableGeometry() # 获取可用屏幕大小
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

        self.show()
        QApplication.processEvents()

    def _enable_native_window_effect(self):
        """Enable native window chrome without placing a view over Qt content."""
        if os.environ.get('QT_QPA_PLATFORM') == 'offscreen':
            return
        if sys.platform == 'darwin':
            try:
                # qframelesswindow's macOS acrylic helper creates a
                # QMacCocoaViewContainer.  Depending on the initialization
                # order that container can cover every Qt child widget.  Keep
                # the real AppKit title-bar controls and native window colour,
                # but do not add an extra Cocoa view to the content hierarchy.
                import Cocoa
                from qframelesswindow.utils.mac_utils import getNSWindow

                ns_window = getNSWindow(self.winId())
                ns_window.setTitlebarAppearsTransparent_(True)
                ns_window.setBackgroundColor_(Cocoa.NSColor.windowBackgroundColor())
            except Exception as exc:
                print(f"macOS 原生窗口材质启用失败: {exc}")
        elif sys.platform == 'win32':
            self.setMicaEffectEnabled(True)

    def systemTitleBarRect(self, size):
        if sys.platform == 'darwin':
            return QRect(10, 7 if not self.isFullScreen() else 0, 75, size.height())
        return super().systemTitleBarRect(size)

    def initInterface(self):
        self.homeInterface = HomeInterface(self)
        self.serialTerminalInterface = SerialTerminalInterface(self)
        self.partLibraryInterface = PartLibraryInterface(self)
        # self.dataInterface = DataInterface(self)
        self.miniToolInterface = MiniToolInterface(self)
        self.codeConfigurationInterface = CodeConfigurationInterface(self)
        self.financeInterface = FinanceInterface(self)
        self.mechDesignInterface = MechDesignInterface(self)
        self.aiInterface = None
        if is_ai_beta_enabled():
            self._create_ai_interface()
        self.aboutInterface = AboutInterface(self)
        self.aboutInterface.ai_beta_changed.connect(self.set_ai_beta_enabled)
        self.miniToolInterface.set_ai_beta_enabled(is_ai_beta_enabled())


    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, self.tr('主页'))
        # self.addSubInterface(self.dataInterface, FIF.CODE, self.tr('代码生成'))
        self.addSubInterface(self.codeConfigurationInterface, FIF.CODE, self.tr('代码生成'))
        if self.aiInterface is not None:
            self.addSubInterface(self.aiInterface, FIF.ROBOT, self.tr('AI 工作台 Beta'), isTransparent=True)
        self.addSubInterface(self.serialTerminalInterface, FIF.COMMAND_PROMPT,self.tr('串口助手'))
        self.addSubInterface(self.partLibraryInterface, FIF.ZIP_FOLDER, self.tr('零件库'))
        self.addSubInterface(self.mechDesignInterface, FIF.SETTING, self.tr('机械设计'))
        # self.addSubInterface(self.financeInterface, FIF.DOCUMENT, self.tr('财务做账'))
        self.addSubInterface(self.miniToolInterface, FIF.LIBRARY, self.tr('迷你工具箱'))
        self.addSubInterface(self.aboutInterface, FIF.INFO, self.tr('关于'), position=NavigationItemPosition.BOTTOM)

        if sys.platform == 'darwin':
            # Reserve the first navigation row for native traffic-light buttons.
            return_button = self.navigationInterface.panel.returnButton
            return_button.setEnabled(False)
            return_button.setIcon(QIcon())
            return_button.setToolTip("")
            return_button.setAttribute(Qt.WA_TransparentForMouseEvents)
            self.titleBar.hBoxLayout.setContentsMargins(50, 0, 0, 0)



        self.themeBtn = NavigationPushButton(FIF.BRUSH, "切换主题", False, self.navigationInterface)
        self.themeBtn.clicked.connect(self._safe_toggle_theme)
        self.navigationInterface.addWidget(
            'themeButton',
            self.themeBtn,
            None,
            NavigationItemPosition.BOTTOM
        )

    def _create_ai_interface(self):
        if self.aiInterface is None:
            from .ai_interface import AIInterface

            self.aiInterface = AIInterface(self)
        return self.aiInterface

    def _insert_ai_navigation(self) -> None:
        interface = self._create_ai_interface()
        if self.stackedWidget.indexOf(interface) >= 0:
            return
        interface.setProperty("isStackedTransparent", True)
        self.stackedWidget.addWidget(interface)
        self.navigationInterface.insertItem(
            4,  # return/menu controls occupy the first two layout positions
            routeKey=interface.objectName(),
            icon=FIF.ROBOT,
            text=self.tr("AI 工作台 Beta"),
            onClick=lambda: self.switchTo(interface),
            tooltip=self.tr("AI 工作台 Beta"),
        )
        self._updateStackedBackground()

    def set_ai_beta_enabled(self, enabled: bool) -> None:
        """Persist and immediately apply the explicit AI Beta opt-in."""
        set_ai_beta_enabled(enabled)
        self.aboutInterface.set_ai_beta_enabled(enabled)
        self.miniToolInterface.set_ai_beta_enabled(enabled)
        if not self._navigation_ready:
            return
        if enabled:
            self._insert_ai_navigation()
            return
        if self.aiInterface is None:
            return
        if self.stackedWidget.currentWidget() is self.aiInterface:
            self.switchTo(self.homeInterface)
        self.navigationInterface.removeWidget(self.aiInterface.objectName())
        self.stackedWidget.removeWidget(self.aiInterface)
        self.aiInterface.close()
        self.aiInterface.deleteLater()
        self.aiInterface = None
        self._updateStackedBackground()

    def open_ai_workspace(self) -> bool:
        if not is_ai_beta_enabled():
            InfoBar.info(
                title="AI 工作台尚未启用",
                content="请先在“关于 → 实验性功能”中启用 MRobot AI 工作台（Beta）。",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=5000,
            )
            return False
        self._insert_ai_navigation()
        self.switchTo(self.aiInterface)
        return True
    
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
        settings = QSettings("MRobot", "MRobot")
        if not settings.value("updates/autoCheck", True, type=bool):
            return
        self.updateCheckThread = UpdateCheckThread(__version__)
        self.updateCheckThread.update_found.connect(self._background_update_found)
        self.updateCheckThread.error_occurred.connect(
            lambda message: print(f"后台检查更新失败: {message}")
        )
        self.updateCheckThread.start()

    def _background_update_found(self, update_info):
        self.aboutInterface.accept_background_update(update_info)
        version = update_info.get("version", "")
        settings = QSettings("MRobot", "MRobot")
        if settings.value("updates/autoInstall", False, type=bool):
            InfoBar.success(
                title="正在自动更新",
                content=f"MRobot v{version} 将在下载和校验完成后自动安装并重启。",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=5000,
            )
            self.aboutInterface.start_update()
        else:
            InfoBar.info(
                title="发现新版本",
                content=f"MRobot v{version} 已发布，请在“关于”页面一键更新。",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=6000,
            )

    # main_window.py 只需修改关闭事件
    def closeEvent(self, e):
        # if self.themeListener and self.themeListener.isRunning():
        #     self.themeListener.terminate()
        #     self.themeListener.deleteLater()
        super().closeEvent(e)
