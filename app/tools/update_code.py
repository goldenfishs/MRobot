import os
import requests
import zipfile
import io
import shutil

def update_code(parent=None, info_callback=None, error_callback=None):
    url = "http://gitea.qutrobot.top/robofish/MRobot/archive/User_code.zip"
    local_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../assets/User_code")
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
        if info_callback:
            info_callback(parent)
        return True
    except Exception as e:
        if error_callback:
            error_callback(parent, str(e))
        return False