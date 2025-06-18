import sys
import os
import serial
import serial.tools.list_ports

from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QComboBox, QPushButton, QTextEdit, QLineEdit, QLabel, QSizePolicy,
    QFileDialog, QMessageBox, QStackedLayout
)

from qfluentwidgets import (
    Theme, setTheme, FluentIcon, SwitchButton, BodyLabel, SubtitleLabel,
    StrongBodyLabel, HorizontalSeparator, InfoBar, MessageDialog, Dialog,
    AvatarWidget, NavigationItemPosition, FluentWindow, NavigationAvatarWidget,
    PushButton, TextEdit, LineEdit, ComboBox, ImageLabel
)
from qfluentwidgets import FluentIcon as FIF
import requests
import shutil
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView, QHeaderView

from qfluentwidgets import (
    TreeWidget, InfoBar, InfoBarPosition, MessageDialog, TreeItemDelegate
)
from qfluentwidgets import CheckBox
from qfluentwidgets import TreeWidget
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QFileDialog
from qfluentwidgets import ProgressBar

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

        # layout.addStretch()

# ===================== 代码生成页面 =====================
class DataInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("dataInterface")
        self.stacked_layout = QStackedLayout()
        self.setLayout(self.stacked_layout)

        # --- 页面1：工程路径选择 ---
        self.select_widget = QWidget()
        select_layout = QVBoxLayout(self.select_widget)
        select_layout.addSpacing(40)
        select_layout.addWidget(SubtitleLabel("MRobot 代码生成"))
        select_layout.addWidget(HorizontalSeparator())
        select_layout.addSpacing(10)
        select_layout.addWidget(BodyLabel("请选择包含 .ioc 文件的工程文件夹，点击下方按钮进行选择。"))
        select_layout.addSpacing(20)
        self.choose_btn = PushButton("选择工程路径")
        self.choose_btn.clicked.connect(self.choose_project_folder)
        select_layout.addWidget(self.choose_btn)
        select_layout.addStretch()
        self.stacked_layout.addWidget(self.select_widget)

        # --- 页面2：代码配置 ---
        self.config_widget = QWidget()
        self.config_layout = QVBoxLayout(self.config_widget)
        # 左上角小返回按钮
        top_bar = QHBoxLayout()
        self.back_btn = PushButton('返回', icon=FluentIcon.SKIP_BACK)
        # self.back_btn.setFixedSize(32, 32)
        self.back_btn.clicked.connect(self.back_to_select)
        self.back_btn.setToolTip("返回")
        top_bar.addWidget(self.back_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        top_bar.addStretch()
        self.config_layout.addLayout(top_bar)
        self.config_layout.addWidget(SubtitleLabel("工程配置信息"))
        self.config_layout.addWidget(HorizontalSeparator())
        self.project_info_labels = []
        self.config_layout.addStretch()
        self.stacked_layout.addWidget(self.config_widget)

        # 默认显示选择页面
        self.stacked_layout.setCurrentWidget(self.select_widget)

    def choose_project_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "请选择代码项目文件夹")
        if not folder:
            return
        ioc_files = [f for f in os.listdir(folder) if f.endswith('.ioc')]
        if not ioc_files:
            QMessageBox.warning(self, "提示", "未找到.ioc文件，请确认项目文件夹。")
            return
        self.project_path = folder
        self.project_name = os.path.basename(folder)
        self.ioc_file = os.path.join(folder, ioc_files[0])
        self.show_config_page()

    def show_config_page(self):
        # 清理旧内容
        for label in self.project_info_labels:
            self.config_layout.removeWidget(label)
            label.deleteLater()
        self.project_info_labels.clear()
        # 显示项目信息
        l1 = BodyLabel(f"项目名称: {self.project_name}")
        l2 = BodyLabel(f"项目路径: {self.project_path}")
        l3 = BodyLabel(f"IOC 文件: {self.ioc_file}")
        self.config_layout.insertWidget(2, l1)
        self.config_layout.insertWidget(3, l2)
        self.config_layout.insertWidget(4, l3)
        self.project_info_labels.extend([l1, l2, l3])
        self.stacked_layout.setCurrentWidget(self.config_widget)

    def back_to_select(self):
        self.stacked_layout.setCurrentWidget(self.select_widget)

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
        #快捷指令居中
        preset_vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preset_commands = [
            ("线程监视器", "RESET"),
            ("陀螺仪校准", "GET_VERSION"),
            ("性能监视", "START"),
            ("重启", "STOP"),
            ("显示所有设备", "SELF_TEST"),
            ("查询id", "STATUS"),
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
        self.auto_enter_checkbox = CheckBox("自动回车")
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
                    # 判断是否自动回车
                    if self.auto_enter_checkbox.isChecked():
                        self.ser.write('\n'.encode())
            except Exception as e:
                self.text_edit.append(f"发送失败: {e}")
            self.input_line.clear()


# ===================== 零件库页面 =====================

# ...existing code...
class DownloadThread(QThread):
    progressChanged = pyqtSignal(int)
    finished = pyqtSignal(list, list)  # success, fail

    def __init__(self, files, server_url, secret_key, local_dir, parent=None):
        super().__init__(parent)
        self.files = files
        self.server_url = server_url
        self.secret_key = secret_key
        self.local_dir = local_dir

    def run(self):
        success, fail = [], []
        total = len(self.files)
        max_retry = 3  # 最大重试次数
        for idx, rel_path in enumerate(self.files):
            retry = 0
            while retry < max_retry:
                try:
                    url = f"{self.server_url}/download/{rel_path}"
                    params = {"key": self.secret_key}
                    resp = requests.get(url, params=params, stream=True, timeout=10)
                    if resp.status_code == 200:
                        local_path = os.path.join(self.local_dir, rel_path)
                        os.makedirs(os.path.dirname(local_path), exist_ok=True)
                        with open(local_path, "wb") as f:
                            shutil.copyfileobj(resp.raw, f)
                        success.append(rel_path)
                        break  # 下载成功，跳出重试循环
                    else:
                        print(f"下载失败({resp.status_code}): {rel_path}，第{retry+1}次尝试")
                        retry += 1
                except Exception as e:
                    print(f"下载异常: {rel_path}，第{retry+1}次尝试，错误: {e}")
                    retry += 1
            else:
                fail.append(rel_path)
            self.progressChanged.emit(int((idx + 1) / total * 100))
        self.finished.emit(success, fail)


class PartLibraryInterface(BaseInterface):
    SERVER_URL = "http://154.37.215.220:5000"
    SECRET_KEY = "MRobot_Download"
    LOCAL_LIB_DIR = "mech_lib"

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("partLibraryInterface")
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        layout.addWidget(SubtitleLabel("零件库（在线bate版）"))
        layout.addWidget(HorizontalSeparator())
        layout.addWidget(BodyLabel("可浏览服务器零件库，选择需要的文件下载到本地。（如无法使用或者下载失败，请尝试重新下载或检查网络连接）"))

        btn_layout = QHBoxLayout()
        refresh_btn = PushButton(FluentIcon.SYNC, "刷新列表")
        refresh_btn.clicked.connect(self.refresh_list)
        btn_layout.addWidget(refresh_btn)

        # 新增：打开本地零件库按钮
        open_local_btn = PushButton(FluentIcon.FOLDER, "打开本地零件库")
        open_local_btn.clicked.connect(self.open_local_lib)
        btn_layout.addWidget(open_local_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.tree = TreeWidget(self)

        self.tree.setHeaderLabels(["名称", "类型"])
        self.tree.setSelectionMode(self.tree.ExtendedSelection)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree.setCheckedColor("#0078d4", "#2d7d9a")
        self.tree.setBorderRadius(8)
        self.tree.setBorderVisible(True)
        layout.addWidget(self.tree, stretch=1)

        download_btn = PushButton(FluentIcon.DOWNLOAD, "下载选中文件")
        download_btn.clicked.connect(self.download_selected_files)
        layout.addWidget(download_btn)

        self.refresh_list(first=True)

    def refresh_list(self, first=False):
        self.tree.clear()
        try:
            resp = requests.get(
                f"{self.SERVER_URL}/list",
                params={"key": self.SECRET_KEY},
                timeout=5
            )
            resp.raise_for_status()
            tree = resp.json()
            self.populate_tree(self.tree, tree, "")
            if not first:
                InfoBar.success(
                    title="刷新成功",
                    content="零件库已经是最新的！",
                    parent=self,
                    position=InfoBarPosition.TOP,
                    duration=2000
                )
        except Exception as e:
            InfoBar.error(
                title="刷新失败",
                content=f"获取零件库失败: {e}",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )

    def populate_tree(self, parent, node, path_prefix):
        from PyQt5.QtWidgets import QTreeWidgetItem
        for dname, dnode in node.get("dirs", {}).items():
            item = QTreeWidgetItem([dname, "文件夹"])
            if isinstance(parent, TreeWidget):
                parent.addTopLevelItem(item)
            else:
                parent.addChild(item)
            self.populate_tree(item, dnode, os.path.join(path_prefix, dname))
        for fname in node.get("files", []):
            item = QTreeWidgetItem([fname, "文件"])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Unchecked)
            item.setData(0, Qt.UserRole, os.path.join(path_prefix, fname))
            if isinstance(parent, TreeWidget):
                parent.addTopLevelItem(item)
            else:
                parent.addChild(item)

    def get_checked_files(self):
        files = []
        def _traverse(item):
            for i in range(item.childCount()):
                child = item.child(i)
                if child.text(1) == "文件" and child.checkState(0) == Qt.Checked:
                    files.append(child.data(0, Qt.UserRole))
                _traverse(child)
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            _traverse(root.child(i))
        return files

    def download_selected_files(self):
        files = self.get_checked_files()
        if not files:
            InfoBar.info(
                title="提示",
                content="请先勾选要下载的文件。",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
            return

        # 进度条对话框
        self.progress_dialog = Dialog(
            title="正在下载",
            content="正在下载选中文件，请稍候...",
            parent=self
        )
        self.progress_bar = ProgressBar()
        self.progress_bar.setValue(0)
        # 插入进度条到内容布局
        self.progress_dialog.textLayout.addWidget(self.progress_bar)
        self.progress_dialog.show()

        # 启动下载线程
        self.download_thread = DownloadThread(
            files, self.SERVER_URL, self.SECRET_KEY, self.LOCAL_LIB_DIR
        )
        self.download_thread.progressChanged.connect(self.progress_bar.setValue)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.finished.connect(self.download_thread.deleteLater)
        self.download_thread.start()

    def on_download_finished(self, success, fail):
        self.progress_dialog.close()
        msg = f"成功下载: {len(success)} 个文件\n失败: {len(fail)} 个文件"
        dialog = Dialog(
            title="下载结果",
            content=msg,
            parent=self
        )
        # 添加“打开文件夹”按钮
        open_btn = PushButton("打开文件夹")
        def open_folder():
            folder = os.path.abspath(self.LOCAL_LIB_DIR)
            # 打开文件夹（macOS用open，Windows用explorer，Linux用xdg-open）
            import platform, subprocess
            if platform.system() == "Darwin":
                subprocess.call(["open", folder])
            elif platform.system() == "Windows":
                subprocess.call(["explorer", folder])
            else:
                subprocess.call(["xdg-open", folder])
            dialog.close()
        open_btn.clicked.connect(open_folder)
        # 添加按钮到Dialog布局
        dialog.textLayout.addWidget(open_btn)
        dialog.exec()

    def open_local_lib(self):
        folder = os.path.abspath(self.LOCAL_LIB_DIR)
        import platform, subprocess
        if platform.system() == "Darwin":
            subprocess.call(["open", folder])
        elif platform.system() == "Windows":
            subprocess.call(["explorer", folder])
        else:
            subprocess.call(["xdg-open", folder])

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
            (PartLibraryInterface(self), FIF.DOWNLOAD, "零件库", NavigationItemPosition.SCROLL),  # ← 加上这一行
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