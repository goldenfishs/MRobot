from PyQt5.QtCore import QThread, pyqtSignal
import requests
import shutil
import os
from urllib.parse import quote

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
        max_retry = 3
        for idx, rel_path in enumerate(self.files):
            retry = 0
            while retry < max_retry:
                try:
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
                        break
                    else:
                        retry += 1
                except Exception:
                    retry += 1
            else:
                fail.append(rel_path)
            self.progressChanged.emit(int((idx + 1) / total * 100))
        self.finished.emit(success, fail)