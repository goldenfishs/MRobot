from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QWidget, QScrollArea
from qfluentwidgets import (
    BodyLabel, TitleLabel, HorizontalSeparator, PushButton, PrimaryPushButton,
    LineEdit, SpinBox, DoubleSpinBox, CheckBox, TextEdit
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
        self.del_btn = PushButton("删除当前任务")
        self.del_btn.setAutoDefault(False)  # 禁止回车触发
        self.del_btn.setDefault(False)
        self.add_btn.clicked.connect(self.add_task)
        self.del_btn.clicked.connect(self.delete_current_task)
        btn_layout.addWidget(self.add_btn)
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
            tasks.append(task)
        return tasks