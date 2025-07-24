import serial
import serial.tools.list_ports
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QSizePolicy
from PyQt5.QtWidgets import QWidget
from qfluentwidgets import (
    FluentIcon, PushButton, ComboBox, TextEdit, LineEdit, CheckBox,
    SubtitleLabel, BodyLabel, HorizontalSeparator
)

class SerialReadThread(QThread):
    data_received = pyqtSignal(str)

    def __init__(self, ser):
        super().__init__()
        self.ser = ser
        self._running = True

    def run(self):
        while self._running: 
            if self.ser and self.ser.is_open and self.ser.in_waiting:
                try:
                    data = self.ser.readline().decode(errors='ignore')
                    self.data_received.emit(data)
                except Exception:
                    pass

    def stop(self):
        self._running = False
        self.wait()

class SerialTerminalInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("serialTerminalInterface")
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        # 顶部：串口设置区
        top_hbox = QHBoxLayout()
        top_hbox.addWidget(BodyLabel("串口:"))
        self.port_combo = ComboBox()
        self.refresh_ports()
        top_hbox.addWidget(self.port_combo)
        top_hbox.addWidget(BodyLabel("波特率:"))
        self.baud_combo = ComboBox()
        self.baud_combo.addItems(['9600', '115200', '57600', '38400', '19200', '4800'])
        top_hbox.addWidget(self.baud_combo)
        self.connect_btn = PushButton("连接")
        self.connect_btn.clicked.connect(self.toggle_connection)
        top_hbox.addWidget(self.connect_btn)
        self.refresh_btn = PushButton(FluentIcon.SYNC, "刷新")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        top_hbox.addWidget(self.refresh_btn)
        top_hbox.addStretch()
        main_layout.addLayout(top_hbox)

        main_layout.addWidget(HorizontalSeparator())

        # 中部：左侧预设命令，右侧显示区
        center_hbox = QHBoxLayout()
        # 左侧：预设命令竖排
        preset_vbox = QVBoxLayout()
        preset_vbox.addWidget(SubtitleLabel("快捷指令"))
        preset_vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preset_commands = [
            ("线程监视器", "htop"),
            ("陀螺仪校准", "cali_gyro"),
            ("性能监视", "htop"),
            ("重启", "reset"),
            ("显示所有设备", "ls /dev"),
            ("查询id", "id"),
        ]
        for label, cmd in self.preset_commands:
            btn = PushButton(label)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            btn.clicked.connect(lambda _, c=cmd: self.send_preset_command(c))
            preset_vbox.addWidget(btn)
        preset_vbox.addStretch()
        main_layout.addLayout(center_hbox, stretch=1)

        # 右侧：串口数据显示区
        self.text_edit = TextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMinimumWidth(400)
        center_hbox.addWidget(self.text_edit, 3)
        center_hbox.addLayout(preset_vbox, 1)

        main_layout.addWidget(HorizontalSeparator())

        # 底部：输入区
        bottom_hbox = QHBoxLayout()
        self.input_line = LineEdit()
        self.input_line.setPlaceholderText("输入内容，回车发送")
        self.input_line.returnPressed.connect(self.send_data)
        bottom_hbox.addWidget(self.input_line, 4)
        send_btn = PushButton("发送")
        send_btn.clicked.connect(self.send_data)
        bottom_hbox.addWidget(send_btn, 1)
        self.auto_enter_checkbox = CheckBox("自动回车   ")
        self.auto_enter_checkbox.setChecked(True)
        bottom_hbox.addWidget(self.auto_enter_checkbox)
        bottom_hbox.addStretch()
        main_layout.addLayout(bottom_hbox)

        self.ser = None
        self.read_thread = None

    def send_preset_command(self, cmd):
        self.input_line.setText(cmd)
        self.send_data()

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(port.device)

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        port = self.port_combo.currentText()
        baud = int(self.baud_combo.currentText())
        try:
            self.ser = serial.Serial(port, baud, timeout=0.1)
            self.connect_btn.setText("断开")
            self.text_edit.append(f"已连接到 {port} @ {baud}")
            self.read_thread = SerialReadThread(self.ser)
            self.read_thread.data_received.connect(self.display_data)
            self.read_thread.start()
        except Exception as e:
            self.text_edit.append(f"连接失败: {e}")

    def disconnect_serial(self):
        if self.read_thread:
            self.read_thread.stop()
            self.read_thread = None
        if self.ser:
            self.ser.close()
            self.ser = None
        self.connect_btn.setText("连接")
        self.text_edit.append("已断开连接")

    def display_data(self, data):
        self.text_edit.moveCursor(QTextCursor.End)
        self.text_edit.insertPlainText(data)
        self.text_edit.moveCursor(QTextCursor.End)

    def send_data(self):
        if self.ser and self.ser.is_open:
            text = self.input_line.text()
            try:
                if not text:
                    self.ser.write('\n'.encode())
                else:
                    for char in text:
                        self.ser.write(char.encode())
                    if self.auto_enter_checkbox.isChecked():
                        self.ser.write('\n'.encode())
            except Exception as e:
                self.text_edit.append(f"发送失败: {e}")
            self.input_line.clear()