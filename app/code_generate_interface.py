from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QTreeWidget, QTreeWidgetItem, QStackedWidget
from PyQt5.QtCore import Qt
from qfluentwidgets import TitleLabel, BodyLabel, PushButton
from app.tools.analyzing_ioc import analyzing_ioc
from app.code_page.bsp_interface import bsp

import os
import csv
import importlib

class CodeGenerateInterface(QWidget):
    def __init__(self, project_path, parent=None):
        super().__init__(parent)
        self.setObjectName("CodeGenerateInterface")
        self.project_path = project_path

        self._init_ui()

    def _init_ui(self):
        """初始化界面布局"""
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        main_layout.setContentsMargins(10, 10, 10, 10)

        top_layout = self._create_top_layout()
        main_layout.addLayout(top_layout)

        # 下方主区域，左右分栏
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 10, 0, 0)
        main_layout.addLayout(content_layout)

        # 左侧树形列表
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setMaximumWidth(250)
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

        # 生成代码按钮
        generate_btn = PushButton("Generate Code")
        generate_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        generate_btn.clicked.connect(self.generate_code)
        top_layout.addWidget(generate_btn, alignment=Qt.AlignRight)

        return top_layout

    def generate_code(self):
        """生成代码逻辑"""
        # 收集所有已加载的页面对象
        pages = []
        for i in range(self.stack.count()):
            widget = self.stack.widget(i)
            pages.append(widget)
        bsp.generate_bsp(self.project_path, pages)
        # component.generate_component(self.project_path)
        # device.generate_device(self.project_path)


    def _get_freertos_status(self):
        """获取FreeRTOS状态"""
        ioc_files = [f for f in os.listdir(self.project_path) if f.endswith('.ioc')]
        if ioc_files:
            ioc_path = os.path.join(self.project_path, ioc_files[0])
            return "开启" if analyzing_ioc.is_freertos_enabled_from_ioc(ioc_path) else "未开启"
        return "未找到.ioc文件"

    def _load_csv_and_build_tree(self):
        # 获取脚本目录
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

    def _get_or_create_page(self, class_name):
        for i in range(self.stack.count()):
            w = self.stack.widget(i)
            if w.objectName() == class_name:
                return w
        try:
            module_name = f"app.code_page.{class_name.split('_')[0]}_interface"
            module = importlib.import_module(module_name)
            cls = getattr(module, class_name)
            widget = cls(self.project_path)
            widget.setObjectName(class_name)
            self.stack.addWidget(widget)
            print(f"加载页面类: {class_name} 来自模块: {module_name}")
            return widget
        except Exception as e:
            # 自动识别通用外设页面
            from app.code_page.bsp_interface import BspSimplePeripheral
            peripheral_name = class_name.split('_')[1] if '_' in class_name else class_name
            # 模板文件名自动推断
            template_names = {
                'header': f"{peripheral_name.lower()}.h",
                'source': f"{peripheral_name.lower()}.c"
            }
            widget = BspSimplePeripheral(self.project_path, peripheral_name, template_names)
            widget.setObjectName(class_name)
            self.stack.addWidget(widget)
            print(f"自动加载通用外设页面: {class_name}")
            return widget