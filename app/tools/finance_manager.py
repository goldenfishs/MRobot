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
                 payment_path: Optional[str] = None, purchase_path: Optional[str] = None,
                 category: str = ""):
        self.id = trans_id or str(uuid.uuid4())
        self.date = date or datetime.now().strftime("%Y-%m-%d")
        self.amount = amount
        self.trader = trader
        self.notes = notes
        self.invoice_path = invoice_path  # 相对路径
        self.payment_path = payment_path
        self.purchase_path = purchase_path
        self.category = category  # 交易分类，用户自定义
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
            'category': self.category,
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
            purchase_path=data.get('purchase_path'),
            category=data.get('category', '')
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
        self.categories: List[str] = []  # 空列表，用户自定义分类
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
            'categories': self.categories,
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
        account.categories = data.get('categories', [])  # 使用存储的分类，如果没有则为空列表
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
        
        # 如果没有账户，自动创建 admin 账户
        if len(self.accounts) == 0:
            self.create_account(
                account_name="admin",
                description="默认管理账户"
            )
    
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
            'categories': account.categories,
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
                         'payment_path', 'purchase_path', 'category']
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
                          amount_max: Optional[float] = None, trader: Optional[str] = None,
                          category: Optional[str] = None) -> List[Transaction]:
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
            
            # 分类筛选
            if category and trans.category != category:
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
            account.categories = metadata.get('categories', [])  # 从元数据加载分类
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
                writer.writerow(['日期', '金额', '交易人', '分类', '备注', '创建时间'])
                
                for trans in account.transactions:
                    writer.writerow([
                        trans.date,
                        trans.amount,
                        trans.trader,
                        trans.category,
                        trans.notes,
                        trans.created_at
                    ])
            
            return True
        except Exception as e:
            print(f"导出CSV出错: {e}")
            return False
    
    def add_category(self, account_id: str, category: str) -> bool:
        """添加交易分类"""
        account = self.accounts.get(account_id)
        if not account:
            return False
        
        if category not in account.categories:
            account.categories.append(category)
            account.updated_at = datetime.now().isoformat()
            self._save_account_metadata(account)
            return True
        return False
    
    def rename_category(self, account_id: str, old_name: str, new_name: str) -> bool:
        """重命名交易分类"""
        account = self.accounts.get(account_id)
        if not account:
            return False
        
        if old_name not in account.categories:
            return False
        
        if new_name in account.categories:
            return False  # 新分类名已存在
        
        # 重命名分类
        idx = account.categories.index(old_name)
        account.categories[idx] = new_name
        
        # 更新所有使用旧分类的交易
        account_dir = self._get_account_dir(account_id)
        for trans_dir in account_dir.iterdir():
            if not trans_dir.is_dir() or trans_dir.name in ['invoice', 'payment', 'purchase']:
                continue
            
            data_file = trans_dir / 'data.json'
            if data_file.exists():
                try:
                    with open(data_file, 'r', encoding='utf-8') as f:
                        transaction_data = json.load(f)
                    
                    if transaction_data.get('category') == old_name:
                        transaction_data['category'] = new_name
                        with open(data_file, 'w', encoding='utf-8') as f:
                            json.dump(transaction_data, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    print(f"更新交易分类出错: {e}")
        
        account.updated_at = datetime.now().isoformat()
        self._save_account_metadata(account)
        return True
    
    def delete_category(self, account_id: str, category: str) -> bool:
        """删除交易分类"""
        account = self.accounts.get(account_id)
        if not account:
            return False
        
        if category in account.categories:
            account.categories.remove(category)
            
            # 清除所有使用此分类的交易的分类字段
            account_dir = self._get_account_dir(account_id)
            for trans_dir in account_dir.iterdir():
                if not trans_dir.is_dir() or trans_dir.name in ['invoice', 'payment', 'purchase']:
                    continue
                
                data_file = trans_dir / 'data.json'
                if data_file.exists():
                    try:
                        with open(data_file, 'r', encoding='utf-8') as f:
                            transaction_data = json.load(f)
                        
                        if transaction_data.get('category') == category:
                            transaction_data['category'] = ""
                            with open(data_file, 'w', encoding='utf-8') as f:
                                json.dump(transaction_data, f, ensure_ascii=False, indent=2)
                    except Exception as e:
                        print(f"清除交易分类出错: {e}")
            
            account.updated_at = datetime.now().isoformat()
            self._save_account_metadata(account)
            return True
        return False
    
    def get_categories(self, account_id: str) -> List[str]:
        """获取账户的所有分类"""
        account = self.accounts.get(account_id)
        if not account:
            return []
        return account.categories
    
    def export_to_mrobot_format(self, account_id: str, transaction_ids: List[str], output_path: str) -> bool:
        """导出交易为 .mrobot 专用格式（ZIP 文件）
        
        格式说明：
        - 文件扩展名：.mrobot（实际上是 ZIP 文件）
        - 结构：
          - metadata.json（交易元数据）
          - images/（所有相关图片）
        """
        try:
            account = self.accounts.get(account_id)
            if not account:
                return False
            
            output_file = Path(output_path)
            if not output_file.parent.exists():
                output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建 ZIP 文件
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                # 收集交易数据和图片
                transactions_data = []
                image_index = 0
                
                for trans_id in transaction_ids:
                    transaction = self._load_transaction_data(account_id, trans_id)
                    if not transaction:
                        continue
                    
                    # 转换交易为字典
                    trans_dict = transaction.to_dict()
                    
                    # 处理图片，存储相对路径
                    image_map = {}
                    
                    if transaction.invoice_path:
                        img_path = self.get_transaction_image_path(account_id, transaction.invoice_path)
                        if img_path and img_path.exists():
                            archive_path = f"images/invoice_{image_index}{img_path.suffix}"
                            zf.write(str(img_path), archive_path)
                            image_map['invoice'] = archive_path
                            image_index += 1
                    
                    if transaction.payment_path:
                        img_path = self.get_transaction_image_path(account_id, transaction.payment_path)
                        if img_path and img_path.exists():
                            archive_path = f"images/payment_{image_index}{img_path.suffix}"
                            zf.write(str(img_path), archive_path)
                            image_map['payment'] = archive_path
                            image_index += 1
                    
                    if transaction.purchase_path:
                        img_path = self.get_transaction_image_path(account_id, transaction.purchase_path)
                        if img_path and img_path.exists():
                            archive_path = f"images/purchase_{image_index}{img_path.suffix}"
                            zf.write(str(img_path), archive_path)
                            image_map['purchase'] = archive_path
                            image_index += 1
                    
                    trans_dict['image_map'] = image_map
                    transactions_data.append(trans_dict)
                
                # 创建元数据 JSON
                metadata = {
                    'version': '1.0',
                    'account_name': account.name,
                    'account_description': account.description,
                    'export_date': datetime.now().isoformat(),
                    'transactions': transactions_data,
                    'transaction_count': len(transactions_data)
                }
                
                # 将元数据写入 ZIP
                metadata_json = json.dumps(metadata, ensure_ascii=False, indent=2)
                zf.writestr('metadata.json', metadata_json)
            
            return True
        
        except Exception as e:
            print(f"导出失败: {e}")
            return False