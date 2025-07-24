import requests
from packaging.version import parse as vparse

def check_update(local_version, repo="goldenfishs/MRobot"):
    """
    检查 GitHub 上是否有新版本
    :param local_version: 当前版本号字符串，如 "1.0.2"
    :param repo: 仓库名，格式 "用户名/仓库名"
    :return: 最新版本号字符串（如果有新版本），否则 None
    """
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            latest = resp.json()["tag_name"].lstrip("v")
            if vparse(latest) > vparse(local_version):
                return latest
    except Exception as e:
        print(f"检查更新失败: {e}")
    return None