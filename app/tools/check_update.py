import requests
from packaging.version import parse as vparse

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