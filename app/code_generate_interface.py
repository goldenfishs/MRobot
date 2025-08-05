from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QTreeWidget, QTreeWidgetItem, QStackedWidget
from PyQt5.QtCore import Qt
from qfluentwidgets import TitleLabel, BodyLabel, PushButton, TreeWidget, FluentIcon, InfoBar
from app.tools.analyzing_ioc import analyzing_ioc
from app.code_page.bsp_interface import bsp
from app.data_interface import DataInterface

import os
import csv
import sys
import importlib

class CodeGenerateInterface(QWidget):
    def __init__(self, project_path, parent=None):
        super().__init__(parent)
        self.setObjectName("CodeGenerateInterface")
        self.project_path = project_path
        
        # 初始化页面缓存
        self.page_cache = {}

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setContentsMargins(10, 10, 10, 10)

        top_layout = self._create_top_layout()
        main_layout.addLayout(top_layout)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 10, 0, 0)
        main_layout.addLayout(content_layout)

        # 左侧树形列表（使用qfluentwidgets的TreeWidget）
        self.tree = TreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setMaximumWidth(250)
        self.tree.setBorderRadius(8)
        self.tree.setBorderVisible(True)
        content_layout.addWidget(self.tree)

        # 右侧内容区
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)

        self._load_csv_and_build_tree()
        self.tree.itemClicked.connect(self.on_tree_item_clicked)

    def _create_top_layout(self):
        """创建顶部横向布局"""
        top_layout = QHBoxLayout()
        top_layout.setAlignment(Qt.AlignTop)

        # 项目名称标签
        project_name = os.path.basename(self.project_path)
        name_label = BodyLabel(f"项目名称: {project_name}")
        name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        top_layout.addWidget(name_label)

        # FreeRTOS状态标签
        freertos_label = BodyLabel(f"FreeRTOS: {self._get_freertos_status()}")
        freertos_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        top_layout.addWidget(freertos_label)

        # 配置并生成FreeRTOS任务按钮，直接调用已有方法
        freertos_task_btn = PushButton(FluentIcon.SETTING, "配置并生成FreeRTOS任务")
        freertos_task_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        freertos_task_btn.clicked.connect(self.on_task_code_btn_clicked)
        top_layout.addWidget(freertos_task_btn, alignment=Qt.AlignRight)

        # 生成代码按钮
        generate_btn = PushButton(FluentIcon.PROJECTOR,"生成代码")
        generate_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        generate_btn.clicked.connect(self.generate_code)
        top_layout.addWidget(generate_btn, alignment=Qt.AlignRight)

        return top_layout

    def on_task_code_btn_clicked(self):
        # 检查是否开启 FreeRTOS
        ioc_files = [f for f in os.listdir(self.project_path) if f.endswith('.ioc')]
        if ioc_files:
            ioc_path = os.path.join(self.project_path, ioc_files[0])
            if not analyzing_ioc.is_freertos_enabled_from_ioc(ioc_path):
                InfoBar.error(
                    title="错误",
                    content="请先在 .ioc 文件中开启 FreeRTOS，再进行任务配置！",
                    parent=self,
                    duration=3000
                )
                return
        else:
            InfoBar.error(
                title="错误",
                content="未找到 .ioc 文件，无法检测 FreeRTOS 状态！",
                parent=self,
                duration=3000
            )
            return

        # 直接弹出任务配置对话框并生成代码
        dlg = DataInterface()
        dlg.project_path = self.project_path
        result = dlg.open_task_config_dialog()
        # 生成任务成功后弹出 InfoBar 提示
        if getattr(dlg, "task_generate_success", False):
            InfoBar.success(
                title="任务生成成功",
                content="FreeRTOS任务代码已生成！",
                parent=self,
                duration=2000
            )

    def generate_code(self):
        """生成代码逻辑"""
        # 收集所有已加载的页面对象
        pages = []
        for i in range(self.stack.count()):
            widget = self.stack.widget(i)
            pages.append(widget)
        
        # 生成 BSP 代码
        bsp_result = bsp.generate_bsp(self.project_path, pages)
        
        # 生成 Component 代码
        from app.code_page.component_interface import component
        component_result = component.generate_component(self.project_path, pages)
        
        # 合并结果信息
        combined_result = f"BSP代码生成:\n{bsp_result}\n\nComponent代码生成:\n{component_result}"
        
        # 用 InfoBar 在主界面弹出
        InfoBar.success(
            title="代码生成结果",
            content=combined_result,
            parent=self,
            duration=5000  # 增加显示时间，因为内容更多
        )

    def _get_freertos_status(self):
        """获取FreeRTOS状态"""
        ioc_files = [f for f in os.listdir(self.project_path) if f.endswith('.ioc')]
        if ioc_files:
            ioc_path = os.path.join(self.project_path, ioc_files[0])
            return "开启" if analyzing_ioc.is_freertos_enabled_from_ioc(ioc_path) else "未开启"
        return "未找到.ioc文件"

    def _load_csv_and_build_tree(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(script_dir, "../assets/User_code/config.csv")
        csv_path = os.path.abspath(csv_path)
        print(f"加载CSV路径: {csv_path}")
        if not os.path.exists(csv_path):
            print(f"配置文件未找到: {csv_path}")
            return
        self.tree.clear()
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                row = [cell.strip() for cell in row if cell.strip()]
                if not row:
                    continue
                main_title = row[0]
                main_item = QTreeWidgetItem([main_title])
                for sub in row[1:]:
                    sub_item = QTreeWidgetItem([sub])
                    main_item.addChild(sub_item)
                self.tree.addTopLevelItem(main_item)
        self.tree.repaint()

    def on_tree_item_clicked(self, item, column):
        if item.parent():
            main_title = item.parent().text(0)
            sub_title = item.text(0)
            class_name = f"{main_title}_{sub_title}".replace("-", "_")
            widget = self._get_or_create_page(class_name)
            if widget:
                self.stack.setCurrentWidget(widget)

# ...existing code...
    def _get_or_create_page(self, class_name):
        """获取或创建页面"""
        if class_name in self.page_cache:
            return self.page_cache[class_name]
        
        # 如果是第一次创建组件页面，初始化组件管理器
        if not hasattr(self, 'component_manager'):
            from app.code_page.component_interface import ComponentManager
            self.component_manager = ComponentManager()
        
        try:
            if class_name.startswith('bsp_'):
                # BSP页面
                from app.code_page.bsp_interface import get_bsp_page
                # 提取外设名，如 bsp_delay -> delay
                periph_name = class_name[len('bsp_'):].replace("_", " ")
                page = get_bsp_page(periph_name, self.project_path)
            elif class_name.startswith('component_'):
                from app.code_page.component_interface import get_component_page
                comp_name = class_name[len('component_'):].replace("_", " ")
                page = get_component_page(comp_name, self.project_path, self.component_manager)
                self.component_manager.register_component(page.component_name, page)
            else:
                print(f"未知的页面类型: {class_name}")
                return None
            
            self.page_cache[class_name] = page
            self.stack.addWidget(page)
            return page
        except Exception as e:
            print(f"创建页面 {class_name} 失败: {e}")
            return None

# ...existing code...