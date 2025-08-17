from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QTreeWidget, QTreeWidgetItem, QStackedWidget
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from qfluentwidgets import TitleLabel, BodyLabel, PushButton, TreeWidget, FluentIcon, InfoBar
from app.tools.analyzing_ioc import analyzing_ioc
from app.code_page.bsp_interface import bsp
from app.data_interface import DataInterface
<<<<<<< HEAD
from app.code_page.bsp_interface import bsp
from app.code_page.component_interface import component
from app.code_page.device_interface import device
=======
from app.tools.code_generator import CodeGenerator
>>>>>>> temp-merge-branch

import os
import csv
import sys
import importlib

def resource_path(relative_path):
    """获取资源文件的绝对路径，兼容打包和开发环境"""
    try:
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
            return os.path.join(base_path, relative_path)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        while current_dir != os.path.dirname(current_dir):
            if os.path.basename(current_dir) == 'MRobot':
                break
            current_dir = os.path.dirname(current_dir)
        return os.path.join(current_dir, relative_path)
    except Exception as e:
        print(f"资源路径获取失败: {e}")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "..", relative_path)

class CodeGenerateThread(QThread):
    finished = pyqtSignal(str, str)  # (状态, 信息)

    def __init__(self, project_path, page_cache, component_manager, stack):
        super().__init__()
        self.project_path = project_path
        self.page_cache = page_cache
        self.component_manager = component_manager
        self.stack = stack

    def run(self):
        try:
            csv_path = resource_path("assets/User_code/config.csv")
            csv_path = os.path.abspath(csv_path)
            if not os.path.exists(csv_path):
                self.finished.emit("error", f"未找到配置文件: {csv_path}")
                return
            all_class_names = []
            try:
                with open(csv_path, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        row = [cell.strip() for cell in row if cell.strip()]
                        if not row:
                            continue
                        main_title = row[0]
                        for sub in row[1:]:
                            class_name = f"{main_title}_{sub}".replace("-", "_")
                            all_class_names.append(class_name)
            except Exception as e:
                self.finished.emit("error", f"读取配置文件时出错: {str(e)}")
                return

            try:
                test_file = os.path.join(self.project_path, "test_write_permission.tmp")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
            except Exception as e:
                self.finished.emit("error", f"无法写入项目目录，请检查权限: {str(e)}")
                return

            try:
                from app.code_page.bsp_interface import get_bsp_page
                from app.code_page.component_interface import get_component_page, ComponentManager
                from app.code_page.device_interface import get_device_page
            except Exception as e:
                self.finished.emit("error", f"模块导入失败: {str(e)}")
                return

            if not self.component_manager:
                self.component_manager = ComponentManager()

            bsp_pages = []
            component_pages = []
            device_pages = []

            for class_name in all_class_names:
                page = None
                try:
                    if class_name in self.page_cache:
                        page = self.page_cache[class_name]
                    else:
                        if class_name.startswith('bsp_'):
                            periph_name = class_name[len('bsp_'):]
                            page = get_bsp_page(periph_name, self.project_path)
                        elif class_name.startswith('component_'):
                            comp_name = class_name[len('component_'):]
                            page = get_component_page(comp_name, self.project_path, self.component_manager)
                            if page and hasattr(page, 'component_name'):
                                self.component_manager.register_component(page.component_name, page)
                        elif class_name.startswith('device_'):
                            device_name = class_name[len('device_'):]
                            page = get_device_page(device_name, self.project_path)
                        if page:
                            self.page_cache[class_name] = page
                            self.stack.addWidget(page)
                except Exception:
                    continue
                if page:
                    if hasattr(page, '_generate_bsp_code_internal') and page not in bsp_pages:
                        bsp_pages.append(page)
                    elif hasattr(page, '_generate_component_code_internal') and page not in component_pages:
                        component_pages.append(page)
                    elif hasattr(page, '_generate_device_code_internal') and page not in device_pages:
                        device_pages.append(page)

            try:
                bsp_result = bsp.generate_bsp(self.project_path, bsp_pages) if bsp_pages else ""
            except Exception:
                bsp_result = ""
            try:
                component_result = component.generate_component(self.project_path, component_pages) if component_pages else ""
            except Exception:
                component_result = ""
            try:
                device_result = device.generate_device(self.project_path, device_pages) if device_pages else ""
            except Exception:
                device_result = ""

            if not bsp_result and not component_result and not device_result:
                self.finished.emit("warning", "未生成任何代码，请检查是否启用了相关模块！")
                return

            results = []
            if bsp_result:
                results.append(f"BSP: {bsp_result}")
            if component_result:
                results.append(f"Component: {component_result}")
            if device_result:
                results.append(f"Device: {device_result}")
            combined_result = "\n".join(results)
            self.finished.emit("success", combined_result)
        except Exception as e:
            self.finished.emit("error", f"代码生成过程中出现错误: {str(e)}")

class CodeGenerateInterface(QWidget):
    def __init__(self, project_path, parent=None):
        super().__init__(parent)
        self.setObjectName("CodeGenerateInterface")
        self.project_path = project_path
        self.page_cache = {}
        self.component_manager = None
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
        self.tree = TreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setMaximumWidth(250)
        self.tree.setBorderRadius(8)
        self.tree.setBorderVisible(True)
        content_layout.addWidget(self.tree)
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)
        self._load_csv_and_build_tree()
        self.tree.itemClicked.connect(self.on_tree_item_clicked)

    def _create_top_layout(self):
        top_layout = QHBoxLayout()
        top_layout.setAlignment(Qt.AlignTop)
        project_name = os.path.basename(self.project_path)
        name_label = BodyLabel(f"项目名称: {project_name}")
        name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        top_layout.addWidget(name_label)
        freertos_label = BodyLabel(f"FreeRTOS: {self._get_freertos_status()}")
        freertos_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        top_layout.addWidget(freertos_label)
        auto_task_btn = PushButton(FluentIcon.SEND, "自动生成FreeRTOS任务")
        auto_task_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        auto_task_btn.clicked.connect(self.on_freertos_task_btn_clicked)
        top_layout.addWidget(auto_task_btn, alignment=Qt.AlignRight)
        freertos_task_btn = PushButton(FluentIcon.SETTING, "配置并生成FreeRTOS任务")
        freertos_task_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        freertos_task_btn.clicked.connect(self.on_task_code_btn_clicked)
        top_layout.addWidget(freertos_task_btn, alignment=Qt.AlignRight)
        self.generate_btn = PushButton(FluentIcon.PROJECTOR,"生成代码")
        self.generate_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.generate_btn.clicked.connect(self.generate_code)
        top_layout.addWidget(self.generate_btn, alignment=Qt.AlignRight)
        return top_layout

    def on_task_code_btn_clicked(self):
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
        dlg = DataInterface()
        dlg.project_path = self.project_path
        result = dlg.open_task_config_dialog()
        if getattr(dlg, "task_generate_success", False):
            InfoBar.success(
                title="任务生成成功",
                content="FreeRTOS任务代码已生成！",
                parent=self,
                duration=2000
            )

    def on_freertos_task_btn_clicked(self):
        ioc_files = [f for f in os.listdir(self.project_path) if f.endswith('.ioc')]
        if ioc_files:
            ioc_path = os.path.join(self.project_path, ioc_files[0])
            if not analyzing_ioc.is_freertos_enabled_from_ioc(ioc_path):
                InfoBar.error(
                    title="错误",
                    content="请先在 .ioc 文件中开启 FreeRTOS，再自动生成任务！",
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
        from app.data_interface import DataInterface
        di = DataInterface()
        di.project_path = self.project_path
        di.generate_freertos_task()
        InfoBar.success(
            title="自动生成成功",
            content="FreeRTOS任务代码已自动生成！",
            parent=self,
            duration=2000
        )

<<<<<<< HEAD
=======


    def generate_code(self):
        """生成所有代码，包括未加载页面"""
        try:
            # 先收集所有页面名（从CSV配置文件读取）
            csv_path = os.path.join(CodeGenerator.get_assets_dir("User_code"), "config.csv")
            all_class_names = []
            if os.path.exists(csv_path):
                with open(csv_path, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        row = [cell.strip() for cell in row if cell.strip()]
                        if not row:
                            continue
                        main_title = row[0]
                        for sub in row[1:]:
                            class_name = f"{main_title}_{sub}".replace("-", "_")
                            all_class_names.append(class_name)

            # 创建所有页面对象（无论是否点击过）
            bsp_pages = []
            component_pages = []
            device_pages = []
            for class_name in all_class_names:
                widget = self._get_or_create_page(class_name)
                if widget:
                    if hasattr(widget, '_generate_bsp_code_internal') and widget not in bsp_pages:
                        bsp_pages.append(widget)
                    elif hasattr(widget, '_generate_component_code_internal') and widget not in component_pages:
                        component_pages.append(widget)
                    elif hasattr(widget, '_generate_device_code_internal') and widget not in device_pages:
                        device_pages.append(widget)

            # 确保导入成功
            from app.code_page.bsp_interface import bsp
            from app.code_page.component_interface import component
            from app.code_page.device_interface import device

            # 生成 BSP 代码
            bsp_result = bsp.generate_bsp(self.project_path, bsp_pages)

            # 生成 Component 代码  
            component_result = component.generate_component(self.project_path, component_pages)

            # 生成 Device 代码
            device_result = device.generate_device(self.project_path, device_pages)

            # 合并结果信息
            combined_result = f"BSP代码生成:\n{bsp_result}\n\nComponent代码生成:\n{component_result}\n\nDevice代码生成:\n{device_result}"

            InfoBar.success(
                title="代码生成结果",
                content=combined_result,
                parent=self,
                duration=5000
            )

        except ImportError as e:
            InfoBar.error(
                title="导入错误", 
                content=f"模块导入失败: {str(e)}",
                parent=self,
                duration=3000
            )
        except Exception as e:
            InfoBar.error(
                title="生成失败",
                content=f"代码生成过程中出现错误: {str(e)}",
                parent=self,
                duration=3000
            )


>>>>>>> temp-merge-branch
    def _get_freertos_status(self):
        ioc_files = [f for f in os.listdir(self.project_path) if f.endswith('.ioc')]
        if ioc_files:
            ioc_path = os.path.join(self.project_path, ioc_files[0])
            return "开启" if analyzing_ioc.is_freertos_enabled_from_ioc(ioc_path) else "未开启"
        return "未找到.ioc文件"

    def _load_csv_and_build_tree(self):
<<<<<<< HEAD
        csv_path = resource_path("assets/User_code/config.csv")
        csv_path = os.path.abspath(csv_path)
=======
        csv_path = os.path.join(CodeGenerator.get_assets_dir("User_code"), "config.csv")
>>>>>>> temp-merge-branch
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

    def generate_code(self):
        self.generate_btn.setEnabled(False)
        self.thread = CodeGenerateThread(self.project_path, self.page_cache, self.component_manager, self.stack)
        self.thread.finished.connect(self.on_code_generate_finished)
        self.thread.start()

    def on_code_generate_finished(self, status, msg):
        self.generate_btn.setEnabled(True)
        if status == "success":
            InfoBar.success(title="代码生成成功", content=msg, parent=self, duration=5000)
        elif status == "warning":
            InfoBar.warning(title="无代码生成", content=msg, parent=self, duration=3000)
        else:
            InfoBar.error(title="生成失败", content=msg, parent=self, duration=3000)

    def _get_or_create_page(self, class_name):
        if class_name in self.page_cache:
            return self.page_cache[class_name]
        try:
            from app.code_page.bsp_interface import get_bsp_page
            from app.code_page.component_interface import get_component_page, ComponentManager
            from app.code_page.device_interface import get_device_page
            page = None
            if class_name.startswith('bsp_'):
                periph_name = class_name[len('bsp_'):]
                page = get_bsp_page(periph_name, self.project_path)
            elif class_name.startswith('component_'):
                comp_name = class_name[len('component_'):]
                if not self.component_manager:
                    self.component_manager = ComponentManager()
                page = get_component_page(comp_name, self.project_path, self.component_manager)
                if page and hasattr(page, 'component_name'):
                    self.component_manager.register_component(page.component_name, page)
            elif class_name.startswith('device_'):
                device_name = class_name[len('device_'):]
                page = get_device_page(device_name, self.project_path)
            if page:
                self.page_cache[class_name] = page
                self.stack.addWidget(page)
            return page
        except Exception as e:
            print(f"创建页面 {class_name} 失败: {e}")
            return None