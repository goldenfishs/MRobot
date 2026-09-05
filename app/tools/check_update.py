import requests
import platform
from packaging.version import parse as vparse
from typing import Optional

def check_update(local_version, repo="goldenfishs/MRobot"):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    resp = requests.get(url, timeout=5)
    if resp.status_code == 200:
        latest = resp.json()["tag_name"].lstrip("v")
        if vparse(latest) > vparse(local_version):
            return latest
        else:
            return None
    else:
        raise RuntimeError("GitHub API 请求失败")

def check_update_availability(current_version: str, repo: str = "goldenfishs/MRobot") -> Optional[dict]:
    """检查更新并返回详细信息"""
    try:
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            release_data = response.json()
            latest_version = release_data["tag_name"].lstrip("v")
            
            if vparse(latest_version) > vparse(current_version):
                # 获取适合当前平台的下载链接和文件大小
                download_url, asset_size, asset_name = _get_platform_asset(release_data)
                
                return {
                    'version': latest_version,
                    'download_url': download_url,
                    'asset_size': asset_size,
                    'asset_name': asset_name,
                    'release_notes': release_data.get('body', ''),
                    'release_date': release_data.get('published_at', ''),
                }
            return None
        else:
            raise Exception(f"GitHub API请求失败: {response.status_code}")
            
    except Exception as e:
        raise Exception(f"检查更新失败: {str(e)}")

def _get_platform_asset(release_data: dict) -> tuple:
    """获取适合当前平台的资源文件信息"""
    assets = release_data.get('assets', [])
    system = platform.system().lower()
    
    # 根据操作系统选择合适的安装包
    for asset in assets:
        name = asset['name'].lower()
        
        if system == 'windows':
            if 'installer' in name and name.endswith('.exe'):
                return asset['browser_download_url'], asset.get('size', 0), asset['name']
            if name.endswith('.exe') or name.endswith('.zip'):
                return asset['browser_download_url'], asset.get('size', 0), asset['name']
        elif system == 'darwin':  # macOS
            if name.endswith('.dmg') or name.endswith('.zip'):
                return asset['browser_download_url'], asset.get('size', 0), asset['name']
        elif system == 'linux':
            if name.endswith('.tar.gz') or name.endswith('.zip'):
                return asset['browser_download_url'], asset.get('size', 0), asset['name']
    
    # 如果没找到特定平台的，返回第一个可用文件
    for asset in assets:
        name = asset['name'].lower()
        if any(name.endswith(ext) for ext in ['.zip', '.exe', '.dmg', '.tar.gz']):
            return asset['browser_download_url'], asset.get('size', 0), asset['name']
    
    return None, 0, None