"""
财务做账模块 - 数据管理系统
管理所有财务账目、图片、文件等数据的存储和检索
"""

import os
import json
import shutil
import zipfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
from enum import Enum


class TransactionType(Enum):
    """交易类型"""
    INVOICE = "invoice"  # 发票
    PAYMENT = "payment"  # 支付记录
    PURCHASE = "purchase"  # 购买记录


class Transaction:
    """单个交易记录数据模型"""
    
    def __init__(self, trans_id: Optional[str] = None, date: Optional[str] = None, amount: float = 0.0,
                 trader: str = "", notes: str = "", invoice_path: Optional[str] = None,
                 payment_path: Optional[str] = None, purchase_path: Optional[str] = None):
        self.id = trans_id or str(uuid.uuid4())
        self.date = date or datetime.now().strftime("%Y-%m-%d")
        self.amount = amount
        self.trader = trader
        self.notes = notes
        self.invoice_path = invoice_path  # 相对路径
        self.payment_path = payment_path
        self.purchase_path = purchase_path
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """转换为字典格式（用于JSON序列化）"""
        return {
            'id': self.id,
            'date': self.date,
            'amount': self.amount,
            'trader': self.trader,
            'notes': self.notes,
            'invoice_path': self.invoice_path,
            'payment_path': self.payment_path,
            'purchase_path': self.purchase_path,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Transaction':
        """从字典创建Transaction对象"""
        trans = cls(
            trans_id=data.get('id'),
            date=data.get('date'),
            amount=data.get('amount', 0.0),
            trader=data.get('trader', ''),
            notes=data.get('notes', ''),
            invoice_path=data.get('invoice_path'),
            payment_path=data.get('payment_path'),
            purchase_path=data.get('purchase_path')
        )
        if 'created_at' in data:
            trans.created_at = data['created_at']
        if 'updated_at' in data:
            trans.updated_at = data['updated_at']
        return trans


class Account:
    """账户数据模型"""
    
    def __init__(self, account_id: Optional[str] = None, account_name: str = "", description: str = ""):
        self.id = account_id or str(uuid.uuid4())
        self.name = account_name
        self.description = description
        self.transactions: List[Transaction] = []
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def add_transaction(self, transaction: Transaction) -> None:
        """添加交易记录"""
        self.transactions.append(transaction)
        self.updated_at = datetime.now().isoformat()
    
    def remove_transaction(self, trans_id: str) -> bool:
        """移除交易记录"""
        original_len = len(self.transactions)
        self.transactions = [t for t in self.transactions if t.id != trans_id]
        if len(self.transactions) < original_len:
            self.updated_at = datetime.now().isoformat()
            return True
        return False
    
    def get_transaction(self, trans_id: str) -> Optional[Transaction]:
        """获取单个交易记录"""
        for t in self.transactions:
            if t.id == trans_id:
                return t
        return None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'transactions': [t.to_dict() for t in self.transactions],
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Account':
        """从字典创建Account对象"""
        account = cls(
            account_id=data.get('id'),
            account_name=data.get('name', ''),
            description=data.get('description', '')
        )
        account.transactions = [Transaction.from_dict(t) for t in data.get('transactions', [])]
        if 'created_at' in data:
            account.created_at = data['created_at']
        if 'updated_at' in data:
            account.updated_at = data['updated_at']
        return account


class FinanceManager:
    """财务管理系统 - 处理所有数据操作和文件管理"""
    
    def __init__(self, data_root: Optional[str] = None):
        """初始化财务管理系统
        
        Args:
            data_root: 数据存储根目录，默认为 assets/Finance_Data
        """
        if data_root:
            self.data_root = Path(data_root)
        else:
            # 获取项目根目录
            import os
            current_dir = Path(os.getcwd())
            self.data_root = current_dir / "assets" / "Finance_Data"
        
        self._ensure_directory_structure()
        self.accounts: Dict[str, Account] = {}
        self.load_all_accounts()
    
    def _ensure_directory_structure(self) -> None:
        """确保目录结构完整"""
        self.data_root.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        subdirs = ['accounts', 'backups', 'images', 'invoices', 'payments', 'purchases']
        for subdir in subdirs:
            (self.data_root / subdir).mkdir(exist_ok=True)
    
    def _get_account_dir(self, account_id: str) -> Path:
        """获取账户目录"""
        account_dir = self.data_root / 'accounts' / account_id
        account_dir.mkdir(parents=True, exist_ok=True)
        return account_dir
    
    def _get_transaction_dir(self, account_id: str, trans_id: str) -> Path:
        """获取交易记录目录"""
        trans_dir = self._get_account_dir(account_id) / trans_id
        trans_dir.mkdir(parents=True, exist_ok=True)
        return trans_dir
    
    def _save_account_metadata(self, account: Account) -> None:
        """保存账户元数据（不包含交易详情）"""
        account_dir = self._get_account_dir(account.id)
        metadata_file = account_dir / 'metadata.json'
        
        metadata = {
            'id': account.id,
            'name': account.name,
            'description': account.description,
            'created_at': account.created_at,
            'updated_at': account.updated_at
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def _load_account_metadata(self, account_id: str) -> Optional[dict]:
        """加载账户元数据"""
        metadata_file = self._get_account_dir(account_id) / 'metadata.json'
        if not metadata_file.exists():
            return None
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_transaction_data(self, account_id: str, transaction: Transaction) -> None:
        """保存交易记录数据"""
        trans_dir = self._get_transaction_dir(account_id, transaction.id)
        data_file = trans_dir / 'data.json'
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(transaction.to_dict(), f, ensure_ascii=False, indent=2)
    
    def _load_transaction_data(self, account_id: str, trans_id: str) -> Optional[Transaction]:
        """加载交易记录数据"""
        data_file = self._get_transaction_dir(account_id, trans_id) / 'data.json'
        if not data_file.exists():
            return None
        
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return Transaction.from_dict(data)
    
    def create_account(self, account_name: str, description: str = "") -> Account:
        """创建新账户"""
        account = Account(account_name=account_name, description=description)
        self.accounts[account.id] = account
        self._save_account_metadata(account)
        return account
    
    def get_account(self, account_id: str) -> Optional[Account]:
        """获取账户"""
        return self.accounts.get(account_id)
    
    def get_all_accounts(self) -> List[Account]:
        """获取所有账户"""
        return list(self.accounts.values())
    
    def delete_account(self, account_id: str) -> bool:
        """删除账户及其所有数据"""
        if account_id not in self.accounts:
            return False
        
        account_dir = self._get_account_dir(account_id)
        try:
            shutil.rmtree(account_dir)
            del self.accounts[account_id]
            return True
        except Exception as e:
            print(f"删除账户出错: {e}")
            return False
    
    def update_account(self, account_id: str, account_name: Optional[str] = None, description: Optional[str] = None) -> bool:
        """更新账户信息"""
        account = self.accounts.get(account_id)
        if not account:
            return False
        
        if account_name:
            account.name = account_name
        if description is not None:
            account.description = description
        
        account.updated_at = datetime.now().isoformat()
        self._save_account_metadata(account)
        return True
    
    def add_transaction(self, account_id: str, transaction: Transaction) -> bool:
        """添加交易记录到账户"""
        account = self.accounts.get(account_id)
        if not account:
            return False
        
        account.add_transaction(transaction)
        self._save_transaction_data(account_id, transaction)
        return True
    
    def save_image_for_transaction(self, account_id: str, trans_id: str, 
                                   image_type: TransactionType, image_path: str) -> Optional[str]:
        """保存交易相关的图片，返回相对路径"""
        trans_dir = self._get_transaction_dir(account_id, trans_id)
        
        source_path = Path(image_path)
        if not source_path.exists():
            return None
        
        # 保存图片到对应的图片目录
        dest_dir = trans_dir / image_type.value
        dest_dir.mkdir(exist_ok=True)
        
        dest_path = dest_dir / source_path.name
        shutil.copy2(source_path, dest_path)
        
        # 返回相对于data_root的路径
        relative_path = str(dest_path.relative_to(self.data_root))
        return relative_path
    
    def get_transaction_image_path(self, account_id: str, relative_path: str) -> Optional[Path]:
        """获取交易图片的完整路径"""
        if not relative_path:
            return None
        return self.data_root / relative_path
    
    def delete_transaction(self, account_id: str, trans_id: str) -> bool:
        """删除交易记录"""
        account = self.accounts.get(account_id)
        if not account:
            return False
        
        # 删除磁盘上的文件
        trans_dir = self._get_transaction_dir(account_id, trans_id)
        try:
            shutil.rmtree(trans_dir)
        except Exception as e:
            print(f"删除交易记录文件出错: {e}")
        
        # 从账户中移除
        return account.remove_transaction(trans_id)
    
    def update_transaction(self, account_id: str, trans_id: str, **kwargs) -> bool:
        """更新交易记录"""
        account = self.accounts.get(account_id)
        if not account:
            return False
        
        transaction = account.get_transaction(trans_id)
        if not transaction:
            return False
        
        # 更新允许的字段
        allowed_fields = ['date', 'amount', 'trader', 'notes', 'invoice_path', 
                         'payment_path', 'purchase_path']
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(transaction, field, value)
        
        transaction.updated_at = datetime.now().isoformat()
        self._save_transaction_data(account_id, transaction)
        return True
    
    def get_transaction(self, account_id: str, trans_id: str) -> Optional[Transaction]:
        """获取单个交易记录"""
        account = self.accounts.get(account_id)
        if not account:
            return None
        return account.get_transaction(trans_id)
    
    def query_transactions(self, account_id: str, date_start: Optional[str] = None, 
                          date_end: Optional[str] = None, amount_min: Optional[float] = None,
                          amount_max: Optional[float] = None, trader: Optional[str] = None) -> List[Transaction]:
        """查询交易记录（支持多条件筛选）"""
        account = self.accounts.get(account_id)
        if not account:
            return []
        
        results = []
        for trans in account.transactions:
            # 日期范围筛选
            if date_start and trans.date < date_start:
                continue
            if date_end and trans.date > date_end:
                continue
            
            # 金额范围筛选
            if amount_min is not None and trans.amount < amount_min:
                continue
            if amount_max is not None and trans.amount > amount_max:
                continue
            
            # 交易人筛选（模糊匹配）
            if trader and trader.lower() not in trans.trader.lower():
                continue
            
            results.append(trans)
        
        # 按日期排序
        results.sort(key=lambda x: x.date, reverse=True)
        return results
    
    def get_account_summary(self, account_id: str) -> Optional[dict]:
        """获取账户汇总信息"""
        account = self.accounts.get(account_id)
        if not account:
            return None
        
        total_amount = sum(t.amount for t in account.transactions)
        transaction_count = len(account.transactions)
        
        return {
            'account_id': account_id,
            'account_name': account.name,
            'total_amount': total_amount,
            'transaction_count': transaction_count,
            'created_at': account.created_at,
            'updated_at': account.updated_at
        }
    
    def export_account_package(self, account_id: str, export_path: str) -> bool:
        """导出账户为可转移的压缩包"""
        account_dir = self._get_account_dir(account_id)
        if not account_dir.exists():
            return False
        
        try:
            export_file = Path(export_path) / f"{self.accounts[account_id].name}_{account_id}.zip"
            
            with zipfile.ZipFile(export_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(account_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(account_dir)
                        zipf.write(file_path, arcname)
            
            return True
        except Exception as e:
            print(f"导出账户出错: {e}")
            return False
    
    def import_account_package(self, zip_path: str) -> Optional[str]:
        """导入账户压缩包，返回导入的账户ID"""
        try:
            zip_path = Path(zip_path)
            if not zip_path.exists():
                return None
            
            # 先加载元数据以获取账户ID
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                metadata_content = zipf.read('metadata.json')
                metadata = json.loads(metadata_content)
                account_id = metadata['id']
            
            # 如果账户已存在，创建新ID
            if account_id in self.accounts:
                account_id = str(uuid.uuid4())
                # 更新元数据中的ID
                metadata['id'] = account_id
            
            # 解压到临时目录
            temp_dir = self.data_root / f"_temp_{uuid.uuid4()}"
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # 更新临时目录中的元数据文件
            metadata_file = temp_dir / 'metadata.json'
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # 移动到正式目录
            account_dir = self._get_account_dir(account_id)
            if account_dir.exists():
                shutil.rmtree(account_dir)
            
            shutil.move(str(temp_dir), str(account_dir))
            
            # 重新加载账户
            self.load_all_accounts()
            return account_id
        except Exception as e:
            print(f"导入账户出错: {e}")
            return None
    
    def backup_all_accounts(self) -> bool:
        """备份所有账户"""
        try:
            backup_dir = self.data_root / 'backups'
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"backup_{timestamp}.zip"
            
            accounts_dir = self.data_root / 'accounts'
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(accounts_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(self.data_root / 'accounts')
                        zipf.write(file_path, arcname)
            
            return True
        except Exception as e:
            print(f"备份账户出错: {e}")
            return False
    
    def load_all_accounts(self) -> None:
        """加载所有账户"""
        self.accounts.clear()
        accounts_dir = self.data_root / 'accounts'
        
        if not accounts_dir.exists():
            return
        
        for account_dir in accounts_dir.iterdir():
            if not account_dir.is_dir():
                continue
            
            metadata = self._load_account_metadata(account_dir.name)
            if not metadata:
                continue
            
            account = Account(
                account_id=metadata['id'],
                account_name=metadata['name'],
                description=metadata.get('description', '')
            )
            account.created_at = metadata.get('created_at')
            account.updated_at = metadata.get('updated_at')
            
            # 加载该账户的所有交易记录
            trans_dirs = [d for d in account_dir.iterdir() 
                         if d.is_dir() and d.name not in ['invoice', 'payment', 'purchase']]
            
            for trans_dir in trans_dirs:
                transaction = self._load_transaction_data(account_dir.name, trans_dir.name)
                if transaction:
                    account.transactions.append(transaction)
            
            # 按日期排序
            account.transactions.sort(key=lambda x: x.date, reverse=True)
            
            self.accounts[account.id] = account
    
    def export_to_csv(self, account_id: str, csv_path: str) -> bool:
        """导出账户数据为CSV格式"""
        account = self.accounts.get(account_id)
        if not account:
            return False
        
        try:
            import csv
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['日期', '金额', '交易人', '备注', '创建时间'])
                
                for trans in account.transactions:
                    writer.writerow([
                        trans.date,
                        trans.amount,
                        trans.trader,
                        trans.notes,
                        trans.created_at
                    ])
            
            return True
        except Exception as e:
            print(f"导出CSV出错: {e}")
            return False
