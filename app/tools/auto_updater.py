"""
自动更新模块
实现软件的自动更新功能，包括下载、解压、安装等完整流程
"""

import os
import sys
import shutil
import tempfile
import zipfile
import subprocess
import platform
from pathlib import Path
from typing import Optional, Callable
from urllib.parse import urlparse

import requests
from packaging.version import parse as vparse
from PyQt5.QtCore import QThread, pyqtSignal, QObject


class UpdaterSignals(QObject):
    """更新器信号类"""
    progress_changed = pyqtSignal(int)  # 进度变化信号 (0-100)
    status_changed = pyqtSignal(str)    # 状态变化信号
    error_occurred = pyqtSignal(str)    # 错误信号
    update_completed = pyqtSignal()     # 更新完成信号
    update_cancelled = pyqtSignal()     # 更新取消信号


class AutoUpdater(QThread):
    """自动更新器类"""
    
    def __init__(self, current_version: str, repo: str = "goldenfishs/MRobot"):
        super().__init__()
        self.current_version = current_version
        self.repo = repo
        self.signals = UpdaterSignals()
        self.cancelled = False
        
        # 获取当前程序信息
        self.is_frozen = getattr(sys, 'frozen', False)
        self.app_dir = self._get_app_directory()
        self.temp_dir = None
        
    def _get_app_directory(self) -> str:
        """获取应用程序目录"""
        if self.is_frozen:
            # 如果是打包的exe，返回exe所在目录
            return os.path.dirname(sys.executable)
        else:
            # 如果是Python脚本，返回项目根目录
            return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    def cancel_update(self):
        """取消更新"""
        self.cancelled = True
        self.signals.update_cancelled.emit()
    
    def check_for_updates(self) -> Optional[dict]:
        """检查是否有新版本可用"""
        try:
            self.signals.status_changed.emit("正在检查更新...")
            
            url = f"https://api.github.com/repos/{self.repo}/releases/latest"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data["tag_name"].lstrip("v")
                
                if vparse(latest_version) > vparse(self.current_version):
                    return {
                        'version': latest_version,
                        'download_url': self._get_download_url(release_data),
                        'release_notes': release_data.get('body', ''),
                        'release_date': release_data.get('published_at', ''),
                        'asset_name': self._get_asset_name(release_data)
                    }
                return None
            else:
                raise Exception(f"GitHub API请求失败: {response.status_code}")
                
        except Exception as e:
            self.signals.error_occurred.emit(f"检查更新失败: {str(e)}")
            return None
    
    def _get_download_url(self, release_data: dict) -> Optional[str]:
        """从release数据中获取适合当前平台的下载链接"""
        assets = release_data.get('assets', [])
        system = platform.system().lower()
        
        # 根据操作系统选择合适的安装包
        for asset in assets:
            name = asset['name'].lower()
            
            if system == 'windows':
                if 'installer' in name and name.endswith('.exe'):
                    return asset['browser_download_url']
                if name.endswith('.exe') or name.endswith('.zip'):
                    return asset['browser_download_url']
            elif system == 'darwin':  # macOS
                if name.endswith('.dmg') or name.endswith('.zip'):
                    return asset['browser_download_url']
            elif system == 'linux':
                if name.endswith('.tar.gz') or name.endswith('.zip'):
                    return asset['browser_download_url']
        
        # 如果没找到特定平台的，返回第一个可用文件
        for asset in assets:
            name = asset['name'].lower()
            if any(name.endswith(ext) for ext in ['.zip', '.exe', '.dmg', '.tar.gz']):
                return asset['browser_download_url']
        
        return None
    
    def _get_asset_name(self, release_data: dict) -> Optional[str]:
        """获取资源文件名"""
        download_url = self._get_download_url(release_data)
        if download_url:
            return os.path.basename(urlparse(download_url).path)
        return None
    
    def download_update(self, download_url: str, filename: str) -> Optional[str]:
        """下载更新文件"""
        try:
            self.signals.status_changed.emit("正在下载更新...")
            
            # 创建临时目录
            self.temp_dir = tempfile.mkdtemp(prefix="MRobot_update_")
            file_path = os.path.join(self.temp_dir, filename)
            
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.cancelled:
                        return None
                    
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if total_size > 0:
                            progress = int((downloaded_size / total_size) * 50)  # 下载占50%进度
                            self.signals.progress_changed.emit(progress)
            
            self.signals.status_changed.emit("下载完成")
            return file_path
            
        except Exception as e:
            self.signals.error_occurred.emit(f"下载失败: {str(e)}")
            return None
    
    def extract_update(self, file_path: str) -> Optional[str]:
        """解压更新文件"""
        try:
            self.signals.status_changed.emit("正在解压文件...")
            self.signals.progress_changed.emit(50)
            
            if not self.temp_dir:
                raise Exception("临时目录未初始化")
                
            extract_dir = os.path.join(self.temp_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            
            # 根据文件扩展名选择解压方法
            if file_path.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            elif file_path.endswith('.tar.gz'):
                import tarfile
                with tarfile.open(file_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(extract_dir)
            else:
                raise Exception(f"不支持的文件格式: {file_path}")
            
            self.signals.progress_changed.emit(70)
            self.signals.status_changed.emit("解压完成")
            return extract_dir
            
        except Exception as e:
            self.signals.error_occurred.emit(f"解压失败: {str(e)}")
            return None
    
    def install_update(self, extract_dir: str) -> bool:
        """安装更新"""
        try:
            self.signals.status_changed.emit("正在安装更新...")
            self.signals.progress_changed.emit(80)
            
            if not self.temp_dir:
                raise Exception("临时目录未初始化")
            
            # 创建备份目录
            backup_dir = os.path.join(self.temp_dir, "backup")
            os.makedirs(backup_dir, exist_ok=True)
            
            # 备份当前程序文件
            self._backup_current_files(backup_dir)
            
            # 复制新文件
            self._copy_update_files(extract_dir)
            
            self.signals.progress_changed.emit(95)
            self.signals.status_changed.emit("安装完成")
            
            return True
            
        except Exception as e:
            self.signals.error_occurred.emit(f"安装失败: {str(e)}")
            # 尝试恢复备份
            self._restore_backup(backup_dir)
            return False
    
    def _backup_current_files(self, backup_dir: str):
        """备份当前程序文件"""
        important_files = ['MRobot.py', 'MRobot.exe', 'app/', 'assets/']
        
        for item in important_files:
            src_path = os.path.join(self.app_dir, item)
            if os.path.exists(src_path):
                dst_path = os.path.join(backup_dir, item)
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    shutil.copy2(src_path, dst_path)
    
    def _copy_update_files(self, extract_dir: str):
        """复制更新文件到应用程序目录"""
        # 查找解压目录中的主要文件/文件夹
        extract_contents = os.listdir(extract_dir)
        
        # 如果解压后只有一个文件夹，进入该文件夹
        if len(extract_contents) == 1 and os.path.isdir(os.path.join(extract_dir, extract_contents[0])):
            extract_dir = os.path.join(extract_dir, extract_contents[0])
        
        # 复制文件到应用程序目录
        for item in os.listdir(extract_dir):
            src_path = os.path.join(extract_dir, item)
            dst_path = os.path.join(self.app_dir, item)
            
            if os.path.isdir(src_path):
                if os.path.exists(dst_path):
                    shutil.rmtree(dst_path)
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
    
    def _restore_backup(self, backup_dir: str):
        """恢复备份文件"""
        try:
            for item in os.listdir(backup_dir):
                src_path = os.path.join(backup_dir, item)
                dst_path = os.path.join(self.app_dir, item)
                
                if os.path.isdir(src_path):
                    if os.path.exists(dst_path):
                        shutil.rmtree(dst_path)
                    shutil.copytree(src_path, dst_path)
                else:
                    shutil.copy2(src_path, dst_path)
        except Exception as e:
            print(f"恢复备份失败: {e}")
    
    def restart_application(self):
        """重启应用程序"""
        try:
            self.signals.status_changed.emit("正在重启应用程序...")
            
            if self.is_frozen:
                # 如果是打包的exe
                executable = sys.executable
            else:
                # 如果是Python脚本
                executable = sys.executable
                script_path = os.path.join(self.app_dir, "MRobot.py")
                
            # 启动新进程
            if platform.system() == 'Windows':
                subprocess.Popen([executable] + ([script_path] if not self.is_frozen else []))
            else:
                subprocess.Popen([executable] + ([script_path] if not self.is_frozen else []))
            
            # 退出当前进程
            sys.exit(0)
            
        except Exception as e:
            self.signals.error_occurred.emit(f"重启失败: {str(e)}")
    
    def cleanup(self):
        """清理临时文件"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"清理临时文件失败: {e}")
    
    def run(self):
        """执行更新流程"""
        try:
            # 检查更新
            update_info = self.check_for_updates()
            if not update_info or self.cancelled:
                return
            
            # 下载更新
            downloaded_file = self.download_update(
                update_info['download_url'], 
                update_info['asset_name']
            )
            if not downloaded_file or self.cancelled:
                return
            
            # 解压更新
            extract_dir = self.extract_update(downloaded_file)
            if not extract_dir or self.cancelled:
                return
            
            # 安装更新
            if self.install_update(extract_dir) and not self.cancelled:
                self.signals.progress_changed.emit(100)
                self.signals.update_completed.emit()
            
        except Exception as e:
            self.signals.error_occurred.emit(f"更新过程中发生错误: {str(e)}")
        finally:
            # 清理临时文件
            self.cleanup()


def check_update_availability(current_version: str, repo: str = "goldenfishs/MRobot") -> Optional[dict]:
    """快速检查是否有新版本可用（不下载）"""
    updater = AutoUpdater(current_version, repo)
    return updater.check_for_updates()