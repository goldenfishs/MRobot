from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QCheckBox, QComboBox, QTableWidget, QHeaderView, QMessageBox
from qfluentwidgets import TitleLabel, BodyLabel, PushButton
from app.tools.analyzing_ioc import analyzing_ioc
from app.tools.code_generator import CodeGenerator
import os
import csv

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
        layout.addWidget(TitleLabel(f"{self.peripheral_name} 配置"))
        desc = self.descriptions.get(self.peripheral_name.lower(), "")
        if desc:
            layout.addWidget(BodyLabel(f"功能说明：{desc}"))
        self.generate_checkbox = QCheckBox(f"启用 {self.peripheral_name}")
        layout.addWidget(self.generate_checkbox)

    def is_need_generate(self):
        return self.generate_checkbox.isChecked()

    def _generate_bsp_code_internal(self):
        if not self.is_need_generate():
            return False
        template_dir = CodeGenerator.get_template_dir()
        # 直接拷贝模板，无需特殊处理
        for key, filename in self.template_names.items():
            template_path = os.path.join(template_dir, filename)
            template_content = CodeGenerator.load_template(template_path)
            if not template_content:
                return False
            output_path = os.path.join(self.project_path, f"User/bsp/{filename}")
            if not CodeGenerator.save_file(template_content, output_path):
                return False
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
        layout.addWidget(TitleLabel(f"{self.peripheral_name} 配置"))
        desc = self.descriptions.get(self.peripheral_name.lower(), "")
        if desc:
            layout.addWidget(BodyLabel(f"功能说明：{desc}"))
        self.generate_checkbox = QCheckBox(f"生成 {self.peripheral_name} 代码")
        self.generate_checkbox = QCheckBox(f"生成 {self.peripheral_name} 代码")
        self.generate_checkbox.stateChanged.connect(self._on_generate_changed)
        layout.addWidget(self.generate_checkbox)
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        self._get_available_list()
        if not self.available_list:
            content_layout.addWidget(BodyLabel(f"在 .ioc 文件中未找到已启用的 {self.peripheral_name}"))
        else:
            content_layout.addWidget(BodyLabel(f"可用的 {self.peripheral_name}: {', '.join(self.available_list)}"))
            self.table = QTableWidget(0, 3)
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
        name_edit = QLineEdit()
        name_edit.setPlaceholderText(f"输入设备名称")
        self.table.setCellWidget(row, 0, name_edit)
        combo = QComboBox()
        combo.addItems(self.available_list)
        self.table.setCellWidget(row, 1, combo)
        del_btn = PushButton("删除")
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
        QMessageBox.information(self, "成功", f"{self.peripheral_name} 代码生成成功！")
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
        return CodeGenerator.save_file(content, output_path)

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
            handle_lines.append(f"      return &h{instance.lower()};")
        content = CodeGenerator.replace_auto_generated(
            content, f"AUTO GENERATED {self.enum_prefix}_GET_HANDLE", "\n".join(handle_lines)
        )
        output_path = os.path.join(self.project_path, f"User/bsp/{self.template_names['source']}")
        return CodeGenerator.save_file(content, output_path)

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
        self.available_list = get_available_gpio(project_path)
        # 新增：加载描述
        describe_path = os.path.join(os.path.dirname(__file__), "../../assets/User_code/bsp/describe.csv")
        self.descriptions = load_descriptions(describe_path)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(TitleLabel("GPIO 配置"))
        # 新增：显示描述
        desc = self.descriptions.get("gpio", "")
        if desc:
            layout.addWidget(BodyLabel(f"功能说明：{desc}"))
        self.generate_checkbox = QCheckBox("生成 GPIO 代码")
        layout.addWidget(self.generate_checkbox)
        if not self.available_list:
            layout.addWidget(BodyLabel("在 .ioc 文件中未找到可用的 GPIO"))
        else:
            self.table = QTableWidget(len(self.available_list), 1)
            self.table.setHorizontalHeaderLabels(["Label"])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            for row, item in enumerate(self.available_list):
                from PyQt5.QtWidgets import QTableWidgetItem
                self.table.setItem(row, 0, QTableWidgetItem(item['label']))
            self.table.setEditTriggers(QTableWidget.NoEditTriggers)
            layout.addWidget(self.table)

    def is_need_generate(self):
        return self.generate_checkbox.isChecked() and bool(self.available_list)

    def _generate_bsp_code_internal(self):
        if not self.is_need_generate():
            return False
        template_dir = CodeGenerator.get_template_dir()
        if not self._generate_header_file(template_dir):
            return False
        if not self._generate_source_file(template_dir):
            return False
        self._save_config()
        return True

    def _generate_header_file(self, template_dir):
            template_path = os.path.join(template_dir, "gpio.h")
            template_content = CodeGenerator.load_template(template_path)
            if not template_content:
                return False
            # 如有需要可在此处插入自动生成内容
            output_path = os.path.join(self.project_path, "User/bsp/gpio.h")
            return CodeGenerator.save_file(template_content, output_path)

    def _generate_source_file(self, template_dir):
        template_path = os.path.join(template_dir, "gpio.c")
        template_content = CodeGenerator.load_template(template_path)
        if not template_content:
            return False
        # 生成 IRQ 使能/禁用代码
        enable_lines = []
        disable_lines = []
        for item in self.available_list:
            label = item['label']
            enable_lines.append(f"    case {label}_Pin:")
            enable_lines.append(f"      HAL_NVIC_EnableIRQ({label}_EXTI_IRQn);")
            enable_lines.append(f"      break;")
            disable_lines.append(f"    case {label}_Pin:")
            disable_lines.append(f"      HAL_NVIC_DisableIRQ({label}_EXTI_IRQn);")
            disable_lines.append(f"      break;")
        content = CodeGenerator.replace_auto_generated(
            template_content, "AUTO GENERATED BSP_GPIO_ENABLE_IRQ", "\n".join(enable_lines)
        )
        content = CodeGenerator.replace_auto_generated(
            content, "AUTO GENERATED BSP_GPIO_DISABLE_IRQ", "\n".join(disable_lines)
        )
        output_path = os.path.join(self.project_path, "User/bsp/gpio.c")
        return CodeGenerator.save_file(content, output_path)

    def _save_config(self):
        config_path = os.path.join(self.project_path, "User/bsp/bsp_config.yaml")
        config_data = CodeGenerator.load_config(config_path)
        config_data['gpio'] = {
            'enabled': True,
            'labels': [item['label'] for item in self.available_list]
        }
        CodeGenerator.save_config(config_data, config_path)


class bsp(QWidget):
    def __init__(self, project_path):
        super().__init__()
        self.project_path = project_path

    @staticmethod
    def generate_bsp(project_path, pages):
        total = 0
        success_count = 0
        fail_count = 0
        fail_list = []
        for page in pages:
            name = page.objectName() if hasattr(page, "objectName") else str(page)
            if hasattr(page, "is_need_generate") and page.is_need_generate():
                total += 1
                try:
                    result = page._generate_bsp_code_internal()
                    if result:
                        success_count += 1
                    else:
                        fail_count += 1
                        fail_list.append(name)
                except Exception as e:
                    fail_count += 1
                    fail_list.append(f"{name} (异常: {e})")
        msg = f"总共尝试生成 {total} 项，成功 {success_count} 项，失败 {fail_count} 项。"
        if fail_list:
            msg += "\n失败项：\n" + "\n".join(fail_list)
        QMessageBox.information(None, "代码生成结果", msg)