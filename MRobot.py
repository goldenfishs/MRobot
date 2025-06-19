import sys
import os
import serial
import serial.tools.list_ports

from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QSizePolicy,
    QFileDialog, QMessageBox, QStackedLayout
)

from qfluentwidgets import (
    Theme, setTheme, FluentIcon, SwitchButton, BodyLabel, SubtitleLabel,TitleLabel,
    StrongBodyLabel, HorizontalSeparator, InfoBar, MessageDialog, Dialog,
    AvatarWidget, NavigationItemPosition, FluentWindow, NavigationAvatarWidget,
    PushButton, TextEdit, LineEdit, ComboBox, ImageLabel, 
)
from qfluentwidgets import FluentIcon as FIF
import requests
import shutil
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHeaderView

from qfluentwidgets import (
    TreeWidget, InfoBar, InfoBarPosition,
)
from qfluentwidgets import CheckBox
from qfluentwidgets import TreeWidget
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QFileDialog
from qfluentwidgets import ProgressBar
import zipfile
import io
import jinja2 
from PyQt5.QtWidgets import QTreeWidgetItem as TreeItem
import yaml  # 确保已安装 pyyaml
import requests
from PyQt5.QtCore import Qt, QTimer
from qfluentwidgets import (
    SettingCardGroup, SettingCard, ExpandSettingCard, HyperlinkButton, PushButton,
    SubtitleLabel, StrongBodyLabel, BodyLabel, HorizontalSeparator, FluentIcon, InfoBar, InfoBarPosition
)
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import (
    SettingCardGroup, ExpandSettingCard, SubtitleLabel, BodyLabel, HorizontalSeparator, FluentIcon, InfoBar
    
)
# 添加quote
from urllib.parse import quote

from packaging.version import parse as vparse
__version__ = "1.0.0"

# ===================== 页面基类 =====================
class BaseInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

# ===================== 启动界面 =====================
from qfluentwidgets import ImageLabel, TitleLabel, BodyLabel, ProgressBar, PushSettingCard, HyperlinkCard
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt
# ...existing code...

from qfluentwidgets import isDarkTheme  # 加入主题判断

class SplashScreen(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 自动适配主题
        dark = isDarkTheme()
        bg_color = "#23272e" if dark else "#f7fafd"
        text_color = "#e9f6ff" if dark else "#2d7d9a"
        sub_color = "#b0b8c1" if dark else "#6b7b8c"
        border_color = "#3a3f4b" if dark else "#e0e6ef"

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedSize(420, 260)
        self.setStyleSheet(f"""
            QDialog {{
                background: {bg_color};
                border-radius: 18px;
                border: 1px solid {border_color};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 36, 36, 36)
        layout.setSpacing(18)

        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Logo
        self.logo = ImageLabel('img/MRobot.png')
        self.logo.setFixedSize(220, 56)
        self.logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logo, alignment=Qt.AlignCenter)

        # 应用名
        self.title = TitleLabel("MRobot Toolbox")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet(f"font-size: 26px; font-weight: bold; color: {text_color};")
        layout.addWidget(self.title)

        # 状态文本
        self.status = BodyLabel("正在启动...")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet(f"font-size: 15px; color: {sub_color};")
        layout.addWidget(self.status)

        # 进度条
        self.progress = ProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedHeight(10)
        layout.addWidget(self.progress)

        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def set_status(self, text, value=None):
        self.status.setText(text)
        if value is not None:
            self.progress.setValue(value)

# ===================== 首页界面 =====================
class HomeInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("homeInterface")

        # 外层居中布局
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        outer_layout.addStretch()

        # 直接用布局和控件，无卡片
        content_layout = QVBoxLayout()
        content_layout.setSpacing(24)
        content_layout.setContentsMargins(48, 48, 48, 48)

        # Logo
        logo = ImageLabel('img/MRobot.png')
        logo.setFixedSize(320, 80)
        logo.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(logo, alignment=Qt.AlignHCenter)

        content_layout.addSpacing(8)
        content_layout.addStretch()
        # 主标题
        title = SubtitleLabel("MRobot Toolbox")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: bold;")
        content_layout.addWidget(title)

        # 副标题
        subtitle = BodyLabel("现代化，多功能机器人开发工具箱")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 18px; color: #4a6fa5;")
        content_layout.addWidget(subtitle)

        # 欢迎语
        welcome = BodyLabel("欢迎使用 MRobot Toolbox！一站式支持代码生成、硬件管理、串口调试与零件库下载。")
        welcome.setAlignment(Qt.AlignCenter)
        welcome.setStyleSheet("font-size: 15px;")
        content_layout.addWidget(welcome)

        content_layout.addSpacing(16)
        content_layout.addStretch()

        # 直接加到主布局
        outer_layout.addLayout(content_layout)
        outer_layout.addStretch()

       # 版权信息置底
        copyright_label = BodyLabel("© 2025 MRobot | Powered by QUT RM&RCer")
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setStyleSheet("font-size: 13px;")
        outer_layout.addWidget(copyright_label)
        outer_layout.addSpacing(18)

# ===================== 代码生成页面 =====================
class IocConfig:
    def __init__(self, ioc_path):
        self.ioc_path = ioc_path
        self.config = {}
        self._parse()

    def _parse(self):
        with open(self.ioc_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    self.config[key.strip()] = value.strip()

    def is_freertos_enabled(self):
        # 判断是否开启FreeRTOS
        ip_keys = [k for k in self.config if k.startswith('Mcu.IP')]
        for k in ip_keys:
            if self.config[k] == 'FREERTOS':
                return True
        for k in self.config:
            if k.startswith('FREERTOS.'):
                return True
        return False

    # 可扩展：添加更多参数获取方法
    def get_parameter(self, key, default=None):
        return self.config.get(key, default)

    def get_all_with_prefix(self, prefix):
        return {k: v for k, v in self.config.items() if k.startswith(prefix)}

class DataInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("dataInterface")

        # 属性初始化
        self.project_path = ""
        self.project_name = ""
        self.ioc_file = ""
        self.freertos_enabled = False  # 新增属性

        # 主布局
        self.stacked_layout = QStackedLayout(self)
        self.setLayout(self.stacked_layout)

        # --- 页面1：工程路径选择 ---
        self.select_widget = QWidget()
        outer_layout = QVBoxLayout(self.select_widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addStretch()

        # 直接用布局和控件，无卡片
        content_layout = QVBoxLayout()
        content_layout.setSpacing(28)
        content_layout.setContentsMargins(48, 48, 48, 48)

        # 主标题
        title = TitleLabel("MRobot 代码生成")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 36px; font-weight: bold; color: #2d7d9a;")
        content_layout.addWidget(title)

        # 副标题
        subtitle = BodyLabel("请选择您的由CUBEMX生成的工程路径（.ico所在的目录），然后开启代码之旅！")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 16px; color: #4a6fa5;")
        content_layout.addWidget(subtitle)

        # 简要说明
        desc = BodyLabel("支持自动配置和生成任务，自主选择模块代码倒入，自动识别cubemx配置！")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("font-size: 14px; color: #6b7b8c;")
        content_layout.addWidget(desc)

        content_layout.addSpacing(18)

        # 选择项目路径按钮
        self.choose_btn = PushButton(FluentIcon.FOLDER, "选择项目路径")
        self.choose_btn.setFixedWidth(200)
        self.choose_btn.setStyleSheet("font-size: 17px;")
        self.choose_btn.clicked.connect(self.choose_project_folder)
        content_layout.addWidget(self.choose_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # 更新代码库按钮
        self.update_template_btn = PushButton(FluentIcon.SYNC, "更新代码库")
        self.update_template_btn.setFixedWidth(200)
        self.update_template_btn.setStyleSheet("font-size: 17px;")
        self.update_template_btn.clicked.connect(self.update_user_template)
        content_layout.addWidget(self.update_template_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        content_layout.addSpacing(10)
        content_layout.addStretch()

        
        outer_layout.addLayout(content_layout)
        outer_layout.addStretch()

        self.stacked_layout.addWidget(self.select_widget)


        # --- 页面2：主配置页面 ---
        self.config_widget = QWidget()
        main_layout = QVBoxLayout(self.config_widget)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(18)

        # 顶部项目信息
        info_layout = QHBoxLayout()
        self.back_btn = PushButton(FluentIcon.SKIP_BACK, "返回")
        self.back_btn.setFixedWidth(90)
        self.back_btn.clicked.connect(self.back_to_select)
        info_layout.addWidget(self.back_btn)  # 返回按钮放最左
        self.project_name_label = StrongBodyLabel()
        self.project_path_label = BodyLabel()
        self.ioc_file_label = BodyLabel()
        self.freertos_label = BodyLabel()
        info_layout.addWidget(self.project_name_label)
        info_layout.addWidget(self.project_path_label)
        info_layout.addWidget(self.ioc_file_label)
        info_layout.addWidget(self.freertos_label)
        info_layout.addStretch()
        main_layout.addLayout(info_layout)
        main_layout.addWidget(HorizontalSeparator())

        # ======= 新增：左右分栏 =======
        content_hbox = QHBoxLayout()
        content_hbox.setSpacing(24)

        # 左侧：文件树
        left_vbox = QVBoxLayout()
        left_vbox.addWidget(SubtitleLabel("用户代码模块选择"))
        left_vbox.addWidget(HorizontalSeparator())
        self.file_tree = TreeWidget()
        self.file_tree.setHeaderLabels(["模块名"])
        self.file_tree.setSelectionMode(self.file_tree.ExtendedSelection)
        self.file_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.file_tree.setCheckedColor("#0078d4", "#2d7d9a")
        self.file_tree.setBorderRadius(8)
        self.file_tree.setBorderVisible(True)
        left_vbox.addWidget(self.file_tree, stretch=1)
        content_hbox.addLayout(left_vbox, 2)

        # 右侧：操作按钮和说明
        right_vbox = QVBoxLayout()
        right_vbox.setSpacing(18)
        right_vbox.addWidget(SubtitleLabel("操作区"))
        right_vbox.addWidget(HorizontalSeparator())

        # 操作按钮分组
        btn_group = QVBoxLayout()
        # 自动环境配置按钮
        self.env_btn = PushButton("自动环境配置")
        self.env_btn.setFixedWidth(200)
        self.env_btn.setToolTip("自动检测并配置常用开发环境（功能开发中）")
        self.env_btn.clicked.connect(self.auto_env_config)
        btn_group.addWidget(self.env_btn)
        # FreeRTOS相关按钮
        self.freertos_task_btn = PushButton("自动生成FreeRTOS任务")
        self.freertos_task_btn.setFixedWidth(200)
        self.freertos_task_btn.setToolTip("自动在 freertos.c 中插入任务创建代码")
        self.freertos_task_btn.clicked.connect(self.on_freertos_task_btn_clicked)
        btn_group.addWidget(self.freertos_task_btn)
        self.task_code_btn = PushButton("配置并生成任务代码")
        self.task_code_btn.setFixedWidth(200)
        self.task_code_btn.setToolTip("配置任务参数并一键生成任务代码文件")
        self.task_code_btn.clicked.connect(self.on_task_code_btn_clicked)
        btn_group.addWidget(self.task_code_btn)
        self.generate_btn = PushButton(FluentIcon.CODE, "生成代码")
        self.generate_btn.setFixedWidth(200)
        self.generate_btn.setToolTip("将选中的用户模块代码复制到工程 User 目录")
        self.generate_btn.clicked.connect(self.generate_code)
        btn_group.addWidget(self.generate_btn)
        btn_group.addSpacing(10)
        right_vbox.addLayout(btn_group)
        right_vbox.addStretch()

        content_hbox.addLayout(right_vbox, 1)
        main_layout.addLayout(content_hbox, stretch=1)
        self.stacked_layout.addWidget(self.config_widget)
        self.file_tree.itemChanged.connect(self.on_tree_item_changed)

    def auto_env_config(self):
        InfoBar.info(
            title="敬请期待",
            content="自动环境配置功能暂未实现，等待后续更新。",
            parent=self,
            duration=2000
        )

    def choose_project_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "请选择代码项目文件夹")
        if not folder:
            return
        ioc_files = [f for f in os.listdir(folder) if f.endswith('.ioc')]
        if not ioc_files:
            InfoBar.warning(
                title="提示",
                content="未找到.ioc文件，请确认项目文件夹。",
                parent=self,
                duration=2000
            )
            return
        self.project_path = folder
        self.project_name = os.path.basename(folder)
        self.ioc_file = os.path.join(folder, ioc_files[0])
        self.show_config_page()

    def show_config_page(self):
        # 更新项目信息
        self.project_name_label.setText(f"项目名称: {self.project_name}")
        self.project_path_label.setText(f"项目路径: {self.project_path}")
        # self.ioc_file_label.setText(f"IOC 文件: {self.ioc_file}")
        try:
            ioc = IocConfig(self.ioc_file)
            self.freertos_enabled = ioc.is_freertos_enabled()  # 记录状态
            freertos_status = "已启用" if self.freertos_enabled else "未启用"
            self.freertos_label.setText(f"FreeRTOS: {freertos_status}")
            # self.freertos_task_btn.setEnabled(self.freertos_enabled)
        except Exception as e:
            self.freertos_label.setText(f"IOC解析失败: {e}")
            self.freertos_task_btn.hide()
            self.freertos_enabled = False
        self.show_user_code_files()
        self.stacked_layout.setCurrentWidget(self.config_widget)

    def on_freertos_task_btn_clicked(self):
        if not self.freertos_enabled:
            InfoBar.warning(
                title="未开启 FreeRTOS",
                content="请先在 CubeMX 中开启 FreeRTOS！",
                parent=self,
                duration=2000
            )
            return
        self.generate_freertos_task()

    def on_task_code_btn_clicked(self):
        if not self.freertos_enabled:
            InfoBar.warning(
                title="未开启 FreeRTOS",
                content="请先在 CubeMX 中开启 FreeRTOS！",
                parent=self,
                duration=2000
            )
            return
        self.open_task_config_dialog()

    def back_to_select(self):
        self.stacked_layout.setCurrentWidget(self.select_widget)

    def update_user_template(self):
        url = "http://gitea.qutrobot.top/robofish/MRobot/archive/User_code.zip"
        local_dir = "User_code"
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            z = zipfile.ZipFile(io.BytesIO(resp.content))
            if os.path.exists(local_dir):
                shutil.rmtree(local_dir)
            for member in z.namelist():
                rel_path = os.path.relpath(member, z.namelist()[0])
                if rel_path == ".":
                    continue
                target_path = os.path.join(local_dir, rel_path)
                if member.endswith('/'):
                    os.makedirs(target_path, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with open(target_path, "wb") as f:
                        f.write(z.read(member))
            InfoBar.success(
                title="更新成功",
                content="用户模板已更新到最新版本！",
                parent=self,
                duration=2000
            )
        except Exception as e:
            InfoBar.error(
                title="更新失败",
                content=f"用户模板更新失败: {e}",
                parent=self,
                duration=3000
            )

    def show_user_code_files(self):
        self.file_tree.clear()
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "User_code")
        user_dir = os.path.join(self.project_path, "User")
        sub_dirs = ["bsp", "component", "device", "module"]
    
        # 读取所有 describe.csv 和 dependencies.csv
        describe_map = {}
        dependencies_map = {}
        for sub in sub_dirs:
            dir_path = os.path.join(base_dir, sub)
            if not os.path.isdir(dir_path):
                continue
            # describe
            desc_path = os.path.join(dir_path, "describe.csv")
            if os.path.exists(desc_path):
                with open(desc_path, encoding="utf-8") as f:
                    for line in f:
                        if "," in line:
                            k, v = line.strip().split(",", 1)
                            describe_map[f"{sub}/{k.strip()}"] = v.strip()
            # dependencies
            dep_path = os.path.join(dir_path, "dependencies.csv")
            if os.path.exists(dep_path):
                with open(dep_path, encoding="utf-8") as f:
                    for line in f:
                        if "," in line:
                            a, b = line.strip().split(",", 1)
                            dependencies_map.setdefault(f"{sub}/{a.strip()}", []).append(b.strip())
    
        self._describe_map = describe_map
        self._dependencies_map = dependencies_map
    
        self.file_tree.setHeaderLabels(["模块名", "描述"])
        self.file_tree.setSelectionMode(self.file_tree.ExtendedSelection)
        self.file_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.file_tree.header().setSectionResizeMode(1, QHeaderView.Stretch)  # 描述列自适应
        self.file_tree.setCheckedColor("#0078d4", "#2d7d9a")
        self.file_tree.setBorderRadius(8)
        self.file_tree.setBorderVisible(True)
    
        for sub in sub_dirs:
            dir_path = os.path.join(base_dir, sub)
            if not os.path.isdir(dir_path):
                continue
            group_item = TreeItem([sub, ""])
            self.file_tree.addTopLevelItem(group_item)
            has_file = False
            for root, _, files in os.walk(dir_path):
                rel_root = os.path.relpath(root, base_dir)
                for f in sorted(files):
                    if f.endswith(".c"):
                        mod_name = os.path.splitext(f)[0]
                        rel_c = os.path.join(rel_root, f)
                        key = f"{rel_root}/{mod_name}".replace("\\", "/")
                        desc = describe_map.get(key, "")
                        file_item = TreeItem([mod_name, desc])
                        file_item.setFlags(file_item.flags() | Qt.ItemIsUserCheckable)
                        file_item.setData(0, Qt.UserRole, rel_c)
                        file_item.setData(0, Qt.UserRole + 1, key)  # 存模块key
                        file_item.setToolTip(1, desc)
                        file_item.setTextAlignment(1, Qt.AlignLeft | Qt.AlignVCenter)
                        group_item.addChild(file_item)
                        dst_c = os.path.join(user_dir, rel_c)
                        if os.path.exists(dst_c):
                            file_item.setCheckState(0, Qt.Unchecked)
                            file_item.setText(0, f"{mod_name}（已存在）")
                            file_item.setForeground(0, Qt.gray)
                        else:
                            file_item.setCheckState(0, Qt.Unchecked)
                        group_item.addChild(file_item)
                        has_file = True
            if not has_file:
                empty_item = TreeItem(["（无 .c 文件）", ""])
                group_item.addChild(empty_item)
        self.file_tree.expandAll()
    
    # 勾选依赖自动勾选
    def on_tree_item_changed(self, item, column):
        if column != 0:
            return
        if item.childCount() > 0:
            return  # 只处理叶子
        if item.checkState(0) == Qt.Checked:
            key = item.data(0, Qt.UserRole + 1)
            deps = self._dependencies_map.get(key, [])
            if deps:
                checked = []
                root = self.file_tree.invisibleRootItem()
                for i in range(root.childCount()):
                    group = root.child(i)
                    for j in range(group.childCount()):
                        child = group.child(j)
                        ckey = child.data(0, Qt.UserRole + 1)
                        if ckey in deps and child.checkState(0) != Qt.Checked:
                            child.setCheckState(0, Qt.Checked)
                            checked.append(ckey)
                if checked:
                    descs = [self._describe_map.get(dep, dep) for dep in checked]
                    InfoBar.info(
                        title="依赖自动勾选",
                        content="已自动勾选依赖模块: " + "，".join(descs),
                        parent=self,
                        duration=2000
                    )
    

    def get_checked_files(self):
        files = []
        def _traverse(item):
            for i in range(item.childCount()):
                child = item.child(i)
                if child.childCount() == 0 and child.checkState(0) == Qt.Checked:
                    files.append(child.data(0, Qt.UserRole))
                _traverse(child)
        root = self.file_tree.invisibleRootItem()
        for i in range(root.childCount()):
            _traverse(root.child(i))
        return files

    def generate_code(self):
        import shutil
        base_dir = "User_code"
        user_dir = os.path.join(self.project_path, "User")
        copied = []
        files = self.get_checked_files()
        skipped = []
        for rel_c in files:
            rel_h = rel_c[:-2] + ".h"
            src_c = os.path.join(base_dir, rel_c)
            src_h = os.path.join(base_dir, rel_h)
            dst_c = os.path.join(user_dir, rel_c)
            dst_h = os.path.join(user_dir, rel_h)
            # 如果目标文件已存在则跳过
            if os.path.exists(dst_c):
                skipped.append(dst_c)
            else:
                os.makedirs(os.path.dirname(dst_c), exist_ok=True)
                shutil.copy2(src_c, dst_c)
                copied.append(dst_c)
            if os.path.exists(src_h):
                if os.path.exists(dst_h):
                    skipped.append(dst_h)
                else:
                    os.makedirs(os.path.dirname(dst_h), exist_ok=True)
                    shutil.copy2(src_h, dst_h)
                    copied.append(dst_h)
        msg = f"已拷贝 {len(copied)} 个文件到 User 目录"
        if skipped:
            msg += f"\n{len(skipped)} 个文件已存在，未覆盖"
        InfoBar.success(
            title="生成完成",
            content=msg,
            parent=self,
            duration=2000
        )
        # 生成后刷新文件树，更新标记
        self.show_user_code_files()

    def generate_freertos_task(self):
        import re
        freertos_path = os.path.join(self.project_path, "Core", "Src", "freertos.c")
        if not os.path.exists(freertos_path):
            InfoBar.error(
                title="未找到 freertos.c",
                content="未找到 Core/Src/freertos.c 文件，请确认工程路径。",
                parent=self,
                duration=2500
            )
            return
        with open(freertos_path, "r", encoding="utf-8") as f:
            code = f.read()
    
        changed = False
        error_msgs = []
    
        # 1. 添加 #include "task/user_task.h"
        include_line = '#include "task/user_task.h"'
        if include_line not in code:
            # 只插入到 USER CODE BEGIN Includes 区域
            include_pattern = r'(\/\* *USER CODE BEGIN Includes *\*\/\s*)'
            if re.search(include_pattern, code):
                code = re.sub(
                    include_pattern,
                    r'\1' + include_line + '\n',
                    code
                )
                changed = True
            else:
                error_msgs.append("未找到 /* USER CODE BEGIN Includes */ 区域，无法插入 include。")
    
        # 2. 在 /* USER CODE BEGIN RTOS_THREADS */ 区域添加 osThreadNew(Task_Init, NULL, &attr_init);
        rtos_threads_pattern = r'(\/\* *USER CODE BEGIN RTOS_THREADS *\*\/\s*)(.*?)(\/\* *USER CODE END RTOS_THREADS *\*\/)'
        match = re.search(rtos_threads_pattern, code, re.DOTALL)
        task_line = '  initTaskHandle = osThreadNew(Task_Init, NULL, &attr_init); // 创建初始化任务\n'
        if match:
            threads_code = match.group(2)
            if 'Task_Init' not in threads_code:
                # 保留原有内容，追加新行
                new_threads_code = match.group(1) + threads_code + task_line + match.group(3)
                code = code[:match.start()] + new_threads_code + code[match.end():]
                changed = True
        else:
            error_msgs.append("未找到 /* USER CODE BEGIN RTOS_THREADS */ 区域，无法插入任务创建代码。")
    
        # 3. 清空 StartDefaultTask 的 USER CODE 区域，只保留 osThreadTerminate
        sdt_pattern = r'(\/\* *USER CODE BEGIN StartDefaultTask *\*\/\s*)(.*?)(\/\* *USER CODE END StartDefaultTask *\*\/)'
        match = re.search(sdt_pattern, code, re.DOTALL)
        if match:
            if 'osThreadTerminate(osThreadGetId());' not in match.group(2):
                new_sdt_code = match.group(1) + '  osThreadTerminate(osThreadGetId());\n' + match.group(3)
                code = code[:match.start()] + new_sdt_code + code[match.end():]
                changed = True
        else:
            error_msgs.append("未找到 /* USER CODE BEGIN StartDefaultTask */ 区域，无法插入终止代码。")
    
        if changed:
            with open(freertos_path, "w", encoding="utf-8") as f:
                f.write(code)
            InfoBar.success(
                title="生成成功",
                content="FreeRTOS任务代码已自动生成！",
                parent=self,
                duration=2000
            )
        elif error_msgs:
            InfoBar.error(
                title="生成失败",
                content="\n".join(error_msgs),
                parent=self,
                duration=3000
            )
        else:
            InfoBar.info(
                title="无需修改",
                content="FreeRTOS任务相关代码已存在，无需重复生成。",
                parent=self,
                duration=2000
            )

    def open_task_config_dialog(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
        import yaml
        import os

        class TaskConfigDialog(QDialog):
            def __init__(self, parent=None, config_path=None):
                super().__init__(parent)
                self.setWindowTitle("任务配置")
                self.resize(800, 420)
                layout = QVBoxLayout(self)
                self.table = QTableWidget(0, 5)
                self.table.setHorizontalHeaderLabels(["任务名称", "运行频率", "初始化延迟", "堆栈大小", "任务描述"])
                self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
                self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
                self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
                self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
                self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
                self.table.setColumnWidth(4, 320)  # 任务描述更宽
                layout.addWidget(self.table)
                btn_layout = QHBoxLayout()
                add_btn = QPushButton("添加任务")
                del_btn = QPushButton("删除选中")
                ok_btn = QPushButton("生成")
                cancel_btn = QPushButton("取消")
                btn_layout.addWidget(add_btn)
                btn_layout.addWidget(del_btn)
                btn_layout.addStretch()
                btn_layout.addWidget(ok_btn)
                btn_layout.addWidget(cancel_btn)
                layout.addLayout(btn_layout)
                add_btn.clicked.connect(self.add_row)
                del_btn.clicked.connect(self.del_row)
                ok_btn.clicked.connect(self.accept)
                cancel_btn.clicked.connect(self.reject)


                # 自动读取配置文件
                if config_path and os.path.exists(config_path):
                    try:
                        with open(config_path, "r", encoding="utf-8") as f:
                            tasks = yaml.safe_load(f)
                        if tasks:
                            for t in tasks:
                                row = self.table.rowCount()
                                self.table.insertRow(row)
                                for col, key in enumerate(["name", "frequency", "delay", "stack", "description"]):
                                    item = QTableWidgetItem(str(t.get(key, "")))
                                    item.setTextAlignment(Qt.AlignCenter)
                                    self.table.setItem(row, col, item)
                    except Exception as e:
                        pass  # 配置文件损坏时忽略

            def add_row(self):
                row = self.table.rowCount()
                self.table.insertRow(row)
                default_values = [
                    f"Task{row+1}", "500", "0", "256", "不要偷懒，请写清楚每个任务的作用！（如果你看到任务上面是这句话，说明作者是个懒蛋）"
                ]
                for col, val in enumerate(default_values):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, col, item)

            def del_row(self):
                rows = set([i.row() for i in self.table.selectedItems()])
                for r in sorted(rows, reverse=True):
                    self.table.removeRow(r)

            def get_tasks(self):
                tasks = []
                for row in range(self.table.rowCount()):
                    name = self.table.item(row, 0).text().strip()
                    freq = int(self.table.item(row, 1).text())
                    delay = int(self.table.item(row, 2).text())
                    stack = int(self.table.item(row, 3).text())
                    desc = self.table.item(row, 4).text().strip()
                    # 校验 stack 必须为 128*2^n
                    if stack < 128 or (stack & (stack - 1)) != 0 or stack % 128 != 0:
                        raise ValueError(f"第{row+1}行任务“{name}”的堆栈大小必须为128、256、512、1024等（128*2^n）")
                    tasks.append({
                        "name": name,
                        "function": f"Task_{name}",
                        "frequency": freq,
                        "delay": delay,
                        "stack": stack,
                        "description": desc
                    })
                return tasks

        config_path = os.path.join(self.project_path, "User", "task", "config.yaml")
        dlg = TaskConfigDialog(self, config_path=config_path)
        if dlg.exec() == QDialog.Accepted:
            try:
                tasks = dlg.get_tasks()
            except Exception as e:
                InfoBar.error(
                    title="参数错误",
                    content=str(e),
                    parent=self,
                    duration=3000
                )
                return
            if not tasks:
                InfoBar.warning(
                    title="未配置任务",
                    content="请至少添加一个任务！",
                    parent=self,
                    duration=2000
                )
                return
            try:
                self.generate_task_code(tasks)
                InfoBar.success(
                    title="生成成功",
                    content="任务代码已生成到 User/task 目录！",
                    parent=self,
                    duration=2000
                )
            except Exception as e:
                InfoBar.error(
                    title="生成失败",
                    content=f"任务代码生成失败: {e}",
                    parent=self,
                    duration=3000
                )
    
    def generate_task_code(self, task_list):
        import os
        from jinja2 import Template
        import yaml
        import re
        import textwrap

        base_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(base_dir, "User_code", "task")
        output_dir = os.path.join(self.project_path, "User", "task")
        os.makedirs(output_dir, exist_ok=True)

        # 模板路径
        user_task_h_tpl = os.path.join(template_dir, "user_task.h.template")
        user_task_c_tpl = os.path.join(template_dir, "user_task.c.template")
        init_c_tpl = os.path.join(template_dir, "init.c.template")
        task_c_tpl = os.path.join(template_dir, "task.c.template")

        def render_template(path, context):
            with open(path, encoding="utf-8") as f:
                tpl = Template(f.read())
            return tpl.render(**context)

    
        # 构造模板上下文
        context_h = {
            "thread_definitions": "\n".join([f"        osThreadId_t {t['name']};" for t in task_list]),
            "freq_definitions": "\n".join([f"        float {t['name']};" for t in task_list]),
            "stack_definitions": "\n".join([f"        UBaseType_t {t['name']};" for t in task_list]),
            "last_up_time_definitions": "\n".join([f"        float {t['name']};" for t in task_list]),
            "task_frequency_definitions": "\n".join([f"#define {t['name'].upper()}_FREQ ({t['frequency']})" for t in task_list]),
            "task_init_delay_definitions": "\n".join([f"#define {t['name'].upper()}_INIT_DELAY ({t['delay']})" for t in task_list]),
            "task_attr_declarations": "\n".join([f"extern const osThreadAttr_t attr_{t['name']};" for t in task_list]),
            "task_function_declarations": "\n".join([f"void {t['function']}(void *argument);" for t in task_list]),
        }
    
        # ----------- 用户区域保护函数 -----------
        def preserve_user_region(new_code, old_code, region_name):
            """
            替换 new_code 中 region_name 区域为 old_code 中的内容（如果有）
            region_name: 如 'USER INCLUDE'
            """
            pattern = re.compile(
                rf"/\*\s*{region_name}\s*BEGIN\s*\*/(.*?)/\*\s*{region_name}\s*END\s*\*/",
                re.DOTALL
            )
            old_match = pattern.search(old_code or "")
            if not old_match:
                return new_code  # 旧文件没有该区域，直接返回新代码
    
            old_content = old_match.group(1)
            def repl(m):
                return m.group(0).replace(m.group(1), old_content)
            # 替换新代码中的该区域
            return pattern.sub(repl, new_code, count=1)
    
        # ----------- 生成 user_task.h -----------
        user_task_h_path = os.path.join(output_dir, "user_task.h")
        new_user_task_h = render_template(user_task_h_tpl, context_h)
    
        # 检查并保留所有用户区域
        if os.path.exists(user_task_h_path):
            with open(user_task_h_path, "r", encoding="utf-8") as f:
                old_code = f.read()
            # 只保留有内容的用户区域
            for region in ["USER INCLUDE", "USER MESSAGE", "USER CONFIG"]:
                # 如果旧文件该区域有内容，则保留
                pattern = re.compile(
                    rf"/\*\s*{region}\s*BEGIN\s*\*/(.*?)/\*\s*{region}\s*END\s*\*/",
                    re.DOTALL
                )
                old_match = pattern.search(old_code)
                if old_match and old_match.group(1).strip():
                    new_user_task_h = preserve_user_region(new_user_task_h, old_code, region)
        # 写入
        with open(user_task_h_path, "w", encoding="utf-8") as f:
            f.write(new_user_task_h)
    
        # ----------- 生成 user_task.c -----------
        context_c = {
            "task_attr_definitions": "\n".join([
                f"const osThreadAttr_t attr_{t['name']} = {{\n"
                f"    .name = \"{t['name']}\",\n"
                f"    .priority = osPriorityNormal,\n"
                f"    .stack_size = {t['stack']} * 4,\n"
                f"}};"
                for t in task_list
            ])
        }
        user_task_c = render_template(user_task_c_tpl, context_c)
        with open(os.path.join(output_dir, "user_task.c"), "w", encoding="utf-8") as f:
            f.write(user_task_c)
    
        # ----------- 生成 init.c -----------
        # 线程创建代码
        thread_creation_code = "\n".join([
            f"  task_runtime.thread.{t['name']} = osThreadNew({t['function']}, NULL, &attr_{t['name']});"
            for t in task_list
        ])

        context_init = {
            "thread_creation_code": thread_creation_code,
        }
        # 渲染模板
        init_c = render_template(init_c_tpl, context_init)

        # 保留 USER MESSAGE 区域
        def preserve_user_region(new_code, old_code, region_name):
            pattern = re.compile(
                rf"/\*\s*{region_name}\s*BEGIN\s*\*/(.*?)/\*\s*{region_name}\s*END\s*\*/",
                re.DOTALL
            )
            old_match = pattern.search(old_code or "")
            if not old_match:
                return new_code
            old_content = old_match.group(1)
            def repl(m):
                return m.group(0).replace(m.group(1), old_content)
            return pattern.sub(repl, new_code, count=1)

        init_c_path = os.path.join(output_dir, "init.c")
        if os.path.exists(init_c_path):
            with open(init_c_path, "r", encoding="utf-8") as f:
                old_code = f.read()
            # 保留 USER MESSAGE 区域
            init_c = preserve_user_region(init_c, old_code, "USER MESSAGE")

        with open(init_c_path, "w", encoding="utf-8") as f:
            f.write(init_c)
    
        # ----------- 生成 task.c -----------
        task_c_tpl = os.path.join(template_dir, "task.c.template")
        for t in task_list:
            # 自动换行任务描述
            desc = t.get("description", "")
            desc_wrapped = "\n    ".join(textwrap.wrap(desc, 20))
            context_task = {
                "task_name": t["name"],
                "task_function": t["function"],
                "task_frequency": f"{t['name'].upper()}_FREQ",         # 使用宏定义
                "task_delay": f"{t['name'].upper()}_INIT_DELAY",       # 使用宏定义
                "task_description": desc_wrapped
            }
            # 渲染模板
            with open(task_c_tpl, encoding="utf-8") as f:
                tpl = Template(f.read())
            code = tpl.render(**context_task)
            # 保留USER区域
            task_c_path = os.path.join(output_dir, f"{t['name']}.c")
            if os.path.exists(task_c_path):
                with open(task_c_path, "r", encoding="utf-8") as f:
                    old_code = f.read()
                # 只保留USER区域
                def preserve_user_region(new_code, old_code, region_name):
                    pattern = re.compile(
                        rf"/\*\s*{region_name}\s*BEGIN\s*\*/(.*?)/\*\s*{region_name}\s*END\s*\*/",
                        re.DOTALL
                    )
                    old_match = pattern.search(old_code or "")
                    if not old_match:
                        return new_code
                    old_content = old_match.group(1)
                    def repl(m):
                        return m.group(0).replace(m.group(1), old_content)
                    return pattern.sub(repl, new_code, count=1)
                for region in ["USER INCLUDE", "USER STRUCT", "USER CODE", "USER INIT CODE"]:
                    code = preserve_user_region(code, old_code, region)
            with open(task_c_path, "w", encoding="utf-8") as f:
                f.write(code)
        # ----------- 保存任务配置到 config.yaml -----------
        config_path = os.path.join(output_dir, "config.yaml")
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(task_list, f, allow_unicode=True)

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
                    # 判断是否自动回车
                    if self.auto_enter_checkbox.isChecked():
                        self.ser.write('\n'.encode())
            except Exception as e:
                self.text_edit.append(f"发送失败: {e}")
            self.input_line.clear()

# ===================== 零件库页面 =====================
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
                    # 先统一分隔符，再编码
                    rel_path_unix = rel_path.replace("\\", "/")
                    encoded_path = quote(rel_path_unix)
                    url = f"{self.server_url}/download/{encoded_path}"
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
        layout.addWidget(BodyLabel("感谢重庆邮电大学整理的零件库，选择需要的文件下载到本地。（如无法使用或者下载失败，请尝试重新下载或检查网络连接）"))

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

# ...existing code...


# 注意：PushSettingCard、HyperlinkCard 已由你的 SettingCard 文件定义

# ...existing code...

from PyQt5.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QMessageBox
from qfluentwidgets import ScrollArea, VBoxLayout
from qfluentwidgets import VBoxLayout
class HelpInterface(BaseInterface):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("helpInterface")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout) 

        content_widget = QWidget()
        main_layout = VBoxLayout(content_widget)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(18)
        # 标题
        main_layout.addWidget(SubtitleLabel("帮助中心"))
        main_layout.addWidget(HorizontalSeparator())

        # 版本与更新
        version_card = PushSettingCard(
            "检查更新",
            FluentIcon.INFO,
            f"当前版本：MRobot Toolbox v{__version__}",
            "点击按钮检查是否有新版本。",
            parent=self
        )
        version_card.clicked.connect(self.check_update)
        main_layout.addWidget(version_card)

        # FAQ分组
        faq_group = SettingCardGroup("常见问题", self)
        faq_card1 = PushSettingCard(
            "查看解决方法",
            FluentIcon.HELP,
            "启动报错/界面异常怎么办？",
            "遇到启动问题请尝试重启、检查依赖，或加入交流群获取帮助。",
            parent=self
        )
        faq_card1.clicked.connect(lambda: self.show_info(
            "启动报错/界面异常解决方法",
            "1. 尝试重启软件。\n2. 检查Python和依赖库版本。\n3. 如仍有问题，请在GitHub提交Issue。"
        ))
        faq_group.addSettingCard(faq_card1)

        faq_card2 = PushSettingCard(
            "查看解决方法",
            FluentIcon.LIBRARY,
            "零件库无法下载怎么办？",
            "如遇网络问题或下载失败，请多次尝试或联系管理员。",
            parent=self
        )
        faq_card2.clicked.connect(lambda: self.show_info(
            "零件库无法下载解决方法",
            "1. 检查网络连接。\n2. 多次刷新或重启软件。\n3. 若仍无法下载，请加入QQ群：857466609 反馈。"
        ))
        faq_group.addSettingCard(faq_card2)

        # faq_card3 = PushSettingCard(
        #     "获取下载链接",
        #     FluentIcon.DOWNLOAD,
        #     "如何下载最新版？",
        #     "点击按钮获取最新版下载地址。",
        #     parent=self
        # )
        # faq_card3.clicked.connect(lambda: self.show_info(
        #     "最新版下载地址",
        #     "GitHub发布页：https://github.com/goldenfishs/MRobot/releases\n如遇下载问题，请联系QQ群：857466609"
        # ))
        # faq_group.addSettingCard(faq_card3)
        main_layout.addWidget(faq_group)

        # 联系方式
        contact_group = SettingCardGroup("联系方式", self)
        contact_card = PushSettingCard(
            "复制邮箱",
            FluentIcon.MESSAGE,
            "联系开发团队",
            "点击按钮复制邮箱地址：support@mrobot.com",
            parent=self
        )
        contact_card.clicked.connect(lambda: self.copy_text("support@mrobot.com", "邮箱已复制：1683502971@qq.com"))
        contact_group.addSettingCard(contact_card)
        main_layout.addWidget(contact_group)

        main_layout.addStretch()
        # 不使用滚动区，直接添加内容区
        layout.addWidget(content_widget)

    def copy_text(self, text, message):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        InfoBar.info(
            title="已复制",
            content=message,
            parent=self,
            position=InfoBarPosition.TOP,
            duration=2000
        )

    def check_update(self):
        latest = check_update()
        if latest:
            self.show_info(
                "发现新版本",
                f"检测到新版本 {latest}，请前往 GitHub 下载：\nhttps://github.com/goldenfishs/MRobot/releases"
            )
        else:
            InfoBar.info(
                title="已是最新版",
                content="当前已是最新版本。",
                parent=self,
                duration=2000
            )

    def show_info(self, title, content):
        dialog = Dialog(
            title=title,
            content=content,
            parent=self
        )
        dialog.exec()

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
        self.resize(800, 600)
        self.setMinimumSize(640, 480)
        self.setWindowFlag(Qt.Window)
        # 记录当前主题
        self.current_theme = Theme.DARK
        latest = check_update()
        if latest:
            InfoBar.info(
                title="发现新版本",
                content=f"检测到新版本 {latest}，请前往 GitHub 下载更新。",
                parent=self,
                duration=5000
            )
        # 创建页面实例
        self.setting_page = SettingInterface(self)
        self.setting_page.themeSwitchRequested.connect(self.toggle_theme)

        self.page_registry = [
            (HomeInterface(self), FluentIcon.HOME, "首页", NavigationItemPosition.TOP),
            (DataInterface(self), FluentIcon.LIBRARY, "MRobot代码生成", NavigationItemPosition.SCROLL),
            (SerialTerminalInterface(self), FluentIcon.COMMAND_PROMPT, "Mini_Shell", NavigationItemPosition.SCROLL),
            (PartLibraryInterface(self), FluentIcon.DOWNLOAD, "零件库", NavigationItemPosition.SCROLL),  # ← 加上这一行
            (self.setting_page, FluentIcon.SETTING, "设置", NavigationItemPosition.BOTTOM),
            (HelpInterface(self), FluentIcon.HELP, "帮助", NavigationItemPosition.BOTTOM),
            # (AboutInterface(self), FluentIcon.INFO, "关于", NavigationItemPosition.BOTTOM),
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
            title="MRobot",
            content="账号：VIP内测版",
            parent=self
        )
        dialog.exec()

def check_update():
    try:
        repo = "goldenfishs/MRobot"
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            latest = resp.json()["tag_name"].lstrip("v")
            print(f"本地版本: {__version__}, 最新版本: {latest}")  # 调试用
            if vparse(latest) > vparse(__version__):
                return latest
    except Exception as e:
        print(f"检查更新失败: {e}")
    return None

# ===================== 程序入口 =====================
def main():
    from PyQt5.QtWidgets import QApplication  # <-- 移到这里，所有平台都能用
    import platform
    if platform.system() == "Windows":
        try:
            from PyQt5.QtCore import Qt
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    # 跟随系统主题
    setTheme(Theme.DARK)
    splash = SplashScreen()
    setTheme(Theme.DARK)
    splash.show()
    setTheme(Theme.DARK)
    app.processEvents()

    # 步骤1：获取零件库
    splash.set_status("正在获取零件仓库...", 20)
    try:
        import requests
        resp = requests.get("http://154.37.215.220:5000/list", params={"key": "MRobot_Download"}, timeout=5)
        resp.raise_for_status()
    except Exception:
        pass
    app.processEvents()

    # 步骤2：检查更新
    splash.set_status("正在检查软件更新...", 60)
    latest = check_update()
    app.processEvents()

    # 步骤3：加载主窗口
    splash.set_status("正在加载主界面...", 90)
    window = MainWindow()
    window.show()
    setTheme(Theme.DARK)
    splash.set_status("启动完成", 100)
    from PyQt5.QtCore import QTimer
    QTimer.singleShot(500, splash.close)

    # 有新版本弹窗
    if latest:
        InfoBar.info(
            title="发现新版本",
            content=f"检测到新版本 {latest}，请前往帮助页面下载新版。",
            parent=window,
            duration=5000
        )

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()