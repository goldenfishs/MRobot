"""
财务模块 - 编程接口文档

本文档说明如何在代码中使用财务模块的API
"""

# ============================================================================
# 1. 基础数据模型
# ============================================================================

from app.tools.finance_manager import FinanceManager, Transaction, Account, TransactionType
from datetime import datetime

# 创建财务管理器实例
fm = FinanceManager()  # 使用默认路径 assets/Finance_Data
# 或指定自定义路径
# fm = FinanceManager(data_root="/custom/path/to/finance_data")


# ============================================================================
# 2. 账户操作
# ============================================================================

# 创建新账户
account = fm.create_account(
    account_name="2024年项目经费",
    description="用于记录项目开发期间的所有支出"
)
print(f"创建账户: {account.id}")

# 获取所有账户
all_accounts = fm.get_all_accounts()
for acc in all_accounts:
    print(f"账户: {acc.name} (ID: {acc.id})")

# 获取单个账户
account = fm.get_account(account.id)
print(f"账户名称: {account.name}")
print(f"账户描述: {account.description}")

# 更新账户信息
fm.update_account(
    account.id,
    account_name="2024年项目经费V2",
    description="更新的描述"
)

# 删除账户（删除所有相关数据）
# fm.delete_account(account.id)


# ============================================================================
# 3. 交易记录操作
# ============================================================================

# 创建交易记录
transaction = Transaction(
    date="2024-01-15",
    amount=1500.50,
    trader="张三",
    notes="购买办公用品和文具"
)

# 添加到账户
fm.add_transaction(account.id, transaction)
print(f"交易记录ID: {transaction.id}")

# 获取交易记录
trans = fm.get_transaction(account.id, transaction.id)
print(f"交易人: {trans.trader}")
print(f"金额: ¥{trans.amount}")

# 更新交易记录
fm.update_transaction(
    account.id,
    transaction.id,
    amount=1600.50,
    notes="购买办公用品、文具和咖啡机"
)

# 删除交易记录
# fm.delete_transaction(account.id, transaction.id)


# ============================================================================
# 4. 图片管理
# ============================================================================

# 保存交易相关的图片
# 参数：账户ID、交易ID、图片类型、本地图片路径
relative_path = fm.save_image_for_transaction(
    account.id,
    transaction.id,
    TransactionType.INVOICE,  # 发票图片
    "/path/to/invoice.jpg"
)
print(f"保存发票图片: {relative_path}")

# 获取图片的完整路径（用于显示或处理）
full_path = fm.get_transaction_image_path(account.id, relative_path)
print(f"完整路径: {full_path}")

# 一次性保存多个图片
image_types_and_paths = {
    TransactionType.INVOICE: "/path/to/invoice.jpg",
    TransactionType.PAYMENT: "/path/to/payment_screenshot.png",
    TransactionType.PURCHASE: "/path/to/order.jpg"
}

for image_type, image_path in image_types_and_paths.items():
    fm.save_image_for_transaction(
        account.id,
        transaction.id,
        image_type,
        image_path
    )


# ============================================================================
# 5. 查询功能
# ============================================================================

# 基础查询 - 获取账户的所有交易
all_transactions = account.transactions
print(f"总交易数: {len(all_transactions)}")

# 高级查询 - 带条件过滤
results = fm.query_transactions(
    account.id,
    date_start="2024-01-01",      # 开始日期
    date_end="2024-12-31",        # 结束日期
    amount_min=100.0,              # 最小金额
    amount_max=5000.0,             # 最大金额
    trader="张三"                  # 交易人（模糊匹配）
)
print(f"查询结果: {len(results)} 条记录")

# 按日期倒序排列（默认已排序）
for trans in results:
    print(f"{trans.date} - {trans.trader}: ¥{trans.amount}")

# 只查询特定日期范围
january_records = fm.query_transactions(
    account.id,
    date_start="2024-01-01",
    date_end="2024-01-31"
)

# 只查询特定金额范围
expensive_records = fm.query_transactions(
    account.id,
    amount_min=1000.0
)

# 只查询特定交易人
zhang_records = fm.query_transactions(
    account.id,
    trader="张"  # 支持模糊匹配，不区分大小写
)


# ============================================================================
# 6. 账户汇总
# ============================================================================

# 获取账户汇总信息
summary = fm.get_account_summary(account.id)
print(f"账户名: {summary['account_name']}")
print(f"总金额: ¥{summary['total_amount']:.2f}")
print(f"交易数: {summary['transaction_count']}")
print(f"创建时间: {summary['created_at']}")
print(f"更新时间: {summary['updated_at']}")


# ============================================================================
# 7. 导入导出功能
# ============================================================================

# 导出账户为ZIP包（用于转移）
success = fm.export_account_package(
    account.id,
    export_path="/Users/username/Desktop"
)
if success:
    print("账户导出成功")

# 导入账户ZIP包
imported_account_id = fm.import_account_package(
    zip_path="/Users/username/Desktop/2024年项目经费_xxx.zip"
)
if imported_account_id:
    print(f"账户导入成功，ID: {imported_account_id}")

# 导出为CSV格式（用于Excel分析）
success = fm.export_to_csv(
    account.id,
    csv_path="/Users/username/Desktop/report.csv"
)
if success:
    print("CSV导出成功")

# 备份所有账户
success = fm.backup_all_accounts()
if success:
    print("备份创建成功，位置: assets/Finance_Data/backups/")


# ============================================================================
# 8. 数据序列化
# ============================================================================

# 将交易记录转换为字典（用于JSON序列化）
trans_dict = transaction.to_dict()
print(f"交易记录字典: {trans_dict}")

# 从字典创建交易记录
new_trans = Transaction.from_dict(trans_dict)

# 将账户转换为字典
account_dict = account.to_dict()
print(f"账户字典（包含所有交易）")

# 从字典创建账户
new_account = Account.from_dict(account_dict)


# ============================================================================
# 9. 实用示例
# ============================================================================

# 示例1: 计算月度支出
def get_monthly_expense(finance_manager, account_id, month_str):
    """
    获取指定月份的总支出
    month_str: 格式为 "2024-01"
    """
    date_start = f"{month_str}-01"
    # 计算月末日期
    year, month = map(int, month_str.split('-'))
    if month == 12:
        date_end = f"{year + 1}-01-01"
    else:
        date_end = f"{year}-{month + 1:02d}-01"
    
    transactions = finance_manager.query_transactions(
        account_id,
        date_start=date_start,
        date_end=date_end
    )
    total = sum(t.amount for t in transactions)
    return total

monthly_total = get_monthly_expense(fm, account.id, "2024-01")
print(f"1月份总支出: ¥{monthly_total:.2f}")


# 示例2: 按交易人统计支出
def get_trader_total(finance_manager, account_id, trader_name):
    """获取特定交易人的总支出"""
    transactions = finance_manager.query_transactions(
        account_id,
        trader=trader_name
    )
    total = sum(t.amount for t in transactions)
    count = len(transactions)
    return total, count

total, count = get_trader_total(fm, account.id, "张三")
print(f"与张三的交易: {count}笔，总额 ¥{total:.2f}")


# 示例3: 查找最大支出
def get_max_transaction(finance_manager, account_id):
    """找到金额最大的交易记录"""
    account = finance_manager.get_account(account_id)
    if not account.transactions:
        return None
    return max(account.transactions, key=lambda t: t.amount)

max_trans = get_max_transaction(fm, account.id)
if max_trans:
    print(f"最大支出: {max_trans.trader} - ¥{max_trans.amount}")


# 示例4: 导出月度报告
def export_monthly_report(finance_manager, account_id, month_str, output_path):
    """
    导出指定月份的报告
    """
    date_start = f"{month_str}-01"
    year, month = map(int, month_str.split('-'))
    if month == 12:
        date_end = f"{year + 1}-01-01"
    else:
        date_end = f"{year}-{month + 1:02d}-01"
    
    transactions = finance_manager.query_transactions(
        account_id,
        date_start=date_start,
        date_end=date_end
    )
    
    # 创建CSV内容
    import csv
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['日期', '交易人', '金额', '备注'])
        
        for trans in transactions:
            writer.writerow([
                trans.date,
                trans.trader,
                trans.amount,
                trans.notes
            ])

export_monthly_report(fm, account.id, "2024-01", "/tmp/report_2024-01.csv")


# ============================================================================
# 10. 错误处理
# ============================================================================

try:
    # 尝试获取不存在的账户
    result = fm.get_account("non-existent-id")
    if result is None:
        print("账户不存在")
except Exception as e:
    print(f"错误: {e}")

try:
    # 验证交易金额
    if transaction.amount <= 0:
        raise ValueError("金额必须大于0")
except ValueError as e:
    print(f"验证错误: {e}")

try:
    # 删除交易前检查
    if not fm.delete_transaction(account.id, "invalid-id"):
        print("删除失败，交易记录不存在")
except Exception as e:
    print(f"删除错误: {e}")


# ============================================================================
# 11. 性能优化建议
# ============================================================================

"""
1. 缓存:
   - 使用 fm.get_account() 获取账户后，交易记录已加载到内存
   - 避免频繁重新加载同一账户
   
2. 查询优化:
   - 使用查询条件过滤，而不是加载所有后手动过滤
   - 日期范围会显著提升查询性能
   
3. 批量操作:
   - 需要添加多条记录时，推荐循环调用 add_transaction()
   - 每次操作都会自动保存到磁盘
   
4. 大数据量:
   - 单个账户建议不超过10000条记录
   - 考虑按时间周期分账户
   - 定期归档和备份
"""


# ============================================================================
# 12. 完整工作流示例
# ============================================================================

def complete_workflow_example():
    """完整的财务做账工作流"""
    
    # 1. 初始化
    fm = FinanceManager()
    
    # 2. 创建账户
    account = fm.create_account(
        account_name="2024年度账目",
        description="全年财务记录"
    )
    
    # 3. 添加多条记录
    records_data = [
        ("2024-01-10", 500.0, "王五", "办公桌购买"),
        ("2024-01-15", 1200.0, "李四", "电脑软件许可"),
        ("2024-02-05", 300.0, "张三", "文具采购"),
    ]
    
    for date, amount, trader, notes in records_data:
        trans = Transaction(
            date=date,
            amount=amount,
            trader=trader,
            notes=notes
        )
        fm.add_transaction(account.id, trans)
    
    # 4. 查询数据
    jan_records = fm.query_transactions(
        account.id,
        date_start="2024-01-01",
        date_end="2024-01-31"
    )
    
    # 5. 统计分析
    total = sum(t.amount for t in jan_records)
    print(f"1月份支出: ¥{total}")
    
    # 6. 生成报告
    account_summary = fm.get_account_summary(account.id)
    print(f"账户总计: ¥{account_summary['total_amount']}")
    
    # 7. 备份数据
    fm.backup_all_accounts()
    
    return account.id

# 执行工作流
# account_id = complete_workflow_example()
