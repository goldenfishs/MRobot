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

# 移除多线程下载器依赖


class UpdaterSignals(QObject):
    """更新器信号类"""
    progress_changed = pyqtSignal(int)  # 进度变化信号 (0-100)
    download_progress = pyqtSignal(int, int, float, float)  # 下载进度: 已下载字节, 总字节, 速度MB/s, 剩余时间秒
    status_changed = pyqtSignal(str)    # 状态变化信号
    error_occurred = pyqtSignal(str)    # 错误信号
    update_completed = pyqtSignal(str)  # 更新完成信号，可选包含文件路径
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
        
        # 多线程下载器
        self.downloader = None
        
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
        if self.downloader:
            self.downloader.cancel()
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
                    download_url = self._get_download_url(release_data)
                    asset_size = self._get_asset_size(release_data, download_url) if download_url else 0
                    return {
                        'version': latest_version,
                        'download_url': download_url,
                        'release_notes': release_data.get('body', ''),
                        'release_date': release_data.get('published_at', ''),
                        'asset_name': self._get_asset_name(release_data),
                        'asset_size': asset_size
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
                # 优先选择 dmg 或 zip 文件
                if name.endswith('.dmg'):
                    return asset['browser_download_url']
                if name.endswith('.zip') and 'macos' in name:
                    return asset['browser_download_url']
            elif system == 'linux':
                if name.endswith('.tar.gz') or (name.endswith('.zip') and 'linux' in name):
                    return asset['browser_download_url']
        
        # 如果没找到特定平台的，在 macOS 上避免选择 .exe 文件
        for asset in assets:
            name = asset['name'].lower()
            if system == 'darwin':
                # macOS 优先选择非 exe 文件
                if name.endswith('.zip') or name.endswith('.dmg') or name.endswith('.tar.gz'):
                    return asset['browser_download_url']
            else:
                if any(name.endswith(ext) for ext in ['.zip', '.exe', '.dmg', '.tar.gz']):
                    return asset['browser_download_url']
        
        # 最后才选择 exe 文件（如果没有其他选择）
        if system == 'darwin':
            for asset in assets:
                name = asset['name'].lower()
                if name.endswith('.exe'):
                    return asset['browser_download_url']
        
        return None
    
    def _get_asset_name(self, release_data: dict) -> Optional[str]:
        """获取资源文件名"""
        download_url = self._get_download_url(release_data)
        if download_url:
            return os.path.basename(urlparse(download_url).path)
        return None
    
    def _get_asset_size(self, release_data: dict, download_url: str) -> int:
        """获取资源文件大小"""
        if not download_url:
            return 0
        
        assets = release_data.get('assets', [])
        for asset in assets:
            if asset.get('browser_download_url') == download_url:
                return asset.get('size', 0)
        return 0
    
    def download_update(self, download_url: str, filename: str) -> Optional[str]:
        """下载更新文件 - 使用简单的单线程下载"""
        try:
            self.signals.status_changed.emit("开始下载...")
            
            # 创建临时目录
            self.temp_dir = tempfile.mkdtemp(prefix="MRobot_update_")
            file_path = os.path.join(self.temp_dir, filename)
            
            print(f"Downloading to: {file_path}")
            
            # 使用简单的requests下载
            import requests
            headers = {
                'User-Agent': 'MRobot-Updater/1.0',
                'Accept': '*/*',
            }
            
            response = requests.get(download_url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # 获取文件总大小
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded_size = 0
            
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 下载文件
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.cancelled:
                        print("Download cancelled by user")
                        return None
                    
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 更新进度
                        if total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            self.signals.progress_changed.emit(progress)
                            
                            # 发送详细进度信息
                            speed = 0  # 简化版本不计算速度
                            remaining = 0
                            self.signals.download_progress.emit(downloaded_size, total_size, speed, remaining)
            
            # 验证下载的文件
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                print(f"Download completed successfully: {file_path}")
                self.signals.status_changed.emit("下载完成！")
                return file_path
            else:
                raise Exception("下载的文件不存在或为空")
            
        except Exception as e:
            error_msg = f"下载失败: {str(e)}"
            print(f"Download error: {error_msg}")
            self.signals.error_occurred.emit(error_msg)
            return None
    
    def _on_download_progress(self, downloaded: int, total: int, speed: float, remaining: float):
        """处理下载进度"""
        # 转发详细下载进度
        self.signals.download_progress.emit(downloaded, total, speed, remaining)
        
        # 计算总体进度 (下载占80%，其他操作占20%)
        if total > 0:
            download_progress = int((downloaded / total) * 80)
            self.signals.progress_changed.emit(download_progress)
    
    def extract_update(self, file_path: str) -> Optional[str]:
        """解压更新文件"""
        try:
            self.signals.status_changed.emit("正在解压文件...")
            self.signals.progress_changed.emit(85)
            
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
            elif file_path.endswith('.exe'):
                # 对于 .exe 文件，在非 Windows 系统上提示手动安装
                current_system = platform.system()
                if current_system != 'Windows':
                    self.signals.error_occurred.emit(f"下载的是 Windows 安装程序，当前系统是 {current_system}。\n请手动下载适合您系统的版本。")
                    return None
                else:
                    # Windows 系统直接返回文件路径，由安装函数处理
                    return file_path
            else:
                raise Exception(f"不支持的文件格式: {file_path}")
            
            self.signals.progress_changed.emit(90)
            self.signals.status_changed.emit("解压完成")
            return extract_dir
            
        except Exception as e:
            self.signals.error_occurred.emit(f"解压失败: {str(e)}")
            return None
    
    def install_update(self, extract_dir: str) -> bool:
        """安装更新"""
        try:
            self.signals.status_changed.emit("正在安装更新...")
            self.signals.progress_changed.emit(95)
            
            if not self.temp_dir:
                raise Exception("临时目录未初始化")
            
            # 创建备份目录
            backup_dir = os.path.join(self.temp_dir, "backup")
            os.makedirs(backup_dir, exist_ok=True)
            
            # 备份当前程序文件
            self._backup_current_files(backup_dir)
            
            # 复制新文件
            self._copy_update_files(extract_dir)
            
            self.signals.progress_changed.emit(99)
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
        print(f"cleanup() called, temp_dir: {self.temp_dir}")  # 调试输出
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                print(f"Removing temp directory: {self.temp_dir}")  # 调试输出
                shutil.rmtree(self.temp_dir)
                print("Temp directory removed successfully")  # 调试输出
            except Exception as e:
                print(f"清理临时文件失败: {e}")
        else:
            print("No temp directory to clean up")  # 调试输出
    
    def run(self):
        """执行更新流程"""
        try:
            self.signals.status_changed.emit("开始更新流程...")
            
            # 检查更新
            self.signals.status_changed.emit("正在获取更新信息...")
            update_info = self.check_for_updates()
            if not update_info or self.cancelled:
                self.signals.status_changed.emit("未找到更新信息或已取消")
                return
            
            self.signals.status_changed.emit(f"准备下载版本 {update_info['version']}")
            
            # 下载更新
            downloaded_file = self.download_update(
                update_info['download_url'], 
                update_info['asset_name']
            )
            if not downloaded_file or self.cancelled:
                self.signals.status_changed.emit("下载失败或已取消")
                return
            
            self.signals.status_changed.emit("下载完成！")
            self.signals.progress_changed.emit(100)
            
            # 检查是否为exe文件且当前系统非Windows
            current_system = platform.system()
            print(f"Downloaded file: {downloaded_file}")  # 调试输出
            print(f"Current system: {current_system}")  # 调试输出
            if downloaded_file.endswith('.exe') and current_system != 'Windows':
                # 直接完成，返回文件路径
                print(f"Emitting update_completed signal with file path: {downloaded_file}")  # 调试输出
                self.signals.update_completed.emit(downloaded_file)
                # 不要立即清理，让用户有时间访问文件
                print("Skipping cleanup to preserve downloaded file")  # 调试输出
                return
            
            # 对于其他情况，继续原有流程
            self.signals.status_changed.emit("下载完成，开始解压...")
            
            # 解压更新
            extract_dir = self.extract_update(downloaded_file)
            if not extract_dir or self.cancelled:
                self.signals.status_changed.emit("解压失败或已取消")
                return
            
            # 安装更新
            self.signals.status_changed.emit("开始安装更新...")
            if self.install_update(extract_dir) and not self.cancelled:
                self.signals.progress_changed.emit(100)
                self.signals.status_changed.emit("更新安装完成")
                self.signals.update_completed.emit("")  # 传递空字符串表示正常安装完成
            else:
                self.signals.status_changed.emit("安装失败或已取消")
            
        except Exception as e:
            error_msg = f"更新过程中发生错误: {str(e)}"
            print(f"AutoUpdater error: {error_msg}")  # 调试输出
            self.signals.error_occurred.emit(error_msg)
        finally:
            # 对于下载完成的情况，延迟清理临时文件
            # 这样用户有时间访问下载的文件
            pass  # 暂时不在这里清理


def check_update_availability(current_version: str, repo: str = "goldenfishs/MRobot") -> Optional[dict]:
    """快速检查是否有新版本可用（不下载）"""
    updater = AutoUpdater(current_version, repo)
    return updater.check_for_updates()