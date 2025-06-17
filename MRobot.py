import sys
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication
import serial
import serial.tools.list_ports
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QComboBox, QPushButton, QTextEdit, QLineEdit, QLabel
from PyQt5.QtWidgets import QGroupBox, QGridLayout, QSizePolicy
from qfluentwidgets import Theme, setTheme
from qfluentwidgets import (
    NavigationItemPosition, Theme, FluentWindow, NavigationAvatarWidget,
    PushButton, FluentIcon
)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import Theme, setTheme, FluentIcon, SwitchButton
from qfluentwidgets import BodyLabel
from qfluentwidgets import BodyLabel, TextEdit, LineEdit, ComboBox, PushButton, SwitchButton
from qfluentwidgets import BodyLabel, SubtitleLabel, StrongBodyLabel, HorizontalSeparator, InfoBar
from qfluentwidgets import MessageDialog
from qfluentwidgets import Dialog, StrongBodyLabel, BodyLabel, SubtitleLabel, AvatarWidget
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from qfluentwidgets import Dialog
from qfluentwidgets import StrongBodyLabel, SubtitleLabel, BodyLabel, PushButton, AvatarWidget, HorizontalSeparator
from qfluentwidgets import ImageLabel

# ===================== 页面基类 =====================
class BaseInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

# ===================== 首页界面 =====================
# ...existing code...

# ...existing code...

class HomeInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("homeInterface")
        layout = QVBoxLayout()
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(32)
        self.setLayout(layout)

        # 顶部logo和欢迎区
        top_layout = QHBoxLayout()
        logo = ImageLabel('img/MRobot.png')
        logo.setFixedSize(260, 80)
        top_layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignTop)
        title_layout = QVBoxLayout()
        title_layout.addWidget(StrongBodyLabel("欢迎使用 MRobot Toolbox"))
        title_layout.addWidget(SubtitleLabel("让你的机器人开发更高效、更智能"))
        top_layout.addLayout(title_layout)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        layout.addWidget(HorizontalSeparator())

        # 项目简介
        layout.addWidget(BodyLabel(
            "MRobot Toolbox 是一款集成化的机器人开发辅助工具，"
            "支持代码生成、串口终端、主题切换等多种实用功能。\n"
            "点击左侧导航栏可快速切换各功能页面。"
        ))

        # 开发者与项目目标
        layout.addWidget(HorizontalSeparator())
        layout.addWidget(SubtitleLabel("开发者与项目目标"))
        layout.addWidget(BodyLabel("开发团队：QUT 青岛理工大学 MOVE 战队"))
        layout.addWidget(BodyLabel("项目目标：为所有 rmer 和 rcer 提供现代化、简单、高效的机器人开发方式，"
                                  "让机器人开发变得更轻松、更智能。"))
        layout.addWidget(BodyLabel("适用于 RM、RC、各类嵌入式机器人项目。"))

        # # 开源与版本信息
        # layout.addWidget(HorizontalSeparator())
        # layout.addWidget(SubtitleLabel("项目信息"))
        # layout.addWidget(BodyLabel("开源地址: https://github.com/QUT-MOVE/MRobot-Toolbox"))
        # layout.addWidget(BodyLabel("当前版本: v1.0.0"))
        # layout.addWidget(BodyLabel("反馈邮箱: move@qut.edu.cn"))

        # # 致谢
        # layout.addWidget(HorizontalSeparator())
        # layout.addWidget(SubtitleLabel("致谢"))
        # layout.addWidget(BodyLabel("感谢所有开源社区贡献者，特别感谢 RM/RC 机器人开发者的持续支持。"))

        layout.addStretch()

# ...existing code...

# ...existing code...


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
        self.port_combo = ComboBox()  # 替换QComboBox为ComboBox
        self.refresh_ports()
        self.baud_combo = ComboBox()  # 替换QComboBox为ComboBox
        self.baud_combo.addItems(['9600', '115200', '57600', '38400', '19200', '4800'])
        self.connect_btn = PushButton("连接")  # 替换QPushButton为PushButton
        self.connect_btn.clicked.connect(self.toggle_connection)
        hbox.addWidget(BodyLabel("串口:"))
        hbox.addWidget(self.port_combo)
        hbox.addWidget(BodyLabel("波特率:"))
        hbox.addWidget(self.baud_combo)
        hbox.addWidget(self.connect_btn)
        layout.addLayout(hbox)

        # 预设命令区
        preset_group = QGroupBox("预设命令")
        preset_layout = QGridLayout()
        self.preset_commands = [
            ("线程监视器", "RESET"),
            ("陀螺仪校准", "GET_VERSION"),
            ("性能监视", "START"),
            ("重启", "STOP"),
            ("显示所有device", "SELF_TEST"),
            ("查询id", "STATUS"),
        ]
        for i, (label, cmd) in enumerate(self.preset_commands):
            btn = PushButton(label)  # 替换QPushButton为PushButton
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            btn.clicked.connect(lambda _, c=cmd: self.send_preset_command(c))
            preset_layout.addWidget(btn, i // 3, i % 3)
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)

        # 显示区
        self.text_edit = TextEdit()  # 替换QTextEdit为TextEdit
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        # 输入区
        input_hbox = QHBoxLayout()
        self.input_line = LineEdit()
        self.input_line.setPlaceholderText("输入内容，回车发送")
        self.input_line.returnPressed.connect(self.send_data)
        send_btn = PushButton("发送")
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
                    self.ser.write('\n'.encode())
                else:
                    for char in text:
                        self.ser.write(char.encode())
                    self.ser.write('\n'.encode())
            except Exception as e:
                self.text_edit.append(f"发送失败: {e}")
            self.input_line.clear()

# ===================== 设置界面 =====================
class SettingInterface(BaseInterface):
    themeSwitchRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("settingInterface")
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 标题
        layout.addSpacing(10)
        layout.addWidget(SubtitleLabel("设置中心"))
        layout.addSpacing(10)
        layout.addWidget(HorizontalSeparator())

        # 主题切换区域
        theme_title = StrongBodyLabel("外观设置")
        theme_desc = BodyLabel("切换夜间/白天模式，适应不同环境。")
        theme_desc.setWordWrap(True)
        layout.addSpacing(10)
        layout.addWidget(theme_title)
        layout.addWidget(theme_desc)

        theme_box = QHBoxLayout()
        self.theme_label = BodyLabel("夜间模式")
        self.theme_switch = SwitchButton()
        self.theme_switch.setChecked(Theme.DARK == Theme.DARK)
        self.theme_switch.checkedChanged.connect(self.on_theme_switch)
        theme_box.addWidget(self.theme_label)
        theme_box.addWidget(self.theme_switch)
        theme_box.addStretch()
        layout.addLayout(theme_box)

        layout.addSpacing(15)
        layout.addWidget(HorizontalSeparator())

        # 其它设置区域（示例）
        other_title = StrongBodyLabel("其它设置")
        other_desc = BodyLabel("更多功能正在开发中，敬请期待。")
        other_desc.setWordWrap(True)
        layout.addSpacing(10)
        layout.addWidget(other_title)
        layout.addWidget(other_desc)

        # 版权信息
        layout.addStretch()
        copyright_label = BodyLabel("© 2025 MRobot Toolbox")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(copyright_label)
        layout.addSpacing(10)

    def on_theme_switch(self, checked):
        self.themeSwitchRequested.emit()
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

        # 记录当前主题
        self.current_theme = Theme.DARK

        # 创建页面实例
        self.setting_page = SettingInterface(self)
        self.setting_page.themeSwitchRequested.connect(self.toggle_theme)

        self.page_registry = [
            (HomeInterface(self), FIF.HOME, "首页", NavigationItemPosition.TOP),
            (DataInterface(self), FIF.LIBRARY, "MRobot代码生成", NavigationItemPosition.SCROLL),
            (SerialTerminalInterface(self), FIF.COMMAND_PROMPT, "Mini_Shell", NavigationItemPosition.SCROLL),
            (self.setting_page, FIF.SETTING, "设置", NavigationItemPosition.BOTTOM),
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
            onClick=self.show_user_info,  # 这里改为 self.show_user_info
            position=NavigationItemPosition.BOTTOM
        )

    def toggle_theme(self):
        # 切换主题
        if self.current_theme == Theme.DARK:
            self.current_theme = Theme.LIGHT
        else:
            self.current_theme = Theme.DARK
        setTheme(self.current_theme)
        # 同步设置界面按钮状态
        self.setting_page.theme_switch.setChecked(self.current_theme == Theme.DARK)
    
    def show_user_info(self):
        dialog = Dialog(
            title="用户信息",
            content="用户：MRobot至尊VIP用户",
            parent=self
        )
        dialog.exec()

# ===================== 程序入口 =====================
def main():
    app = QApplication(sys.argv)
    setTheme(Theme.DARK)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()