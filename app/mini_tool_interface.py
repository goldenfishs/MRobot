from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QSizePolicy
from PyQt5.QtCore import Qt
from qfluentwidgets import PushSettingCard, FluentIcon, TabBar

from .function_fit_interface import FunctionFitInterface
from .ai_interface import AIInterface

class MiniToolInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("minitoolInterface")
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setContentsMargins(10, 0, 10, 10) # 设置外边距

        # 顶部标签栏，横向拉伸
        self.tabBar = TabBar(self)
        self.tabBar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.vBoxLayout.addWidget(self.tabBar)  # 移除 Qt.AlignLeft

        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout.addWidget(self.stackedWidget)  # 加入布局


        # 初始主页面
        self.mainPage = QWidget(self)
        mainLayout = QVBoxLayout(self.mainPage)
        mainLayout.setAlignment(Qt.AlignTop)  # 卡片靠顶部
        self.card = PushSettingCard(
            text="▶ 启动",
            icon=FluentIcon.UNIT,
            title="曲线拟合工具",
            content="简单的曲线拟合工具，支持多种函数类型",
        )
        mainLayout.addWidget(self.card)

        self.mainPage.setLayout(mainLayout)
        self.aiCard = PushSettingCard(
            text="▶ 启动",
            icon=FluentIcon.ROBOT,
            title="MRobot AI助手",
            content="与 MRobot 进行图一乐交流, 使用开源模型qwen3:0.6b。",
        )
        mainLayout.addWidget(self.aiCard)
        self.aiCard.clicked.connect(self.open_ai_tab)
        # 添加主页面到堆叠窗口
        self.addSubInterface(self.mainPage, "mainPage", "工具箱主页")

        self.setLayout(self.vBoxLayout)

        # 信号连接
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        # self.tabBar.tabAddRequested.connect(self.onAddNewTab)
        self.tabBar.tabCloseRequested.connect(self.onCloseTab)
        self.card.clicked.connect(self.open_fit_tab)

    def addSubInterface(self, widget: QWidget, objectName: str, text: str):
        widget.setObjectName(objectName)
        self.stackedWidget.addWidget(widget)
        self.tabBar.addTab(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        self.tabBar.setCurrentTab(widget.objectName())

    def onAddNewTab(self):
        pass  # 可自定义添加新标签页逻辑

    def onCloseTab(self, index: int):
        item = self.tabBar.tabItem(index)
        widget = self.findChild(QWidget, item.routeKey())
        # 禁止关闭主页
        if widget.objectName() == "mainPage":
            return
        self.stackedWidget.removeWidget(widget)
        self.tabBar.removeTab(index)
        widget.deleteLater()

    def open_fit_tab(self):
        # 检查是否已存在标签页，避免重复添加
        for i in range(self.stackedWidget.count()):
            widget = self.stackedWidget.widget(i)
            if widget.objectName() == "fitPage":
                self.stackedWidget.setCurrentWidget(widget)
                self.tabBar.setCurrentTab("fitPage")
                return
        fit_page = FunctionFitInterface(self)
        self.addSubInterface(fit_page, "fitPage", "曲线拟合")
        self.stackedWidget.setCurrentWidget(fit_page)
        self.tabBar.setCurrentTab("fitPage")

    def open_ai_tab(self):
        # 检查是否已存在标签页，避免重复添加
        for i in range(self.stackedWidget.count()):
            widget = self.stackedWidget.widget(i)
            if widget.objectName() == "aiPage":
                self.stackedWidget.setCurrentWidget(widget)
                self.tabBar.setCurrentTab("aiPage")
                return
        ai_page = AIInterface(self)
        self.addSubInterface(ai_page, "aiPage", "AI问答")
        self.stackedWidget.setCurrentWidget(ai_page)
        self.tabBar.setCurrentTab("aiPage")
