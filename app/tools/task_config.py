from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout
from qfluentwidgets import TitleLabel, BodyLabel, TableWidget, PushButton, SubtitleLabel, SpinBox, InfoBar, InfoBarPosition, LineEdit, CheckBox
from PyQt5.QtCore import Qt
import yaml
import os

class TaskConfigDialog(QDialog):
    def __init__(self, parent=None, config_path=None):
        super().__init__(parent)
        self.setWindowTitle("任务配置")
        self.resize(900, 480)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(18)

        layout.addWidget(TitleLabel("FreeRTOS 任务配置"))
        layout.addWidget(BodyLabel("请添加并配置您的任务参数，支持频率控制与描述。"))

        self.table = TableWidget(self)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["任务名称", "运行频率", "初始化延迟", "堆栈大小", "任务描述", "频率控制"])
        self.table.horizontalHeader().setSectionResizeMode(0, self.table.horizontalHeader().Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, self.table.horizontalHeader().ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, self.table.horizontalHeader().ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, self.table.horizontalHeader().ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, self.table.horizontalHeader().Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, self.table.horizontalHeader().ResizeToContents)
        self.table.setMinimumHeight(260)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.add_btn = PushButton("添加任务")
        self.del_btn = PushButton("删除选中")
        self.ok_btn = PushButton("生成")
        self.cancel_btn = PushButton("取消")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.del_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.add_btn.clicked.connect(self.add_row)
        self.del_btn.clicked.connect(self.del_row)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        # 自动读取配置文件
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    tasks = yaml.safe_load(f)
                if tasks:
                    for t in tasks:
                        self.add_row(t)
            except Exception:
                pass

    def add_row(self, task=None):
        row = self.table.rowCount()
        self.table.insertRow(row)
        name = LineEdit(task.get("name", f"Task{row+1}") if task else f"Task{row+1}")
        freq = SpinBox()
        freq.setRange(1, 10000)
        freq.setValue(task.get("frequency", 500) if task else 500)
        delay = SpinBox()
        delay.setRange(0, 10000)
        delay.setValue(task.get("delay", 0) if task else 0)
        stack = SpinBox()
        stack.setRange(128, 8192)
        stack.setSingleStep(128)
        stack.setValue(task.get("stack", 256) if task else 256)
        desc = LineEdit(task.get("description", "") if task else "请填写任务描述")
        freq_ctrl = CheckBox("启用")
        freq_ctrl.setChecked(task.get("freq_control", True) if task else True)

        self.table.setCellWidget(row, 0, name)
        self.table.setCellWidget(row, 1, freq)
        self.table.setCellWidget(row, 2, delay)
        self.table.setCellWidget(row, 3, stack)
        self.table.setCellWidget(row, 4, desc)
        self.table.setCellWidget(row, 5, freq_ctrl)

    def del_row(self):
        selected = self.table.selectedItems()
        if selected:
            rows = set(item.row() for item in selected)
            for row in sorted(rows, reverse=True):
                self.table.removeRow(row)

    def get_tasks(self):
        tasks = []
        for row in range(self.table.rowCount()):
            name = self.table.cellWidget(row, 0).text().strip()
            freq = self.table.cellWidget(row, 1).value()
            delay = self.table.cellWidget(row, 2).value()
            stack = self.table.cellWidget(row, 3).value()
            desc = self.table.cellWidget(row, 4).text().strip()
            freq_ctrl = self.table.cellWidget(row, 5).isChecked()
            # 校验 stack 必须为 128*2^n
            if stack < 128 or (stack & (stack - 1)) != 0 or stack % 128 != 0:
                raise ValueError(f"第{row+1}行任务“{name}”的堆栈大小必须为128、256、512、1024等（128*2^n）")
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