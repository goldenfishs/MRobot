import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtGui import QDesktopServices

from qfluentwidgets import (
    PrimaryPushSettingCard, FluentIcon, InfoBar, InfoBarPosition, 
    SubtitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel,
    ElevatedCardWidget, PrimaryPushButton, PushButton, 
    ProgressBar, TextEdit
)

from .function_fit_interface import FunctionFitInterface
from app.tools.check_update import check_update
from app.tools.auto_updater import AutoUpdater, check_update_availability
from app.tools.update_check_thread import UpdateCheckThread

__version__ = "1.1.0"

class AboutInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("aboutInterface")
        
        # 初始化更新相关变量
        self.updater = None
        self.update_info = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(20, 30, 20, 20)

        # 版本信息卡片
        version_card = ElevatedCardWidget()
        version_layout = QVBoxLayout(version_card)
        version_layout.setContentsMargins(24, 20, 24, 20)
        
        version_title = StrongBodyLabel("版本信息")
        version_layout.addWidget(version_title)
        
        current_version_label = BodyLabel(f"当前版本：v{__version__}")
        version_layout.addWidget(current_version_label)

        
        layout.addWidget(version_card)
        
        # 检查更新按钮
        self.check_update_card = PrimaryPushSettingCard(
            text="检查更新",
            icon=FluentIcon.SYNC,
            title="检查更新",
            content="检查是否有新版本可用（需要能够连接github）",
        )
        self.check_update_card.clicked.connect(self.check_for_updates)
        layout.addWidget(self.check_update_card)
        
        # 更新信息卡片（初始隐藏）
        self.update_info_card = ElevatedCardWidget()
        self.update_info_card.hide()
        self._setup_update_info_card()
        layout.addWidget(self.update_info_card)
        
        layout.addStretch()
    
    def _setup_update_info_card(self):
        """设置更新信息卡片"""
        layout = QVBoxLayout(self.update_info_card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        # 标题
        self.update_title = StrongBodyLabel("发现新版本")
        layout.addWidget(self.update_title)
        
        # 版本对比
        version_layout = QHBoxLayout()
        
        current_layout = QVBoxLayout()
        current_layout.addWidget(CaptionLabel("当前版本"))
        self.current_version_label = SubtitleLabel(f"v{__version__}")
        current_layout.addWidget(self.current_version_label)
        
        arrow_label = SubtitleLabel("→")
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow_label.setFixedWidth(30)
        
        latest_layout = QVBoxLayout()
        latest_layout.addWidget(CaptionLabel("最新版本"))
        self.latest_version_label = SubtitleLabel("v--")
        latest_layout.addWidget(self.latest_version_label)
        
        version_layout.addLayout(current_layout)
        version_layout.addWidget(arrow_label)
        version_layout.addLayout(latest_layout)
        
        layout.addLayout(version_layout)
        
        # 更新信息
        info_layout = QHBoxLayout()
        self.file_size_label = BodyLabel("文件大小: --")
        self.release_date_label = BodyLabel("发布时间: --")
        
        info_layout.addWidget(self.file_size_label)
        info_layout.addStretch()
        info_layout.addWidget(self.release_date_label)
        
        layout.addLayout(info_layout)
        
        # 更新说明
        layout.addWidget(CaptionLabel("更新说明:"))
        
        self.notes_display = TextEdit()
        self.notes_display.setReadOnly(True)
        self.notes_display.setMaximumHeight(200)
        self.notes_display.setMinimumHeight(80)
        self.notes_display.setText("暂无更新说明")
        layout.addWidget(self.notes_display)
        
        # 进度条（初始隐藏）
        self.progress_widget = QWidget()
        progress_layout = QVBoxLayout(self.progress_widget)
        
        self.progress_label = BodyLabel("准备更新...")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = ProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        # 详细下载信息
        self.download_info = BodyLabel("")
        self.download_info.setWordWrap(True)
        progress_layout.addWidget(self.download_info)
        
        self.progress_widget.hide()
        layout.addWidget(self.progress_widget)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.manual_btn = PushButton("手动下载")
        self.manual_btn.setIcon(FluentIcon.LINK)
        self.manual_btn.clicked.connect(self.open_manual_download)
        
        self.update_btn = PrimaryPushButton("开始更新")
        self.update_btn.setIcon(FluentIcon.DOWNLOAD)
        self.update_btn.clicked.connect(self.start_update)
        
        self.cancel_btn = PushButton("取消")
        self.cancel_btn.clicked.connect(self.cancel_update)
        
        button_layout.addWidget(self.manual_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.update_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)

    def check_for_updates(self):
        """检查更新"""
        self.check_update_card.setEnabled(False)
        self.check_update_card.setContent("正在检查更新...")
        
        # 延迟执行检查，避免阻塞UI
        QTimer.singleShot(100, self._perform_check)
    
    def _perform_check(self):
        """执行更新检查"""
        try:
            # 获取最新版本信息（包括当前版本的详细信息）
            latest_info = self._get_latest_release_info()
            
            # 检查是否有可用更新
            self.update_info = check_update_availability(__version__)
            
            if self.update_info:
                self._show_update_available()
            else:
                self._show_no_update(latest_info)
                
        except Exception as e:
            self._show_error(f"检查更新失败: {str(e)}")
    
    def _get_latest_release_info(self):
        """获取最新发布信息，不论版本是否需要更新"""
        try:
            import requests
            from packaging.version import parse as vparse
            
            url = f"https://api.github.com/repos/goldenfishs/MRobot/releases/latest"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data["tag_name"].lstrip("v")
                
                # 获取下载URL和文件大小
                assets = release_data.get('assets', [])
                asset_size = 0
                download_url = None
                
                if assets:
                    # 选择第一个资源文件
                    asset = assets[0]
                    asset_size = asset.get('size', 0)
                    download_url = asset.get('browser_download_url', '')
                
                return {
                    'version': latest_version,
                    'release_notes': release_data.get('body', '暂无更新说明'),
                    'release_date': release_data.get('published_at', ''),
                    'asset_size': asset_size,
                    'download_url': download_url
                }
            else:
                return None
                
        except Exception as e:
            print(f"获取发布信息失败: {e}")
            return None
    
    def _show_update_available(self):
        """显示发现更新"""
        # 更新按钮状态
        self.check_update_card.setEnabled(True)
        self.check_update_card.setContent("发现新版本！")
        
        # 显示更新信息卡片
        self.update_info_card.show()
        
        # 设置版本信息
        if self.update_info:
            version = self.update_info.get('version', 'Unknown')
            self.latest_version_label.setText(f"v{version}")
            
            # 设置文件信息
            asset_size = self.update_info.get('asset_size', 0)
            file_size = self._format_file_size(asset_size)
            self.file_size_label.setText(f"文件大小: {file_size}")
            
            # 设置发布时间
            release_date = self.update_info.get('release_date', '')
            formatted_date = self._format_date(release_date)
            self.release_date_label.setText(f"发布时间: {formatted_date}")
            
            # 设置更新说明
            notes = self.update_info.get('release_notes', '暂无更新说明')
            self.notes_display.setText(notes[:500] + ('...' if len(notes) > 500 else ''))
        
        InfoBar.success(
            title="发现新版本",
            content=f"检测到新版本 v{version}",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=3000
        )
    
    def _show_no_update(self, latest_info=None):
        """显示无更新，但展示最新版本信息"""
        self.check_update_card.setEnabled(True)
        self.check_update_card.setContent("已是最新版本")
        
        # 如果有最新版本信息，显示详情卡片
        if latest_info:
            self.update_info_card.show()
            
            # 显示版本信息（当前版本就是最新版本）
            self.latest_version_label.setText(f"v{__version__}")
            
            # 设置文件信息
            asset_size = latest_info.get('asset_size', 0)
            file_size = self._format_file_size(asset_size)
            self.file_size_label.setText(f"文件大小: {file_size}")
            
            # 设置发布时间
            release_date = latest_info.get('release_date', '')
            formatted_date = self._format_date(release_date)
            self.release_date_label.setText(f"发布时间: {formatted_date}")
            
            # 设置更新说明
            notes = latest_info.get('release_notes', '暂无更新说明')
            self.notes_display.setText(notes[:500] + ('...' if len(notes) > 500 else ''))
            
            # 修改标题和按钮
            self.update_title.setText("版本信息")
            self.update_btn.setText("手动下载")
            self.update_btn.setIcon(FluentIcon.DOWNLOAD)
            self.update_btn.setEnabled(True)
            self.manual_btn.setEnabled(True)
            
            # 连接手动下载功能
            self.update_btn.clicked.disconnect()
            self.update_btn.clicked.connect(self.open_manual_download)
        
        InfoBar.info(
            title="已是最新版本",
            content="当前已是最新版本，无需更新。",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=3000
        )
    
    def _show_error(self, error_msg: str):
        """显示错误"""
        self.check_update_card.setEnabled(True)
        self.check_update_card.setContent("检查更新失败")
        
        InfoBar.error(
            title="检查更新失败",
            content=error_msg,
            parent=self,
            position=InfoBarPosition.TOP,
            duration=4000
        )
    
    def start_update(self):
        """开始更新"""
        if not self.update_info:
            return
        
        # 显示进度UI
        self.progress_widget.show()
        self.update_btn.setEnabled(False)
        self.manual_btn.setEnabled(False)
        
        # 启动更新器（使用简化的单线程下载）
        self.updater = AutoUpdater(__version__)
        self.updater.signals.progress_changed.connect(self.update_progress)
        self.updater.signals.download_progress.connect(self.update_download_progress)
        self.updater.signals.status_changed.connect(self.update_status)
        self.updater.signals.error_occurred.connect(self.update_error)
        self.updater.signals.update_completed.connect(self.update_completed)
        
        # 开始更新流程
        self.updater.start()
    
    def update_progress(self, value: int):
        """更新进度"""
        self.progress_bar.setValue(value)
    
    def update_download_progress(self, downloaded: int, total: int, speed: float, remaining: float):
        """更新下载进度详情"""
        if total > 0:
            downloaded_str = self._format_bytes(downloaded)
            total_str = self._format_bytes(total)
            percentage = (downloaded / total) * 100
            
            info_text = f"已下载: {downloaded_str} / {total_str} ({percentage:.1f}%)"
            
            self.download_info.setText(info_text)
    
    def _format_bytes(self, size_bytes: int) -> str:
        """格式化字节大小"""
        if size_bytes == 0:
            return "0 B"
        
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def update_status(self, status: str):
        """更新状态"""
        self.progress_label.setText(status)
    
    def update_error(self, error_msg: str):
        """更新错误"""
        self.progress_widget.hide()
        self.update_btn.setEnabled(True)
        self.manual_btn.setEnabled(True)
        
        # 如果是平台兼容性问题，提供更友好的提示
        if "Windows 安装程序" in error_msg and "当前系统是" in error_msg:
            InfoBar.warning(
                title="平台不兼容",
                content="检测到 Windows 安装程序，请点击'手动下载'获取适合 macOS 的版本",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=6000
            )
        else:
            InfoBar.error(
                title="更新失败",
                content=error_msg,
                parent=self,
                position=InfoBarPosition.TOP,
                duration=4000
            )
    
    def update_completed(self, file_path=None):
        """更新完成 - 显示下载文件位置"""
        print(f"update_completed called with file_path: {file_path}")  # 调试输出
        
        self.progress_label.setText("下载完成！")
        self.progress_bar.setValue(100)
        
        # 重新启用按钮
        self.update_btn.setEnabled(True)
        self.manual_btn.setEnabled(True)
        
        if file_path and os.path.exists(file_path):
            print(f"File exists: {file_path}")  # 调试输出
            InfoBar.success(
                title="下载完成",
                content="安装文件已下载完成，点击下方按钮打开文件位置",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=5000
            )
            
            # 添加打开文件夹按钮
            self._add_open_folder_button(file_path)
        else:
            print(f"File does not exist or file_path is None: {file_path}")  # 调试输出
            InfoBar.success(
                title="下载完成",
                content="文件下载完成",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
    
    def _add_open_folder_button(self, file_path):
        """添加打开文件夹按钮"""        
        def open_file_location():
            folder_path = os.path.dirname(file_path)
            # 在 macOS 上使用 Finder 打开文件夹
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))
            
            InfoBar.info(
                title="已打开文件夹",
                content=f"文件位置: {folder_path}",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
        
        # 直接替换更新按钮的文本和功能
        self.update_btn.setText("打开文件位置")
        self.update_btn.setIcon(FluentIcon.FOLDER)
        # 断开原有连接
        self.update_btn.clicked.disconnect()
        # 连接新功能
        self.update_btn.clicked.connect(open_file_location)
        
        # 修改取消按钮为清理按钮
        self.cancel_btn.setText("清理临时文件")
        self.cancel_btn.setIcon(FluentIcon.DELETE)
        self.cancel_btn.clicked.disconnect()
        
        def cleanup_temp_files():
            if self.updater:
                self.updater.cleanup()
            InfoBar.success(
                title="已清理",
                content="临时文件已清理完成",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
            # 重置界面
            self.update_info_card.hide()
            self.check_update_card.setContent("检查是否有新版本可用")
        
        self.cancel_btn.clicked.connect(cleanup_temp_files)
    
    def cancel_update(self):
        """取消更新"""
        if hasattr(self, 'updater') and self.updater and self.updater.isRunning():
            self.updater.cancel_update()
            self.updater.cleanup()
        
        self.update_info_card.hide()
        self.check_update_card.setContent("检查是否有新版本可用")
    
    def open_manual_download(self):
        """打开手动下载页面"""
        QDesktopServices.openUrl(QUrl("https://github.com/goldenfishs/MRobot/releases/latest"))
        
        InfoBar.info(
            title="手动下载",
            content="已为您打开下载页面",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=2000
        )
    
    def _restart_app(self):
        """重启应用程序"""
        if self.updater:
            self.updater.restart_application()
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "--"
        
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def _format_date(self, date_str: str) -> str:
        """格式化日期"""
        if not date_str:
            return "--"
        
        try:
            from datetime import datetime
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_obj.strftime('%Y-%m-%d')
        except:
            return date_str[:10] if len(date_str) >= 10 else date_str