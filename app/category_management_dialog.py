"""
分类管理对话框
提供新增、重命名、删除分类的功能
"""

from typing import Optional
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt
from qfluentwidgets import (BodyLabel, PushButton, PrimaryPushButton, LineEdit, 
                           InfoBar, InfoBarPosition)
from .tools.finance_manager import FinanceManager


class CategoryManagementDialog(QDialog):
    """分类管理对话框"""
    
    def __init__(self, parent=None, finance_manager: Optional[FinanceManager] = None, account_id: Optional[str] = None):
        super().__init__(parent)
        self.finance_manager = finance_manager
        self.account_id = account_id
        self.setWindowTitle("分类管理")
        self.setGeometry(100, 100, 500, 400)
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        
        # 标签
        title_label = BodyLabel("选择分类进行管理:")
        main_layout.addWidget(title_label)
        
        # 分类列表
        self.category_list = QListWidget()
        self.category_list.itemSelectionChanged.connect(self.on_category_selected)
        main_layout.addWidget(self.category_list)
        
        # 加载分类
        self.load_categories()
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        # 新增按钮
        add_btn = PrimaryPushButton("新增")
        add_btn.clicked.connect(self.on_add_category)
        btn_layout.addWidget(add_btn)
        
        # 重命名按钮
        self.rename_btn = PushButton("重命名")
        self.rename_btn.clicked.connect(self.on_rename_category)
        self.rename_btn.setEnabled(False)
        btn_layout.addWidget(self.rename_btn)
        
        # 删除按钮
        self.delete_btn = PushButton("删除")
        self.delete_btn.clicked.connect(self.on_delete_category)
        self.delete_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_btn)
        
        # 关闭按钮
        close_btn = PushButton("关闭")
        close_btn.clicked.connect(self.accept)
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
        from PyQt5.QtWidgets import QLabel
        
        dialog = QStdDialog(self)
        dialog.setWindowTitle("新增分类")
        dialog.setGeometry(150, 150, 400, 150)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(BodyLabel("分类名称:"))
        
        input_edit = LineEdit()
        input_edit.setPlaceholderText("例如：食品、交通、娱乐等")
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
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        create_btn = PrimaryPushButton("创建")
        create_btn.clicked.connect(on_create)
        btn_layout.addWidget(create_btn)
        
        layout.addLayout(btn_layout)
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
        dialog.setGeometry(150, 150, 400, 150)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(BodyLabel(f"原分类名: {old_name}"))
        layout.addWidget(BodyLabel("新分类名:"))
        
        input_edit = LineEdit()
        input_edit.setText(old_name)
        input_edit.selectAll()
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
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        rename_btn = PrimaryPushButton("重命名")
        rename_btn.clicked.connect(on_rename)
        btn_layout.addWidget(rename_btn)
        
        layout.addLayout(btn_layout)
        dialog.exec()
    
    def on_delete_category(self):
        """删除分类"""
        current_item = self.category_list.currentItem()
        if not current_item:
            return
        
        category_name = current_item.text()
        
        # 确认删除
        from PyQt5.QtWidgets import QMessageBox
        
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
