"""
分类管理对话框
提供新增、重命名、删除分类的功能
"""

from typing import Optional
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QMessageBox, QScrollArea, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QColor, QFont
from qfluentwidgets import (BodyLabel, PushButton, PrimaryPushButton, LineEdit, 
                           InfoBar, InfoBarPosition, SubtitleLabel, TitleLabel,
                           HorizontalSeparator, CardWidget, FluentIcon, StrongBodyLabel, theme, Theme)
from .tools.finance_manager import FinanceManager


class CategoryManagementDialog(QDialog):
    """分类管理对话框"""
    
    def __init__(self, parent=None, finance_manager: Optional[FinanceManager] = None, account_id: Optional[str] = None):
        super().__init__(parent)
        self.finance_manager = finance_manager
        self.account_id = account_id
        self.setWindowTitle("分类管理")
        self.setGeometry(100, 100, 650, 550)
        self.setMinimumWidth(600)
        self.setMinimumHeight(480)
        
        # 设置背景色跟随主题
        if theme() == Theme.DARK:
            self.setStyleSheet("background-color: #232323;")
        else:
            self.setStyleSheet("background-color: #f7f9fc;")
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)
        
        # 标题区域
        title_layout = QVBoxLayout()
        title_layout.setSpacing(6)
        
        title_label = TitleLabel("分类管理")
        title_layout.addWidget(title_label)
        
        desc_label = BodyLabel("新增、编辑或删除您的交易分类")
        title_layout.addWidget(desc_label)
        
        main_layout.addLayout(title_layout)
        main_layout.addWidget(HorizontalSeparator())
        
        # 内容区域（分类列表）
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)
        
        # 左侧：分类列表卡片
        list_card = CardWidget()
        list_card_layout = QVBoxLayout()
        list_card_layout.setContentsMargins(0, 0, 0, 0)
        list_card_layout.setSpacing(0)
        
        list_label = StrongBodyLabel("现有分类")
        list_label.setStyleSheet("padding: 12px 16px; border-bottom: 1px solid var(--border-color);")
        list_card_layout.addWidget(list_label)
        
        # 分类列表
        self.category_list = QListWidget()
        self.category_list.itemSelectionChanged.connect(self.on_category_selected)
        self.category_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
            }
            QListWidget::item {
                padding: 10px 12px;
                border-radius: 4px;
                margin: 2px 4px;
            }
            QListWidget::item:hover {
                background-color: rgba(0, 0, 0, 0.05);
            }
            QListWidget::item:selected {
                background-color: var(--highlight-color);
                color: var(--highlight-text-color);
                font-weight: bold;
            }
        """)
        list_card_layout.addWidget(self.category_list, 1)
        list_card.setLayout(list_card_layout)
        list_card.setMinimumHeight(280)
        content_layout.addWidget(list_card, 1)
        
        main_layout.addLayout(content_layout, 1)
        
        # 加载分类
        self.load_categories()
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        # 新增按钮
        add_btn = PrimaryPushButton()
        add_btn.setIcon(FluentIcon.ADD)
        add_btn.setText("新增分类")
        add_btn.clicked.connect(self.on_add_category)
        add_btn.setMinimumWidth(120)
        btn_layout.addWidget(add_btn)
        
        # 重命名按钮
        self.rename_btn = PushButton()
        self.rename_btn.setIcon(FluentIcon.EDIT)
        self.rename_btn.setText("重命名")
        self.rename_btn.clicked.connect(self.on_rename_category)
        self.rename_btn.setEnabled(False)
        self.rename_btn.setMinimumWidth(110)
        btn_layout.addWidget(self.rename_btn)
        
        # 删除按钮
        self.delete_btn = PushButton()
        self.delete_btn.setIcon(FluentIcon.DELETE)
        self.delete_btn.setText("删除")
        self.delete_btn.clicked.connect(self.on_delete_category)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setMinimumWidth(110)
        btn_layout.addWidget(self.delete_btn)
        
        btn_layout.addStretch()
        
        # 关闭按钮
        close_btn = PushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumWidth(110)
        btn_layout.addWidget(close_btn)
        
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)
    
    def load_categories(self):
        """加载分类列表"""
        if not self.finance_manager or not self.account_id:
            return
        
        self.category_list.clear()
        categories = self.finance_manager.get_categories(self.account_id)
        for category in categories:
            item = QListWidgetItem(category)
            self.category_list.addItem(item)
    
    def on_category_selected(self):
        """分类被选择"""
        has_selection = self.category_list.currentItem() is not None
        self.rename_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def on_add_category(self):
        """新增分类"""
        # 弹出输入对话框
        from PyQt5.QtWidgets import QDialog as QStdDialog
        
        dialog = QStdDialog(self)
        dialog.setWindowTitle("新增分类")
        dialog.setGeometry(150, 150, 450, 220)
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # 标题
        title = StrongBodyLabel("创建新分类")
        layout.addWidget(title)
        
        # 说明文字
        desc = BodyLabel("请输入分类名称")
        desc.setStyleSheet("color: #606366;")
        layout.addWidget(desc)
        
        # 输入框
        input_edit = LineEdit()
        input_edit.setPlaceholderText("例如：食品、交通、娱乐、购物等")
        input_edit.setMinimumHeight(40)
        layout.addWidget(input_edit)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        def on_create():
            category_name = input_edit.text().strip()
            if not category_name:
                InfoBar.warning(
                    title="提示",
                    content="分类名称不能为空",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
            
            if self.finance_manager.add_category(self.account_id, category_name):
                InfoBar.success(
                    title="成功",
                    content=f"分类 '{category_name}' 创建成功",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                self.load_categories()
                dialog.accept()
            else:
                InfoBar.warning(
                    title="提示",
                    content="分类已存在",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
        
        cancel_btn = PushButton("取消")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        create_btn = PrimaryPushButton("创建")
        create_btn.setMinimumWidth(100)
        create_btn.clicked.connect(on_create)
        btn_layout.addWidget(create_btn)
        
        layout.addSpacing(12)
        layout.addLayout(btn_layout)
        
        # 回车快速创建
        input_edit.returnPressed.connect(on_create)
        
        dialog.exec()
    
    def on_rename_category(self):
        """重命名分类"""
        current_item = self.category_list.currentItem()
        if not current_item:
            return
        
        old_name = current_item.text()
        
        # 弹出输入对话框
        from PyQt5.QtWidgets import QDialog as QStdDialog
        
        dialog = QStdDialog(self)
        dialog.setWindowTitle("重命名分类")
        dialog.setGeometry(150, 150, 450, 280)
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # 标题
        title = StrongBodyLabel("重命名分类")
        layout.addWidget(title)
        
        # 原名称显示
        old_info_layout = QHBoxLayout()
        old_label = BodyLabel("原分类名:")
        old_label.setMinimumWidth(80)
        old_value = StrongBodyLabel(old_name)
        old_value.setStyleSheet("color: #1976d2;")
        old_info_layout.addWidget(old_label)
        old_info_layout.addWidget(old_value)
        old_info_layout.addStretch()
        layout.addLayout(old_info_layout)
        
        # 新名称输入
        new_label = BodyLabel("新分类名:")
        new_label.setMinimumWidth(80)
        layout.addWidget(new_label)
        
        input_edit = LineEdit()
        input_edit.setText(old_name)
        input_edit.selectAll()
        input_edit.setMinimumHeight(40)
        layout.addWidget(input_edit)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        def on_rename():
            new_name = input_edit.text().strip()
            if not new_name:
                InfoBar.warning(
                    title="提示",
                    content="分类名称不能为空",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return
            
            if new_name == old_name:
                dialog.accept()
                return
            
            if self.finance_manager.rename_category(self.account_id, old_name, new_name):
                InfoBar.success(
                    title="成功",
                    content=f"分类已重命名为 '{new_name}'",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                self.load_categories()
                dialog.accept()
            else:
                InfoBar.warning(
                    title="提示",
                    content="重命名失败，可能分类已存在",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
        
        cancel_btn = PushButton("取消")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        rename_btn = PrimaryPushButton("重命名")
        rename_btn.setMinimumWidth(100)
        rename_btn.clicked.connect(on_rename)
        btn_layout.addWidget(rename_btn)
        
        layout.addSpacing(12)
        layout.addLayout(btn_layout)
        
        # 回车快速重命名
        input_edit.returnPressed.connect(on_rename)
        
        dialog.exec()
    
    def on_delete_category(self):
        """删除分类"""
        current_item = self.category_list.currentItem()
        if not current_item:
            return
        
        category_name = current_item.text()
        
        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除分类 '{category_name}' 吗？\n\n使用该分类的交易记录分类将被清空。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.finance_manager.delete_category(self.account_id, category_name):
                InfoBar.success(
                    title="成功",
                    content=f"分类 '{category_name}' 已删除",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                self.load_categories()
            else:
                InfoBar.warning(
                    title="错误",
                    content="删除分类失败",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
