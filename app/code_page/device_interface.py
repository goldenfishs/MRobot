from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import BodyLabel, CheckBox, ComboBox, SubtitleLabel
from PyQt5.QtCore import Qt
from app.tools.code_generator import CodeGenerator
import os
import yaml
import re

def get_available_bsp_devices(project_path, bsp_type, gpio_type=None):
    """获取可用的BSP设备，GPIO可选类型过滤"""
    bsp_config_path = os.path.join(project_path, "User/bsp/bsp_config.yaml")
    if not os.path.exists(bsp_config_path):
        return []
    try:
        with open(bsp_config_path, 'r', encoding='utf-8') as f:
            bsp_config = yaml.safe_load(f)
        if bsp_type == "gpio" and bsp_config.get("gpio", {}).get("enabled", False):
            configs = bsp_config["gpio"].get("configs", [])
            # 增加类型过滤
            if gpio_type:
                configs = [cfg for cfg in configs if cfg.get('type', '').lower() == gpio_type.lower()]
            return [f"BSP_GPIO_{cfg['custom_name']}" for cfg in configs]
        elif bsp_type == "pwm" and bsp_config.get("pwm", {}).get("enabled", False):
            # PWM使用configs结构
            configs = bsp_config["pwm"].get("configs", [])
            return [f"BSP_PWM_{cfg['custom_name']}" for cfg in configs]
        elif bsp_type in bsp_config and bsp_config[bsp_type].get('enabled', False):
            devices = bsp_config[bsp_type].get('devices', [])
            return [f"BSP_{bsp_type.upper()}_{device['name']}" for device in devices]
    except Exception as e:
        print(f"读取BSP配置失败: {e}")
    return []

def generate_device_header(project_path, enabled_devices):
    """生成device.h文件"""
    from app.tools.code_generator import CodeGenerator
    device_dir = CodeGenerator.get_assets_dir("User_code/device")
    template_path = os.path.join(device_dir, "device.h")
    dst_path = os.path.join(project_path, "User/device/device.h")
    
    # 优先读取项目中已存在的文件，如果不存在则使用模板
    if os.path.exists(dst_path):
        # 读取现有文件以保留用户区域
        with open(dst_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        # 文件不存在时从模板创建
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
    
    # 收集所有需要的信号定义
    signals = []
    current_bit = 0
    
    # 加载设备配置来获取信号信息
    config_path = os.path.join(device_dir, "config.yaml")
    device_configs = CodeGenerator.load_device_config(config_path)
    
    for device_name in enabled_devices:
        device_key = device_name.lower()
        if device_key in device_configs.get('devices', {}):
            device_config = device_configs['devices'][device_key]
            thread_signals = device_config.get('thread_signals', [])
            
            for signal in thread_signals:
                signal_name = signal['name']
                signals.append(f"#define {signal_name} (1u << {current_bit})")
                current_bit += 1
    
    # 生成信号定义文本
    signals_text = '\n'.join(signals) if signals else '/* No signals defined */'
    
    # 替换AUTO GENERATED SIGNALS部分，保留其他所有用户区域
    pattern = r'/\* AUTO GENERATED SIGNALS BEGIN \*/(.*?)/\* AUTO GENERATED SIGNALS END \*/'
    replacement = f'/* AUTO GENERATED SIGNALS BEGIN */\n{signals_text}\n/* AUTO GENERATED SIGNALS END */'
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # 使用save_with_preserve保存文件以保留用户区域
    CodeGenerator.save_with_preserve(dst_path, content)




class DeviceSimple(QWidget):
    """简单设备界面"""
    
    def __init__(self, project_path, device_name, device_config):
        super().__init__()
        self.project_path = project_path
        self.device_name = device_name
        self.device_config = device_config

        # 添加必要的属性，确保兼容性
        self.component_name = device_name  # 添加这个属性以兼容现有代码
        
        self._init_ui()
        self._load_config()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # 顶部横向布局：左侧复选框，居中标题
        top_layout = QHBoxLayout()
        top_layout.setAlignment(Qt.AlignVCenter)
        
        self.generate_checkbox = CheckBox(f"启用 {self.device_name}")
        self.generate_checkbox.stateChanged.connect(self._on_checkbox_changed)
        top_layout.addWidget(self.generate_checkbox, alignment=Qt.AlignLeft)
        
        # 弹性空间
        top_layout.addStretch()
        
        title = SubtitleLabel(f"{self.device_name} 配置             ")
        title.setAlignment(Qt.AlignHCenter)
        top_layout.addWidget(title, alignment=Qt.AlignHCenter)
        
        # 再加一个弹性空间，保证标题居中
        top_layout.addStretch()
        
        layout.addLayout(top_layout)
        
        # 功能说明
        desc = self.device_config.get('description', '')
        if desc:
            desc_label = BodyLabel(f"功能说明：{desc}")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
        
        # 依赖信息
        self._add_dependency_info(layout)
        
        # BSP配置区域
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        
        self._add_bsp_config(content_layout)
        
        layout.addWidget(self.content_widget)
        self.content_widget.setEnabled(False)
        
        layout.addStretch()
    
    def _add_dependency_info(self, layout):
        """添加依赖信息显示"""
        bsp_deps = self.device_config.get('dependencies', {}).get('bsp', [])
        comp_deps = self.device_config.get('dependencies', {}).get('component', [])
        
        if bsp_deps or comp_deps:
            deps_text = "依赖: "
            if bsp_deps:
                deps_text += f"BSP({', '.join(bsp_deps)})"
            if comp_deps:
                if bsp_deps:
                    deps_text += ", "
                deps_text += f"Component({', '.join(comp_deps)})"
            
            deps_label = BodyLabel(deps_text)
            deps_label.setWordWrap(True)
            deps_label.setStyleSheet("color: #888888;")
            layout.addWidget(deps_label)
    
    def _add_bsp_config(self, layout):
        bsp_requirements = self.device_config.get('bsp_requirements', [])
        self.bsp_combos = {}
        if bsp_requirements:
            layout.addWidget(BodyLabel("BSP设备配置:"))
            for req in bsp_requirements:
                bsp_type = req['type']
                var_name = req['var_name']
                description = req.get('description', '')
                gpio_type = req.get('gpio_type', None)  # 新增
                req_layout = QHBoxLayout()
                label = BodyLabel(f"{bsp_type.upper()}:")
                label.setMinimumWidth(80)
                req_layout.addWidget(label)
                combo = ComboBox()
                # 传递gpio_type参数
                self._update_bsp_combo(combo, bsp_type, gpio_type)
                req_layout.addWidget(combo)
                if description:
                    desc_label = BodyLabel(f"({description})")
                    desc_label.setStyleSheet("color: #666666; font-size: 12px;")
                    req_layout.addWidget(desc_label)
                req_layout.addStretch()
                layout.addLayout(req_layout)
                self.bsp_combos[var_name] = combo
    
    def _update_bsp_combo(self, combo, bsp_type, gpio_type=None):
        combo.clear()
        available_devices = get_available_bsp_devices(self.project_path, bsp_type, gpio_type)
        if available_devices:
            combo.addItems(available_devices)
        else:
            combo.addItem(f"未找到可用的{bsp_type.upper()}设备")
            combo.setEnabled(False)

    
    def refresh_bsp_combos(self):
        """刷新所有BSP组合框"""
        bsp_requirements = self.device_config.get('bsp_requirements', [])
        for req in bsp_requirements:
            bsp_type = req['type']
            var_name = req['var_name']
            if var_name in self.bsp_combos:
                current_text = self.bsp_combos[var_name].currentText()
                self._update_bsp_combo(self.bsp_combos[var_name], bsp_type)
                # 尝试恢复之前的选择
                index = self.bsp_combos[var_name].findText(current_text)
                if index >= 0:
                    self.bsp_combos[var_name].setCurrentIndex(index)
    
    def _on_checkbox_changed(self, state):
        """处理复选框状态变化"""
        self.content_widget.setEnabled(state == 2)
    
    def is_need_generate(self):
        """检查是否需要生成代码"""
        return self.generate_checkbox.isChecked()
    
    def get_bsp_config(self):
        """获取BSP配置"""
        config = {}
        for var_name, combo in self.bsp_combos.items():
            if combo.isEnabled():
                config[var_name] = combo.currentText()
        return config
    
    def _generate_device_code_internal(self):
        """生成设备代码"""
        # 检查是否需要生成
        if not self.is_need_generate():
            # 如果未勾选，检查文件是否已存在，如果存在则跳过
            files = self.device_config.get('files', {})
            for filename in files.values():
                output_path = os.path.join(self.project_path, f"User/device/{filename}")
                if os.path.exists(output_path):
                    return "skipped"  # 返回特殊值表示跳过
            return "not_needed"  # 返回特殊值表示不需要生成
        
        # 获取BSP配置
        bsp_config = self.get_bsp_config()
        
        # 复制并修改文件
        template_dir = self._get_device_template_dir()
        files = self.device_config.get('files', {})
        
        for file_type, filename in files.items():
            src_path = os.path.join(template_dir, filename)
            dst_path = os.path.join(self.project_path, f"User/device/{filename}")

            if os.path.exists(src_path):
                # 读取模板文件内容
                with open(src_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 替换BSP设备名称
                for var_name, device_name in bsp_config.items():
                    content = content.replace(var_name, device_name)
                
                # 根据文件类型选择保存方式
                if file_type == 'header':
                    # 头文件需要保留用户区域
                    CodeGenerator.save_with_preserve(dst_path, content)
                else:
                    # 源文件直接保存（不需要保留用户区域）
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    with open(dst_path, 'w', encoding='utf-8') as f:
                        f.write(content)
        
        self._save_config()
        return True

    def _get_device_template_dir(self):
        """获取设备模板目录"""
        return CodeGenerator.get_assets_dir("User_code/device")
    
    def _save_config(self):
        """保存配置"""
        config_path = os.path.join(self.project_path, "User/device/device_config.yaml")
        config_data = CodeGenerator.load_config(config_path)
        config_data[self.device_name.lower()] = {
            'enabled': self.is_need_generate(),
            'bsp_config': self.get_bsp_config()
        }
        CodeGenerator.save_config(config_data, config_path)
    
    def _load_config(self):
        """加载配置"""
        config_path = os.path.join(self.project_path, "User/device/device_config.yaml")
        config_data = CodeGenerator.load_config(config_path)
        conf = config_data.get(self.device_name.lower(), {})
        
        if conf.get('enabled', False):
            self.generate_checkbox.setChecked(True)
            
            # 恢复BSP配置
            bsp_config = conf.get('bsp_config', {})
            for var_name, device_name in bsp_config.items():
                if var_name in self.bsp_combos:
                    combo = self.bsp_combos[var_name]
                    index = combo.findText(device_name)
                    if index >= 0:
                        combo.setCurrentIndex(index)

def get_device_page(device_name, project_path):
    """根据设备名返回对应的页面类"""
    # 加载设备配置
    from app.tools.code_generator import CodeGenerator
    device_dir = CodeGenerator.get_assets_dir("User_code/device")
    config_path = os.path.join(device_dir, "config.yaml")
    device_configs = CodeGenerator.load_device_config(config_path)
    
    devices = device_configs.get('devices', {})
    device_key = device_name.lower()
    
    if device_key in devices:
        device_config = devices[device_key]
        page = DeviceSimple(project_path, device_name, device_config)
    else:
        # 如果配置中没有找到，返回一个基本的设备页面
        basic_config = {
            'name': device_name,
            'description': f'{device_name}设备',
            'files': {'header': f'{device_name.lower()}.h', 'source': f'{device_name.lower()}.c'},
            'bsp_requirements': [],
            'dependencies': {'bsp': [], 'component': []}
        }
        page = DeviceSimple(project_path, device_name, basic_config)
    
    # 确保页面有必要的属性
    page.device_name = device_name
    
    return page

class device(QWidget):
    """设备管理器"""
    
    def __init__(self, project_path):
        super().__init__()
        self.project_path = project_path
    
    @staticmethod
    def generate_device(project_path, pages):
        """生成所有设备代码"""
        success_count = 0
        fail_count = 0
        skipped_count = 0
        fail_list = []
        skipped_list = []
        enabled_devices = []
        
        # 生成设备代码
        for page in pages:
            if hasattr(page, "device_name") and hasattr(page, "is_need_generate"):
                # 先检查是否有文件存在但未勾选的情况
                if not page.is_need_generate():
                    try:
                        result = page._generate_device_code_internal()
                        if result == "skipped":
                            skipped_count += 1
                            skipped_list.append(page.device_name)
                    except Exception:
                        pass  # 忽略未勾选页面的错误
                else:
                    # 勾选的页面，正常处理
                    try:
                        result = page._generate_device_code_internal()
                        if result == "skipped":
                            skipped_count += 1
                            skipped_list.append(page.device_name)
                        elif result:
                            success_count += 1
                            enabled_devices.append(page.device_name)
                        else:
                            fail_count += 1
                            fail_list.append(page.device_name)
                    except Exception as e:
                        fail_count += 1
                        fail_list.append(f"{page.device_name} (异常: {e})")
        
        # 生成device.h文件
        try:
            generate_device_header(project_path, enabled_devices)
            success_count += 1
        except Exception as e:
            fail_count += 1
            fail_list.append(f"device.h (异常: {e})")
        
        # 刷新所有页面的BSP组合框选项
        for page in pages:
            if hasattr(page, 'refresh_bsp_combos'):
                try:
                    page.refresh_bsp_combos()
                except Exception as e:
                    print(f"刷新页面 {getattr(page, 'device_name', 'Unknown')} 的BSP选项失败: {e}")
        
        total_items = success_count + fail_count + skipped_count
        msg = f"设备代码生成完成：总共处理 {total_items} 项，成功生成 {success_count} 项，跳过 {skipped_count} 项，失败 {fail_count} 项。"
        if skipped_list:
            msg += f"\n跳过项（文件已存在且未勾选）：\n" + "\n".join(skipped_list)
        if fail_list:
            msg += "\n失败项：\n" + "\n".join(fail_list)
        
        return msg