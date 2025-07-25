from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedLayout, QFileDialog, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidgetItem as TreeItem
from qfluentwidgets import TitleLabel, BodyLabel, SubtitleLabel, StrongBodyLabel, HorizontalSeparator, PushButton, TreeWidget, InfoBar,FluentIcon
import os
import requests
import zipfile
import io
import re
import shutil
import yaml
import textwrap
from jinja2 import Template

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
        ip_keys = [k for k in self.config if k.startswith('Mcu.IP')]
        for k in ip_keys:
            if self.config[k] == 'FREERTOS':
                return True
        for k in self.config:
            if k.startswith('FREERTOS.'):
                return True
        return False

class DataInterface(QWidget):
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
        content_layout.addWidget(title)

        # 副标题
        subtitle = BodyLabel("请选择您的由CUBEMX生成的工程路径（.ico所在的目录），然后开启代码之旅！")
        subtitle.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(subtitle)

        # 简要说明
        desc = BodyLabel("支持自动配置和生成任务，自主选择模块代码倒入，自动识别cubemx配置！")
        desc.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(desc)

        content_layout.addSpacing(18)

        # 选择项目路径按钮
        self.choose_btn = PushButton(FluentIcon.FOLDER, "选择项目路径")
        self.choose_btn.setFixedWidth(200)
        self.choose_btn.clicked.connect(self.choose_project_folder)
        content_layout.addWidget(self.choose_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # 更新代码库按钮
        self.update_template_btn = PushButton(FluentIcon.SYNC, "更新代码库")
        self.update_template_btn.setFixedWidth(200)
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
        local_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../assets/User_code")
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
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../assets/User_code")
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
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../assets/User_code")
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
        task_line = ' osThreadNew(Task_Init, NULL, &attr_init); // 创建初始化任务\n'
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
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox
        import yaml
        import os

        class TaskConfigDialog(QDialog):
            def __init__(self, parent=None, config_path=None):
                super().__init__(parent)
                self.setWindowTitle("任务配置")
                self.resize(900, 420)
                layout = QVBoxLayout(self)
                self.table = QTableWidget(0, 6)
                self.table.setHorizontalHeaderLabels(["任务名称", "运行频率", "初始化延迟", "堆栈大小", "任务描述", "频率控制"])
                self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
                self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
                self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
                self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
                self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
                self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
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
                                # 新增频率控制复选框
                                freq_ctrl = QCheckBox()
                                freq_ctrl.setChecked(t.get("freq_control", True))
                                self.table.setCellWidget(row, 5, freq_ctrl)
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
                freq_ctrl = QCheckBox()
                freq_ctrl.setChecked(True)
                self.table.setCellWidget(row, 5, freq_ctrl)

            def del_row(self):
                rows = set([i.row() for i in self.table.selectedItems()])
                for r in sorted(rows, reverse=True):
                    self.table.removeRow(r)

            def get_tasks(self):
                tasks = []
                for row in range(self.table.rowCount()):
                    name = self.table.item(row, 0).text().strip()
                    freq = self.table.item(row, 1).text()
                    delay = int(self.table.item(row, 2).text())
                    stack = int(self.table.item(row, 3).text())
                    desc = self.table.item(row, 4).text().strip()
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
                        task["frequency"] = int(freq)
                    tasks.append(task)
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

    def preserve_user_region(self, new_code, old_code, region_name):
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

    def generate_task_code(self, task_list):

        base_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(base_dir, "../assets/User_code/task")
        output_dir = os.path.join(self.project_path, "User", "task")
        os.makedirs(output_dir, exist_ok=True)

        user_task_h_tpl = os.path.join(template_dir, "user_task.h.template")
        user_task_c_tpl = os.path.join(template_dir, "user_task.c.template")
        init_c_tpl = os.path.join(template_dir, "init.c.template")
        task_c_tpl = os.path.join(template_dir, "task.c.template")

        freq_tasks = [t for t in task_list if t.get("freq_control", True)]

        def render_template(path, context):
            with open(path, encoding="utf-8") as f:
                tpl = Template(f.read())
            return tpl.render(**context)

        context_h = {
            "thread_definitions": "\n".join([f"        osThreadId_t {t['name']};" for t in task_list]),
            "freq_definitions": "\n".join([f"        float {t['name']};" for t in freq_tasks]),
            "stack_definitions": "\n".join([f"        UBaseType_t {t['name']};" for t in task_list]),
            "last_up_time_definitions": "\n".join([f"        float {t['name']};" for t in freq_tasks]),
            "task_frequency_definitions": "\n".join([f"#define {t['name'].upper()}_FREQ ({t['frequency']})" for t in freq_tasks]),
            "task_init_delay_definitions": "\n".join([f"#define {t['name'].upper()}_INIT_DELAY ({t['delay']})" for t in task_list]),
            "task_attr_declarations": "\n".join([f"extern const osThreadAttr_t attr_{t['name']};" for t in task_list]),
            "task_function_declarations": "\n".join([f"void {t['function']}(void *argument);" for t in task_list]),
        }

        # ----------- 生成 user_task.h -----------
        user_task_h_path = os.path.join(output_dir, "user_task.h")
        new_user_task_h = render_template(user_task_h_tpl, context_h)

        if os.path.exists(user_task_h_path):
            with open(user_task_h_path, "r", encoding="utf-8") as f:
                old_code = f.read()
            for region in ["USER INCLUDE", "USER MESSAGE", "USER CONFIG"]:
                pattern = re.compile(
                    rf"/\*\s*{region}\s*BEGIN\s*\*/(.*?)/\*\s*{region}\s*END\s*\*/",
                    re.DOTALL
                )
                old_match = pattern.search(old_code)
                if old_match and old_match.group(1).strip():
                    new_user_task_h = self.preserve_user_region(
                        new_user_task_h, old_code, region
                    )
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
        thread_creation_code = "\n".join([
            f"  task_runtime.thread.{t['name']} = osThreadNew({t['function']}, NULL, &attr_{t['name']});"
            for t in task_list
        ])
        context_init = {
            "thread_creation_code": thread_creation_code,
        }
        init_c = render_template(init_c_tpl, context_init)
        init_c_path = os.path.join(output_dir, "init.c")
        if os.path.exists(init_c_path):
            with open(init_c_path, "r", encoding="utf-8") as f:
                old_code = f.read()
            for region in ["USER INCLUDE", "USER CODE", "USER CODE INIT"]:
                init_c = self.preserve_user_region(
                    init_c, old_code, region
                )
        with open(init_c_path, "w", encoding="utf-8") as f:
            f.write(init_c)

        # ----------- 生成 task.c -----------
        for t in task_list:
            desc = t.get("description", "")
            desc_wrapped = "\n    ".join(textwrap.wrap(desc, 20))
            context_task = {
                "task_name": t["name"],
                "task_function": t["function"],
                "task_frequency": f"{t['name'].upper()}_FREQ" if t.get("freq_control", True) else None,
                "task_delay": f"{t['name'].upper()}_INIT_DELAY",
                "task_description": desc_wrapped,
                "freq_control": t.get("freq_control", True)
            }
            with open(task_c_tpl, encoding="utf-8") as f:
                tpl = Template(f.read())
            code = tpl.render(**context_task)
            task_c_path = os.path.join(output_dir, f"{t['name']}.c")
            if os.path.exists(task_c_path):
                with open(task_c_path, "r", encoding="utf-8") as f:
                    old_code = f.read()
                for region in ["USER INCLUDE", "USER STRUCT", "USER CODE", "USER CODE INIT"]:
                    code = self.preserve_user_region(
                        code, old_code, region
                    )
            with open(task_c_path, "w", encoding="utf-8") as f:
                f.write(code)

        # ----------- 保存任务配置到 config.yaml -----------
        config_yaml_path = os.path.join(output_dir, "config.yaml")
        with open(config_yaml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(task_list, f, allow_unicode=True)

