"""
财务做账应用主界面
包含做账、查询、导出三个功能标签页
"""

from typing import Optional
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QStackedLayout, QStackedWidget,
                             QFileDialog, QScrollArea, QFrame,
                             QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QTreeWidget, QTreeWidgetItem)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QMimeData, QRect, QSize, QItemSelectionModel
from PyQt5.QtGui import QIcon, QPixmap, QDrag, QFont, QColor
from qfluentwidgets import (TitleLabel, BodyLabel, SubtitleLabel, StrongBodyLabel, 
                           HorizontalSeparator, CardWidget, PushButton, LineEdit, 
                           SpinBox, CheckBox, TextEdit, PrimaryPushButton, 
                           InfoBar, InfoBarPosition, FluentIcon as FIF, ComboBox,
                           DoubleSpinBox, DateEdit, SearchLineEdit, StateToolTip,
                           Dialog, SegmentedWidget, TreeWidget)
from pathlib import Path
from datetime import datetime, timedelta
import json
import os
import shutil

from .tools.finance_manager import FinanceManager, TransactionType, Transaction, Account
from .category_management_dialog import CategoryManagementDialog
from .batch_export_dialog import BatchExportDialog


class CreateTransactionDialog(QDialog):
    """创建/编辑交易记录对话框"""
    
    def __init__(self, parent=None, transaction: Optional[Transaction] = None, account_id: Optional[str] = None, finance_manager=None):
        super().__init__(parent)
        self.transaction = transaction
        self.account_id = account_id
        self.finance_manager = finance_manager if finance_manager else FinanceManager()
        
        self.setWindowTitle("新建交易记录" if not transaction else "编辑交易记录")
        self.setGeometry(100, 100, 700, 650)
        self.setMinimumWidth(650)
        self.setMinimumHeight(580)
        
        # 设置背景色跟随主题
        from qfluentwidgets import theme, Theme
        if theme() == Theme.DARK:
            self.setStyleSheet("background-color: #232323;")
        else:
            self.setStyleSheet("background-color: #f7f9fc;")
        
        self.init_ui()
        
        if transaction:
            self.load_transaction_data(transaction)
        else:
            # 新建时默认为"入账"
            self.transaction_type_combo.setCurrentIndex(0)
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # 标题区域
        title_layout = QVBoxLayout()
        title_layout.setSpacing(6)
        title_label = TitleLabel("交易记录" if not self.transaction else "编辑交易")
        title_layout.addWidget(title_label)
        desc_label = BodyLabel("请填写交易的相关信息")
        title_layout.addWidget(desc_label)
        layout.addLayout(title_layout)
        layout.addWidget(HorizontalSeparator())
        
        # 使用ScrollArea实现可滚动的内容区
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(12)
        
        # 交易类型
        type_layout = QHBoxLayout()
        type_label = BodyLabel("交易类型:")
        type_label.setMinimumWidth(80)
        type_layout.addWidget(type_label)
        self.transaction_type_combo = ComboBox()
        self.transaction_type_combo.addItem("入账 (正数)")
        self.transaction_type_combo.addItem("支出 (负数)")
        self.transaction_type_combo.setMaximumWidth(250)
        type_layout.addWidget(self.transaction_type_combo)
        type_layout.addStretch()
        scroll_layout.addLayout(type_layout)
        
        # 分类
        category_layout = QHBoxLayout()
        cat_label = BodyLabel("分类:")
        cat_label.setMinimumWidth(80)
        category_layout.addWidget(cat_label)
        self.category_combo = ComboBox()
        # 从财务管理器获取分类列表
        categories = []
        if self.account_id:
            # 确保账户数据已加载
            account = self.finance_manager.get_account(self.account_id)
            if account:
                categories = account.categories
        
        # 如果没有分类，提示用户创建
        if not categories:
            self.category_combo.addItem("请先在做账页创建分类")
            self.category_combo.setEnabled(False)
        else:
            for cat in categories:
                self.category_combo.addItem(cat)
            self.category_combo.setEnabled(True)
        
        self.category_combo.setMaximumWidth(250)
        category_layout.addWidget(self.category_combo)
        category_layout.addStretch()
        scroll_layout.addLayout(category_layout)
        
        # 日期
        date_layout = QHBoxLayout()
        date_label = BodyLabel("日期:")
        date_label.setMinimumWidth(80)
        date_layout.addWidget(date_label)
        self.date_edit = DateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setMaximumWidth(250)
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()
        scroll_layout.addLayout(date_layout)
        
        # 金额
        amount_layout = QHBoxLayout()
        amt_label = BodyLabel("金额 (元):")
        amt_label.setMinimumWidth(80)
        amount_layout.addWidget(amt_label)
        self.amount_spin = DoubleSpinBox()
        self.amount_spin.setRange(0, 999999999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setMaximumWidth(250)
        amount_layout.addWidget(self.amount_spin)
        amount_layout.addStretch()
        scroll_layout.addLayout(amount_layout)
        
        # 交易人
        trader_layout = QHBoxLayout()
        trader_label = BodyLabel("交易人:")
        trader_label.setMinimumWidth(80)
        trader_layout.addWidget(trader_label)
        self.trader_edit = LineEdit()
        self.trader_edit.setMaximumWidth(250)
        trader_layout.addWidget(self.trader_edit)
        trader_layout.addStretch()
        scroll_layout.addLayout(trader_layout)
        
        # 备注
        notes_layout = QVBoxLayout()
        notes_label = BodyLabel("备注:")
        notes_layout.addWidget(notes_label)
        self.notes_edit = TextEdit()
        self.notes_edit.setMaximumHeight(100)
        self.notes_edit.setMinimumHeight(70)
        notes_layout.addWidget(self.notes_edit)
        scroll_layout.addLayout(notes_layout)
        
        # 图片部分
        scroll_layout.addWidget(HorizontalSeparator())
        scroll_layout.addWidget(SubtitleLabel("相关文件 (可选)"))
        
        # 发票
        invoice_layout = QHBoxLayout()
        invoice_label = BodyLabel("发票图片:")
        invoice_label.setMinimumWidth(80)
        invoice_layout.addWidget(invoice_label)
        self.invoice_label = BodyLabel("未选择")
        invoice_layout.addWidget(self.invoice_label, 1)
        invoice_btn = PushButton("选择")
        invoice_btn.setMaximumWidth(100)
        invoice_btn.clicked.connect(lambda: self.select_image("invoice"))
        invoice_layout.addWidget(invoice_btn)
        scroll_layout.addLayout(invoice_layout)
        
        # 支付记录
        payment_layout = QHBoxLayout()
        payment_label = BodyLabel("支付记录:")
        payment_label.setMinimumWidth(80)
        payment_layout.addWidget(payment_label)
        self.payment_label = BodyLabel("未选择")
        payment_layout.addWidget(self.payment_label, 1)
        payment_btn = PushButton("选择")
        payment_btn.setMaximumWidth(100)
        payment_btn.clicked.connect(lambda: self.select_image("payment"))
        payment_layout.addWidget(payment_btn)
        scroll_layout.addLayout(payment_layout)
        
        # 购买记录
        purchase_layout = QHBoxLayout()
        purchase_label = BodyLabel("购买记录:")
        purchase_label.setMinimumWidth(80)
        purchase_layout.addWidget(purchase_label)
        self.purchase_label = BodyLabel("未选择")
        purchase_layout.addWidget(self.purchase_label, 1)
        purchase_btn = PushButton("选择")
        purchase_btn.setMaximumWidth(100)
        purchase_btn.clicked.connect(lambda: self.select_image("purchase"))
        purchase_layout.addWidget(purchase_btn)
        scroll_layout.addLayout(purchase_layout)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area, 1)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        
        cancel_btn = PushButton("取消")
        cancel_btn.setMinimumWidth(110)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = PrimaryPushButton("保存")
        save_btn.setMinimumWidth(110)
        save_btn.clicked.connect(self.save_transaction)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
        
        # 存储图片路径
        self.selected_images: dict = {
            'invoice': None,
            'payment': None,
            'purchase': None
        }
    
    def select_image(self, image_type: str):
        """选择图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"选择{image_type}图片",
            "", "图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*)"
        )
        
        if file_path:
            self.selected_images[image_type] = file_path
            filename = Path(file_path).name
            
            if image_type == 'invoice':
                self.invoice_label.setText(filename)
            elif image_type == 'payment':
                self.payment_label.setText(filename)
            elif image_type == 'purchase':
                self.purchase_label.setText(filename)
    
    def load_transaction_data(self, transaction: Transaction):
        """加载交易记录数据到表单"""
        # 根据金额的正负设置交易类型
        if transaction.amount >= 0:
            self.transaction_type_combo.setCurrentIndex(0)  # 入账
        else:
            self.transaction_type_combo.setCurrentIndex(1)  # 支出
        
        # 设置分类
        category_index = self.category_combo.findText(transaction.category)
        if category_index >= 0:
            self.category_combo.setCurrentIndex(category_index)
        else:
            self.category_combo.setCurrentIndex(0)  # 默认为第一个
        
        self.date_edit.setDate(QDate.fromString(transaction.date, "yyyy-MM-dd"))
        # 显示绝对值
        self.amount_spin.setValue(abs(transaction.amount))
        self.trader_edit.setText(transaction.trader)
        self.notes_edit.setText(transaction.notes)
        
        if transaction.invoice_path:
            self.invoice_label.setText(Path(transaction.invoice_path).name)
        if transaction.payment_path:
            self.payment_label.setText(Path(transaction.payment_path).name)
        if transaction.purchase_path:
            self.purchase_label.setText(Path(transaction.purchase_path).name)
    
    def save_transaction(self):
        """保存交易记录"""
        if not self.account_id:
            dialog = Dialog(
                title="错误",
                content="账户ID未设置",
                parent=self
            )
            dialog.yesButton.setText("确定")
            dialog.cancelButton.hide()
            dialog.exec()
            return
        
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        amount = self.amount_spin.value()
        trader = self.trader_edit.text().strip()
        notes = self.notes_edit.toPlainText().strip()
        category = self.category_combo.currentText()
        
        # 检查分类是否有效
        if not category or category == "请先在做账页创建分类":
            dialog = Dialog(
                title="验证错误",
                content="请先创建分类后再添加交易",
                parent=self
            )
            dialog.yesButton.setText("确定")
            dialog.cancelButton.hide()
            dialog.exec()
            return
        
        if not trader:
            dialog = Dialog(
                title="验证错误",
                content="请输入交易人",
                parent=self
            )
            dialog.yesButton.setText("确定")
            dialog.cancelButton.hide()
            dialog.exec()
            return
        
        if amount <= 0:
            dialog = Dialog(
                title="验证错误",
                content="金额必须大于0",
                parent=self
            )
            dialog.yesButton.setText("确定")
            dialog.cancelButton.hide()
            dialog.exec()
            return
        
        # 根据交易类型设置金额符号：入账为正数，支出为负数
        is_income = self.transaction_type_combo.currentIndex() == 0
        final_amount = amount if is_income else -amount
        
        if self.transaction:
            # 编辑现有交易记录
            trans_id = self.transaction.id
            self.finance_manager.update_transaction(
                self.account_id, trans_id,
                date=date_str, amount=final_amount,
                trader=trader, notes=notes, category=category
            )
        else:
            # 创建新交易记录
            transaction = Transaction(
                date=date_str, amount=final_amount,
                trader=trader, notes=notes, category=category
            )
            self.finance_manager.add_transaction(self.account_id, transaction)
            trans_id = transaction.id
        
        # 保存图片
        for image_type_str, image_path in self.selected_images.items():
            if image_path:
                image_type = TransactionType[image_type_str.upper()]
                relative_path = self.finance_manager.save_image_for_transaction(
                    self.account_id, trans_id, image_type, image_path
                )
                if relative_path:
                    self.finance_manager.update_transaction(
                        self.account_id, trans_id,
                        **{f"{image_type_str}_path": relative_path}
                    )
        
        self.accept()


class RecordViewDialog(QDialog):
    """查看和编辑交易记录详情对话框"""
    
    def __init__(self, parent=None, account_id: Optional[str] = None, transaction: Optional[Transaction] = None):
        super().__init__(parent)
        self.account_id = account_id
        self.transaction = transaction
        self.finance_manager = FinanceManager()
        
        self.setWindowTitle("记录详情")
        self.setGeometry(100, 100, 750, 650)
        self.setMinimumWidth(700)
        self.setMinimumHeight(580)
        
        # 设置背景色跟随主题
        from qfluentwidgets import theme, Theme
        if theme() == Theme.DARK:
            self.setStyleSheet("background-color: #232323;")
        else:
            self.setStyleSheet("background-color: #f7f9fc;")
        
        self.init_ui()
        
        if transaction:
            self.load_transaction_data()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # 标题区域
        title_layout = QVBoxLayout()
        title_layout.setSpacing(6)
        title_label = TitleLabel("交易记录详情")
        title_layout.addWidget(title_label)
        desc_label = BodyLabel("查看交易的完整信息和相关文件")
        title_layout.addWidget(desc_label)
        layout.addLayout(title_layout)
        layout.addWidget(HorizontalSeparator())
        
        # 使用ScrollArea实现可滚动的内容区
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(12)
        
        # 基本信息
        date_layout = QHBoxLayout()
        date_label = BodyLabel("日期:")
        date_label.setMinimumWidth(80)
        date_layout.addWidget(date_label)
        self.date_label = BodyLabel()
        date_layout.addWidget(self.date_label, 1)
        date_layout.addStretch()
        scroll_layout.addLayout(date_layout)
        
        amount_layout = QHBoxLayout()
        amount_label = BodyLabel("金额:")
        amount_label.setMinimumWidth(80)
        amount_layout.addWidget(amount_label)
        self.amount_label = BodyLabel()
        amount_layout.addWidget(self.amount_label, 1)
        amount_layout.addStretch()
        scroll_layout.addLayout(amount_layout)
        
        trader_layout = QHBoxLayout()
        trader_label = BodyLabel("交易人:")
        trader_label.setMinimumWidth(80)
        trader_layout.addWidget(trader_label)
        self.trader_label = BodyLabel()
        trader_layout.addWidget(self.trader_label, 1)
        trader_layout.addStretch()
        scroll_layout.addLayout(trader_layout)
        
        notes_layout = QVBoxLayout()
        notes_title = BodyLabel("备注:")
        notes_layout.addWidget(notes_title)
        self.notes_label = BodyLabel()
        self.notes_label.setWordWrap(True)
        notes_layout.addWidget(self.notes_label)
        scroll_layout.addLayout(notes_layout)
        
        scroll_layout.addWidget(HorizontalSeparator())
        
        # 图片预览
        scroll_layout.addWidget(SubtitleLabel("相关文件预览"))
        
        preview_layout = QHBoxLayout()
        preview_layout.setSpacing(16)
        
        # 发票
        invoice_layout = QVBoxLayout()
        invoice_layout.addWidget(BodyLabel("发票:"))
        self.invoice_preview = BodyLabel("无")
        self.invoice_preview.setMinimumSize(140, 140)
        invoice_layout.addWidget(self.invoice_preview)
        preview_layout.addLayout(invoice_layout)
        
        # 支付记录
        payment_layout = QVBoxLayout()
        payment_layout.addWidget(BodyLabel("支付记录:"))
        self.payment_preview = BodyLabel("无")
        self.payment_preview.setMinimumSize(140, 140)
        payment_layout.addWidget(self.payment_preview)
        preview_layout.addLayout(payment_layout)
        
        # 购买记录
        purchase_layout = QVBoxLayout()
        purchase_layout.addWidget(BodyLabel("购买记录:"))
        self.purchase_preview = BodyLabel("无")
        self.purchase_preview.setMinimumSize(140, 140)
        purchase_layout.addWidget(self.purchase_preview)
        preview_layout.addLayout(purchase_layout)
        
        scroll_layout.addLayout(preview_layout)
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area, 1)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()
        
        export_images_btn = PushButton()
        export_images_btn.setText("导出图片")
        export_images_btn.setMinimumWidth(120)
        export_images_btn.clicked.connect(self.on_export_images)
        btn_layout.addWidget(export_images_btn)
        
        close_btn = PushButton("关闭")
        close_btn.setMinimumWidth(110)
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        self.invoice_preview.setMinimumSize(150, 150)
        invoice_layout.addWidget(self.invoice_preview)
        preview_layout.addLayout(invoice_layout)
        
        # 支付记录
        payment_layout = QVBoxLayout()
        payment_layout.addWidget(BodyLabel("支付记录:"))
        self.payment_preview = BodyLabel("无")
        self.payment_preview.setMinimumSize(150, 150)
        payment_layout.addWidget(self.payment_preview)
        preview_layout.addLayout(payment_layout)
        
        # 购买记录
        purchase_layout = QVBoxLayout()
        purchase_layout.addWidget(BodyLabel("购买记录:"))
        self.purchase_preview = BodyLabel("无")
        self.purchase_preview.setMinimumSize(150, 150)
        purchase_layout.addWidget(self.purchase_preview)
        preview_layout.addLayout(purchase_layout)
        
        layout.addLayout(preview_layout)
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        export_images_btn = PushButton("导出图片")
        export_images_btn.clicked.connect(self.on_export_images)
        btn_layout.addWidget(export_images_btn)
        
        close_btn = PushButton("关闭")
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def load_transaction_data(self):
        """加载交易记录数据"""
        if not self.transaction:
            return
        
        self.date_label.setText(self.transaction.date)
        self.amount_label.setText(f"¥ {self.transaction.amount:.2f}")
        self.trader_label.setText(self.transaction.trader)
        self.notes_label.setText(self.transaction.notes or "无")
        
        # 加载图片预览
        self._load_image_preview('invoice', self.transaction.invoice_path if self.transaction else None, self.invoice_preview)
        self._load_image_preview('payment', self.transaction.payment_path if self.transaction else None, self.payment_preview)
        self._load_image_preview('purchase', self.transaction.purchase_path if self.transaction else None, self.purchase_preview)
    
    def _load_image_preview(self, image_type: str, relative_path: Optional[str], label: BodyLabel):
        """加载并显示图片预览"""
        if not relative_path:
            return
        
        full_path = self.finance_manager.get_transaction_image_path(self.account_id or "", relative_path)
        if full_path and full_path.exists():
            pixmap = QPixmap(str(full_path))
            scaled_pixmap = pixmap.scaledToWidth(150)
            label.setPixmap(scaled_pixmap)
    
    def on_export_images(self):
        """导出交易的所有图片"""
        if not self.transaction or not self.account_id:
            InfoBar.warning(
                title="提示",
                content="没有可导出的图片",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        # 检查是否有图片
        has_images = False
        image_paths = {}
        
        if self.transaction.invoice_path:
            full_path = self.finance_manager.get_transaction_image_path(self.account_id, self.transaction.invoice_path)
            if full_path and full_path.exists():
                image_paths['发票'] = full_path
                has_images = True
        
        if self.transaction.payment_path:
            full_path = self.finance_manager.get_transaction_image_path(self.account_id, self.transaction.payment_path)
            if full_path and full_path.exists():
                image_paths['支付记录'] = full_path
                has_images = True
        
        if self.transaction.purchase_path:
            full_path = self.finance_manager.get_transaction_image_path(self.account_id, self.transaction.purchase_path)
            if full_path and full_path.exists():
                image_paths['购买记录'] = full_path
                has_images = True
        
        if not has_images:
            InfoBar.warning(
                title="提示",
                content="该交易没有关联的图片",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        # 打开文件夹选择对话框
        export_dir = QFileDialog.getExistingDirectory(
            self,
            "选择导出文件夹",
            str(Path.home() / "Downloads")
        )
        
        if not export_dir:
            return
        
        export_path = Path(export_dir)
        
        # 创建文件夹，命名为 "日期_金额"
        folder_name = f"{self.transaction.date}_{self.transaction.amount:.2f}"
        folder_name = folder_name.replace(":", "-")  # 替换不允许的字符
        transaction_folder = export_path / folder_name
        transaction_folder.mkdir(parents=True, exist_ok=True)
        
        # 复制图片
        try:
            for img_name, img_path in image_paths.items():
                ext = img_path.suffix
                dest_file = transaction_folder / f"{img_name}{ext}"
                shutil.copy(str(img_path), str(dest_file))
            
            InfoBar.success(
                title="成功",
                content=f"图片已导出到 {transaction_folder.name}",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            InfoBar.warning(
                title="错误",
                content=f"导出失败: {str(e)}",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )


class FinanceInterface(QWidget):
    """财务做账主界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("financeInterface")
        self.finance_manager = FinanceManager()
        
        self.layout_main = QVBoxLayout(self)
        self.layout_main.setContentsMargins(0, 0, 0, 0)
        self.layout_main.setSpacing(0)
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        # 创建顶部标签切换器
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        self.segmented_widget = SegmentedWidget()
        self.segmented_widget.insertItem(0, "bookkeeping", "做账")
        self.segmented_widget.insertItem(1, "query", "查询")
        self.segmented_widget.insertItem(2, "export", "导出")
        self.segmented_widget.currentItemChanged.connect(self.on_tab_changed)
        top_layout.addWidget(self.segmented_widget)
        top_layout.addStretch()
        self.layout_main.addLayout(top_layout)
        
        # 内容堆叠
        self.stacked_widget = QStackedWidget()
        
        # 做账标签页
        self.bookkeeping_tab = self.create_bookkeeping_tab()
        self.stacked_widget.addWidget(self.bookkeeping_tab)
        
        # 查询标签页
        self.query_tab = self.create_query_tab()
        self.stacked_widget.addWidget(self.query_tab)
        
        # 导出标签页
        self.export_tab = self.create_export_tab()
        self.stacked_widget.addWidget(self.export_tab)
        
        self.layout_main.addWidget(self.stacked_widget)
        
        # 初始化时获取默认账户
        self.init_default_account()
    
    def on_tab_changed(self, route_key: str):
        """标签切换时更新显示"""
        tab_index = {"bookkeeping": 0, "query": 1, "export": 2}
        index = tab_index.get(route_key, 0)
        self.stacked_widget.setCurrentIndex(index)
    
    def create_bookkeeping_tab(self) -> QWidget:
        """创建做账标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题和操作按钮
        title_layout = QHBoxLayout()
        title_layout.addWidget(SubtitleLabel("交易记录"))
        
        # 管理分类按钮
        manage_category_btn = PushButton("管理分类")
        manage_category_btn.setFixedWidth(90)
        manage_category_btn.clicked.connect(self.on_manage_category_clicked)
        title_layout.addWidget(manage_category_btn)
        
        title_layout.addStretch()
        
        new_record_btn = PrimaryPushButton("新建记录")
        new_record_btn.clicked.connect(self.create_new_record)
        title_layout.addWidget(new_record_btn)
        
        layout.addLayout(title_layout)
        
        # 记录表格 - 使用 TreeWidget 风格
        self.records_table = TreeWidget()
        self.records_table.setHeaderLabels(["日期", "交易人", "分类", "金额 (元)", "备注"])
        self.records_table.setSelectionMode(self.records_table.SingleSelection)
        self.records_table.setIndentation(0)
        
        # 设置 TreeWidget 样式
        header = self.records_table.header()
        if header:
            header.setStretchLastSection(False)
            # 列宽自适应，可拖动调整
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.Stretch)
            # 启用列宽可拖动
            header.setSectionsMovable(False)
            header.setStretchLastSection(False)
        
        self.records_table.setCheckedColor("#0078d4", "#2d7d9a")
        self.records_table.setBorderRadius(8)
        self.records_table.setBorderVisible(True)
        self.records_table.itemSelectionChanged.connect(self.on_record_selection_changed)
        
        layout.addWidget(self.records_table)
        
        # 操作按钮区
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.view_record_btn = PushButton("查看详情")
        self.view_record_btn.setFixedWidth(90)
        self.view_record_btn.clicked.connect(self.on_view_record_clicked)
        self.view_record_btn.setEnabled(False)
        btn_layout.addWidget(self.view_record_btn)
        
        self.edit_record_btn = PushButton("编辑")
        self.edit_record_btn.setFixedWidth(75)
        self.edit_record_btn.clicked.connect(self.on_edit_record_clicked)
        self.edit_record_btn.setEnabled(False)
        btn_layout.addWidget(self.edit_record_btn)
        
        self.delete_record_btn = PushButton("删除")
        self.delete_record_btn.setFixedWidth(75)
        self.delete_record_btn.clicked.connect(self.on_delete_record_clicked)
        self.delete_record_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_record_btn)
        
        layout.addLayout(btn_layout)
        
        # 统计信息卡片
        stats_card = CardWidget()
        stats_layout = QHBoxLayout(stats_card)
        stats_layout.setContentsMargins(20, 15, 20, 15)
        stats_layout.setSpacing(30)
        
        stats_layout.addWidget(BodyLabel("总额:"))
        self.total_amount_label = StrongBodyLabel("¥ 0.00")
        self.total_amount_label.setStyleSheet("color: #d32f2f;")
        stats_layout.addWidget(self.total_amount_label)
        
        stats_layout.addSpacing(30)
        stats_layout.addWidget(BodyLabel("记录数:"))
        self.record_count_label = StrongBodyLabel("0")
        stats_layout.addWidget(self.record_count_label)
        
        stats_layout.addStretch()
        layout.addWidget(stats_card)
        
        return widget
    
    def create_query_tab(self) -> QWidget:
        """创建查询标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 搜索过滤区 - 卡片样式
        filter_card = CardWidget()
        filter_layout = QVBoxLayout(filter_card)
        filter_layout.setContentsMargins(20, 15, 20, 15)
        filter_layout.setSpacing(15)  # 增加间距为15
        
        # 第一行：日期范围
        date_layout = QHBoxLayout()
        date_layout.addWidget(BodyLabel("日期范围:"))
        self.query_date_start = DateEdit()
        self.query_date_start.setDate(QDate.currentDate().addMonths(-1))
        date_layout.addWidget(self.query_date_start, 1)
        date_layout.addWidget(BodyLabel("至"))
        self.query_date_end = DateEdit()
        self.query_date_end.setDate(QDate.currentDate())
        date_layout.addWidget(self.query_date_end, 1)
        filter_layout.addLayout(date_layout)
        
        # 第二行：交易类型和分类
        type_category_layout = QHBoxLayout()
        type_category_layout.addWidget(BodyLabel("交易类型:"))
        self.query_transaction_type = ComboBox()
        self.query_transaction_type.addItem("全部")
        self.query_transaction_type.addItem("收入 (正数)")
        self.query_transaction_type.addItem("支出 (负数)")
        type_category_layout.addWidget(self.query_transaction_type, 1)
        
        type_category_layout.addWidget(BodyLabel("分类:"))
        self.query_category = ComboBox()
        self.query_category.addItem("全部")
        # 初始化时加载现有分类
        account_id = self.get_current_account_id()
        if account_id:
            account = self.finance_manager.get_account(account_id)
            if account:
                for cat in account.categories:
                    self.query_category.addItem(cat)
        type_category_layout.addWidget(self.query_category, 1)
        filter_layout.addLayout(type_category_layout)
        
        # 第三行：金额范围
        amount_layout = QHBoxLayout()
        amount_layout.addWidget(BodyLabel("金额范围:"))
        self.query_amount_min = DoubleSpinBox()
        self.query_amount_min.setRange(0, 999999)
        self.query_amount_min.setPrefix("¥ ")
        amount_layout.addWidget(self.query_amount_min, 1)
        amount_layout.addWidget(BodyLabel("至"))
        self.query_amount_max = DoubleSpinBox()
        self.query_amount_max.setRange(0, 999999)
        self.query_amount_max.setValue(999999)
        self.query_amount_max.setPrefix("¥ ")
        amount_layout.addWidget(self.query_amount_max, 1)
        filter_layout.addLayout(amount_layout)
        
        # 第四行：交易人搜索和查询按钮
        trader_layout = QHBoxLayout()
        trader_layout.addWidget(BodyLabel("交易人:"))
        self.query_trader_edit = SearchLineEdit()
        self.query_trader_edit.setPlaceholderText("输入交易人名称...")
        trader_layout.addWidget(self.query_trader_edit, 1)
        
        query_btn = PrimaryPushButton("查询")
        query_btn.clicked.connect(self.perform_query)
        trader_layout.addWidget(query_btn)
        filter_layout.addLayout(trader_layout)
        
        layout.addWidget(filter_card)
        layout.addWidget(HorizontalSeparator())
        
        # 查询结果表格 - 使用 TreeWidget 风格
        self.query_result_table = TreeWidget()
        self.query_result_table.setHeaderLabels(["", "日期", "交易人", "分类", "金额 (元)", "备注"])
        self.query_result_table.setSelectionMode(self.query_result_table.MultiSelection)
        self.query_result_table.setIndentation(0)
        
        # 设置 TreeWidget 样式
        header = self.query_result_table.header()
        if header:
            header.setStretchLastSection(False)
            # 列宽自适应，可拖动调整
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 复选框列
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 日期
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 交易人
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 分类
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 金额
            header.setSectionResizeMode(5, QHeaderView.Stretch)          # 备注
            # 启用列宽可拖动
            header.setSectionsMovable(False)
            header.setStretchLastSection(False)
        
        self.query_result_table.setCheckedColor("#0078d4", "#2d7d9a")
        self.query_result_table.setBorderRadius(8)
        self.query_result_table.setBorderVisible(True)
        self.query_result_table.itemSelectionChanged.connect(self.on_query_result_selection_changed)
        
        layout.addWidget(self.query_result_table)
        
        # 查询结果操作按钮
        query_btn_layout = QHBoxLayout()
        
        # 批量导出按钮
        self.batch_export_btn = PushButton("批量导出")
        self.batch_export_btn.setFixedWidth(90)
        self.batch_export_btn.clicked.connect(self.on_batch_export)
        self.batch_export_btn.setEnabled(False)
        query_btn_layout.addWidget(self.batch_export_btn)
        
        query_btn_layout.addStretch()
        
        self.query_view_btn = PushButton("查看详情")
        self.query_view_btn.setFixedWidth(90)
        self.query_view_btn.clicked.connect(self.on_query_view_clicked)
        self.query_view_btn.setEnabled(False)
        query_btn_layout.addWidget(self.query_view_btn)
        
        layout.addLayout(query_btn_layout)
        
        return widget
    
    def create_export_tab(self) -> QWidget:
        """创建导出标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        layout.addWidget(TitleLabel("数据导出和导入"))
        layout.addWidget(HorizontalSeparator())
        
        # 导出选项
        layout.addWidget(SubtitleLabel("导出选项"))
        
        export_layout = QVBoxLayout()
        
        # 导出账户为压缩包
        account_export_layout = QHBoxLayout()
        account_export_layout.addWidget(BodyLabel("导出当前账户:"))
        account_export_layout.addStretch()
        export_account_btn = PrimaryPushButton("导出为ZIP包")
        export_account_btn.clicked.connect(self.export_account)
        account_export_layout.addWidget(export_account_btn)
        export_layout.addLayout(account_export_layout)
        
        # 导出为CSV
        csv_export_layout = QHBoxLayout()
        csv_export_layout.addWidget(BodyLabel("导出为Excel格式:"))
        csv_export_layout.addStretch()
        export_csv_btn = PrimaryPushButton("导出CSV")
        export_csv_btn.clicked.connect(self.export_csv)
        csv_export_layout.addWidget(export_csv_btn)
        export_layout.addLayout(csv_export_layout)
        
        # 备份所有账户
        backup_layout = QHBoxLayout()
        backup_layout.addWidget(BodyLabel("备份所有账户:"))
        backup_layout.addStretch()
        backup_btn = PrimaryPushButton("创建备份")
        backup_btn.clicked.connect(self.backup_all)
        backup_layout.addWidget(backup_btn)
        export_layout.addLayout(backup_layout)
        
        layout.addLayout(export_layout)
        layout.addWidget(HorizontalSeparator())
        
        # 导入选项
        layout.addWidget(SubtitleLabel("导入选项"))
        
        import_layout = QVBoxLayout()
        
        # 导入账户
        account_import_layout = QHBoxLayout()
        account_import_layout.addWidget(BodyLabel("导入账户ZIP包:"))
        account_import_layout.addStretch()
        import_account_btn = PrimaryPushButton("导入账户")
        import_account_btn.clicked.connect(self.import_account)
        account_import_layout.addWidget(import_account_btn)
        import_layout.addLayout(account_import_layout)
        
        layout.addLayout(import_layout)
        layout.addStretch()
        
        return widget
    
    def init_default_account(self):
        """初始化默认账户为 'admin'"""
        accounts = self.finance_manager.get_all_accounts()
        
        # 查找 admin 账户（通常应该存在，因为 FinanceManager 会自动创建）
        admin_account = None
        for account in accounts:
            if account.name == "admin":
                admin_account = account
                break
        
        # 设置为当前账户
        if admin_account:
            self.default_account_id = admin_account.id
        elif accounts:
            # 备用方案：如果找不到 admin，使用第一个账户
            self.default_account_id = accounts[0].id
        else:
            # 如果没有任何账户（不应该发生），创建 admin
            admin_account = self.finance_manager.create_account(
                account_name="admin",
                description="默认管理账户"
            )
            self.default_account_id = admin_account.id
        
        self.refresh_records_display()
    
    def refresh_account_list(self):
        """刷新账户列表（已移除，保留兼容性）"""
        pass
    
    def get_current_account_id(self) -> Optional[str]:
        """获取当前账户ID"""
        if hasattr(self, 'default_account_id'):
            return self.default_account_id
        
        # 备用：如果还没初始化，从财务管理器获取第一个账户
        accounts = self.finance_manager.get_all_accounts()
        if accounts:
            return accounts[0].id
        return None
    
    def on_account_changed(self):
        """账户改变时刷新显示（已移除，保留兼容性）"""
        pass
    
    def refresh_records_display(self):
        """刷新记录显示"""
        account_id = self.get_current_account_id()
        if not account_id:
            return
        
        # 重新加载所有账户，从磁盘获取最新数据
        self.finance_manager.load_all_accounts()
        account = self.finance_manager.get_account(account_id)
        if not account:
            return
        
        self.clear_records_table()
        
        for transaction in account.transactions:
            # 创建树形项
            item = QTreeWidgetItem()
            item.setText(0, transaction.date)
            item.setText(1, transaction.trader)
            item.setText(2, transaction.category)
            item.setText(3, f"¥ {transaction.amount:.2f}")
            item.setText(4, transaction.notes or "")
            # 存储交易ID到第一列的 UserRole (Qt.UserRole = 32)
            item.setData(0, 32, transaction.id)
            
            self.records_table.addTopLevelItem(item)
        
        # 更新统计信息
        total_amount = sum(t.amount for t in account.transactions)
        self.total_amount_label.setText(f"¥ {total_amount:.2f}")
        self.record_count_label.setText(str(len(account.transactions)))
    
    def clear_records_table(self):
        """清空记录表格"""
        self.records_table.clear()
        self.total_amount_label.setText("¥ 0.00")
        self.record_count_label.setText("0")
    
    def create_new_account(self):
        """创建新账户（已移除）"""
        pass
    
    def delete_current_account(self):
        """删除当前账户（已移除）"""
        pass
    
    def create_new_record(self):
        """创建新记录"""
        account_id = self.get_current_account_id()
        if not account_id:
            InfoBar.warning(
                title="提示",
                content="请先创建或选择一个账户",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
        
        dialog = CreateTransactionDialog(self, account_id=account_id, finance_manager=self.finance_manager)
        result = dialog.exec_()
        # 无论是否成功，都尝试刷新表格
        if result == QDialog.Accepted:
            # 对话框正常关闭（保存）
            self.refresh_records_display()
            InfoBar.success(
                title="成功",
                content="记录已添加",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        else:
            # 对话框被取消，也刷新以防万一
            self.refresh_records_display()
    
    def edit_record(self, trans_id: str):
        """编辑记录"""
        account_id = self.get_current_account_id()
        if not account_id:
            return
        
        transaction = self.finance_manager.get_transaction(account_id, trans_id)
        if not transaction:
            return
        
        dialog = CreateTransactionDialog(self, transaction=transaction, account_id=account_id, finance_manager=self.finance_manager)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.refresh_records_display()
            InfoBar.success(
                title="成功",
                content="记录已更新",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        else:
            # 对话框被取消，也刷新以防万一
            self.refresh_records_display()
    
    def delete_record(self, trans_id: str):
        """删除记录"""
        account_id = self.get_current_account_id()
        if not account_id:
            return
        
        def on_delete_confirm():
            self.finance_manager.delete_transaction(account_id, trans_id)
            self.refresh_records_display()
            InfoBar.success(
                title="成功",
                content="记录已删除",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        
        dialog = Dialog(
            title="确认删除",
            content="确定要删除这条记录吗?",
            parent=self
        )
        dialog.yesButton.setText("删除")
        dialog.cancelButton.setText("取消")
        dialog.yesButton.clicked.connect(on_delete_confirm)
        dialog.exec()
    
    def view_record(self, trans_id: str):
        """查看记录详情"""
        account_id = self.get_current_account_id()
        if not account_id:
            return
        
        transaction = self.finance_manager.get_transaction(account_id, trans_id)
        if not transaction:
            return
        
        dialog = RecordViewDialog(self, account_id=account_id, transaction=transaction)
        dialog.exec_()
    
    def perform_query(self):
        """执行查询"""
        account_id = self.get_current_account_id()
        if not account_id:
            InfoBar.warning(
                title="提示",
                content="请先创建或选择一个账户",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
        
        # 重新加载最新数据
        self.finance_manager.load_all_accounts()
        
        # 更新分类下拉框（如果分类列表发生变化）
        account = self.finance_manager.get_account(account_id)
        if account:
            # 检查分类是否已经存在于下拉框中
            current_count = self.query_category.count()
            expected_count = len(account.categories) + 1  # +1 是因为有"全部"选项
            
            # 只有在分类数量变化时才重新加载
            if current_count != expected_count:
                current_category = self.query_category.currentText()
                self.query_category.clear()
                self.query_category.addItem("全部")
                for cat in account.categories:
                    self.query_category.addItem(cat)
                # 尽量恢复之前的选择
                index = self.query_category.findText(current_category)
                if index >= 0:
                    self.query_category.setCurrentIndex(index)
                else:
                    self.query_category.setCurrentIndex(0)  # 默认选择"全部"
        
        date_start = self.query_date_start.date().toString("yyyy-MM-dd")
        date_end = self.query_date_end.date().toString("yyyy-MM-dd")
        amount_min = self.query_amount_min.value() if self.query_amount_min.value() > 0 else None
        amount_max = self.query_amount_max.value() if self.query_amount_max.value() < 999999999 else None
        trader = self.query_trader_edit.text().strip() or None
        
        # 分类查询 - 获取当前选择的分类
        category_text = self.query_category.currentText()
        category = None if category_text == "全部" else category_text
        
        results = self.finance_manager.query_transactions(
            account_id,
            date_start=date_start, date_end=date_end,
            amount_min=amount_min, amount_max=amount_max,
            trader=trader, category=category
        )
        
        # 根据交易类型过滤
        transaction_type_index = self.query_transaction_type.currentIndex()
        if transaction_type_index == 1:  # 收入（正数）
            results = [t for t in results if t.amount >= 0]
        elif transaction_type_index == 2:  # 支出（负数）
            results = [t for t in results if t.amount < 0]
        # 如果是 0（全部），不进行过滤
        
        self.query_result_table.clear()
        
        for transaction in results:
            # 创建树形项
            item = QTreeWidgetItem()
            # 第一列添加复选框
            # flags: ItemIsSelectable=1, ItemIsEnabled=2, ItemIsUserCheckable=32
            item.setFlags(item.flags() | 32)  # 32 = Qt.ItemIsUserCheckable
            item.setCheckState(0, 0)  # 0 = Qt.Unchecked
            # 其他列是数据
            item.setText(1, transaction.date)
            item.setText(2, transaction.trader)
            item.setText(3, transaction.category)
            item.setText(4, f"¥ {transaction.amount:.2f}")
            item.setText(5, transaction.notes or "")
            # 存储交易ID（在第一列）
            item.setData(0, 32, transaction.id)
            
            self.query_result_table.addTopLevelItem(item)
        
        InfoBar.success(
            title="查询成功",
            content=f"找到 {len(results)} 条记录",
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def export_account(self):
        """导出账户为ZIP包"""
        account_id = self.get_current_account_id()
        if not account_id:
            InfoBar.warning(
                title="提示",
                content="请先选择一个账户",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
        
        export_dir = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if export_dir:
            if self.finance_manager.export_account_package(account_id, export_dir):
                InfoBar.success(
                    title="成功",
                    content="账户导出成功",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            else:
                InfoBar.error(
                    title="失败",
                    content="导出账户失败",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
    
    def import_account(self):
        """导入账户ZIP包"""
        zip_file, _ = QFileDialog.getOpenFileName(
            self, "选择要导入的账户文件",
            "", "ZIP文件 (*.zip)"
        )
        
        if zip_file:
            account_id = self.finance_manager.import_account_package(zip_file)
            if account_id:
                # 重新初始化默认账户
                self.init_default_account()
                InfoBar.success(
                    title="成功",
                    content="账户导入成功",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            else:
                InfoBar.error(
                    title="失败",
                    content="导入账户失败",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
    
    def export_csv(self):
        """导出为CSV"""
        account_id = self.get_current_account_id()
        if not account_id:
            InfoBar.warning(
                title="提示",
                content="请先选择一个账户",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
        
        account = self.finance_manager.get_account(account_id)
        if not account:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存CSV文件",
            f"{account.name}.csv",
            "CSV文件 (*.csv)"
        )
        
        if file_path:
            if self.finance_manager.export_to_csv(account_id, file_path):
                InfoBar.success(
                    title="成功",
                    content="已导出为CSV",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            else:
                InfoBar.error(
                    title="失败",
                    content="导出CSV失败",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
    
    def backup_all(self):
        """备份所有账户"""
        if self.finance_manager.backup_all_accounts():
            InfoBar.success(
                title="成功",
                content="备份创建成功，已保存到 assets/Finance_Data/backups",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        else:
            InfoBar.error(
                title="失败",
                content="创建备份失败",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def on_record_selection_changed(self):
        """记录表格选择改变时"""
        selected_items = self.records_table.selectedItems()
        has_selection = len(selected_items) > 0
        self.view_record_btn.setEnabled(has_selection)
        self.edit_record_btn.setEnabled(has_selection)
        self.delete_record_btn.setEnabled(has_selection)
    
    def on_query_result_selection_changed(self):
        """查询结果表格选择改变时"""
        selected_items = self.query_result_table.selectedItems()
        has_selection = len(selected_items) > 0
        self.query_view_btn.setEnabled(has_selection)
        self.batch_export_btn.setEnabled(has_selection)
    
    def on_view_record_clicked(self):
        """查看记录按钮点击"""
        current_item = self.records_table.currentItem()
        if current_item:
            trans_id = current_item.data(0, 32)  # Qt.UserRole = 32
            if trans_id:
                self.view_record(trans_id)
    
    def on_edit_record_clicked(self):
        """编辑记录按钮点击"""
        current_item = self.records_table.currentItem()
        if current_item:
            trans_id = current_item.data(0, 32)  # Qt.UserRole = 32
            if trans_id:
                self.edit_record(trans_id)
    
    def on_delete_record_clicked(self):
        """删除记录按钮点击"""
        current_item = self.records_table.currentItem()
        if current_item:
            trans_id = current_item.data(0, 32)  # Qt.UserRole = 32
            if trans_id:
                self.delete_record(trans_id)
    
    def on_batch_export(self):
        """批量导出选中的交易"""
        account_id = self.get_current_account_id()
        if not account_id:
            InfoBar.warning(
                title="提示",
                content="请先选择账户",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        # 获取选中的项目
        selected_items = self.query_result_table.selectedItems()
        if not selected_items:
            InfoBar.warning(
                title="提示",
                content="请先选择要导出的交易",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        # 提取交易 ID（从任何可用的列）
        transaction_ids = set()
        for item in selected_items:
            trans_id = None
            for col in range(6):  # 检查所有列
                trans_id = item.data(col, 32)
                if trans_id:
                    break
            if trans_id:
                transaction_ids.add(trans_id)
        
        if not transaction_ids:
            InfoBar.warning(
                title="提示",
                content="无法获取交易信息",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        # 打开导出方式选择对话框
        export_dialog = BatchExportDialog(self)
        if export_dialog.exec() != QFileDialog.Accepted:
            return
        
        export_type = export_dialog.get_export_type()
        
        # 根据导出方式选择
        if export_type == BatchExportDialog.EXPORT_MROBOT:
            # MRobot 格式导出
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getSaveFileName(
                self,
                "保存为 MRobot 文件",
                str(Path.home() / "Downloads" / "export.mrobot"),
                "MRobot Files (*.mrobot)"
            )
            
            if not file_path:
                return
            
            if self.finance_manager.export_to_mrobot_format(account_id, list(transaction_ids), file_path):
                InfoBar.success(
                    title="导出成功",
                    content=f"已导出 {len(transaction_ids)} 个交易到 {Path(file_path).name}",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            else:
                InfoBar.warning(
                    title="导出失败",
                    content="导出 MRobot 格式文件失败",
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
        else:
            # 普通文件夹导出
            export_dir = QFileDialog.getExistingDirectory(
                self,
                "选择导出文件夹",
                str(Path.home() / "Downloads")
            )
            
            if not export_dir:
                return
            
            export_path = Path(export_dir)
            success_count = 0
            
            # 遍历选中的交易，导出它们的图片
            for trans_id in transaction_ids:
                transaction = self.finance_manager._load_transaction_data(account_id, trans_id)
                if not transaction:
                    continue
                
                # 创建文件夹，命名为 "日期_金额"
                folder_name = f"{transaction.date}_{transaction.amount:.2f}"
                folder_name = folder_name.replace(":", "-")  # 替换不允许的字符
                transaction_folder = export_path / folder_name
                transaction_folder.mkdir(parents=True, exist_ok=True)
                
                # 收集图片文件
                images_found = False
                try:
                    if transaction.invoice_path:
                        img_path = self.finance_manager.get_transaction_image_path(account_id, transaction.invoice_path)
                        if img_path and img_path.exists():
                            shutil.copy(str(img_path), str(transaction_folder / f"发票{img_path.suffix}"))
                            images_found = True
                    
                    if transaction.payment_path:
                        img_path = self.finance_manager.get_transaction_image_path(account_id, transaction.payment_path)
                        if img_path and img_path.exists():
                            shutil.copy(str(img_path), str(transaction_folder / f"支付记录{img_path.suffix}"))
                            images_found = True
                    
                    if transaction.purchase_path:
                        img_path = self.finance_manager.get_transaction_image_path(account_id, transaction.purchase_path)
                        if img_path and img_path.exists():
                            shutil.copy(str(img_path), str(transaction_folder / f"购买记录{img_path.suffix}"))
                            images_found = True
                    
                    if images_found:
                        success_count += 1
                except Exception as e:
                    print(f"导出交易 {trans_id} 失败: {e}")
                    continue
            
            InfoBar.success(
                title="导出完成",
                content=f"成功导出 {success_count} 个交易",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
    
    def on_query_view_clicked(self):
        """查询结果查看详情按钮点击"""
        current_item = self.query_result_table.currentItem()
        if current_item:
            trans_id = current_item.data(0, 32)  # Qt.UserRole = 32
            if trans_id:
                self.view_record(trans_id)
    
    def on_manage_category_clicked(self):
        """分类管理按钮点击"""
        account_id = self.get_current_account_id()
        if not account_id:
            InfoBar.warning(
                title="提示",
                content="请先创建或选择一个账户",
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
        
        # 打开分类管理对话框
        dialog = CategoryManagementDialog(self, self.finance_manager, account_id)
        if dialog.exec():
            # 刷新查询页面的分类下拉框
            self.refresh_query_category_dropdown()
    
    def refresh_query_category_dropdown(self):
        """刷新查询页面的分类下拉框"""
        account_id = self.get_current_account_id()
        if not account_id or not hasattr(self, 'query_category'):
            return
        
        current_text = self.query_category.currentText()
        self.query_category.clear()
        self.query_category.addItem("全部")
        
        categories = self.finance_manager.get_categories(account_id)
        for category in categories:
            self.query_category.addItem(category)
        
        # 恢复之前的选择
        index = self.query_category.findText(current_text)
        if index >= 0:
            self.query_category.setCurrentIndex(index)
