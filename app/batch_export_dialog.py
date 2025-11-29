"""
批量导出选项对话框
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QButtonGroup, QRadioButton, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette
from qfluentwidgets import (BodyLabel, PushButton, PrimaryPushButton, SubtitleLabel,
                           TitleLabel, HorizontalSeparator, CardWidget, FluentIcon, StrongBodyLabel,
                           theme, Theme)


class BatchExportDialog(QDialog):
    """批量导出选项对话框"""
    
    EXPORT_NORMAL = 0  # 普通文件夹导出
    EXPORT_MROBOT = 1  # MRobot 格式导出
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出选项")
        self.setGeometry(200, 200, 680, 550)
        self.setMinimumWidth(640)
        self.setMinimumHeight(480)
        
        # 设置背景色跟随主题
        if theme() == Theme.DARK:
            self.setStyleSheet("background-color: #232323;")
        else:
            self.setStyleSheet("background-color: #f7f9fc;")
        
        self.export_type = self.EXPORT_NORMAL
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # 标题区域
        title_layout = QVBoxLayout()
        title_layout.setSpacing(8)
        
        title_label = TitleLabel("选择导出方式")
        title_layout.addWidget(title_label)
        
        desc_label = BodyLabel("选择最适合您的导出格式")
        title_layout.addWidget(desc_label)
        
        layout.addLayout(title_layout)
        layout.addWidget(HorizontalSeparator())
        
        # 选项组
        self.button_group = QButtonGroup()
        
        # 普通导出选项卡
        normal_card = self._create_option_card(
            title="普通导出",
            description="将每个交易的图片导出到单独的文件夹",
            details="文件夹名称：日期_金额\n每个交易的图片保存在独立文件夹中，便于查看和管理",
            is_selected=True
        )
        normal_radio = normal_card.findChild(QRadioButton)
        normal_radio.setChecked(True)
        self.button_group.addButton(normal_radio, self.EXPORT_NORMAL)
        layout.addWidget(normal_card)
        
        # MRobot 格式导出选项卡
        mrobot_card = self._create_option_card(
            title="MRobot 专用格式",
            description="导出为 .mrobot 文件（ZIP 格式）",
            details="包含完整的交易数据和图片\n用于转交给他人或备份",
            is_selected=False
        )
        mrobot_radio = mrobot_card.findChild(QRadioButton)
        self.button_group.addButton(mrobot_radio, self.EXPORT_MROBOT)
        layout.addWidget(mrobot_card)
        
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        
        cancel_btn = PushButton("取消")
        cancel_btn.setMinimumWidth(110)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = PrimaryPushButton("确定导出")
        ok_btn.setMinimumWidth(110)
        ok_btn.clicked.connect(self.on_ok)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_option_card(self, title, description, details, is_selected=False):
        """创建导出选项卡片"""
        card = CardWidget()
        card_layout = QHBoxLayout()
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(16)
        
        # 单选按钮
        radio = QRadioButton()
        radio.setMinimumWidth(40)
        card_layout.addWidget(radio)
        
        # 内容区域
        content_layout = QVBoxLayout()
        content_layout.setSpacing(8)
        
        # 标题行
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
        # 图标
        icon_label = BodyLabel()
        icon_label.setText("📁" if title == "普通导出" else "📦")
        icon_label.setStyleSheet("font-size: 20px;")
        title_layout.addWidget(icon_label)
        
        # 标题
        title_label = StrongBodyLabel(title)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        content_layout.addLayout(title_layout)
        
        # 描述
        desc_label = BodyLabel(description)
        desc_label.setWordWrap(True)
        # 使用 QPalette 来自适应主题
        from PyQt5.QtGui import QPalette
        content_layout.addWidget(desc_label)
        
        # 详细信息
        details_label = BodyLabel(details)
        details_label.setWordWrap(True)
        # 使用相对颜色而不是硬编码
        content_layout.addWidget(details_label)
        
        content_layout.addStretch()
        card_layout.addLayout(content_layout, 1)
        
        # 设置卡片样式 - 不使用硬编码颜色，让 CardWidget 自适应主题
        # 只通过边框来显示选中状态
        self._update_card_style(card, is_selected)
        
        card.setLayout(card_layout)
        card.setMinimumHeight(120)
        
        # 点击卡片时选中单选按钮
        def on_card_clicked():
            radio.setChecked(True)
            # 更新卡片样式
            self._update_card_styles(radio)
        
        radio.clicked.connect(on_card_clicked)
        card.mousePressEvent = lambda e: on_card_clicked()
        
        return card
    
    def _update_card_style(self, card, is_selected):
        """更新单个卡片的样式"""
        if is_selected:
            card.setProperty("is_selected", True)
            card.setStyleSheet("""
                CardWidget[is_selected=true] {
                    border: 2px solid palette(highlight);
                }
                CardWidget[is_selected=false] {
                    border: 1px solid palette(mid);
                }
                CardWidget[is_selected=false]:hover {
                    border: 2px solid palette(highlight);
                }
            """)
        else:
            card.setProperty("is_selected", False)
            card.setStyleSheet("""
                CardWidget[is_selected=false] {
                    border: 1px solid palette(mid);
                }
                CardWidget[is_selected=false]:hover {
                    border: 2px solid palette(highlight);
                }
            """)
    
    def _update_card_styles(self, selected_radio):
        """更新所有卡片的样式"""
        for button in self.button_group.buttons():
            card = button.parent()
            while card and not isinstance(card, CardWidget):
                card = card.parent()
            
            if card:
                is_checked = button.isChecked()
                self._update_card_style(card, is_checked)
    
    def on_ok(self):
        """确定按钮点击"""
        checked_button = self.button_group.checkedButton()
        if checked_button:
            self.export_type = self.button_group.id(checked_button)
        self.accept()
    
    def get_export_type(self):
        """获取选择的导出方式"""
        return self.export_type
