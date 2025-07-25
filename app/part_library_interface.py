from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from qfluentwidgets import SubtitleLabel, BodyLabel, HorizontalSeparator, PushButton, TreeWidget, ProgressBar, Dialog, InfoBar, InfoBarPosition, FluentIcon, ProgressRing, Dialog
import requests
import shutil
import os
from .tools.part_download import DownloadThread  # 新增导入

from urllib.parse import quote
class PartLibraryInterface(QWidget):
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

        open_local_btn = PushButton(FluentIcon.FOLDER, "打开本地零件库")
        open_local_btn.clicked.connect(self.open_local_lib)
        btn_layout.addWidget(open_local_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.tree = TreeWidget(self)
        self.tree.setHeaderLabels(["名称", "类型"])
        self.tree.setSelectionMode(self.tree.ExtendedSelection)
        self.tree.header().setSectionResizeMode(0, self.tree.header().Stretch)
        self.tree.header().setSectionResizeMode(1, self.tree.header().ResizeToContents)
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
            dialog = Dialog(
                title="温馨提示",
                content="请先勾选需要下载的文件。",
                parent=self
            )
            dialog.yesButton.setText("知道啦")
            dialog.cancelButton.hide()
            dialog.exec()
            return

        # 创建进度环
        self.progress_ring = ProgressRing()
        self.progress_ring.setRange(0, 100)
        self.progress_ring.setValue(0)
        self.progress_ring.setTextVisible(True)
        self.progress_ring.setFixedSize(32, 32)
        self.progress_ring.setStrokeWidth(4)

        # 展示消息条（关闭按钮即中断下载）
        self.info_bar = InfoBar(
            icon=FluentIcon.DOWNLOAD,
            title="正在下载",
            content="正在下载选中文件...",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=-1  # 不自动消失
        )
        self.info_bar.addWidget(self.progress_ring)
        self.info_bar.closeButton.clicked.connect(self.stop_download)  # 关闭即中断下载
        self.info_bar.show()

        # 启动下载线程
        self.download_thread = DownloadThread(
            files, self.SERVER_URL, self.SECRET_KEY, self.LOCAL_LIB_DIR
        )
        self.download_thread.progressChanged.connect(self.progress_ring.setValue)
        self.download_thread.finished.connect(self.on_download_finished)
        self.download_thread.finished.connect(self.download_thread.deleteLater)
        self.download_thread.start()

    def stop_download(self):
        if hasattr(self, "download_thread") and self.download_thread.isRunning():
            self.download_thread.terminate()
            self.download_thread.wait()
            self.info_bar.close()
            InfoBar.warning(
                title="下载已中断",
                content="已手动中断下载任务。",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
            
    def on_download_finished(self, success, fail):
        self.info_bar.close()
        msg = f"成功下载：{len(success)} 个文件，失败：{len(fail)} 个文件"

        # 创建“打开文件夹”按钮
        open_btn = PushButton("打开文件夹")
        def open_folder():
            folder = os.path.abspath(self.LOCAL_LIB_DIR)
            import platform, subprocess
            if platform.system() == "Darwin":
                subprocess.call(["open", folder])
            elif platform.system() == "Windows":
                subprocess.call(["explorer", folder])
            else:
                subprocess.call(["xdg-open", folder])

        # 展示成功消息条，自动消失
        self.result_bar = InfoBar.success(
            title="下载完成",
            content=msg,
            parent=self,
            position=InfoBarPosition.TOP,
            duration=4000  # 4秒后自动消失
        )
        self.result_bar.addWidget(open_btn)
        open_btn.clicked.connect(open_folder)
        self.result_bar.show()

    def open_local_lib(self):
        folder = os.path.abspath(self.LOCAL_LIB_DIR)
        import platform, subprocess
        if platform.system() == "Darwin":
            subprocess.call(["open", folder])
        elif platform.system() == "Windows":
            subprocess.call(["explorer", folder])
        else:
            subprocess.call(["xdg-open", folder])