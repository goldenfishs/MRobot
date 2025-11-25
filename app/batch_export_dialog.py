"""
批量导出选项对话框
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QButtonGroup, QRadioButton
from PyQt5.QtCore import Qt
from qfluentwidgets import BodyLabel, PushButton, PrimaryPushButton, SubtitleLabel


class BatchExportDialog(QDialog):
    """批量导出选项对话框"""
    
    EXPORT_NORMAL = 0  # 普通文件夹导出
    EXPORT_MROBOT = 1  # MRobot 格式导出
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出选项")
        self.setGeometry(200, 200, 400, 250)
        self.export_type = self.EXPORT_NORMAL
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 标题
        title_label = SubtitleLabel("选择导出方式")
        layout.addWidget(title_label)
        
        # 选项组
        self.button_group = QButtonGroup()
        
        # 普通导出选项
        normal_radio = QRadioButton("普通导出")
        normal_radio.setChecked(True)
        normal_radio.setToolTip("将每个交易的图片导出到单独的文件夹（文件夹名：日期_金额）")
        self.button_group.addButton(normal_radio, self.EXPORT_NORMAL)
        layout.addWidget(normal_radio)
        
        normal_desc = BodyLabel("每个交易的图片保存在独立文件夹中，便于查看和管理")
        layout.addWidget(normal_desc)
        
        layout.addSpacing(15)
        
        # MRobot 格式导出选项
        mrobot_radio = QRadioButton("MRobot 专用格式")
        mrobot_radio.setToolTip("导出为 .mrobot 文件（专用格式，用于数据转交）")
        self.button_group.addButton(mrobot_radio, self.EXPORT_MROBOT)
        layout.addWidget(mrobot_radio)
        
        mrobot_desc = BodyLabel("导出为 .mrobot 文件（ZIP 格式），包含完整的交易数据和图片，用于转交给他人")
        layout.addWidget(mrobot_desc)
        
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = PushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = PrimaryPushButton("确定")
        ok_btn.clicked.connect(self.on_ok)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
    
    def on_ok(self):
        """确定按钮点击"""
        checked_button = self.button_group.checkedButton()
        if checked_button:
            self.export_type = self.button_group.id(checked_button)
        self.accept()
    
    def get_export_type(self):
        """获取选择的导出方式"""
        return self.export_type
