from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QCheckBox, QComboBox, QTableWidget, QHeaderView, QMessageBox, QHBoxLayout, QTextEdit
from qfluentwidgets import TitleLabel, BodyLabel, PushButton, CheckBox, TableWidget, LineEdit, ComboBox, MessageBox, SubtitleLabel, FluentIcon, TextEdit
from qfluentwidgets import InfoBar
from PyQt5.QtCore import Qt, pyqtSignal
from app.tools.code_generator import CodeGenerator
import os
import shutil


def get_component_page(component_name, project_path, component_manager=None):
    """根据组件名返回对应的页面类，没有特殊类则返回默认ComponentSimple"""
    name_lower = component_name.lower()
    special_classes = {
        "pid": component_pid,
        "filter": component_filter,
        # 以后可以继续添加特殊组件
    }
    if name_lower in special_classes:
        return special_classes[name_lower](project_path, component_manager)
    else:
        template_names = {
            'header': f'{name_lower}.h',
            'source': f'{name_lower}.c'
        }
        return ComponentSimple(project_path, component_name, template_names, component_manager)



def get_all_dependency_components(dependencies):
    """获取所有被依赖的组件列表"""
    dependent_components = set()
    for component, deps in dependencies.items():
        for dep_path in deps:
            dep_name = os.path.basename(dep_path)
            dependent_components.add(dep_name.lower())
    return dependent_components


class ComponentSimple(QWidget):
    """简单组件界面 - 只有开启/关闭功能"""
    def __init__(self, project_path, component_name, template_names, component_manager=None):
        super().__init__()
        self.project_path = project_path
        self.component_name = component_name
        self.template_names = template_names
        self.component_manager = component_manager
        
        # 加载描述和依赖信息
        component_dir = CodeGenerator.get_assets_dir("User_code/component")
        describe_path = os.path.join(component_dir, "describe.csv")
        dependencies_path = os.path.join(component_dir, "dependencies.csv")
        self.descriptions = CodeGenerator.load_descriptions(describe_path)
        self.dependencies = CodeGenerator.load_dependencies(dependencies_path)
        
        self._init_ui()
        self._load_config()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        top_layout.setAlignment(Qt.AlignVCenter)
        self.generate_checkbox = CheckBox(f"启用 {self.component_name}")
        self.generate_checkbox.stateChanged.connect(self._on_checkbox_changed)
        top_layout.addWidget(self.generate_checkbox, alignment=Qt.AlignLeft)
        top_layout.addStretch()
        title = SubtitleLabel(f"{self.component_name} 配置             ")
        title.setAlignment(Qt.AlignHCenter)
        top_layout.addWidget(title, alignment=Qt.AlignHCenter)
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        desc = self.descriptions.get(self.component_name.lower(), "")
        if desc:
            desc_label = BodyLabel(f"功能说明：{desc}")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
        
        deps = self.dependencies.get(self.component_name.lower(), [])
        if deps:
            deps_text = f"依赖组件：{', '.join([os.path.basename(dep) for dep in deps])}"
            deps_label = BodyLabel(deps_text)
            deps_label.setWordWrap(True)
            deps_label.setStyleSheet("color: #888888;")
            layout.addWidget(deps_label)
            # 不再自动启用依赖，只做提示
        
        layout.addStretch()
    
    def _on_checkbox_changed(self, state):
        pass  # 不再自动启用依赖
    
    def is_need_generate(self):
        return self.generate_checkbox.isChecked()
    
    def get_enabled_dependencies(self):
        if not self.is_need_generate():
            return []
        return self.dependencies.get(self.component_name.lower(), [])
    
    def _generate_component_code_internal(self):
        # 检查是否需要生成
        if not self.is_need_generate():
            # 如果未勾选，检查文件是否已存在，如果存在则跳过
            for filename in self.template_names.values():
                output_path = os.path.join(self.project_path, f"User/component/{filename}")
                if os.path.exists(output_path):
                    return "skipped"  # 返回特殊值表示跳过
            return "not_needed"  # 返回特殊值表示不需要生成
        
        template_dir = self._get_component_template_dir()
        for key, filename in self.template_names.items():
            template_path = os.path.join(template_dir, filename)
            template_content = CodeGenerator.load_template(template_path)
            if not template_content:
                print(f"模板文件不存在或为空: {template_path}")
                continue
            output_path = os.path.join(self.project_path, f"User/component/{filename}")
            CodeGenerator.save_with_preserve(output_path, template_content)
        self._save_config()
        return True
    
    def _get_component_template_dir(self):
        return CodeGenerator.get_assets_dir("User_code/component")
    
    def _save_config(self):
        config_path = os.path.join(self.project_path, "User/component/component_config.yaml")
        config_data = CodeGenerator.load_config(config_path)
        config_data[self.component_name.lower()] = {
            'enabled': self.is_need_generate(),
            'dependencies': self.dependencies.get(self.component_name.lower(), [])
        }
        CodeGenerator.save_config(config_data, config_path)
    
    def _load_config(self):
        config_path = os.path.join(self.project_path, "User/component/component_config.yaml")
        config_data = CodeGenerator.load_config(config_path)
        conf = config_data.get(self.component_name.lower(), {})
        if conf.get('enabled', False):
            self.generate_checkbox.setChecked(True)

class ComponentManager:
    """组件依赖管理器"""
    
    def __init__(self):
        self.component_pages = {}  # 组件名 -> 页面对象
    
    def register_component(self, component_name, page):
        """注册组件页面"""
        self.component_pages[component_name.lower()] = page
    
    def _sync_dependency_states(self):
        """同步所有依赖状态"""
        # 重新计算所有依赖计数
        new_dependency_count = {}
        
        for page_name, page in self.component_pages.items():
            if page.is_need_generate():
                deps = page.get_enabled_dependencies()
                for dep_path in deps:
                    dep_name = os.path.basename(dep_path).lower()
                    new_dependency_count[dep_name] = new_dependency_count.get(dep_name, 0) + 1
        
        # 更新依赖计数
        self.dependency_count = new_dependency_count
        
        # 更新所有页面的状态
        for page_name, page in self.component_pages.items():
            if page.is_dependency:
                count = self.dependency_count.get(page_name, 0)
                page.set_dependency_count(count)
    
    def enable_dependencies(self, component_name, deps):
        """启用依赖项"""
        for dep_path in deps:
            dep_name = os.path.basename(dep_path).lower()
            
            # 增加依赖计数
            self.dependency_count[dep_name] = self.dependency_count.get(dep_name, 0) + 1
            
            # 更新被依赖的组件状态
            if dep_name in self.component_pages:
                page = self.component_pages[dep_name]
                page.set_dependency_count(self.dependency_count[dep_name])
    
    def disable_dependencies(self, component_name, deps):
        """禁用依赖项"""
        for dep_path in deps:
            dep_name = os.path.basename(dep_path).lower()
            
            # 减少依赖计数
            if dep_name in self.dependency_count:
                self.dependency_count[dep_name] = max(0, self.dependency_count[dep_name] - 1)
                
                # 更新被依赖的组件状态
                if dep_name in self.component_pages:
                    page = self.component_pages[dep_name]
                    page.set_dependency_count(self.dependency_count[dep_name])

# 具体组件类
class component_pid(ComponentSimple):
    def __init__(self, project_path, component_manager=None):
        super().__init__(
            project_path,
            "PID",
            {'header': 'pid.h', 'source': 'pid.c'},
            component_manager
        )

class component_filter(ComponentSimple):
    def __init__(self, project_path, component_manager=None):
        super().__init__(
            project_path,
            "Filter",
            {'header': 'filter.h', 'source': 'filter.c'},
            component_manager
        )

# ...existing code... (component 类的 generate_component 方法保持不变)

class component(QWidget):
    """组件管理器"""
    
    def __init__(self, project_path):
        super().__init__()
        self.project_path = project_path
    
    @staticmethod
    def generate_component(project_path, pages):
        """生成所有组件代码，处理依赖关系"""
        # 在方法开始时导入CodeGenerator以确保可用
        from app.tools.code_generator import CodeGenerator
        
        # 自动添加 component.h
        src_component_h = os.path.join(CodeGenerator.get_assets_dir("User_code/component"), "component.h")
        dst_component_h = os.path.join(project_path, "User/component/component.h")
        os.makedirs(os.path.dirname(dst_component_h), exist_ok=True)
        if os.path.exists(src_component_h):
            with open(src_component_h, 'r', encoding='utf-8') as f:
                content = f.read()
            CodeGenerator.save_with_preserve(dst_component_h, content)
        
        # 收集所有需要生成的组件和它们的依赖
        components_to_generate = set()
        component_pages = {}
        
        for page in pages:
            # 检查是否是组件页面（通过类名或者属性判断）
            if hasattr(page, "component_name") and hasattr(page, "is_need_generate"):
                if page.is_need_generate():
                    component_name = page.component_name.lower()
                    components_to_generate.add(component_name)
                    component_pages[component_name] = page
                    
                    # 添加依赖组件，依赖格式是路径形式如 "component/filter"
                    deps = page.get_enabled_dependencies()
                    for dep_path in deps:
                        # 跳过BSP层依赖
                        if dep_path.startswith('bsp/'):
                            continue
                        # 从路径中提取组件名，如 "component/filter" -> "filter"
                        dep_name = os.path.basename(dep_path)
                        # 只有不包含文件扩展名的才是组件，有扩展名的是文件依赖
                        if not dep_name.endswith(('.h', '.c', '.hpp', '.cpp')):
                            components_to_generate.add(dep_name)
        
        # 为没有对应页面但需要生成的依赖组件创建临时页面
        user_code_dir = CodeGenerator.get_assets_dir("User_code")
        for comp_name in components_to_generate:
            if comp_name not in component_pages:
                # 创建临时组件页面
                template_names = {'header': f'{comp_name}.h', 'source': f'{comp_name}.c'}
                temp_page = ComponentSimple(project_path, comp_name.upper(), template_names)
                # temp_page.set_forced_enabled(True)  # 自动启用依赖组件
                component_pages[comp_name] = temp_page
        
        # 如果没有组件需要生成，返回提示信息
        if not components_to_generate:
            return "没有启用的组件需要生成代码。"
        
        # 生成代码和依赖文件
        success_count = 0
        fail_count = 0
        fail_list = []
        
        # 处理依赖文件的复制
        all_deps = set()
        for page in pages:
            if hasattr(page, "component_name") and hasattr(page, "is_need_generate"):
                if page.is_need_generate():
                    deps = page.get_enabled_dependencies()
                    all_deps.update(deps)
        
        # 复制依赖文件
        for dep_path in all_deps:
            try:
                # 检查是否是 bsp 层依赖
                if dep_path.startswith('bsp/'):
                    # 对于 bsp 层依赖，跳过复制，因为这些由 BSP 代码生成负责
                    print(f"跳过 BSP 层依赖: {dep_path} (由 BSP 代码生成负责)")
                    continue
                
                # dep_path 格式如 "component/filter" 或 "component/user_math.h"
                src_path = os.path.join(user_code_dir, dep_path)
                dst_path = os.path.join(project_path, "User", dep_path)
                
                if os.path.isdir(src_path):
                    # 如果是目录，复制整个目录
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    if os.path.exists(dst_path):
                        shutil.rmtree(dst_path)
                    shutil.copytree(src_path, dst_path)
                elif os.path.isfile(src_path):
                    # 如果是文件，复制单个文件并保留用户区域
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    with open(src_path, 'r', encoding='utf-8') as f:
                        new_content = f.read()
                    CodeGenerator.save_with_preserve(dst_path, new_content)
                else:
                    # 如果既不是文件也不是目录，跳过
                    print(f"跳过不存在的依赖: {dep_path}")
                    continue
                    
                success_count += 1
                print(f"成功复制依赖: {dep_path}")
            except Exception as e:
                # 对于 bsp 层依赖的错误，只记录但不计入失败
                if dep_path.startswith('bsp/'):
                    print(f"BSP 层依赖 {dep_path} 复制失败，但忽略此错误: {e}")
                else:
                    fail_count += 1
                    fail_list.append(f"{dep_path} (依赖复制异常: {e})")
                    print(f"复制依赖失败: {dep_path}, 错误: {e}")
        
        # 生成组件代码
        skipped_count = 0
        skipped_list = []
        
        for comp_name in components_to_generate:
            if comp_name in component_pages:
                page = component_pages[comp_name]
                try:
                    # 确保调用正确的方法名
                    if hasattr(page, '_generate_component_code_internal'):
                        result = page._generate_component_code_internal()
                        if result == "skipped":
                            skipped_count += 1
                            skipped_list.append(comp_name)
                            print(f"跳过组件生成: {comp_name}")
                        elif result:
                            success_count += 1
                            print(f"成功生成组件: {comp_name}")
                        else:
                            fail_count += 1
                            fail_list.append(f"{comp_name} (生成失败)")
                            print(f"生成组件失败: {comp_name}")
                    else:
                        fail_count += 1
                        fail_list.append(f"{comp_name} (缺少生成方法)")
                        print(f"组件页面缺少生成方法: {comp_name}")
                except Exception as e:
                    fail_count += 1
                    fail_list.append(f"{comp_name} (生成异常: {e})")
                    print(f"生成组件异常: {comp_name}, 错误: {e}")
        
        total_items = len(all_deps) + len(components_to_generate)
        msg = f"组件代码生成完成：总共处理 {total_items} 项，成功生成 {success_count} 项，跳过 {skipped_count} 项，失败 {fail_count} 项。"
        if skipped_list:
            msg += f"\n跳过项（文件已存在且未勾选）：\n" + "\n".join(skipped_list)
        if fail_list:
            msg += "\n失败项：\n" + "\n".join(fail_list)
        
        return msg