#!/usr/bin/env python3
"""测试分类功能"""

from app.tools.finance_manager import FinanceManager, Transaction

# 创建财务管理器
fm = FinanceManager()

# 创建一个测试账户
account = fm.create_account("测试账户", "用于测试分类功能")
print(f"创建账户: {account.name} (ID: {account.id})")
print(f"初始分类: {account.categories}")

# 添加新分类
print("\n添加新分类...")
fm.add_category(account.id, "工作支出")
fm.add_category(account.id, "个人投资")

account = fm.get_account(account.id)
print(f"更新后的分类: {account.categories}")

# 创建交易记录
print("\n创建交易记录...")
trans1 = Transaction(
    date="2024-01-01",
    amount=1000,
    trader="张三",
    notes="工资",
    category="工资"
)
fm.add_transaction(account.id, trans1)

trans2 = Transaction(
    date="2024-01-02",
    amount=-500,
    trader="李四",
    notes="午餐",
    category="饮食"
)
fm.add_transaction(account.id, trans2)

trans3 = Transaction(
    date="2024-01-03",
    amount=-200,
    trader="公司",
    notes="项目费用",
    category="工作支出"
)
fm.add_transaction(account.id, trans3)

# 查询交易记录
print("\n所有交易记录:")
account = fm.get_account(account.id)
for trans in account.transactions:
    print(f"  {trans.date} | {trans.trader} | {trans.category} | ¥{trans.amount:.2f} | {trans.notes}")

# 按分类查询
print("\n按分类查询 - 工资:")
results = fm.query_transactions(account.id, category="工资")
for trans in results:
    print(f"  {trans.date} | {trans.trader} | {trans.category} | ¥{trans.amount:.2f}")

print("\n按分类查询 - 饮食:")
results = fm.query_transactions(account.id, category="饮食")
for trans in results:
    print(f"  {trans.date} | {trans.trader} | {trans.category} | ¥{trans.amount:.2f}")

print("\nTest passed! ✓")
