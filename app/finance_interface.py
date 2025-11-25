"""
财务做账应用主界面
包含做账、查询、导出三个功能标签页
"""

from typing import Optional
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QStackedLayout, 
                             QLabel, QLineEdit, QDateEdit, QSpinBox, QDoubleSpinBox,
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                             QFileDialog, QMessageBox, QScrollArea, QTabWidget, QFrame,
                             QComboBox, QCheckBox, QInputDialog, QDialog, QTextEdit)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QMimeData, QRect, QSize
from PyQt5.QtGui import QIcon, QPixmap, QDrag, QFont, QColor
from PyQt5.QtCore import Qt as QtEnum
from PyQt5.QtWidgets import QApplication, QListWidget, QListWidgetItem
from qfluentwidgets import (TitleLabel, BodyLabel, SubtitleLabel, StrongBodyLabel, 
                           HorizontalSeparator, CardWidget, PushButton, LineEdit, 
                           SpinBox, CheckBox, TextEdit, PrimaryPushButton, 
                           InfoBar, InfoBarPosition, FluentIcon as FIF, ComboBox,
                           DoubleSpinBox, DateEdit, SearchLineEdit, StateToolTip)
from pathlib import Path
from datetime import datetime, timedelta
import json
import os

from .tools.finance_manager import FinanceManager, TransactionType, Transaction, Account


class CreateTransactionDialog(QDialog):
    """创建/编辑交易记录对话框"""
    
    def __init__(self, parent=None, transaction: Optional[Transaction] = None, account_id: Optional[str] = None):
        super().__init__(parent)
        self.transaction = transaction
        self.account_id = account_id
        self.finance_manager = FinanceManager()
        
        self.setWindowTitle("新建交易记录" if not transaction else "编辑交易记录")
        self.setGeometry(100, 100, 600, 500)
        self.init_ui()
        
        if transaction:
            self.load_transaction_data(transaction)
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 日期
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("日期:"))
        self.date_edit = DateEdit()
        self.date_edit.setDate(QDate.currentDate())
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()
        layout.addLayout(date_layout)
        
        # 金额
        amount_layout = QHBoxLayout()
        amount_layout.addWidget(QLabel("金额 (元):"))
        self.amount_spin = DoubleSpinBox()
        self.amount_spin.setRange(0, 999999999)
        self.amount_spin.setDecimals(2)
        amount_layout.addWidget(self.amount_spin)
        amount_layout.addStretch()
        layout.addLayout(amount_layout)
        
        # 交易人
        trader_layout = QHBoxLayout()
        trader_layout.addWidget(QLabel("交易人:"))
        self.trader_edit = LineEdit()
        trader_layout.addWidget(self.trader_edit)
        layout.addLayout(trader_layout)
        
        # 备注
        notes_layout = QHBoxLayout()
        notes_layout.addWidget(QLabel("备注:"))
        self.notes_edit = TextEdit()
        self.notes_edit.setMaximumHeight(80)
        notes_layout.addWidget(self.notes_edit)
        layout.addLayout(notes_layout)
        
        # 图片部分
        layout.addWidget(HorizontalSeparator())
        layout.addWidget(SubtitleLabel("相关文件 (可选)"))
        
        # 发票
        invoice_layout = QHBoxLayout()
        invoice_layout.addWidget(QLabel("发票图片:"))
        self.invoice_label = QLabel("未选择")
        invoice_layout.addWidget(self.invoice_label)
        invoice_btn = PushButton("选择")
        invoice_btn.clicked.connect(lambda: self.select_image("invoice"))
        invoice_layout.addWidget(invoice_btn)
        layout.addLayout(invoice_layout)
        
        # 支付记录
        payment_layout = QHBoxLayout()
        payment_layout.addWidget(QLabel("支付记录:"))
        self.payment_label = QLabel("未选择")
        payment_layout.addWidget(self.payment_label)
        payment_btn = PushButton("选择")
        payment_btn.clicked.connect(lambda: self.select_image("payment"))
        payment_layout.addWidget(payment_btn)
        layout.addLayout(payment_layout)
        
        # 购买记录
        purchase_layout = QHBoxLayout()
        purchase_layout.addWidget(QLabel("购买记录:"))
        self.purchase_label = QLabel("未选择")
        purchase_layout.addWidget(self.purchase_label)
        purchase_btn = PushButton("选择")
        purchase_btn.clicked.connect(lambda: self.select_image("purchase"))
        purchase_layout.addWidget(purchase_btn)
        layout.addLayout(purchase_layout)
        
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = PushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = PrimaryPushButton("保存")
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
        self.date_edit.setDate(QDate.fromString(transaction.date, "yyyy-MM-dd"))
        self.amount_spin.setValue(transaction.amount)
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
            QMessageBox.warning(self, "错误", "账户ID未设置")
            return
        
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        amount = self.amount_spin.value()
        trader = self.trader_edit.text().strip()
        notes = self.notes_edit.toPlainText().strip()
        
        if not trader:
            QMessageBox.warning(self, "验证错误", "请输入交易人")
            return
        
        if amount <= 0:
            QMessageBox.warning(self, "验证错误", "金额必须大于0")
            return
        
        if self.transaction:
            # 编辑现有交易记录
            trans_id = self.transaction.id
            self.finance_manager.update_transaction(
                self.account_id, trans_id,
                date=date_str, amount=amount,
                trader=trader, notes=notes
            )
        else:
            # 创建新交易记录
            transaction = Transaction(
                date=date_str, amount=amount,
                trader=trader, notes=notes
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
        self.setGeometry(100, 100, 700, 600)
        self.init_ui()
        
        if transaction:
            self.load_transaction_data()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 基本信息
        info_layout = QVBoxLayout()
        
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("日期:"))
        self.date_label = QLabel()
        date_layout.addWidget(self.date_label)
        date_layout.addStretch()
        info_layout.addLayout(date_layout)
        
        amount_layout = QHBoxLayout()
        amount_layout.addWidget(QLabel("金额:"))
        self.amount_label = QLabel()
        amount_layout.addWidget(self.amount_label)
        amount_layout.addStretch()
        info_layout.addLayout(amount_layout)
        
        trader_layout = QHBoxLayout()
        trader_layout.addWidget(QLabel("交易人:"))
        self.trader_label = QLabel()
        trader_layout.addWidget(self.trader_label)
        trader_layout.addStretch()
        info_layout.addLayout(trader_layout)
        
        notes_layout = QHBoxLayout()
        notes_layout.addWidget(QLabel("备注:"))
        self.notes_label = QLabel()
        self.notes_label.setWordWrap(True)
        notes_layout.addWidget(self.notes_label)
        info_layout.addLayout(notes_layout)
        
        layout.addLayout(info_layout)
        layout.addWidget(HorizontalSeparator())
        
        # 图片预览
        layout.addWidget(SubtitleLabel("相关文件预览"))
        
        preview_layout = QHBoxLayout()
        
        # 发票
        invoice_layout = QVBoxLayout()
        invoice_layout.addWidget(QLabel("发票:"))
        self.invoice_preview = QLabel("无")
        self.invoice_preview.setMinimumSize(150, 150)
        self.invoice_preview.setAlignment(Qt.AlignCenter)
        self.invoice_preview.setStyleSheet("border: 1px solid #ddd;")
        invoice_layout.addWidget(self.invoice_preview)
        preview_layout.addLayout(invoice_layout)
        
        # 支付记录
        payment_layout = QVBoxLayout()
        payment_layout.addWidget(QLabel("支付记录:"))
        self.payment_preview = QLabel("无")
        self.payment_preview.setMinimumSize(150, 150)
        self.payment_preview.setAlignment(Qt.AlignCenter)
        self.payment_preview.setStyleSheet("border: 1px solid #ddd;")
        payment_layout.addWidget(self.payment_preview)
        preview_layout.addLayout(payment_layout)
        
        # 购买记录
        purchase_layout = QVBoxLayout()
        purchase_layout.addWidget(QLabel("购买记录:"))
        self.purchase_preview = QLabel("无")
        self.purchase_preview.setMinimumSize(150, 150)
        self.purchase_preview.setAlignment(Qt.AlignCenter)
        self.purchase_preview.setStyleSheet("border: 1px solid #ddd;")
        purchase_layout.addWidget(self.purchase_preview)
        preview_layout.addLayout(purchase_layout)
        
        layout.addLayout(preview_layout)
        layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
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
    
    def _load_image_preview(self, image_type: str, relative_path: Optional[str], label: QLabel):
        """加载并显示图片预览"""
        if not relative_path:
            return
        
        full_path = self.finance_manager.get_transaction_image_path(self.account_id or "", relative_path)
        if full_path and full_path.exists():
            pixmap = QPixmap(str(full_path))
            scaled_pixmap = pixmap.scaledToWidth(150)
            label.setPixmap(scaled_pixmap)


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
        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabBar::tab {
                padding: 8px 20px;
            }
        """)
        
        # 做账标签页
        self.bookkeeping_tab = self.create_bookkeeping_tab()
        self.tab_widget.addTab(self.bookkeeping_tab, "做账")
        
        # 查询标签页
        self.query_tab = self.create_query_tab()
        self.tab_widget.addTab(self.query_tab, "查询")
        
        # 导出标签页
        self.export_tab = self.create_export_tab()
        self.tab_widget.addTab(self.export_tab, "导出")
        
        self.layout_main.addWidget(self.tab_widget)
        
        # 初始化时获取默认账户
        self.init_default_account()
    
    def create_bookkeeping_tab(self) -> QWidget:
        """创建做账标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题和操作按钮
        title_layout = QHBoxLayout()
        title_layout.addWidget(SubtitleLabel("交易记录"))
        title_layout.addStretch()
        
        new_record_btn = PrimaryPushButton("新建记录")
        new_record_btn.clicked.connect(self.create_new_record)
        title_layout.addWidget(new_record_btn)
        
        layout.addLayout(title_layout)
        
        # 记录表格
        self.records_table = QTableWidget()
        self.records_table.setColumnCount(6)
        self.records_table.setHorizontalHeaderLabels(["日期", "交易人", "金额 (元)", "备注", "操作", ""])
        header = self.records_table.horizontalHeader()
        if header:
            header.setStretchLastSection(False)
        self.records_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.records_table.setAlternatingRowColors(True)
        self.records_table.setMaximumHeight(600)
        
        layout.addWidget(self.records_table)
        
        # 统计信息
        stats_layout = QHBoxLayout()
        stats_layout.addWidget(QLabel("总额:"))
        self.total_amount_label = QLabel("¥ 0.00")
        self.total_amount_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #d32f2f;")
        stats_layout.addWidget(self.total_amount_label)
        
        stats_layout.addSpacing(30)
        stats_layout.addWidget(QLabel("记录数:"))
        self.record_count_label = QLabel("0")
        self.record_count_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        stats_layout.addWidget(self.record_count_label)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        return widget
    
    def create_query_tab(self) -> QWidget:
        """创建查询标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 搜索过滤区
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("日期范围:"))
        self.query_date_start = DateEdit()
        self.query_date_start.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.query_date_start)
        
        filter_layout.addWidget(QLabel("至"))
        self.query_date_end = DateEdit()
        self.query_date_end.setDate(QDate.currentDate())
        filter_layout.addWidget(self.query_date_end)
        
        filter_layout.addSpacing(20)
        filter_layout.addWidget(QLabel("金额范围:"))
        self.query_amount_min = DoubleSpinBox()
        self.query_amount_min.setRange(0, 999999999)
        self.query_amount_min.setPrefix("¥ ")
        filter_layout.addWidget(self.query_amount_min)
        
        filter_layout.addWidget(QLabel("至"))
        self.query_amount_max = DoubleSpinBox()
        self.query_amount_max.setRange(0, 999999999)
        self.query_amount_max.setValue(999999999)
        self.query_amount_max.setPrefix("¥ ")
        filter_layout.addWidget(self.query_amount_max)
        
        layout.addLayout(filter_layout)
        
        # 交易人搜索
        trader_layout = QHBoxLayout()
        trader_layout.addWidget(QLabel("交易人:"))
        self.query_trader_edit = SearchLineEdit()
        self.query_trader_edit.setPlaceholderText("输入交易人名称...")
        trader_layout.addWidget(self.query_trader_edit)
        
        query_btn = PrimaryPushButton("查询")
        query_btn.clicked.connect(self.perform_query)
        trader_layout.addWidget(query_btn)
        
        layout.addLayout(trader_layout)
        layout.addWidget(HorizontalSeparator())
        
        # 查询结果表格
        self.query_result_table = QTableWidget()
        self.query_result_table.setColumnCount(6)
        self.query_result_table.setHorizontalHeaderLabels(["日期", "交易人", "金额 (元)", "备注", "查看详情", ""])
        header = self.query_result_table.horizontalHeader()
        if header:
            header.setStretchLastSection(False)
        self.query_result_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.query_result_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.query_result_table)
        
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
        account_export_layout.addWidget(QLabel("导出当前账户:"))
        account_export_layout.addStretch()
        export_account_btn = PrimaryPushButton("导出为ZIP包")
        export_account_btn.clicked.connect(self.export_account)
        account_export_layout.addWidget(export_account_btn)
        export_layout.addLayout(account_export_layout)
        
        # 导出为CSV
        csv_export_layout = QHBoxLayout()
        csv_export_layout.addWidget(QLabel("导出为Excel格式:"))
        csv_export_layout.addStretch()
        export_csv_btn = PrimaryPushButton("导出CSV")
        export_csv_btn.clicked.connect(self.export_csv)
        csv_export_layout.addWidget(export_csv_btn)
        export_layout.addLayout(csv_export_layout)
        
        # 备份所有账户
        backup_layout = QHBoxLayout()
        backup_layout.addWidget(QLabel("备份所有账户:"))
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
        account_import_layout.addWidget(QLabel("导入账户ZIP包:"))
        account_import_layout.addStretch()
        import_account_btn = PrimaryPushButton("导入账户")
        import_account_btn.clicked.connect(self.import_account)
        account_import_layout.addWidget(import_account_btn)
        import_layout.addLayout(account_import_layout)
        
        layout.addLayout(import_layout)
        layout.addStretch()
        
        return widget
    
    def init_default_account(self):
        """初始化默认账户"""
        accounts = self.finance_manager.get_all_accounts()
        if accounts:
            self.default_account_id = accounts[0].id
            self.refresh_records_display()
        else:
            self.default_account_id = None
            self.clear_records_table()
    
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
        
        account = self.finance_manager.get_account(account_id)
        if not account:
            return
        
        self.clear_records_table()
        
        for transaction in account.transactions:
            row = self.records_table.rowCount()
            self.records_table.insertRow(row)
            
            self.records_table.setItem(row, 0, QTableWidgetItem(transaction.date))
            self.records_table.setItem(row, 1, QTableWidgetItem(transaction.trader))
            self.records_table.setItem(row, 2, QTableWidgetItem(f"¥ {transaction.amount:.2f}"))
            self.records_table.setItem(row, 3, QTableWidgetItem(transaction.notes or ""))
            
            # 操作按钮
            btn_layout = QHBoxLayout()
            edit_btn = PushButton("编辑")
            edit_btn.clicked.connect(lambda checked, tid=transaction.id: self.edit_record(tid))
            btn_layout.addWidget(edit_btn)
            
            delete_btn = PushButton("删除")
            delete_btn.clicked.connect(lambda checked, tid=transaction.id: self.delete_record(tid))
            btn_layout.addWidget(delete_btn)
            
            view_btn = PushButton("查看")
            view_btn.clicked.connect(lambda checked, tid=transaction.id: self.view_record(tid))
            btn_layout.addWidget(view_btn)
            
            btn_widget = QWidget()
            btn_widget.setLayout(btn_layout)
            self.records_table.setCellWidget(row, 4, btn_widget)
        
        # 更新统计信息
        total_amount = sum(t.amount for t in account.transactions)
        self.total_amount_label.setText(f"¥ {total_amount:.2f}")
        self.record_count_label.setText(str(len(account.transactions)))
    
    def clear_records_table(self):
        """清空记录表格"""
        self.records_table.setRowCount(0)
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
            QMessageBox.warning(self, "错误", "请先创建或选择一个账户")
            return
        
        dialog = CreateTransactionDialog(self, account_id=account_id)
        if dialog.exec_():
            self.refresh_records_display()
            InfoBar.success("记录已添加", "", duration=2000, parent=self)
    
    def edit_record(self, trans_id: str):
        """编辑记录"""
        account_id = self.get_current_account_id()
        if not account_id:
            return
        
        transaction = self.finance_manager.get_transaction(account_id, trans_id)
        if not transaction:
            return
        
        dialog = CreateTransactionDialog(self, transaction=transaction, account_id=account_id)
        if dialog.exec_():
            self.refresh_records_display()
            InfoBar.success("记录已更新", "", duration=2000, parent=self)
    
    def delete_record(self, trans_id: str):
        """删除记录"""
        account_id = self.get_current_account_id()
        if not account_id:
            return
        
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除这条记录吗?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.finance_manager.delete_transaction(account_id, trans_id)
            self.refresh_records_display()
            InfoBar.success("记录已删除", "", duration=2000, parent=self)
    
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
            QMessageBox.warning(self, "错误", "请先创建或选择一个账户")
            return
        
        date_start = self.query_date_start.date().toString("yyyy-MM-dd")
        date_end = self.query_date_end.date().toString("yyyy-MM-dd")
        amount_min = self.query_amount_min.value() if self.query_amount_min.value() > 0 else None
        amount_max = self.query_amount_max.value() if self.query_amount_max.value() < 999999999 else None
        trader = self.query_trader_edit.text().strip() or None
        
        results = self.finance_manager.query_transactions(
            account_id,
            date_start=date_start, date_end=date_end,
            amount_min=amount_min, amount_max=amount_max,
            trader=trader
        )
        
        self.query_result_table.setRowCount(0)
        
        for transaction in results:
            row = self.query_result_table.rowCount()
            self.query_result_table.insertRow(row)
            
            self.query_result_table.setItem(row, 0, QTableWidgetItem(transaction.date))
            self.query_result_table.setItem(row, 1, QTableWidgetItem(transaction.trader))
            self.query_result_table.setItem(row, 2, QTableWidgetItem(f"¥ {transaction.amount:.2f}"))
            self.query_result_table.setItem(row, 3, QTableWidgetItem(transaction.notes or ""))
            
            view_btn = PushButton("查看详情")
            view_btn.clicked.connect(lambda checked, tid=transaction.id: self.view_record(tid))
            self.query_result_table.setCellWidget(row, 4, view_btn)
        
        InfoBar.success(f"找到 {len(results)} 条记录", "", duration=2000, parent=self)
    
    def export_account(self):
        """导出账户为ZIP包"""
        account_id = self.get_current_account_id()
        if not account_id:
            QMessageBox.warning(self, "错误", "请先选择一个账户")
            return
        
        export_dir = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if export_dir:
            if self.finance_manager.export_account_package(account_id, export_dir):
                InfoBar.success("账户导出成功", "", duration=2000, parent=self)
            else:
                QMessageBox.warning(self, "错误", "导出账户失败")
    
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
                InfoBar.success("账户导入成功", "", duration=2000, parent=self)
            else:
                QMessageBox.warning(self, "错误", "导入账户失败")
    
    def export_csv(self):
        """导出为CSV"""
        account_id = self.get_current_account_id()
        if not account_id:
            QMessageBox.warning(self, "错误", "请先选择一个账户")
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
                InfoBar.success("已导出为CSV", "", duration=2000, parent=self)
            else:
                QMessageBox.warning(self, "错误", "导出CSV失败")
    
    def backup_all(self):
        """备份所有账户"""
        if self.finance_manager.backup_all_accounts():
            InfoBar.success("备份创建成功", "已保存到 assets/Finance_Data/backups", duration=3000, parent=self)
        else:
            QMessageBox.warning(self, "错误", "创建备份失败")
