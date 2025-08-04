from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QSizePolicy
from PyQt5.QtCore import Qt
from qfluentwidgets import PushSettingCard, FluentIcon, TabBar
from qfluentwidgets import TitleLabel, BodyLabel, PushButton, FluentIcon

from .function_fit_interface import FunctionFitInterface
from .ai_interface import AIInterface
from qfluentwidgets import InfoBar
from .tools.update_code import update_code

class CodeConfigurationInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CodeConfigurationInterface")
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setContentsMargins(10, 0, 10, 10) # 设置外边距

        # 顶部标签栏，横向拉伸
        self.tabBar = TabBar(self)
        self.tabBar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.vBoxLayout.addWidget(self.tabBar)

        self.stackedWidget = QStackedWidget(self)
        self.vBoxLayout.addWidget(self.stackedWidget)

        # 初始主页面
        self.mainPage = QWidget(self)
        mainLayout = QVBoxLayout(self.mainPage)
        mainLayout.setAlignment(Qt.AlignTop)
        mainLayout.setSpacing(28)
        mainLayout.setContentsMargins(48, 48, 48, 48)

        title = TitleLabel("MRobot 代码生成")
        title.setAlignment(Qt.AlignCenter)
        mainLayout.addWidget(title)

        subtitle = BodyLabel("请选择您的由CUBEMX生成的工程路径（.ico所在的目录），然后开启代码之旅！")
        subtitle.setAlignment(Qt.AlignCenter)
        mainLayout.addWidget(subtitle)

        desc = BodyLabel("支持自动配置和生成任务，自主选择模块代码倒入，自动识别cubemx配置！")
        desc.setAlignment(Qt.AlignCenter)
        mainLayout.addWidget(desc)

        mainLayout.addSpacing(18)

        self.choose_btn = PushButton(FluentIcon.FOLDER, "选择项目路径")
        self.choose_btn.setFixedWidth(200)
        mainLayout.addWidget(self.choose_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.update_template_btn = PushButton(FluentIcon.SYNC, "更新代码库")
        self.update_template_btn.setFixedWidth(200)
        mainLayout.addWidget(self.update_template_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        mainLayout.addSpacing(10)
        mainLayout.addStretch()

        # 添加主页面到堆叠窗口
        self.addSubInterface(self.mainPage, "mainPage", "代码生成主页")

        self.setLayout(self.vBoxLayout)

        # 信号连接
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.tabBar.tabCloseRequested.connect(self.onCloseTab)
        # 你可以在此处连接按钮的槽函数
        # self.choose_btn.clicked.connect(self.choose_project_folder)
        self.update_template_btn.clicked.connect(self.on_update_template)

    def on_update_template(self):
        def info(parent):
            InfoBar.success(
                title="更新成功",
                content="用户模板已更新到最新版本！",
                parent=parent,
                duration=2000
            )
        def error(parent, msg):
            InfoBar.error(
                title="更新失败",
                content=f"用户模板更新失败: {msg}",
                parent=parent,
                duration=3000
            )
        update_code(parent=self, info_callback=info, error_callback=error)

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
