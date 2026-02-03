from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QWidget, QScrollArea
from qfluentwidgets import (
    BodyLabel, TitleLabel, HorizontalSeparator, PushButton, PrimaryPushButton,
    LineEdit, SpinBox, DoubleSpinBox, CheckBox, TextEdit, ComboBox
)
from qfluentwidgets import theme, Theme
import yaml
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedLayout, QFileDialog, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidgetItem as TreeItem
from qfluentwidgets import TitleLabel, BodyLabel, SubtitleLabel, StrongBodyLabel, HorizontalSeparator, PushButton, TreeWidget, InfoBar,FluentIcon, Dialog,SubtitleLabel,BodyLabel
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox
from qfluentwidgets import CardWidget, LineEdit, SpinBox, CheckBox, TextEdit, PrimaryPushButton, PushButton, InfoBar, DoubleSpinBox
from qfluentwidgets import HeaderCardWidget
from PyQt5.QtWidgets import QScrollArea, QWidget
from qfluentwidgets import theme, Theme
from PyQt5.QtWidgets import QDoubleSpinBox
import os
class TaskConfigDialog(QDialog):
    def __init__(self, parent=None, config_path=None):
        super().__init__(parent)
        self.setWindowTitle("任务配置")
        self.resize(900, 520)

        # 设置背景色跟随主题
        if theme() == Theme.DARK:
            self.setStyleSheet("background-color: #232323;")
        else:
            self.setStyleSheet("background-color: #f7f9fc;")

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 顶部横向分栏
        self.top_layout = QHBoxLayout()
        self.top_layout.setSpacing(16)

        # ----------- 左侧任务按钮区 -----------
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(8)
        self.task_list_label = BodyLabel("任务列表")
        # self.left_layout.addWidget(self.task_list_label)
        # 添加任务列表居中
        self.task_list_label.setAlignment(Qt.AlignCenter)
        self.left_layout.addWidget(self.task_list_label, alignment=Qt.AlignCenter)

        # 添加一个水平分割线
        self.left_layout.addWidget(HorizontalSeparator())

        # 任务按钮区
        self.task_btn_area = QScrollArea()
        self.task_btn_area.setWidgetResizable(True)
        self.task_btn_area.setFrameShape(QScrollArea.NoFrame)
        self.task_btn_container = QWidget()
        self.task_btn_layout = QVBoxLayout(self.task_btn_container)
        self.task_btn_layout.setContentsMargins(0, 0, 0, 0)
        self.task_btn_layout.setSpacing(4)
        self.task_btn_layout.addStretch()
        self.task_btn_area.setWidget(self.task_btn_container)
        self.left_layout.addWidget(self.task_btn_area, stretch=1)

        self.left_widget.setFixedWidth(180)
        self.top_layout.addWidget(self.left_widget, stretch=0)
        # ----------- 左侧任务按钮区 END -----------

        main_layout.addLayout(self.top_layout, stretch=1)

        # 下方按钮区
        btn_layout = QHBoxLayout()

        # 左下角：添加/删除任务
        self.add_btn = PrimaryPushButton("创建新任务")
        self.add_btn.setAutoDefault(False)  # 禁止回车触发
        self.add_btn.setDefault(False)
        
        # 新增：预设任务按钮
        self.preset_btn = PushButton("使用预设任务")
        self.preset_btn.setAutoDefault(False)
        self.preset_btn.setDefault(False)
        
        self.del_btn = PushButton("删除当前任务")
        self.del_btn.setAutoDefault(False)  # 禁止回车触发
        self.del_btn.setDefault(False)
        self.add_btn.clicked.connect(self.add_task)
        self.preset_btn.clicked.connect(self.add_preset_task)
        self.del_btn.clicked.connect(self.delete_current_task)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.preset_btn)
        btn_layout.addWidget(self.del_btn)
        btn_layout.addStretch()  # 添加/删除靠左，stretch在中间

        # 右下角：生成/取消
        self.ok_btn = PrimaryPushButton("生成任务")
        self.ok_btn.setAutoDefault(False)  # 允许回车触发
        self.ok_btn.setDefault(False)  # 设置为默认按钮
        self.cancel_btn = PushButton("取消")
        self.cancel_btn.setAutoDefault(False)  # 禁止回车触发
        self.cancel_btn.setDefault(False)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(btn_layout)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        self.tasks = []
        self.current_index = -1

        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    tasks = yaml.safe_load(f)
                if tasks:
                    for t in tasks:
                        self.tasks.append(self._make_task_obj(t))
            except Exception:
                pass
        # 允许没有任何任务
        self.current_index = 0 if self.tasks else -1
        self.refresh_task_btns()
        if self.tasks:
            self.show_task_form(self.tasks[self.current_index])
        else:
            self.show_task_form(None)

    def refresh_task_btns(self):
        # 清空旧按钮
        while self.task_btn_layout.count():
            item = self.task_btn_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        # 重新添加按钮
        for idx, t in enumerate(self.tasks):
            btn = PushButton(t["name"])
            btn.setCheckable(True)
            btn.setChecked(idx == self.current_index)
            btn.clicked.connect(lambda checked, i=idx: self.select_task(i))
            self.task_btn_layout.addWidget(btn)
        self.task_btn_layout.addStretch()

    def get_preset_tasks(self):
        """获取所有可用的预设任务"""
        from app.tools.code_generator import CodeGenerator
        task_dir = CodeGenerator.get_assets_dir("User_code/task/template_task")
        preset_tasks = []
        
        if not os.path.exists(task_dir):
            return preset_tasks
            
        for filename in os.listdir(task_dir):
            if filename.endswith('.c') and not filename.endswith('.template'):
                task_name = os.path.splitext(filename)[0]
                preset_tasks.append(task_name)
        
        return preset_tasks

    def load_preset_task_config(self, task_name):
        """从 yaml 配置文件中加载预设任务的配置"""
        try:
            from app.tools.code_generator import CodeGenerator
            template_dir = CodeGenerator.get_assets_dir("User_code/task/template_task")
            config_file = os.path.join(template_dir, "task.yaml")
            
            if not os.path.exists(config_file):
                return None
                
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                
            if config_data and task_name in config_data:
                return config_data[task_name]
            return None
        except Exception as e:
            print(f"加载预设任务配置失败: {e}")
            return None

    def load_preset_task_code(self, task_name):
        """加载预设任务的代码内容"""
        from app.tools.code_generator import CodeGenerator
        task_dir = CodeGenerator.get_assets_dir("User_code/task/template_task")
        task_file = os.path.join(task_dir, f"{task_name}.c")
        
        if os.path.exists(task_file):
            with open(task_file, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def add_preset_task(self):
        """添加预设任务"""
        preset_tasks = self.get_preset_tasks()
        if not preset_tasks:
            InfoBar.warning(
                title="无预设任务",
                content="未找到可用的预设任务模板",
                parent=self,
                duration=2000
            )
            return
        
        # 创建自适应主题的对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("选择预设任务")
        dialog.resize(600, 500)
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        
        # 固定内容区域
        fixed_content = QWidget()
        fixed_content.setFixedHeight(180)  # 减少固定高度
        fixed_layout = QVBoxLayout(fixed_content)
        fixed_layout.setContentsMargins(0, 0, 0, 0)
        fixed_layout.setSpacing(18)
        
        # 标题
        title_label = TitleLabel("选择预设任务模板")
        fixed_layout.addWidget(title_label)
        
        # 说明文字
        desc_label = BodyLabel("选择一个预设任务模板，系统将自动复制相应的代码和配置")
        fixed_layout.addWidget(desc_label)
        
        fixed_layout.addWidget(HorizontalSeparator())
        
        # 任务选择
        select_layout = QHBoxLayout()
        select_layout.setSpacing(12)
        
        select_label = BodyLabel("预设任务：")
        preset_combo = ComboBox()
        preset_combo.addItems(preset_tasks)
        preset_combo.setCurrentIndex(0)
        preset_combo.setMinimumWidth(160)
        
        select_layout.addWidget(select_label)
        select_layout.addWidget(preset_combo)
        select_layout.addStretch()
        
        fixed_layout.addLayout(select_layout)
        
        # 参数信息 - 单行显示
        params_layout = QHBoxLayout()
        params_layout.setSpacing(24)  # 适中的间距
        
        self.info_freq = BodyLabel("")
        self.info_delay = BodyLabel("")
        self.info_stack = BodyLabel("")
        self.info_ctrl = BodyLabel("")
        
        self.info_freq.setMinimumWidth(120)
        self.info_delay.setMinimumWidth(100)
        self.info_stack.setMinimumWidth(120)
        self.info_ctrl.setMinimumWidth(100)
        
        params_layout.addWidget(self.info_freq)
        params_layout.addWidget(self.info_delay)
        params_layout.addWidget(self.info_stack)
        params_layout.addWidget(self.info_ctrl)
        params_layout.addStretch()
        
        fixed_layout.addLayout(params_layout)
        fixed_layout.addStretch()  # 在固定区域内保持紧凑
        
        layout.addWidget(fixed_content)
        
        # 弹性描述区域
        desc_layout = QVBoxLayout()
        desc_layout.setSpacing(8)
        
        desc_title = BodyLabel("描述：")
        desc_title.setStyleSheet("font-weight: bold;")
        desc_layout.addWidget(desc_title)
        
        self.preview_desc = TextEdit()
        self.preview_desc.setReadOnly(True)
        self.preview_desc.setMinimumHeight(60)  # 最小高度
        desc_layout.addWidget(self.preview_desc)
        
        layout.addLayout(desc_layout, stretch=1)  # 弹性伸缩
        
        # 按钮区域
        layout.addWidget(HorizontalSeparator())
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = PushButton("取消")
        ok_btn = PrimaryPushButton("确定添加")
        
        cancel_btn.clicked.connect(dialog.reject)
        ok_btn.clicked.connect(dialog.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)
        
        # 预览更新函数
        def update_preview():
            selected = preset_combo.currentText()
            self.update_preset_preview(selected)
        
        preset_combo.currentTextChanged.connect(update_preview)
        
        # 存储对话框状态
        self.current_preview_dialog = dialog
        self.preview_combo = preset_combo
        
        # 初始化预览
        if preset_tasks:
            update_preview()
        
        # 显示对话框
        if dialog.exec() == QDialog.Accepted:
            selected_task = preset_combo.currentText()
            self.save_form()
            new_idx = len(self.tasks)
            
            # 从配置文件加载预设任务参数
            config = self.load_preset_task_config(selected_task)
            if config:
                new_task = self._make_task_obj({
                    "name": config.get("name", selected_task),
                    "frequency": config.get("frequency", 500),
                    "delay": config.get("delay", 0),
                    "stack": config.get("stack", 256),
                    "description": config.get("description", ""),
                    "freq_control": config.get("freq_control", True)
                })
            else:
                new_task = self._make_task_obj({"name": selected_task})
            
            new_task["preset_task"] = selected_task
            
            self.tasks.append(new_task)
            self.current_index = new_idx
            self.refresh_task_btns()
            self.show_task_form(self.tasks[self.current_index])
            
            InfoBar.success(
                title="添加成功",
                content=f"已添加预设任务：{selected_task}",
                parent=self,
                duration=2000
            )

    def update_preset_preview(self, task_name):
        """更新预设任务预览信息"""        
        # 从配置加载信息
        config = self.load_preset_task_config(task_name)
        if config:
            self.info_freq.setText(f"频率: {config.get('frequency', 500)} Hz")
            self.info_delay.setText(f"延时: {config.get('delay', 0)} ms")
            self.info_stack.setText(f"堆栈: {config.get('stack', 256)} Bytes")
            freq_ctrl = "启用" if config.get('freq_control', True) else "禁用"
            self.info_ctrl.setText(f"频率控制: {freq_ctrl}")
            
            description = config.get('description', f'预设任务：{task_name}')
            self.preview_desc.setText(description)
        else:
            self.info_freq.setText("频率: 500 Hz")
            self.info_delay.setText("延时: 0 ms")
            self.info_stack.setText("堆栈: 256 Bytes")
            self.info_ctrl.setText("频率控制: 启用")
            self.preview_desc.setText(f"预设任务：{task_name}")

    def on_preset_task_selected(self, task_name):
        """预设任务选择事件（向后兼容）"""
        pass

    def get_preset_task_description(self, task_name):
        """获取预设任务的描述信息"""
        # 首先尝试从 yaml 配置中获取描述
        config = self.load_preset_task_config(task_name)
        if config and 'description' in config:
            return f"预设任务：{task_name}\n\n{config['description']}\n\n频率控制：{'启用' if config.get('freq_control', True) else '禁用'}\n运行频率：{config.get('frequency', 500)} Hz\n堆栈大小：{config.get('stack', 256)} Bytes\n初始延时：{config.get('delay', 0)} ms"
        
        # 如果没有配置文件，则从代码注释中提取
        try:
            task_code = self.load_preset_task_code(task_name)
            if task_code:
                # 尝试从注释中提取描述
                lines = task_code.split('\n')
                description_lines = []
                in_comment = False
                
                for line in lines[:20]:  # 只检查前20行
                    line = line.strip()
                    if line.startswith('/*'):
                        in_comment = True
                        if 'Task' in line and line != '/*':
                            description_lines.append(line.replace('/*', '').strip())
                        continue
                    elif line.endswith('*/'):
                        in_comment = False
                        break
                    elif in_comment and line and not line.startswith('*'):
                        description_lines.append(line)
                
                if description_lines:
                    return '\n'.join(description_lines)
                else:
                    return f"预设任务：{task_name}\n这是一个预定义的任务模板，包含完整的实现代码。"
            else:
                return f"预设任务：{task_name}\n无法读取任务描述。"
        except Exception as e:
            return f"预设任务：{task_name}\n读取描述时出现错误：{str(e)}"

    def add_task(self):
        self.save_form()
        new_idx = len(self.tasks)
        self.tasks.append(self._make_task_obj({"name": f"Task{new_idx+1}"}))
        self.current_index = new_idx
        self.refresh_task_btns()
        self.show_task_form(self.tasks[self.current_index])

    def delete_current_task(self):
        if self.current_index < 0 or not self.tasks:
            return
        del self.tasks[self.current_index]
        if not self.tasks:
            self.current_index = -1
            self.refresh_task_btns()
            self.show_task_form(None)
            return
        if self.current_index >= len(self.tasks):
            self.current_index = len(self.tasks) - 1
        self.refresh_task_btns()
        self.show_task_form(self.tasks[self.current_index])

    def select_task(self, idx):
        self.save_form()
        self.current_index = idx
        self.refresh_task_btns()
        self.show_task_form(self.tasks[idx])

    def show_task_form(self, task):
        # 先移除旧的 form_widget
        if hasattr(self, "form_widget") and self.form_widget is not None:
            self.top_layout.removeWidget(self.form_widget)
            self.form_widget.deleteLater()
            self.form_widget = None

        # 新建 form_widget 和 form_layout
        self.form_widget = QWidget()
        self.form_layout = QVBoxLayout(self.form_widget)
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.form_layout.setSpacing(12)

        # 添加到右侧
        self.top_layout.addWidget(self.form_widget, stretch=1)

        if not task:
            label = TitleLabel("暂无任务，请点击下方“添加任务”。")
            label.setAlignment(Qt.AlignCenter)
            self.form_layout.addStretch()
            self.form_layout.addWidget(label)
            self.form_layout.addStretch()
            return

        # 任务名称
        row1 = QHBoxLayout()
        label_name = BodyLabel("任务名称")
        self.name_edit = LineEdit()
        self.name_edit.setText(task["name"])
        self.name_edit.setPlaceholderText("任务名称")
        # 新增：名称编辑完成后刷新按钮
        self.name_edit.editingFinished.connect(self.on_name_edit_finished)
        row1.addWidget(label_name)
        row1.addWidget(self.name_edit)
        self.form_layout.addLayout(row1)

        # 频率
        row2 = QHBoxLayout()
        label_freq = BodyLabel("任务运行频率")
        self.freq_spin = DoubleSpinBox()
        self.freq_spin.setRange(0, 10000)
        self.freq_spin.setDecimals(3)
        self.freq_spin.setSingleStep(1)
        self.freq_spin.setSuffix(" Hz")
        self.freq_spin.setValue(float(task.get("frequency", 500)))
        row2.addWidget(label_freq)
        row2.addWidget(self.freq_spin)
        self.form_layout.addLayout(row2)

        # 延迟
        row3 = QHBoxLayout()
        label_delay = BodyLabel("初始化延时")
        self.delay_spin = SpinBox()
        self.delay_spin.setRange(0, 10000)
        self.delay_spin.setSuffix(" ms")
        self.delay_spin.setValue(task.get("delay", 0))
        row3.addWidget(label_delay)
        row3.addWidget(self.delay_spin)
        self.form_layout.addLayout(row3)

        # 堆栈
        row4 = QHBoxLayout()
        label_stack = BodyLabel("堆栈大小")
        self.stack_spin = SpinBox()
        self.stack_spin.setRange(128, 8192)
        self.stack_spin.setSingleStep(128)
        self.stack_spin.setSuffix(" Byte")  # 添加单位
        self.stack_spin.setValue(task.get("stack", 256))
        row4.addWidget(label_stack)
        row4.addWidget(self.stack_spin)
        self.form_layout.addLayout(row4)

        # 频率控制
        row5 = QHBoxLayout()
        self.freq_ctrl = CheckBox("启用默认频率控制")
        self.freq_ctrl.setChecked(task.get("freq_control", True))
        row5.addWidget(self.freq_ctrl)
        self.form_layout.addLayout(row5)

        # 描述
        label_desc = BodyLabel("任务描述")
        self.desc_edit = TextEdit()
        self.desc_edit.setText(task.get("description", ""))
        self.desc_edit.setPlaceholderText("任务描述")
        self.form_layout.addWidget(label_desc)
        self.form_layout.addWidget(self.desc_edit)

        self.form_layout.addStretch()

    def on_name_edit_finished(self):
        # 保存当前表单内容
        self.save_form()
        # 刷新左侧按钮名称
        self.refresh_task_btns()

    def _make_task_obj(self, task=None):
        return {
            "name": task["name"] if task else f"Task1",
            "frequency": task.get("frequency", 500) if task else 500,
            "delay": task.get("delay", 0) if task else 0,
            "stack": task.get("stack", 256) if task else 256,
            "description": task.get("description", "") if task else "",
            "freq_control": task.get("freq_control", True) if task else True,
        }

    def save_form(self):
        if self.current_index < 0 or self.current_index >= len(self.tasks):
            return
        t = self.tasks[self.current_index]
        t["name"] = self.name_edit.text().strip()
        t["frequency"] = float(self.freq_spin.value())  # 支持小数
        t["delay"] = self.delay_spin.value()
        t["stack"] = self.stack_spin.value()
        t["description"] = self.desc_edit.toPlainText().strip()
        t["freq_control"] = self.freq_ctrl.isChecked()


    def get_tasks(self):
        self.save_form()
        tasks = []
        for idx, t in enumerate(self.tasks):
            name = t["name"].strip()
            freq = t["frequency"]
            delay = t["delay"]
            stack = t["stack"]
            desc = t["description"].strip()
            freq_ctrl = t["freq_control"]
            if stack < 128 or (stack & (stack - 1)) != 0 or stack % 128 != 0:
                raise ValueError(f"第{idx+1}个任务“{name}”的堆栈大小必须为128、256、512、1024等（128*2^n）")
            task = {
                "name": name,
                "function": f"Task_{name}",
                "delay": delay,
                "stack": stack,
                "description": desc,
                "freq_control": freq_ctrl
            }
            if freq_ctrl:
                task["frequency"] = freq
            
            # 保留预设任务信息
            if "preset_task" in t:
                task["preset_task"] = t["preset_task"]
                
            tasks.append(task)
        return tasks