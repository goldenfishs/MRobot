from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QTreeWidget, QTreeWidgetItem, QStackedWidget
from PyQt5.QtCore import Qt
from qfluentwidgets import TitleLabel, BodyLabel, PushButton, TreeWidget, FluentIcon, InfoBar
from app.tools.analyzing_ioc import analyzing_ioc
from app.code_page.bsp_interface import bsp
from app.data_interface import DataInterface
from app.tools.code_generator import CodeGenerator

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

        # 自动生成FreeRTOS任务按钮
        auto_task_btn = PushButton(FluentIcon.SEND, "配置FreeRTOS")
        auto_task_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        auto_task_btn.clicked.connect(self.on_freertos_task_btn_clicked)
        top_layout.addWidget(auto_task_btn, alignment=Qt.AlignRight)

        # 配置并生成FreeRTOS任务按钮
        freertos_task_btn = PushButton(FluentIcon.SETTING, "创建任务")
        freertos_task_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        freertos_task_btn.clicked.connect(self.on_task_code_btn_clicked)
        top_layout.addWidget(freertos_task_btn, alignment=Qt.AlignRight)

        # 配置cmake按钮
        cmake_btn = PushButton(FluentIcon.FOLDER, "配置cmake")
        cmake_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        cmake_btn.clicked.connect(self.on_cmake_config_btn_clicked)
        top_layout.addWidget(cmake_btn, alignment=Qt.AlignRight)

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

    def on_freertos_task_btn_clicked(self):
        # 检查是否开启 FreeRTOS
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

        # 自动生成FreeRTOS任务代码
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

    def on_cmake_config_btn_clicked(self):
        """配置cmake，自动更新CMakeLists.txt中的源文件列表"""
        try:
            from app.tools.update_cmake_sources import find_user_c_files, update_cmake_sources,update_cmake_includes
            from pathlib import Path
            
            # 构建User目录和CMakeLists.txt路径，规范化路径分隔符
            user_dir = os.path.normpath(os.path.join(self.project_path, "User"))
            cmake_file = os.path.normpath(os.path.join(self.project_path, "CMakeLists.txt"))
            
            print(f"项目路径: {self.project_path}")
            print(f"User目录路径: {user_dir}")
            print(f"CMakeLists.txt路径: {cmake_file}")
            
            # 检查User目录是否存在
            if not os.path.exists(user_dir):
                InfoBar.error(
                    title="错误",
                    content=f"User目录不存在: {user_dir}",
                    parent=self,
                    duration=3000
                )
                return
            
            # 检查CMakeLists.txt是否存在
            if not os.path.exists(cmake_file):
                InfoBar.error(
                    title="错误", 
                    content=f"CMakeLists.txt文件不存在: {cmake_file}",
                    parent=self,
                    duration=3000
                )
                return
            
            # 查找User目录下的所有.c文件
            print("开始查找.c文件...")
            c_files = find_user_c_files(user_dir)
            print(f"找到 {len(c_files)} 个.c文件")
            
            if not c_files:
                InfoBar.warning(
                    title="警告",
                    content="在User目录下没有找到.c文件",
                    parent=self,
                    duration=3000
                )
                return
            
            # 更新CMakeLists.txt
            print("开始更新CMakeLists.txt...")
            sources_success = update_cmake_sources(cmake_file, c_files)
            includes_success = update_cmake_includes(cmake_file, user_dir)
            
            if sources_success and includes_success:
                InfoBar.success(
                    title="配置成功",
                    content=f"已成功更新CMakeLists.txt，共添加了 {len(c_files)} 个源文件",
                    parent=self,
                    duration=3000
                )
            elif sources_success:
                InfoBar.warning(
                    title="部分成功",
                    content=f"源文件更新成功，但include路径更新失败",
                    parent=self,
                    duration=3000
                )
            elif includes_success:
                InfoBar.warning(
                    title="部分成功", 
                    content=f"include路径更新成功，但源文件更新失败",
                    parent=self,
                    duration=3000
                )
            else:
                InfoBar.error(
                    title="配置失败",
                    content="更新CMakeLists.txt失败，请检查文件格式",
                    parent=self,
                    duration=3000
                )
                
        except ImportError as e:
            print(f"导入错误: {e}")
            InfoBar.error(
                title="导入错误",
                content=f"无法导入cmake配置模块: {str(e)}",
                parent=self,
                duration=3000
            )
        except Exception as e:
            print(f"cmake配置错误: {e}")
            import traceback
            traceback.print_exc()
            InfoBar.error(
                title="配置失败",
                content=f"cmake配置过程中出现错误: {str(e)}",
                parent=self,
                duration=3000
            )



    def generate_code(self):
        """生成所有代码，包括未加载页面"""
        try:
            # 先收集所有页面名（从CSV配置文件读取）
            from app.tools.code_generator import CodeGenerator  # 在方法内重新导入确保可用
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


    def _get_freertos_status(self):
        """获取FreeRTOS状态"""
        ioc_files = [f for f in os.listdir(self.project_path) if f.endswith('.ioc')]
        if ioc_files:
            ioc_path = os.path.join(self.project_path, ioc_files[0])
            return "开启" if analyzing_ioc.is_freertos_enabled_from_ioc(ioc_path) else "未开启"
        return "未找到.ioc文件"

    def _load_csv_and_build_tree(self):
        from app.tools.code_generator import CodeGenerator  # 在方法内重新导入确保可用
        csv_path = os.path.join(CodeGenerator.get_assets_dir("User_code"), "config.csv")
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
                # 提取外设名，如 bsp_error_detect -> error_detect
                periph_name = class_name[len('bsp_'):]  # 移除 .replace("_", " ")
                page = get_bsp_page(periph_name, self.project_path)
            elif class_name.startswith('component_'):
                from app.code_page.component_interface import get_component_page
                comp_name = class_name[len('component_'):]  # 移除 .replace("_", " ")
                page = get_component_page(comp_name, self.project_path, self.component_manager)
                self.component_manager.register_component(page.component_name, page)
            elif class_name.startswith('device_'):
                # Device页面
                from app.code_page.device_interface import get_device_page
                device_name = class_name[len('device_'):]  # 移除 device_ 前缀
                page = get_device_page(device_name, self.project_path)
            else:
                print(f"未知的页面类型: {class_name}")
                return None
            
            self.page_cache[class_name] = page
            self.stack.addWidget(page)
            return page
        except Exception as e:
            print(f"创建页面 {class_name} 失败: {e}")
            return None