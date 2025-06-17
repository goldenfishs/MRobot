import sys
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication
import serial
import serial.tools.list_ports
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QComboBox, QPushButton, QTextEdit, QLineEdit, QLabel
from PyQt5.QtWidgets import QGroupBox, QGridLayout, QSizePolicy

from qfluentwidgets import (
    NavigationItemPosition, Theme, FluentWindow, NavigationAvatarWidget,
    PushButton, FluentIcon
)
from qfluentwidgets import FluentIcon as FIF

# ===================== 页面基类 =====================
class BaseInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

# ===================== 首页界面 =====================
class HomeInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("homeInterface")
        layout = QVBoxLayout()
        self.setLayout(layout)

# ===================== 代码生成页面 =====================
class DataInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("dataInterface")
        layout = QVBoxLayout()
        self.setLayout(layout)

# ===================== 串口终端界面 =====================
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

class SerialTerminalInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("serialTerminalInterface")
        layout = QVBoxLayout(self)

        # 串口选择和连接
        hbox = QHBoxLayout()
        self.port_combo = QComboBox()
        self.refresh_ports()
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(['9600', '115200', '57600', '38400', '19200', '4800'])
        self.connect_btn = QPushButton("连接")
        self.connect_btn.clicked.connect(self.toggle_connection)
        hbox.addWidget(QLabel("串口:"))
        hbox.addWidget(self.port_combo)
        hbox.addWidget(QLabel("波特率:"))
        hbox.addWidget(self.baud_combo)
        hbox.addWidget(self.connect_btn)
        layout.addLayout(hbox)

        # 预设命令区
        preset_group = QGroupBox("预设命令")
        preset_layout = QGridLayout()
        self.preset_commands = [
            ("复位", "RESET"),
            ("获取版本", "GET_VERSION"),
            ("启动", "START"),
            ("停止", "STOP"),
            ("自检", "SELF_TEST"),
            ("查询状态", "STATUS?"),
        ]
        for i, (label, cmd) in enumerate(self.preset_commands):
            btn = QPushButton(label)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            btn.clicked.connect(lambda _, c=cmd: self.send_preset_command(c))
            preset_layout.addWidget(btn, i // 3, i % 3)
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)

        # 显示区
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet(
            "background-color: #1e1e1e; color: #d4d4d4; font-family: Consolas, 'Courier New', monospace; font-size: 14px;"
        )
        layout.addWidget(self.text_edit)

        # 输入区
        input_hbox = QHBoxLayout()
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("输入内容，回车发送")
        self.input_line.returnPressed.connect(self.send_data)
        send_btn = QPushButton("发送")
        send_btn.clicked.connect(self.send_data)
        input_hbox.addWidget(self.input_line)
        input_hbox.addWidget(send_btn)
        layout.addLayout(input_hbox)

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
                    # 内容为空，只发送换行
                    self.ser.write('\n'.encode())
                else:
                    # 逐字符发送
                    for char in text:
                        self.ser.write(char.encode())
                    # 结尾加换行
                    self.ser.write('\n'.encode())
            except Exception as e:
                self.text_edit.append(f"发送失败: {e}")
            self.input_line.clear()

# ===================== 设置界面 =====================
class SettingInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("settingInterface")
        layout = QVBoxLayout()
        self.setLayout(layout)

# ===================== 帮助与关于界面 =====================
class HelpInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("helpInterface")
        layout = QVBoxLayout()
        self.setLayout(layout)

class AboutInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("aboutInterface")
        layout = QVBoxLayout()
        self.setLayout(layout)

# ===================== 主窗口与导航 =====================
class MainWindow(FluentWindow):
    themeChanged = pyqtSignal(Theme)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MR_ToolBox")
        self.resize(1000, 700)
        self.setMinimumSize(800, 600)

        self.page_registry = [
            (HomeInterface(self), FIF.HOME, "首页", NavigationItemPosition.TOP),
            (DataInterface(self), FIF.LIBRARY, "MRobot代码生成", NavigationItemPosition.SCROLL),
            (SerialTerminalInterface(self), FIF.COMMAND_PROMPT, "串口终端", NavigationItemPosition.SCROLL),
            (SettingInterface(self), FIF.SETTING, "设置", NavigationItemPosition.BOTTOM),
            (HelpInterface(self), FIF.HELP, "帮助", NavigationItemPosition.BOTTOM),
            (AboutInterface(self), FIF.INFO, "关于", NavigationItemPosition.BOTTOM),
        ]
        self.initNavigation()

    def initNavigation(self):
        for page, icon, name, position in self.page_registry:
            self.addSubInterface(page, icon, name, position)
        self.navigationInterface.addSeparator()
        avatar = NavigationAvatarWidget('用户', ':/qfluentwidgets/images/avatar.png')
        self.navigationInterface.addWidget(
            routeKey='avatar',
            widget=avatar,
            onClick=None,
            position=NavigationItemPosition.BOTTOM
        )

# ===================== 程序入口 =====================
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()