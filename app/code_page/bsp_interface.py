from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QCheckBox, QComboBox, QTableWidget, QHeaderView, QMessageBox, QHBoxLayout
from qfluentwidgets import TitleLabel, BodyLabel, PushButton, CheckBox, TableWidget, LineEdit, ComboBox,MessageBox,SubtitleLabel,FluentIcon
from qfluentwidgets import InfoBar
from PyQt5.QtCore import Qt
from app.tools.analyzing_ioc import analyzing_ioc
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
    # 确保目录存在
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_code)

class BspSimplePeripheral(QWidget):
    def __init__(self, project_path, peripheral_name, template_names):
        super().__init__()
        self.project_path = project_path
        self.peripheral_name = peripheral_name
        self.template_names = template_names
        # 加载描述
        describe_path = os.path.join(CodeGenerator.get_assets_dir("User_code/bsp"), "describe.csv")
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
        # 检查是否需要生成
        if not self.is_need_generate():
            # 如果未勾选，检查文件是否已存在，如果存在则跳过
            for filename in self.template_names.values():
                output_path = os.path.join(self.project_path, f"User/bsp/{filename}")
                if os.path.exists(output_path):
                    return "skipped"  # 返回特殊值表示跳过
            return "not_needed"  # 返回特殊值表示不需要生成
        
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
        describe_path = os.path.join(CodeGenerator.get_assets_dir("User_code/bsp"), "describe.csv")
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
        # 检查是否需要生成
        if not self.is_need_generate():
            # 如果未勾选，检查文件是否已存在，如果存在则跳过
            header_file = f"{self.yaml_key}.h"
            source_file = f"{self.yaml_key}.c"
            header_path = os.path.join(self.project_path, f"User/bsp/{header_file}")
            source_path = os.path.join(self.project_path, f"User/bsp/{source_file}")
            if os.path.exists(header_path) or os.path.exists(source_path):
                return "skipped"  # 返回特殊值表示跳过
            return "not_needed"  # 返回特殊值表示不需要生成
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
            
        # CAN_Get函数
        get_lines = []
        for idx, (name, instance) in enumerate(configs):
            if idx == 0:
                get_lines.append(f"    if (hcan->Instance == {instance})")
            else:
                get_lines.append(f"    else if (hcan->Instance == {instance})")
            get_lines.append(f"        return {self.enum_prefix}_{name};")
        content = CodeGenerator.replace_auto_generated(
            template_content, "AUTO GENERATED CAN_GET", "\n".join(get_lines)
        )
        
        # Handle函数
        handle_lines = []
        for name, instance in configs:
            num = ''.join(filter(str.isdigit, instance))  # 提取数字
            handle_lines.append(f"    case {self.enum_prefix}_{name}:")
            handle_lines.append(f"      return &hcan{num};")
        content = CodeGenerator.replace_auto_generated(
            content, f"AUTO GENERATED {self.enum_prefix}_GET_HANDLE", "\n".join(handle_lines)
        )
        
        # 生成CAN初始化代码
        init_lines = []
        
        # 先设置初始化标志
        init_lines.append("    // 先设置初始化标志，以便后续回调注册能通过检查")
        init_lines.append("    inited = true;")
        init_lines.append("")
        
        # 按照新的FIFO分配策略
        can_instances = [instance for _, instance in configs]
        can_count = len(can_instances)
        
        # 根据CAN数量分配FIFO
        if can_count == 1:
            # 只有CAN1 -> 用FIFO0
            self._generate_single_can_init(init_lines, configs, "CAN_RX_FIFO0")
        elif can_count == 2:
            # CAN1和CAN2 -> CAN1用FIFO0，CAN2用FIFO1
            self._generate_dual_can_init(init_lines, configs)
        elif can_count >= 3:
            # CAN1,2,3+ -> CAN1和CAN2用FIFO0，CAN3用FIFO1
            self._generate_multi_can_init(init_lines, configs)
        
        content = CodeGenerator.replace_auto_generated(
            content, "AUTO GENERATED CAN_INIT", "\n".join(init_lines)
        )
        
        output_path = os.path.join(self.project_path, f"User/bsp/{self.template_names['source']}")
        save_with_preserve(output_path, content)
        return True

    def _generate_single_can_init(self, init_lines, configs, fifo_assignment):
        """单个CAN的初始化（使用FIFO0）"""
        name, instance = configs[0]
        can_num = instance[-1]  # CAN1 -> 1
        
        init_lines.extend([
            f"    // 初始化 {instance} - 使用 FIFO0",
            f"    CAN_FilterTypeDef can{can_num}_filter = {{0}};",
            f"    can{can_num}_filter.FilterBank = 0;",
            f"    can{can_num}_filter.FilterIdHigh = 0;",
            f"    can{can_num}_filter.FilterIdLow = 0;",
            f"    can{can_num}_filter.FilterMode = CAN_FILTERMODE_IDMASK;",
            f"    can{can_num}_filter.FilterScale = CAN_FILTERSCALE_32BIT;",
            f"    can{can_num}_filter.FilterMaskIdHigh = 0;",
            f"    can{can_num}_filter.FilterMaskIdLow = 0;",
            f"    can{can_num}_filter.FilterActivation = ENABLE;",
            f"    can{can_num}_filter.SlaveStartFilterBank = 14;",
            f"    can{can_num}_filter.FilterFIFOAssignment = {fifo_assignment};",
            f"    HAL_CAN_ConfigFilter(&hcan{can_num}, &can{can_num}_filter);",
            f"    HAL_CAN_Start(&hcan{can_num});",
            "",
            f"    // 自动注册{instance}接收回调函数",
            f"    BSP_CAN_RegisterCallback({self.enum_prefix}_{name}, HAL_CAN_RX_FIFO0_MSG_PENDING_CB, BSP_CAN_RxFifo0Callback);",
            "",
            f"    // 激活{instance}中断",
            f"    HAL_CAN_ActivateNotification(&hcan{can_num}, CAN_IT_RX_FIFO0_MSG_PENDING);",
            ""
        ])

    def _generate_dual_can_init(self, init_lines, configs):
        """双CAN初始化（CAN1用FIFO0，CAN2用FIFO1）"""
        # 找到CAN1和CAN2
        can1_config = next((cfg for cfg in configs if cfg[1] == 'CAN1'), None)
        can2_config = next((cfg for cfg in configs if cfg[1] == 'CAN2'), None)
        
        if can1_config:
            name, instance = can1_config
            init_lines.extend([
                f"    // 初始化 CAN1 - 使用 FIFO0",
                f"    CAN_FilterTypeDef can1_filter = {{0}};",
                f"    can1_filter.FilterBank = 0;",
                f"    can1_filter.FilterIdHigh = 0;",
                f"    can1_filter.FilterIdLow = 0;",
                f"    can1_filter.FilterMode = CAN_FILTERMODE_IDMASK;",
                f"    can1_filter.FilterScale = CAN_FILTERSCALE_32BIT;",
                f"    can1_filter.FilterMaskIdHigh = 0;",
                f"    can1_filter.FilterMaskIdLow = 0;",
                f"    can1_filter.FilterActivation = ENABLE;",
                f"    can1_filter.SlaveStartFilterBank = 14;",
                f"    can1_filter.FilterFIFOAssignment = CAN_RX_FIFO0;",
                f"    HAL_CAN_ConfigFilter(&hcan1, &can1_filter);",
                f"    HAL_CAN_Start(&hcan1);",
                "",
                f"    // 自动注册CAN1接收回调函数",
                f"    BSP_CAN_RegisterCallback({self.enum_prefix}_{name}, HAL_CAN_RX_FIFO0_MSG_PENDING_CB, BSP_CAN_RxFifo0Callback);",
                "",
                f"    // 激活CAN1中断",
                f"    HAL_CAN_ActivateNotification(&hcan1, CAN_IT_RX_FIFO0_MSG_PENDING | ",
                f"                                        CAN_IT_TX_MAILBOX_EMPTY);  // 激活发送邮箱空中断",
                ""
            ])
        
        if can2_config:
            name, instance = can2_config
            init_lines.extend([
                f"    // 初始化 CAN2 - 使用 FIFO1",
                f"    can1_filter.FilterBank = 14;",
                f"    can1_filter.FilterFIFOAssignment = CAN_RX_FIFO1;",
                f"    HAL_CAN_ConfigFilter(&hcan2, &can1_filter);  // 通过 CAN1 配置",
                f"    HAL_CAN_Start(&hcan2);",
                "",
                f"    // 自动注册CAN2接收回调函数",
                f"    BSP_CAN_RegisterCallback({self.enum_prefix}_{name}, HAL_CAN_RX_FIFO1_MSG_PENDING_CB, BSP_CAN_RxFifo1Callback);",
                "",
                f"    // 激活CAN2中断", 
                f"    HAL_CAN_ActivateNotification(&hcan2, CAN_IT_RX_FIFO1_MSG_PENDING);",
                ""
            ])

    def _generate_multi_can_init(self, init_lines, configs):
        """多CAN初始化（CAN1和CAN2用FIFO0，CAN3+用FIFO1）"""
        can1_config = next((cfg for cfg in configs if cfg[1] == 'CAN1'), None)
        can2_config = next((cfg for cfg in configs if cfg[1] == 'CAN2'), None)
        other_configs = [cfg for cfg in configs if cfg[1] not in ['CAN1', 'CAN2']]
        
        # CAN1 - FIFO0
        if can1_config:
            name, instance = can1_config
            init_lines.extend([
                f"    // 初始化 CAN1 - 使用 FIFO0",
                f"    CAN_FilterTypeDef can1_filter = {{0}};",
                f"    can1_filter.FilterBank = 0;",
                f"    can1_filter.FilterIdHigh = 0;",
                f"    can1_filter.FilterIdLow = 0;",
                f"    can1_filter.FilterMode = CAN_FILTERMODE_IDMASK;",
                f"    can1_filter.FilterScale = CAN_FILTERSCALE_32BIT;",
                f"    can1_filter.FilterMaskIdHigh = 0;",
                f"    can1_filter.FilterMaskIdLow = 0;",
                f"    can1_filter.FilterActivation = ENABLE;",
                f"    can1_filter.SlaveStartFilterBank = 14;",
                f"    can1_filter.FilterFIFOAssignment = CAN_RX_FIFO0;",
                f"    HAL_CAN_ConfigFilter(&hcan1, &can1_filter);",
                f"    HAL_CAN_Start(&hcan1);",
                "",
                f"    // 自动注册CAN1接收回调函数",
                f"    BSP_CAN_RegisterCallback({self.enum_prefix}_{name}, HAL_CAN_RX_FIFO0_MSG_PENDING_CB, BSP_CAN_RxFifo0Callback);",
                "",
                f"    // 激活CAN1中断",
                f"    HAL_CAN_ActivateNotification(&hcan1, CAN_IT_RX_FIFO0_MSG_PENDING);",
                ""
            ])
        
        # CAN2 - FIFO0  
        if can2_config:
            name, instance = can2_config
            init_lines.extend([
                f"    // 初始化 CAN2 - 使用 FIFO0",
                f"    can1_filter.FilterBank = 14;",
                f"    can1_filter.FilterFIFOAssignment = CAN_RX_FIFO0;",
                f"    HAL_CAN_ConfigFilter(&hcan2, &can1_filter);  // 通过 CAN1 配置",
                f"    HAL_CAN_Start(&hcan2);",
                "",
                f"    // 自动注册CAN2接收回调函数",
                f"    BSP_CAN_RegisterCallback({self.enum_prefix}_{name}, HAL_CAN_RX_FIFO0_MSG_PENDING_CB, BSP_CAN_RxFifo0Callback);",
                "",
                f"    // 激活CAN2中断",
                f"    HAL_CAN_ActivateNotification(&hcan2, CAN_IT_RX_FIFO0_MSG_PENDING);",
                ""
            ])
        
        # CAN3+ - FIFO1
        filter_bank = 20  # 从过滤器组20开始分配给CAN3+
        for config in other_configs:
            name, instance = config
            can_num = ''.join(filter(str.isdigit, instance))
            init_lines.extend([
                f"    // 初始化 {instance} - 使用 FIFO1",
                f"    can1_filter.FilterBank = {filter_bank};",
                f"    can1_filter.FilterFIFOAssignment = CAN_RX_FIFO1;",
                f"    HAL_CAN_ConfigFilter(&hcan1, &can1_filter);  // 通过 CAN1 配置",
                f"    HAL_CAN_Start(&hcan{can_num});",
                "",
                f"    // 自动注册{instance}接收回调函数",
                f"    BSP_CAN_RegisterCallback({self.enum_prefix}_{name}, HAL_CAN_RX_FIFO1_MSG_PENDING_CB, BSP_CAN_RxFifo1Callback);",
                "",
                f"    // 激活{instance}中断",
                f"    HAL_CAN_ActivateNotification(&hcan{can_num}, CAN_IT_RX_FIFO1_MSG_PENDING);",
                ""
            ])
            filter_bank += 1  # 为下一个CAN分配不同的过滤器组

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


def patch_uart_interrupts(project_path, uart_instances):
    """自动修改 stm32f4xx_it.c，插入 UART BSP 相关代码"""
    it_path = os.path.join(project_path, "Core/Src/stm32f4xx_it.c")
    if not os.path.exists(it_path):
        return
    with open(it_path, "r", encoding="utf-8") as f:
        code = f.read()

    # 1. 插入 #include "bsp/uart.h"
    include_pattern = r"(/\* USER CODE BEGIN Includes \*/)(.*?)(/\* USER CODE END Includes \*/)"
    if '#include "bsp/uart.h"' not in code:
        code = re.sub(
            include_pattern,
            lambda m: f'{m.group(1)}\n#include "bsp/uart.h"{m.group(2)}{m.group(3)}',
            code,
            flags=re.DOTALL
        )

    # 2. 插入 BSP_UART_IRQHandler(&huartx);
    for instance in uart_instances:
        num = ''.join(filter(str.isdigit, instance))
        irq_pattern = (
            rf"(void\s+USART{num}_IRQHandler\s*\(\s*void\s*\)\s*\{{.*?/\* USER CODE BEGIN USART{num}_IRQn 1 \*/)(.*?)(/\* USER CODE END USART{num}_IRQn 1 \*/)"
        )
        if f"BSP_UART_IRQHandler(&huart{num});" not in code:
            code = re.sub(
                irq_pattern,
                lambda m: f"{m.group(1)}\n  BSP_UART_IRQHandler(&huart{num});{m.group(2)}{m.group(3)}",
                code,
                flags=re.DOTALL
            )
        # 兼容 UARTx 命名
        irq_pattern_uart = (
            rf"(void\s+UART{num}_IRQHandler\s*\(\s*void\s*\)\s*\{{.*?/\* USER CODE BEGIN UART{num}_IRQn 1 \*/)(.*?)(/\* USER CODE END UART{num}_IRQn 1 \*/)"
        )
        if f"BSP_UART_IRQHandler(&huart{num});" not in code:
            code = re.sub(
                irq_pattern_uart,
                lambda m: f"{m.group(1)}\n  BSP_UART_IRQHandler(&huart{num});{m.group(2)}{m.group(3)}",
                code,
                flags=re.DOTALL
            )

    with open(it_path, "w", encoding="utf-8") as f:
        f.write(code)


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
        # 自动补充 stm32f4xx_it.c
        uart_instances = [instance for _, instance in configs]
        patch_uart_interrupts(self.project_path, uart_instances)
        return True
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
        # 检查是否需要生成
        if not self.is_need_generate():
            # 如果未勾选，检查文件是否已存在，如果存在则跳过
            gpio_h_path = os.path.join(self.project_path, "User/bsp/gpio.h")
            gpio_c_path = os.path.join(self.project_path, "User/bsp/gpio.c")
            if os.path.exists(gpio_h_path) or os.path.exists(gpio_c_path):
                return "skipped"  # 返回特殊值表示跳过
            return "not_needed"  # 返回特殊值表示不需要生成
        
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
        
        # 生成EXTI使能代码 - 使用用户自定义的BSP枚举名称
        enable_lines = []
        disable_lines = []
        for config in configs:
            if config['has_exti']:
                ioc_label = config['ioc_label']
                custom_name = config['custom_name']
                enable_lines.append(f"    case BSP_GPIO_{custom_name}:")
                enable_lines.append(f"      HAL_NVIC_EnableIRQ({ioc_label}_EXTI_IRQn);")
                enable_lines.append(f"      break;")
                disable_lines.append(f"    case BSP_GPIO_{custom_name}:")
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
        gpio_configs = []
        for config in configs:
            # 根据 pin 查找原始 available_list 项
            match = next((item for item in self.available_list if item['pin'] == config['pin']), None)
            gpio_type = "EXTI" if config['has_exti'] else (
                "OUTPUT" if match and match.get('is_output') else "INPUT"
            )
            gpio_configs.append({
                'custom_name': config['custom_name'],
                'ioc_label': config['ioc_label'],
                'pin': config['pin'],
                'has_exti': config['has_exti'],
                'type': gpio_type
            })
        config_data['gpio'] = {
            'enabled': True,
            'configs': gpio_configs
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
        # 检查是否需要生成
        if not self.is_need_generate():
            # 如果未勾选，检查文件是否已存在，如果存在则跳过
            pwm_h_path = os.path.join(self.project_path, "User/bsp/pwm.h")
            pwm_c_path = os.path.join(self.project_path, "User/bsp/pwm.c")
            if os.path.exists(pwm_h_path) or os.path.exists(pwm_c_path):
                return "skipped"  # 返回特殊值表示跳过
            return "not_needed"  # 返回特殊值表示不需要生成
        
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
        skipped_count = 0
        fail_list = []
        skipped_list = []
        
        for page in pages:
            # 只处理BSP页面：有 is_need_generate 方法但没有 component_name 属性的页面
            if hasattr(page, 'is_need_generate') and not hasattr(page, 'component_name'):
                # 先检查是否有文件存在但未勾选的情况
                if not page.is_need_generate():
                    try:
                        result = page._generate_bsp_code_internal()
                        if result == "skipped":
                            total += 1
                            skipped_count += 1
                            skipped_list.append(page.__class__.__name__)
                    except Exception:
                        pass  # 忽略未勾选页面的错误
                else:
                    # 勾选的页面，正常处理
                    total += 1
                    try:
                        result = page._generate_bsp_code_internal()
                        if result == "skipped":
                            skipped_count += 1
                            skipped_list.append(page.__class__.__name__)
                        elif result:
                            success_count += 1
                        else:
                            fail_count += 1
                            fail_list.append(page.__class__.__name__)
                    except Exception as e:
                        fail_count += 1
                        fail_list.append(f"{page.__class__.__name__} (异常: {e})")
        
        msg = f"总共处理 {total} 项，成功生成 {success_count} 项，跳过 {skipped_count} 项，失败 {fail_count} 项。"
        if skipped_list:
            msg += f"\n跳过项（文件已存在且未勾选）：\n" + "\n".join(skipped_list)
        if fail_list:
            msg += "\n失败项：\n" + "\n".join(fail_list)
        
        return msg