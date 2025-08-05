from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QCheckBox, QComboBox, QTableWidget, QHeaderView, QMessageBox, QHBoxLayout, QTextEdit
from qfluentwidgets import TitleLabel, BodyLabel, PushButton, CheckBox, TableWidget, LineEdit, ComboBox, MessageBox, SubtitleLabel, FluentIcon, TextEdit
from qfluentwidgets import InfoBar
from PyQt5.QtCore import Qt, pyqtSignal
from app.tools.code_generator import CodeGenerator
import os
import csv
import shutil
import re

def preserve_all_user_regions(new_code, old_code):
    """ Preserves all user-defined regions in the new code based on the old code.
    This function uses regex to find user-defined regions in the old code and replaces them in the new code.
    Args:
        new_code (str): The new code content.
        old_code (str): The old code content.
    Returns:
        str: The new code with preserved user-defined regions.  
    """
    pattern = re.compile(
        r"/\*\s*(USER [A-Z0-9_ ]+)\s*BEGIN\s*\*/(.*?)/\*\s*\1\s*END\s*\*/",
        re.DOTALL
    )
    old_regions = {m.group(1): m.group(2) for m in pattern.finditer(old_code or "")}
    def repl(m):
        region = m.group(1)
        old_content = old_regions.get(region)
        if old_content is not None:
            return m.group(0).replace(m.group(2), old_content)
        return m.group(0)
    return pattern.sub(repl, new_code)

def save_with_preserve(path, new_code):
    """保存文件并保留用户区域"""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            old_code = f.read()
        new_code = preserve_all_user_regions(new_code, old_code)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_code)

def load_descriptions(csv_path):
    """加载组件描述信息"""
    descriptions = {}
    if os.path.exists(csv_path):
        with open(csv_path, encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    key, desc = row[0].strip(), row[1].strip()
                    descriptions[key.lower()] = desc
    return descriptions

def load_dependencies(csv_path):
    """加载组件依赖关系"""
    dependencies = {}
    if os.path.exists(csv_path):
        with open(csv_path, encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    component = row[0].strip()
                    deps = [dep.strip() for dep in row[1:] if dep.strip()]
                    dependencies[component] = deps
    return dependencies


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
    
    # 添加信号，用于通知其他组件状态变化
    dependency_changed = pyqtSignal(str, bool)  # 组件名, 是否启用
    
    def __init__(self, project_path, component_name, template_names, component_manager=None):
        super().__init__()
        self.project_path = project_path
        self.component_name = component_name
        self.template_names = template_names
        self.component_manager = component_manager
        
        # 加载描述和依赖信息
        component_dir = os.path.join(os.path.dirname(__file__), "../../assets/User_code/component")
        describe_path = os.path.join(component_dir, "describe.csv")
        dependencies_path = os.path.join(component_dir, "dependencies.csv")
        
        self.descriptions = load_descriptions(describe_path)
        self.dependencies = load_dependencies(dependencies_path)
        self.all_dependent_components = get_all_dependency_components(self.dependencies)
        
        # 判断当前组件是否被其他组件依赖
        self.is_dependency = self.component_name.lower() in self.all_dependent_components
        
        # 强制启用状态相关
        self._forced_enabled = False
        self._dependency_count = 0  # 有多少个组件依赖此组件
        
        self._init_ui()
        self._load_config()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # 顶部横向布局：左侧复选框，居中标题
        top_layout = QHBoxLayout()
        top_layout.setAlignment(Qt.AlignVCenter)
        
        # 所有组件都有复选框
        self.generate_checkbox = CheckBox(f"启用 {self.component_name}")
        self.generate_checkbox.stateChanged.connect(self._on_checkbox_changed)
        top_layout.addWidget(self.generate_checkbox, alignment=Qt.AlignLeft)
        
        # 如果是被依赖的组件，添加状态标签
        if self.is_dependency:
            self.dependency_status_label = BodyLabel("")
            self.dependency_status_label.setStyleSheet("color: #888888; font-style: italic; margin-left: 10px;")
            top_layout.addWidget(self.dependency_status_label, alignment=Qt.AlignLeft)
        
        # 弹性空间
        top_layout.addStretch()
        
        title = SubtitleLabel(f"{self.component_name} 配置             ")
        title.setAlignment(Qt.AlignHCenter)
        top_layout.addWidget(title, alignment=Qt.AlignHCenter)
        
        # 再加一个弹性空间，保证标题居中
        top_layout.addStretch()
        
        layout.addLayout(top_layout)
        
        # 功能说明
        desc = self.descriptions.get(self.component_name.lower(), "")
        if desc:
            desc_label = BodyLabel(f"功能说明：{desc}")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
        
        # 依赖信息
        deps = self.dependencies.get(self.component_name.lower(), [])
        if deps:
            deps_text = f"依赖组件：{', '.join([os.path.basename(dep) for dep in deps])}"
            self.deps_label = BodyLabel(deps_text)
            self.deps_label.setWordWrap(True)
            self.deps_label.setStyleSheet("color: #888888;")
            layout.addWidget(self.deps_label)
            
            # 依赖状态显示
            self.deps_status_widget = QWidget()
            deps_status_layout = QVBoxLayout(self.deps_status_widget)
            deps_status_layout.setContentsMargins(20, 10, 20, 10)
            
            self.deps_checkboxes = {}
            for dep in deps:
                # 从路径中提取组件名
                dep_name = os.path.basename(dep)
                dep_checkbox = CheckBox(f"自动启用 {dep_name}")
                dep_checkbox.setEnabled(False)  # 依赖项自动管理，不允许手动取消
                deps_status_layout.addWidget(dep_checkbox)
                self.deps_checkboxes[dep] = dep_checkbox
            
            layout.addWidget(self.deps_status_widget)
        
        # 如果是被依赖的组件，显示被哪些组件依赖
        if self.is_dependency:
            dependent_by = []
            for component, deps in self.dependencies.items():
                for dep_path in deps:
                    if os.path.basename(dep_path).lower() == self.component_name.lower():
                        dependent_by.append(component)
            
            if dependent_by:
                dependent_text = f"被以下组件依赖：{', '.join(dependent_by)}"
                dependent_label = BodyLabel(dependent_text)
                dependent_label.setWordWrap(True)
                dependent_label.setStyleSheet("color: #0078d4;")
                layout.addWidget(dependent_label)
        
        layout.addStretch()
        
        # 初始化界面状态
        self._update_ui_state()
    
    def _update_ui_state(self):
        """更新界面状态"""
        if self.is_dependency:
            if self._dependency_count > 0:
                # 有组件依赖此组件，设置为强制启用状态
                self.generate_checkbox.setEnabled(False)
                self.generate_checkbox.setChecked(True)
                self.dependency_status_label.setText(f"(被 {self._dependency_count} 个组件自动启用)")
                self.dependency_status_label.setStyleSheet("color: #0078d4; font-style: italic; margin-left: 10px;")
            else:
                # 没有组件依赖此组件，恢复正常状态
                self.generate_checkbox.setEnabled(True)
                self.dependency_status_label.setText("(可选组件)")
                self.dependency_status_label.setStyleSheet("color: #888888; font-style: italic; margin-left: 10px;")
    
    def _on_checkbox_changed(self, state):
        """处理复选框状态变化，自动管理依赖"""
        # 如果是被强制启用的，不允许用户取消
        if self.is_dependency and self._dependency_count > 0:
            return
            
        if state == 2:  # 选中状态
            # 自动选中所有依赖项
            deps = self.dependencies.get(self.component_name.lower(), [])
            for dep in deps:
                if dep in self.deps_checkboxes:
                    self.deps_checkboxes[dep].setChecked(True)
            
            # 通知组件管理器启用依赖项
            if self.component_manager:
                self.component_manager.enable_dependencies(self.component_name, deps)
        else:  # 未选中状态
            # 取消选中所有依赖项
            if hasattr(self, 'deps_checkboxes'):
                for checkbox in self.deps_checkboxes.values():
                    checkbox.setChecked(False)
            
            # 通知组件管理器禁用依赖项
            if self.component_manager:
                deps = self.dependencies.get(self.component_name.lower(), [])
                self.component_manager.disable_dependencies(self.component_name, deps)
    
    def set_forced_enabled(self, enabled: bool):
        """设置强制启用状态（用于依赖自动启用）"""
        self._forced_enabled = enabled
        if enabled:
            self.set_dependency_count(max(1, self._dependency_count))
        else:
            self.set_dependency_count(0)
            
    def is_need_generate(self):
        """检查是否需要生成代码"""
        return self.generate_checkbox.isChecked()
    
    def set_dependency_count(self, count):
        """设置依赖计数并更新UI状态"""
        self._dependency_count = count
        if count > 0:
            self._forced_enabled = True
            if not self.generate_checkbox.isChecked():
                # 阻止信号触发，直接设置状态
                self.generate_checkbox.blockSignals(True)
                self.generate_checkbox.setChecked(True)
                self.generate_checkbox.blockSignals(False)
        else:
            self._forced_enabled = False
        
        self._update_ui_state()
        self._save_config()  # 保存状态变化
    
    def get_enabled_dependencies(self):
        """获取已启用的依赖项列表"""
        if not self.is_need_generate():
            return []
        return self.dependencies.get(self.component_name.lower(), [])
    
    def _generate_component_code_internal(self):
        """生成组件代码"""
        if not self.is_need_generate():
            return False
        
        template_dir = self._get_component_template_dir()
        
        # 生成头文件和源文件
        for key, filename in self.template_names.items():
            template_path = os.path.join(template_dir, filename)
            template_content = CodeGenerator.load_template(template_path)
            if not template_content:
                print(f"模板文件不存在或为空: {template_path}")
                continue
            
            output_path = os.path.join(self.project_path, f"User/component/{filename}")
            save_with_preserve(output_path, template_content)
        
        self._save_config()
        return True
    
    def _get_component_template_dir(self):
        """获取组件模板目录"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 向上找到 MRobot 根目录
        while os.path.basename(current_dir) != 'MRobot' and current_dir != '/':
            current_dir = os.path.dirname(current_dir)
        
        if os.path.basename(current_dir) == 'MRobot':
            return os.path.join(current_dir, "assets/User_code/component")
        else:
            # 如果找不到，使用相对路径作为备选
            return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets/User_code/component")
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(self.project_path, "User/component/component_config.yaml")
        config_data = CodeGenerator.load_config(config_path)
        config_data[self.component_name.lower()] = {
            'enabled': self.is_need_generate(),
            'dependencies': self.dependencies.get(self.component_name.lower(), []),
            'is_dependency': self.is_dependency,
            'dependency_count': self._dependency_count,
            'forced_enabled': self._forced_enabled
        }
        CodeGenerator.save_config(config_data, config_path)
    
    def _load_config(self):
        """加载配置"""
        config_path = os.path.join(self.project_path, "User/component/component_config.yaml")
        config_data = CodeGenerator.load_config(config_path)
        conf = config_data.get(self.component_name.lower(), {})
        
        # 加载依赖计数
        self._dependency_count = conf.get('dependency_count', 0)
        self._forced_enabled = conf.get('forced_enabled', False)
        
        # 设置复选框状态
        if conf.get('enabled', False):
            self.generate_checkbox.setChecked(True)
        
        # 更新UI状态
        self._update_ui_state()

class ComponentManager:
    """组件依赖管理器"""
    
    def __init__(self):
        self.component_pages = {}  # 组件名 -> 页面对象
        self.dependency_count = {}  # 被依赖组件 -> 依赖计数
    
    def register_component(self, component_name, page):
        """注册组件页面"""
        self.component_pages[component_name.lower()] = page
        
        # 注册后立即同步状态
        self._sync_dependency_states()
    
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
        # 自动添加 component.h
        src_component_h = os.path.join(os.path.dirname(__file__), "../../assets/User_code/component/component.h")
        dst_component_h = os.path.join(project_path, "User/component/component.h")
        os.makedirs(os.path.dirname(dst_component_h), exist_ok=True)
        if os.path.exists(src_component_h):
            shutil.copyfile(src_component_h, dst_component_h)
        
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
                        # 从路径中提取组件名，如 "component/filter" -> "filter"
                        dep_name = os.path.basename(dep_path)
                        components_to_generate.add(dep_name)
        
        # 为没有对应页面但需要生成的依赖组件创建临时页面
        user_code_dir = os.path.join(os.path.dirname(__file__), "../../assets/User_code")
        for comp_name in components_to_generate:
            if comp_name not in component_pages:
                # 创建临时组件页面
                template_names = {'header': f'{comp_name}.h', 'source': f'{comp_name}.c'}
                temp_page = ComponentSimple(project_path, comp_name.upper(), template_names)
                temp_page.set_forced_enabled(True)  # 自动启用依赖组件
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
                # dep_path 格式如 "component/filter"
                src_dir = os.path.join(user_code_dir, dep_path)
                if os.path.isdir(src_dir):
                    # 如果是目录，复制整个目录
                    dst_dir = os.path.join(project_path, "User", dep_path)
                    os.makedirs(os.path.dirname(dst_dir), exist_ok=True)
                    if os.path.exists(dst_dir):
                        shutil.rmtree(dst_dir)
                    shutil.copytree(src_dir, dst_dir)
                else:
                    # 如果是文件，复制单个文件
                    src_file = src_dir
                    dst_file = os.path.join(project_path, "User", dep_path)
                    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                    if os.path.exists(src_file):
                        shutil.copyfile(src_file, dst_file)
                success_count += 1
                print(f"成功复制依赖: {dep_path}")
            except Exception as e:
                fail_count += 1
                fail_list.append(f"{dep_path} (依赖复制异常: {e})")
                print(f"复制依赖失败: {dep_path}, 错误: {e}")
        
        # 生成组件代码
        for comp_name in components_to_generate:
            if comp_name in component_pages:
                page = component_pages[comp_name]
                try:
                    # 确保调用正确的方法名
                    if hasattr(page, '_generate_component_code_internal'):
                        result = page._generate_component_code_internal()
                        if result:
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
        msg = f"组件代码生成完成：总共尝试生成 {total_items} 项，成功 {success_count} 项，失败 {fail_count} 项。"
        if fail_list:
            msg += "\n失败项：\n" + "\n".join(fail_list)
        
        return msg