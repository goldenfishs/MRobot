from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QSizePolicy
from PyQt5.QtCore import Qt
from qfluentwidgets import PushSettingCard, FluentIcon, TabBar
from qfluentwidgets import TitleLabel, BodyLabel, PushButton, FluentIcon
from PyQt5.QtWidgets import QFileDialog, QDialog, QHBoxLayout
from qfluentwidgets import ComboBox, PrimaryPushButton, SubtitleLabel
import os
import shutil
import tempfile
from .function_fit_interface import FunctionFitInterface
from .ai_interface import AIInterface
from qfluentwidgets import InfoBar
from .tools.update_code import update_code
from .code_generate_interface import CodeGenerateInterface

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
        mainLayout.setSpacing(28) # 设置间距
        mainLayout.setContentsMargins(48, 48, 48, 48) # 设置内容边距

        #添加空行
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

        self.preset_ioc_btn = PushButton(FluentIcon.LIBRARY, "获取预设IOC")
        self.preset_ioc_btn.setFixedWidth(200)
        mainLayout.addWidget(self.preset_ioc_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        mainLayout.addSpacing(10)
        mainLayout.addStretch()

        # 添加主页面到堆叠窗口
        self.addSubInterface(self.mainPage, "mainPage", "代码生成主页")

        self.setLayout(self.vBoxLayout)

        # 信号连接
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.tabBar.tabCloseRequested.connect(self.onCloseTab)
        self.choose_btn.clicked.connect(self.choose_project_folder)  # 启用选择项目路径按钮
        self.update_template_btn.clicked.connect(self.on_update_template)
        self.preset_ioc_btn.clicked.connect(self.use_preset_ioc)  # 启用预设工程按钮


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

    def get_preset_ioc_files(self):
        """获取预设的ioc文件列表"""
        try:
            preset_ioc_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "User_code", "ioc")
            if not os.path.exists(preset_ioc_dir):
                return []
            
            ioc_files = []
            for filename in os.listdir(preset_ioc_dir):
                if filename.endswith('.ioc'):
                    ioc_files.append({
                        'name': os.path.splitext(filename)[0],
                        'filename': filename,
                        'path': os.path.join(preset_ioc_dir, filename)
                    })
            return ioc_files
        except Exception as e:
            print(f"获取预设ioc文件失败: {e}")
            return []

    def use_preset_ioc(self):
        """使用预设ioc文件"""
        preset_files = self.get_preset_ioc_files()
        if not preset_files:
            InfoBar.warning(
                title="无预设工程",
                content="未找到可用的预设工程文件",
                parent=self,
                duration=2000
            )
            return

        # 创建选择对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("获取预设IOC")
        dialog.resize(400, 200)
        dialog.setModal(True)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 标题
        title_label = SubtitleLabel("选择要使用的IOC模版")
        layout.addWidget(title_label)

        # 选择下拉框
        select_layout = QHBoxLayout()
        select_label = BodyLabel("预设IOC：")
        preset_combo = ComboBox()
        
        # 修复ComboBox数据问题
        for i, preset in enumerate(preset_files):
            preset_combo.addItem(preset['name'])
        
        select_layout.addWidget(select_label)
        select_layout.addWidget(preset_combo)
        layout.addLayout(select_layout)

        layout.addSpacing(16)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = PushButton("取消")
        ok_btn = PrimaryPushButton("保存到")
        
        cancel_btn.clicked.connect(dialog.reject)
        ok_btn.clicked.connect(dialog.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

        # 显示对话框
        if dialog.exec() == QDialog.Accepted:
            selected_index = preset_combo.currentIndex()
            if selected_index >= 0 and selected_index < len(preset_files):
                selected_preset = preset_files[selected_index]
                self.save_preset_template(selected_preset)

    def save_preset_template(self, preset_info):
        """保存预设模板到用户指定位置"""
        try:
            # 让用户选择保存位置
            save_dir = QFileDialog.getExistingDirectory(
                self, 
                f"选择保存 {preset_info['name']} 模板的位置",
                os.path.expanduser("~")
            )
            
            if not save_dir:
                return
            
            # 复制ioc文件到用户选择的目录
            target_path = os.path.join(save_dir, preset_info['filename'])
            
            # 检查目标文件是否已存在
            if os.path.exists(target_path):
                from qfluentwidgets import Dialog
                dialog = Dialog("文件已存在", f"目标位置已存在 {preset_info['filename']}，是否覆盖？", self)
                if dialog.exec() != Dialog.Accepted:
                    return
            
            # 复制文件
            shutil.copy2(preset_info['path'], target_path)
            
            InfoBar.success(
                title="模板保存成功",
                content=f"预设模板 {preset_info['name']} 已保存到:\n{target_path}",
                parent=self,
                duration=3000
            )
                
        except Exception as e:
            InfoBar.error(
                title="保存失败",
                content=f"保存预设模板失败: {str(e)}",
                parent=self,
                duration=3000
            )

    def open_project_from_path(self, folder_path):
        """从指定路径打开工程"""
        try:
            if not os.path.exists(folder_path):
                return
                
            ioc_files = [f for f in os.listdir(folder_path) if f.endswith('.ioc')]
            if ioc_files:
                # 检查是否已存在 codeGenPage 标签页
                for i in range(self.stackedWidget.count()):
                    widget = self.stackedWidget.widget(i)
                    if widget is not None and widget.objectName() == "codeGenPage":
                        # 如果已存在，则切换到该标签页，并更新路径显示
                        if hasattr(widget, "project_path"):
                            widget.project_path = folder_path
                            if hasattr(widget, "refresh"):
                                widget.refresh()
                        self.stackedWidget.setCurrentWidget(widget)
                        self.tabBar.setCurrentTab("codeGenPage")
                        return
                
                # 不存在则新建
                code_gen_page = CodeGenerateInterface(folder_path, self)
                self.addSubInterface(code_gen_page, "codeGenPage", "代码生成")
                self.stackedWidget.setCurrentWidget(code_gen_page)
                self.tabBar.setCurrentTab("codeGenPage")
            else:
                InfoBar.error(
                    title="未找到.ioc文件",
                    content="所选文件夹不是有效的CUBEMX工程目录",
                    parent=self,
                    duration=3000
                )
        except Exception as e:
            InfoBar.error(
                title="打开工程失败",
                content=f"打开工程失败: {str(e)}",
                parent=self,
                duration=3000
            )

    def choose_project_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择CUBEMX工程目录")
        if not folder:
            return
        ioc_files = [f for f in os.listdir(folder) if f.endswith('.ioc')]
        if ioc_files:
            # 检查是否已存在 codeGenPage 标签页
            for i in range(self.stackedWidget.count()):
                widget = self.stackedWidget.widget(i)
                if widget is not None and widget.objectName() == "codeGenPage":
                    # 如果已存在，则切换到该标签页，并更新路径显示
                    if hasattr(widget, "project_path"):
                        widget.project_path = folder
                        if hasattr(widget, "refresh"):
                            widget.refresh()
                    self.stackedWidget.setCurrentWidget(widget)
                    self.tabBar.setCurrentTab("codeGenPage")
                    return
            # 不存在则新建
            code_gen_page = CodeGenerateInterface(folder, self)
            self.addSubInterface(code_gen_page, "codeGenPage", "代码生成")
            self.stackedWidget.setCurrentWidget(code_gen_page)
            self.tabBar.setCurrentTab("codeGenPage")
        else:
            InfoBar.error(
                title="未找到.ioc文件",
                content="所选文件夹不是有效的CUBEMX工程目录，请重新选择。",
                parent=self,
                duration=3000
            )


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
