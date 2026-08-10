from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, FluentIcon, InfoBar, PushButton, TabBar, TitleLabel

from mcode.errors import MCodeError
from mcode.service import MCodeService

from .code_generate_interface import CodeGenerateInterface
from .function_fit_interface import FunctionFitInterface


class CodeConfigurationInterface(QWidget):
    """Project picker and tab host for the unified MCode frontend."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CodeConfigurationInterface")
        self.mcode = MCodeService()

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setContentsMargins(10, 0, 10, 10)
        self.tabBar = TabBar(self)
        self.tabBar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.vBoxLayout.addWidget(self.tabBar)
        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout.addWidget(self.stackedWidget)

        self.mainPage = QWidget(self)
        main_layout = QVBoxLayout(self.mainPage)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setSpacing(18)
        main_layout.setContentsMargins(48, 48, 48, 48)
        title = TitleLabel("MCode 代码生成", self.mainPage)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        subtitle = BodyLabel(
            "选择 STM32CubeMX 或其他 MCode 工程，直接从官方 registry 安装模块、预览计划并安全生成。",
            self.mainPage,
        )
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        main_layout.addWidget(subtitle)
        detail = BodyLabel(
            "GUI、CLI、VS Code 和 AI 共用同一个 MCodeService；桌面端不再携带或更新旧模板副本。",
            self.mainPage,
        )
        detail.setAlignment(Qt.AlignCenter)
        detail.setWordWrap(True)
        main_layout.addWidget(detail)
        self.choose_btn = PushButton(FluentIcon.FOLDER, "选择工程目录", self.mainPage)
        self.choose_btn.setFixedWidth(220)
        self.choose_btn.clicked.connect(self.choose_project_folder)
        main_layout.addWidget(self.choose_btn, alignment=Qt.AlignCenter)

        self.addSubInterface(self.mainPage, "mainPage", "代码生成主页")
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.tabBar.tabCloseRequested.connect(self.onCloseTab)

    def _is_project(self, folder_path: str) -> tuple[bool, str]:
        try:
            model = self.mcode.inspect(folder_path)
            return True, f"{model.platform} · {model.mcu or 'MCU 未识别'}"
        except MCodeError as exc:
            return False, str(exc)

    def open_project_from_path(self, folder_path: str) -> None:
        root = Path(folder_path).expanduser().resolve()
        if not root.is_dir():
            InfoBar.error(title="工程不存在", content=f"目录不存在：{root}", parent=self, duration=3000)
            return
        valid, message = self._is_project(str(root))
        if not valid:
            InfoBar.error(title="无法识别工程", content=message, parent=self, duration=5000)
            return
        for index in range(self.stackedWidget.count()):
            widget = self.stackedWidget.widget(index)
            if widget is not None and widget.objectName() == "codeGenPage":
                self.stackedWidget.removeWidget(widget)
                self.tabBar.removeTab(index)
                widget.deleteLater()
                break
        page = CodeGenerateInterface(str(root), self)
        self.addSubInterface(page, "codeGenPage", root.name)
        self.stackedWidget.setCurrentWidget(page)
        self.tabBar.setCurrentTab("codeGenPage")
        InfoBar.success(title="工程已打开", content=message, parent=self, duration=2500)

    def choose_project_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择 MCode 工程目录")
        if folder:
            self.open_project_from_path(folder)

    def addSubInterface(self, widget: QWidget, objectName: str, text: str) -> None:
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.tabBar.addTab(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget),
        )

    def onCurrentIndexChanged(self, index: int) -> None:
        widget = self.stackedWidget.widget(index)
        if widget is not None:
            self.tabBar.setCurrentTab(widget.objectName())

    def onCloseTab(self, index: int) -> None:
        item = self.tabBar.tabItem(index)
        widget = self.findChild(QWidget, item.routeKey())
        if widget is None or widget.objectName() == "mainPage":
            return
        self.stackedWidget.removeWidget(widget)
        self.tabBar.removeTab(index)
        widget.deleteLater()

    def open_fit_tab(self) -> None:
        for index in range(self.stackedWidget.count()):
            widget = self.stackedWidget.widget(index)
            if widget.objectName() == "fitPage":
                self.stackedWidget.setCurrentWidget(widget)
                self.tabBar.setCurrentTab("fitPage")
                return
        page = FunctionFitInterface(self)
        self.addSubInterface(page, "fitPage", "曲线拟合")
        self.stackedWidget.setCurrentWidget(page)
        self.tabBar.setCurrentTab("fitPage")

    def open_ai_tab(self) -> None:
        window = self.window()
        if hasattr(window, "open_ai_workspace"):
            window.open_ai_workspace()
