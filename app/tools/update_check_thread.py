"""
更新检查线程
避免阻塞UI界面的更新检查
"""

from PyQt5.QtCore import QThread, pyqtSignal
from app.tools.check_update import check_update_availability


class UpdateCheckThread(QThread):
    """更新检查线程"""
    
    # 信号定义
    update_found = pyqtSignal(dict)  # 发现更新
    no_update = pyqtSignal()  # 无更新
    error_occurred = pyqtSignal(str)  # 检查出错
    
    def __init__(self, current_version: str, repo: str = "goldenfishs/MRobot"):
        super().__init__()
        self.current_version = current_version
        self.repo = repo
    
    def run(self):
        """执行更新检查"""
        try:
            update_info = check_update_availability(self.current_version, self.repo)
            
            if update_info:
                self.update_found.emit(update_info)
            else:
                self.no_update.emit()
                
        except Exception as e:
            self.error_occurred.emit(str(e))