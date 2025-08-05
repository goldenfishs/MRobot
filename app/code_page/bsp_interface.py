from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QCheckBox, QComboBox, QTableWidget, QHeaderView, QMessageBox, QHBoxLayout
from qfluentwidgets import TitleLabel, BodyLabel, PushButton, CheckBox, TableWidget, LineEdit, ComboBox,MessageBox,SubtitleLabel,FluentIcon
from qfluentwidgets import InfoBar
from PyQt5.QtCore import Qt
from app.tools.analyzing_ioc import analyzing_ioc
from app.tools.code_generator import CodeGenerator
import os
import csv
import shutil

def preserve_all_user_regions(new_code, old_code):
    """ Preserves all user-defined regions in the new code based on the old code.
    This function uses regex to find user-defined regions in the old code and replaces them in the new code.
    Args:
        new_code (str): The new code content.
        old_code (str): The old code content.
    Returns:
        str: The new code with preserved user-defined regions.  
    """
    import re
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
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            old_code = f.read()
        new_code = preserve_all_user_regions(new_code, old_code)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_code)

class BspSimplePeripheral(QWidget):
    def __init__(self, project_path, peripheral_name, template_names):
        super().__init__()
        self.project_path = project_path
        self.peripheral_name = peripheral_name
        self.template_names = template_names
        # 加载描述
        describe_path = os.path.join(os.path.dirname(__file__), "../../assets/User_code/bsp/describe.csv")
        self.descriptions = load_descriptions(describe_path)
        self._init_ui()
        self._load_config()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 顶部横向布局：左侧复选框，居中标题
        top_layout = QHBoxLayout()
        top_layout.setAlignment(Qt.AlignVCenter)

        self.generate_checkbox = CheckBox(f"启用 {self.peripheral_name}")
        top_layout.addWidget(self.generate_checkbox, alignment=Qt.AlignLeft)

        # 弹性空间
        top_layout.addStretch()

        title = SubtitleLabel(f"{self.peripheral_name} 配置             ")
        title.setAlignment(Qt.AlignHCenter)
        top_layout.addWidget(title, alignment=Qt.AlignHCenter)

        # 再加一个弹性空间，保证标题居中
        top_layout.addStretch()

        layout.addLayout(top_layout)

        desc = self.descriptions.get(self.peripheral_name.lower(), "")
        if desc:
            desc_label = BodyLabel(f"功能说明：{desc}")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
        layout.addStretch()
    def is_need_generate(self):
        return self.generate_checkbox.isChecked()

    def _generate_bsp_code_internal(self):
        if not self.is_need_generate():
            return False
        template_dir = CodeGenerator.get_template_dir()
        for key, filename in self.template_names.items():
            template_path = os.path.join(template_dir, filename)
            template_content = CodeGenerator.load_template(template_path)
            if not template_content:
                return False
            output_path = os.path.join(self.project_path, f"User/bsp/{filename}")
            save_with_preserve(output_path, template_content)  # 使用保留用户区域的写入
        self._save_config()
        return True


    def _save_config(self):
        config_path = os.path.join(self.project_path, "User/bsp/bsp_config.yaml")
        config_data = CodeGenerator.load_config(config_path)
        config_data[self.peripheral_name.lower()] = {'enabled': True}
        CodeGenerator.save_config(config_data, config_path)

    def _load_config(self):
        config_path = os.path.join(self.project_path, "User/bsp/bsp_config.yaml")
        config_data = CodeGenerator.load_config(config_path)
        conf = config_data.get(self.peripheral_name.lower(), {})
        if conf.get('enabled', False):
            self.generate_checkbox.setChecked(True)

class BspPeripheralBase(QWidget):
    def __init__(self, project_path, peripheral_name, template_names, enum_prefix, handle_prefix, yaml_key, get_available_func):
        super().__init__()
        self.project_path = project_path
        self.peripheral_name = peripheral_name
        self.template_names = template_names
        self.enum_prefix = enum_prefix
        self.handle_prefix = handle_prefix
        self.yaml_key = yaml_key
        self.get_available_func = get_available_func
        self.available_list = []
        # 新增：加载描述
        describe_path = os.path.join(os.path.dirname(__file__), "../../assets/User_code/bsp/describe.csv")
        self.descriptions = load_descriptions(describe_path)
        self._init_ui()
        self._load_config()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        top_layout.setAlignment(Qt.AlignVCenter)

        self.generate_checkbox = CheckBox(f"生成 {self.peripheral_name} 代码")
        self.generate_checkbox.stateChanged.connect(self._on_generate_changed)
        top_layout.addWidget(self.generate_checkbox, alignment=Qt.AlignLeft)

        top_layout.addStretch()

        title = SubtitleLabel(f"{self.peripheral_name} 配置             ")
        title.setAlignment(Qt.AlignHCenter)
        top_layout.addWidget(title, alignment=Qt.AlignHCenter)

        top_layout.addStretch()

        layout.addLayout(top_layout)

        desc = self.descriptions.get(self.peripheral_name.lower(), "")
        if desc:
            desc_label = BodyLabel(f"功能说明：{desc}")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        self._get_available_list()
        if not self.available_list:
            content_layout.addWidget(BodyLabel(f"在 .ioc 文件中未找到已启用的 {self.peripheral_name}"))
        else:
            content_layout.addWidget(BodyLabel(f"可用的 {self.peripheral_name}: {', '.join(self.available_list)}"))
            self.table = TableWidget()
            self.table.setColumnCount(3)
            self.table.setHorizontalHeaderLabels(["设备名称", f"{self.peripheral_name}选择", "操作"])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            content_layout.addWidget(self.table)
            add_btn = PushButton(f"添加 {self.peripheral_name} 设备")
            add_btn.clicked.connect(self._add_device)
            content_layout.addWidget(add_btn)
        layout.addWidget(self.content_widget)
        self.content_widget.setEnabled(False)


    def _get_available_list(self):
        self.available_list = self.get_available_func(self.project_path)

    def _on_generate_changed(self, state):
        self.content_widget.setEnabled(state == 2)

    def _add_device(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        name_edit = LineEdit()
        name_edit.setPlaceholderText(f"输入设备名称")
        self.table.setCellWidget(row, 0, name_edit)
        combo = ComboBox()  # 使用 Fluent 风格 ComboBox
        combo.addItems(self.available_list)
        self.table.setCellWidget(row, 1, combo)
        del_btn = PushButton(FluentIcon.DELETE,"删除" )  # 添加垃圾桶图标
        del_btn.clicked.connect(lambda: self._delete_device(row))
        self.table.setCellWidget(row, 2, del_btn)

    def _delete_device(self, row):
        self.table.removeRow(row)

    def _collect_configs(self):
        configs = []
        for row in range(self.table.rowCount()):
            name_widget = self.table.cellWidget(row, 0)
            sel_widget = self.table.cellWidget(row, 1)
            if name_widget and sel_widget:
                name = name_widget.text().strip()
                sel = sel_widget.currentText()
                if name and sel:
                    configs.append((name.upper(), sel))
        return configs

    def is_need_generate(self):
        return self.generate_checkbox.isChecked() and bool(self._collect_configs())

    def generate_bsp_code(self):
        if not self.is_need_generate():
            return False
        configs = self._collect_configs()
        if not configs:
            return False
        template_dir = CodeGenerator.get_template_dir()
        if not self._generate_header_file(configs, template_dir):
            return False
        if not self._generate_source_file(configs, template_dir):
            return False
        self._save_config(configs)
        InfoBar.success(
            title="任务生成成功",
            content=f"{self.peripheral_name} 代码生成成功！",
            parent=self,
            duration=2000
        )
        return True

    def _generate_header_file(self, configs, template_dir):
        template_path = os.path.join(template_dir, self.template_names['header'])
        template_content = CodeGenerator.load_template(template_path)
        if not template_content:
            return False
        enum_lines = [f"  {self.enum_prefix}_{name}," for name, _ in configs]
        content = CodeGenerator.replace_auto_generated(
            template_content, f"AUTO GENERATED {self.enum_prefix}_NAME", "\n".join(enum_lines)
        )
        output_path = os.path.join(self.project_path, f"User/bsp/{self.template_names['header']}")
        save_with_preserve(output_path, content)  # 使用保留用户区域的写入
        return True

    def _generate_source_file(self, configs, template_dir):
        template_path = os.path.join(template_dir, self.template_names['source'])
        template_content = CodeGenerator.load_template(template_path)
        if not template_content:
            return False
        # Get函数
        get_lines = []
        for idx, (name, instance) in enumerate(configs):
            if idx == 0:
                get_lines.append(f"  if ({self.handle_prefix}->Instance == {instance})")
            else:
                get_lines.append(f"  else if ({self.handle_prefix}->Instance == {instance})")
            get_lines.append(f"    return {self.enum_prefix}_{name};")
        content = CodeGenerator.replace_auto_generated(
            template_content, f"AUTO GENERATED {self.enum_prefix.split('_')[1]}_GET", "\n".join(get_lines)
        )
        # Handle函数
        handle_lines = []
        for name, instance in configs:
            handle_lines.append(f"    case {self.enum_prefix}_{name}:")
            # UART/USART统一用 huart 前缀
            if self.enum_prefix == "BSP_UART":
                # 提取数字部分
                num = ''.join(filter(str.isdigit, instance))
                handle_lines.append(f"      return &huart{num};")
            else:
                handle_lines.append(f"      return &h{instance.lower()};")
        content = CodeGenerator.replace_auto_generated(
            content, f"AUTO GENERATED {self.enum_prefix}_GET_HANDLE", "\n".join(handle_lines)
        )
        output_path = os.path.join(self.project_path, f"User/bsp/{self.template_names['source']}")
        save_with_preserve(output_path, content)  # 使用保留用户区域的写入
        return True

    def _save_config(self, configs):
        config_path = os.path.join(self.project_path, "User/bsp/bsp_config.yaml")
        config_data = CodeGenerator.load_config(config_path)
        config_data[self.yaml_key] = {
            'enabled': True,
            'devices': [{'name': name, 'instance': instance} for name, instance in configs]
        }
        CodeGenerator.save_config(config_data, config_path)

    def _load_config(self):
        config_path = os.path.join(self.project_path, "User/bsp/bsp_config.yaml")
        config_data = CodeGenerator.load_config(config_path)
        conf = config_data.get(self.yaml_key, {})
        if conf.get('enabled', False):
            self.generate_checkbox.setChecked(True)
            devices = conf.get('devices', [])
            for device in devices:
                if self.available_list:
                    self._add_device()
                    row = self.table.rowCount() - 1
                    name_widget = self.table.cellWidget(row, 0)
                    sel_widget = self.table.cellWidget(row, 1)
                    if name_widget:
                        name_widget.setText(device.get('name', ''))
                    if sel_widget:
                        instance = device.get('instance', '')
                        if instance in self.available_list:
                            sel_widget.setCurrentText(instance)

    def _generate_bsp_code_internal(self):
        if not self.is_need_generate():
            return False
        configs = self._collect_configs()
        if not configs:
            return False
        template_dir = CodeGenerator.get_template_dir()
        if not self._generate_header_file(configs, template_dir):
            return False
        if not self._generate_source_file(configs, template_dir):
            return False
        self._save_config(configs)
        return True

def load_descriptions(csv_path):
    descriptions = {}
    if os.path.exists(csv_path):
        with open(csv_path, encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    key, desc = row[0].strip(), row[1].strip()
                    descriptions[key.lower()] = desc
    return descriptions

# 各外设的可用列表获取函数
def get_available_i2c(project_path):
    ioc_files = [f for f in os.listdir(project_path) if f.endswith('.ioc')]
    if ioc_files:
        ioc_path = os.path.join(project_path, ioc_files[0])
        return analyzing_ioc.get_enabled_i2c_from_ioc(ioc_path)
    return []

def get_available_can(project_path):
    ioc_files = [f for f in os.listdir(project_path) if f.endswith('.ioc')]
    if ioc_files:
        ioc_path = os.path.join(project_path, ioc_files[0])
        return analyzing_ioc.get_enabled_can_from_ioc(ioc_path)
    return []

def get_available_spi(project_path):
    ioc_files = [f for f in os.listdir(project_path) if f.endswith('.ioc')]
    if ioc_files:
        ioc_path = os.path.join(project_path, ioc_files[0])
        return analyzing_ioc.get_enabled_spi_from_ioc(ioc_path)
    return []

def get_available_uart(project_path):
    ioc_files = [f for f in os.listdir(project_path) if f.endswith('.ioc')]
    if ioc_files:
        ioc_path = os.path.join(project_path, ioc_files[0])
        return analyzing_ioc.get_enabled_uart_from_ioc(ioc_path)
    return []

def get_available_gpio(project_path):
    ioc_files = [f for f in os.listdir(project_path) if f.endswith('.ioc')]
    if ioc_files:
        ioc_path = os.path.join(project_path, ioc_files[0])
        return analyzing_ioc.get_enabled_gpio_from_ioc(ioc_path)
    return []

def get_available_pwm(project_path):
    """获取可用的PWM通道"""
    ioc_files = [f for f in os.listdir(project_path) if f.endswith('.ioc')]
    if ioc_files:
        ioc_path = os.path.join(project_path, ioc_files[0])
        return analyzing_ioc.get_enabled_pwm_from_ioc(ioc_path)
    return []

# 具体外设类
class bsp_i2c(BspPeripheralBase):
    def __init__(self, project_path):
        super().__init__(
            project_path,
            "I2C",
            {'header': 'i2c.h', 'source': 'i2c.c'},
            "BSP_I2C",
            "hi2c",
            "i2c",
            get_available_i2c
        )

class bsp_can(BspPeripheralBase):
    def __init__(self, project_path):
        super().__init__(
            project_path,
            "CAN",
            {'header': 'can.h', 'source': 'can.c'},
            "BSP_CAN",
            "hcan",
            "can",
            get_available_can
        )

    def _generate_source_file(self, configs, template_dir):
        template_path = os.path.join(template_dir, self.template_names['source'])
        template_content = CodeGenerator.load_template(template_path)
        if not template_content:
            return False
            
        # Get函数
        get_lines = []
        for idx, (name, instance) in enumerate(configs):
            if idx == 0:
                get_lines.append(f"  if (hcan->Instance == {instance})")
            else:
                get_lines.append(f"  else if (hcan->Instance == {instance})")
            get_lines.append(f"    return {self.enum_prefix}_{name};")
        content = CodeGenerator.replace_auto_generated(
            template_content, "AUTO GENERATED CAN_GET", "\n".join(get_lines)
        )
        
        # Handle函数
        handle_lines = []
        for name, instance in configs:
            handle_lines.append(f"    case {self.enum_prefix}_{name}:")
            handle_lines.append(f"      return &h{instance.lower()};")
        content = CodeGenerator.replace_auto_generated(
            content, f"AUTO GENERATED {self.enum_prefix}_GET_HANDLE", "\n".join(handle_lines)
        )
        
        # 生成CAN初始化代码
        init_lines = []
        for idx, (name, instance) in enumerate(configs):
            can_num = instance[-1]  # CAN1 -> 1, CAN2 -> 2
            
            init_lines.append(f"  // 初始化 {instance}")
            init_lines.append(f"  CAN_FilterTypeDef can{can_num}_filter = {{0}};")
            init_lines.append(f"  can{can_num}_filter.FilterBank = {0 if can_num == '1' else 14};")
            init_lines.append(f"  can{can_num}_filter.FilterIdHigh = 0;")
            init_lines.append(f"  can{can_num}_filter.FilterIdLow = 0;")
            init_lines.append(f"  can{can_num}_filter.FilterMode = CAN_FILTERMODE_IDMASK;")
            init_lines.append(f"  can{can_num}_filter.FilterScale = CAN_FILTERSCALE_32BIT;")
            init_lines.append(f"  can{can_num}_filter.FilterMaskIdHigh = 0;")
            init_lines.append(f"  can{can_num}_filter.FilterMaskIdLow = 0;")
            init_lines.append(f"  can{can_num}_filter.FilterActivation = ENABLE;")
            if can_num == '1':
                init_lines.append(f"  can{can_num}_filter.SlaveStartFilterBank = 14;")
                init_lines.append(f"  can{can_num}_filter.FilterFIFOAssignment = CAN_RX_FIFO0;")
            else:
                init_lines.append(f"  can{can_num}_filter.FilterFIFOAssignment = CAN_RX_FIFO1;")
            
            init_lines.append(f"  HAL_CAN_ConfigFilter(BSP_CAN_GetHandle({self.enum_prefix}_{name}), &can{can_num}_filter);")
            init_lines.append(f"  HAL_CAN_Start(BSP_CAN_GetHandle({self.enum_prefix}_{name}));")
            
            # 注册回调和激活中断
            fifo = "FIFO0" if can_num == '1' else "FIFO1"
            init_lines.append(f"  HAL_CAN_ActivateNotification(BSP_CAN_GetHandle({self.enum_prefix}_{name}), CAN_IT_RX_{fifo}_MSG_PENDING);")
            init_lines.append("")
            
        content = CodeGenerator.replace_auto_generated(
            content, "AUTO GENERATED CAN_INIT", "\n".join(init_lines)
        )
        
        output_path = os.path.join(self.project_path, f"User/bsp/{self.template_names['source']}")
        save_with_preserve(output_path, content)
        return True

class bsp_spi(BspPeripheralBase):
    def __init__(self, project_path):
        super().__init__(
            project_path,
            "SPI",
            {'header': 'spi.h', 'source': 'spi.c'},
            "BSP_SPI",
            "hspi",
            "spi",
            get_available_spi
        )

class bsp_uart(BspPeripheralBase):
    def __init__(self, project_path):
        super().__init__(
            project_path,
            "UART",
            {'header': 'uart.h', 'source': 'uart.c'},
            "BSP_UART",
            "huart",
            "uart",
            get_available_uart
        )

class bsp_gpio(QWidget):
    def __init__(self, project_path):
        super().__init__()
        self.project_path = project_path
        self.available_list = self._get_all_gpio_list()
        # 加载描述
        describe_path = os.path.join(os.path.dirname(__file__), "../../assets/User_code/bsp/describe.csv")
        self.descriptions = load_descriptions(describe_path)
        self._init_ui()
        self._load_config()

    def _get_all_gpio_list(self):
        """获取所有GPIO配置"""
        ioc_files = [f for f in os.listdir(self.project_path) if f.endswith('.ioc')]
        if ioc_files:
            ioc_path = os.path.join(self.project_path, ioc_files[0])
            return analyzing_ioc.get_all_gpio_from_ioc(ioc_path)
        return []

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 顶部布局
        top_layout = QHBoxLayout()
        top_layout.setAlignment(Qt.AlignVCenter)

        self.generate_checkbox = CheckBox("生成 GPIO 代码")
        self.generate_checkbox.stateChanged.connect(self._on_generate_changed)
        top_layout.addWidget(self.generate_checkbox, alignment=Qt.AlignLeft)

        top_layout.addStretch()

        title = SubtitleLabel("GPIO 配置             ")
        title.setAlignment(Qt.AlignHCenter)
        top_layout.addWidget(title, alignment=Qt.AlignHCenter)

        top_layout.addStretch()

        layout.addLayout(top_layout)

        desc = self.descriptions.get("gpio", "")
        if desc:
            desc_label = BodyLabel(f"功能说明：{desc}")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        # 内容区域
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)

        if not self.available_list:
            content_layout.addWidget(BodyLabel("在 .ioc 文件中未找到可用的 GPIO"))
        else:
            # 创建表格
            self.table = TableWidget()
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels(["IOC Label", "自定义名称", "类型", "包含"])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            
            # 填充表格
            for row, gpio_info in enumerate(self.available_list):
                self.table.insertRow(row)
                
                # IOC Label (只读)
                from PyQt5.QtWidgets import QTableWidgetItem
                label_item = QTableWidgetItem(gpio_info['label'])
                label_item.setFlags(label_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, 0, label_item)
                
                # 自定义名称 (可编辑)
                name_edit = LineEdit()
                name_edit.setText(gpio_info['label'])  # 默认使用IOC的label
                name_edit.setPlaceholderText("输入自定义名称")
                self.table.setCellWidget(row, 1, name_edit)
                
                # 类型显示
                gpio_type = "EXTI" if gpio_info['has_exti'] else ("输出" if gpio_info['is_output'] else "输入")
                type_item = QTableWidgetItem(gpio_type)
                type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, 2, type_item)
                
                # 包含复选框
                include_checkbox = CheckBox("")
                include_checkbox.setChecked(True)  # 默认选中
                self.table.setCellWidget(row, 3, include_checkbox)

            content_layout.addWidget(self.table)

        layout.addWidget(self.content_widget)
        self.content_widget.setEnabled(False)

    def _on_generate_changed(self, state):
        self.content_widget.setEnabled(state == 2)

    def is_need_generate(self):
        return self.generate_checkbox.isChecked() and bool(self.available_list)

    def _collect_configs(self):
        """收集用户配置"""
        configs = []
        for row in range(self.table.rowCount()):
            include_widget = self.table.cellWidget(row, 3)
            if include_widget and include_widget.isChecked():
                name_widget = self.table.cellWidget(row, 1)
                if name_widget:
                    custom_name = name_widget.text().strip()
                    if custom_name:
                        gpio_info = self.available_list[row]
                        configs.append({
                            'custom_name': custom_name.upper(),
                            'ioc_label': gpio_info['label'],
                            'pin': gpio_info['pin'], 
                            'has_exti': gpio_info['has_exti']
                        })
        return configs

    def _generate_bsp_code_internal(self):
        if not self.is_need_generate():
            return False
        
        configs = self._collect_configs()
        if not configs:
            return False
            
        template_dir = CodeGenerator.get_template_dir()
        if not self._generate_header_file(configs, template_dir):
            return False
        if not self._generate_source_file(configs, template_dir):
            return False
        self._save_config(configs)
        return True

    def _generate_header_file(self, configs, template_dir):
        template_path = os.path.join(template_dir, "gpio.h")
        template_content = CodeGenerator.load_template(template_path)
        if not template_content:
            return False
            
        # 生成枚举
        enum_lines = []
        for config in configs:
            enum_lines.append(f"  BSP_GPIO_{config['custom_name']},")
            
        content = CodeGenerator.replace_auto_generated(
            template_content, "AUTO GENERATED BSP_GPIO_ENUM", "\n".join(enum_lines)
        )
        
        output_path = os.path.join(self.project_path, "User/bsp/gpio.h")
        save_with_preserve(output_path, content)
        return True

    def _generate_source_file(self, configs, template_dir):
        template_path = os.path.join(template_dir, "gpio.c")
        template_content = CodeGenerator.load_template(template_path)
        if not template_content:
            return False
            
        # 生成MAP数组
        map_lines = []
        for config in configs:
            ioc_label = config['ioc_label']
            map_lines.append(f"    {{{ioc_label}_Pin, {ioc_label}_GPIO_Port}},")
            
        content = CodeGenerator.replace_auto_generated(
            template_content, "AUTO GENERATED BSP_GPIO_MAP", "\n".join(map_lines)
        )
        
        # 生成EXTI使能代码
        enable_lines = []
        disable_lines = []
        for config in configs:
            if config['has_exti']:
                ioc_label = config['ioc_label']
                enable_lines.append(f"    case {ioc_label}_Pin:")
                enable_lines.append(f"      HAL_NVIC_EnableIRQ({ioc_label}_EXTI_IRQn);")
                enable_lines.append(f"      break;")
                disable_lines.append(f"    case {ioc_label}_Pin:")
                disable_lines.append(f"      HAL_NVIC_DisableIRQ({ioc_label}_EXTI_IRQn);")
                disable_lines.append(f"      break;")
                
        content = CodeGenerator.replace_auto_generated(
            content, "AUTO GENERATED BSP_GPIO_ENABLE_IRQ", "\n".join(enable_lines)
        )
        content = CodeGenerator.replace_auto_generated(
            content, "AUTO GENERATED BSP_GPIO_DISABLE_IRQ", "\n".join(disable_lines)
        )
        
        output_path = os.path.join(self.project_path, "User/bsp/gpio.c")
        save_with_preserve(output_path, content)
        return True

    def _save_config(self, configs):
        config_path = os.path.join(self.project_path, "User/bsp/bsp_config.yaml")
        config_data = CodeGenerator.load_config(config_path)
        config_data['gpio'] = {
            'enabled': True,
            'configs': [
                {
                    'custom_name': config['custom_name'],
                    'ioc_label': config['ioc_label'],
                    'pin': config['pin'],
                    'has_exti': config['has_exti']
                } for config in configs
            ]
        }
        CodeGenerator.save_config(config_data, config_path)

    def _load_config(self):
        config_path = os.path.join(self.project_path, "User/bsp/bsp_config.yaml")
        config_data = CodeGenerator.load_config(config_path)
        conf = config_data.get('gpio', {})
        if conf.get('enabled', False):
            self.generate_checkbox.setChecked(True)
            saved_configs = conf.get('configs', [])
            # 恢复用户的自定义名称和选择状态
            for saved_config in saved_configs:
                for row in range(len(self.available_list)):
                    if (self.available_list[row]['label'] == saved_config['ioc_label'] and
                        hasattr(self, 'table')):
                        name_widget = self.table.cellWidget(row, 1)
                        if name_widget:
                            name_widget.setText(saved_config['custom_name'])

class bsp_pwm(QWidget):
    def __init__(self, project_path):
        super().__init__()
        self.project_path = project_path
        self.available_list = self._get_pwm_channels()
        # 加载描述
        describe_path = os.path.join(os.path.dirname(__file__), "../../assets/User_code/bsp/describe.csv")
        self.descriptions = load_descriptions(describe_path)
        self._init_ui()
        self._load_config()

    def _get_pwm_channels(self):
        """获取所有PWM通道配置"""
        return get_available_pwm(self.project_path)

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 顶部布局
        top_layout = QHBoxLayout()
        top_layout.setAlignment(Qt.AlignVCenter)

        self.generate_checkbox = CheckBox("生成 PWM 代码")
        self.generate_checkbox.stateChanged.connect(self._on_generate_changed)
        top_layout.addWidget(self.generate_checkbox, alignment=Qt.AlignLeft)

        top_layout.addStretch()

        title = SubtitleLabel("PWM 配置             ")
        title.setAlignment(Qt.AlignHCenter)
        top_layout.addWidget(title, alignment=Qt.AlignHCenter)

        top_layout.addStretch()

        layout.addLayout(top_layout)

        desc = self.descriptions.get("pwm", "")
        if desc:
            desc_label = BodyLabel(f"功能说明：{desc}")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        # 内容区域
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)

        if not self.available_list:
            content_layout.addWidget(BodyLabel("在 .ioc 文件中未找到可用的 PWM 通道"))
        else:
            # 创建表格
            self.table = TableWidget()
            self.table.setColumnCount(4)
            self.table.setHorizontalHeaderLabels(["PWM通道", "自定义名称", "定时器信息", "选择"])
            
            # 设置列宽度 - 手动调整各列的初始宽度
            header = self.table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Interactive)  # PWM通道列可调整
            header.setSectionResizeMode(1, QHeaderView.Stretch)      # 自定义名称列拉伸
            header.setSectionResizeMode(2, QHeaderView.Interactive)  # 定时器信息列可调整
            header.setSectionResizeMode(3, QHeaderView.Fixed)        # 选择列固定宽度
            
            # 设置初始列宽
            self.table.setColumnWidth(0, 150)  # PWM通道列宽度
            self.table.setColumnWidth(2, 120)  # 定时器信息列宽度  
            self.table.setColumnWidth(3, 80)   # 选择列宽度
            
            # 填充表格
            for row, pwm_info in enumerate(self.available_list):
                self.table.insertRow(row)
                
                # PWM通道信息 (只读) - 显示完整的通道信息
                from PyQt5.QtWidgets import QTableWidgetItem
                channel_display = f"{pwm_info['timer']} {pwm_info['channel'].replace('TIM_CHANNEL_', 'CH')}"
                channel_item = QTableWidgetItem(channel_display)
                channel_item.setFlags(channel_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, 0, channel_item)
                
                # 自定义名称 (可编辑)
                name_edit = LineEdit()
                name_edit.setText(pwm_info['label'])  # 默认使用IOC的label
                name_edit.setPlaceholderText("输入自定义名称")
                self.table.setCellWidget(row, 1, name_edit)
                
                # 定时器信息 - 显示引脚和信号
                timer_info = f"{pwm_info['pin']}"
                timer_item = QTableWidgetItem(timer_info)
                timer_item.setFlags(timer_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, 2, timer_item)
                
                # 选择复选框 - 放在中央
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                checkbox_layout.setAlignment(Qt.AlignCenter)
                
                include_checkbox = CheckBox("")
                include_checkbox.setChecked(True)  # 默认选中
                checkbox_layout.addWidget(include_checkbox)
                
                self.table.setCellWidget(row, 3, checkbox_widget)

            content_layout.addWidget(self.table)

        layout.addWidget(self.content_widget)
        self.content_widget.setEnabled(False)

    def _on_generate_changed(self, state):
        self.content_widget.setEnabled(state == 2)

    def is_need_generate(self):
        return self.generate_checkbox.isChecked() and bool(self.available_list)

    def _collect_configs(self):
        """收集用户配置"""
        configs = []
        for row in range(self.table.rowCount()):
            checkbox_widget = self.table.cellWidget(row, 3)
            if checkbox_widget:
                # 获取复选框
                include_checkbox = checkbox_widget.findChild(CheckBox)
                if include_checkbox and include_checkbox.isChecked():
                    name_widget = self.table.cellWidget(row, 1)
                    if name_widget:
                        custom_name = name_widget.text().strip()
                        if custom_name:
                            pwm_info = self.available_list[row]
                            configs.append({
                                'custom_name': custom_name.upper(),
                                'timer': pwm_info['timer'],
                                'channel': pwm_info['channel'],
                                'label': pwm_info['label']
                            })
        return configs

    def _generate_bsp_code_internal(self):
        if not self.is_need_generate():
            return False
        
        configs = self._collect_configs()
        if not configs:
            return False
            
        template_dir = CodeGenerator.get_template_dir()
        if not self._generate_header_file(configs, template_dir):
            return False
        if not self._generate_source_file(configs, template_dir):
            return False
        self._save_config(configs)
        return True

    def _generate_header_file(self, configs, template_dir):
        template_path = os.path.join(template_dir, "pwm.h")
        template_content = CodeGenerator.load_template(template_path)
        if not template_content:
            return False
            
        # 生成枚举
        enum_lines = []
        for config in configs:
            enum_lines.append(f"  BSP_PWM_{config['custom_name']},")
            
        content = CodeGenerator.replace_auto_generated(
            template_content, "AUTO GENERATED BSP_PWM_ENUM", "\n".join(enum_lines)
        )
        
        output_path = os.path.join(self.project_path, "User/bsp/pwm.h")
        save_with_preserve(output_path, content)
        return True

    def _generate_source_file(self, configs, template_dir):
        template_path = os.path.join(template_dir, "pwm.c")
        template_content = CodeGenerator.load_template(template_path)
        if not template_content:
            return False
            
        # 生成MAP数组
        map_lines = []
        for config in configs:
            timer = config['timer'].lower()  # tim1 -> htim1
            channel = config['channel']
            map_lines.append(f"  {{&h{timer}, {channel}}},")
            
        content = CodeGenerator.replace_auto_generated(
            template_content, "AUTO GENERATED BSP_PWM_MAP", "\n".join(map_lines)
        )
        
        output_path = os.path.join(self.project_path, "User/bsp/pwm.c")
        save_with_preserve(output_path, content)
        return True

    def _save_config(self, configs):
        config_path = os.path.join(self.project_path, "User/bsp/bsp_config.yaml")
        config_data = CodeGenerator.load_config(config_path)
        config_data['pwm'] = {
            'enabled': True,
            'configs': [
                {
                    'custom_name': config['custom_name'],
                    'timer': config['timer'],
                    'channel': config['channel'],
                    'label': config['label']
                } for config in configs
            ]
        }
        CodeGenerator.save_config(config_data, config_path)

    def _load_config(self):
        config_path = os.path.join(self.project_path, "User/bsp/bsp_config.yaml")
        config_data = CodeGenerator.load_config(config_path)
        conf = config_data.get('pwm', {})
        if conf.get('enabled', False):
            self.generate_checkbox.setChecked(True)
            saved_configs = conf.get('configs', [])
            # 恢复用户的自定义名称和选择状态
            for saved_config in saved_configs:
                for row in range(len(self.available_list)):
                    if (self.available_list[row]['label'] == saved_config['label'] and
                        hasattr(self, 'table')):
                        name_widget = self.table.cellWidget(row, 1)
                        if name_widget:
                            name_widget.setText(saved_config['custom_name'])

# 更新get_bsp_page函数以包含PWM
def get_bsp_page(peripheral_name, project_path):
    """根据外设名返回对应的页面类，没有特殊类则返回默认BspSimplePeripheral"""
    name_lower = peripheral_name.lower()
    special_classes = {
        "i2c": bsp_i2c,
        "can": bsp_can,
        "spi": bsp_spi,
        "uart": bsp_uart,
        "gpio": bsp_gpio,
        "pwm": bsp_pwm,  # 添加PWM
        # 以后可以继续添加特殊外设
    }
    if name_lower in special_classes:
        return special_classes[name_lower](project_path)
    else:
        template_names = {
            'header': f'{name_lower}.h',
            'source': f'{name_lower}.c'
        }
        return BspSimplePeripheral(project_path, peripheral_name, template_names)


class bsp(QWidget):
    def __init__(self, project_path):
        super().__init__()
        self.project_path = project_path

    @staticmethod
    def generate_bsp(project_path, pages):
        """生成所有BSP代码"""
        # 自动添加 bsp.h
        src_bsp_h = os.path.join(os.path.dirname(__file__), "../../assets/User_code/bsp/bsp.h")
        dst_bsp_h = os.path.join(project_path, "User/bsp/bsp.h")
        os.makedirs(os.path.dirname(dst_bsp_h), exist_ok=True)
        if os.path.exists(src_bsp_h):
            shutil.copyfile(src_bsp_h, dst_bsp_h)
        
        total = 0
        success_count = 0
        fail_count = 0
        fail_list = []
        
        for page in pages:
            # 只处理BSP页面：有 is_need_generate 方法但没有 component_name 属性的页面
            if hasattr(page, 'is_need_generate') and not hasattr(page, 'component_name'):
                if page.is_need_generate():
                    total += 1
                    try:
                        result = page._generate_bsp_code_internal()
                        if result:
                            success_count += 1
                        else:
                            fail_count += 1
                            fail_list.append(page.__class__.__name__)
                    except Exception as e:
                        fail_count += 1
                        fail_list.append(f"{page.__class__.__name__} (异常: {e})")
        
        msg = f"总共尝试生成 {total} 项，成功 {success_count} 项，失败 {fail_count} 项。"
        if fail_list:
            msg += "\n失败项：\n" + "\n".join(fail_list)
        
        return msg