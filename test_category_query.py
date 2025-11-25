#!/usr/bin/env python3
"""
测试分类查询功能
"""

import shutil
from pathlib import Path
from app.tools.finance_manager import FinanceManager, Transaction

# 清除旧数据
data_root = Path("assets/Finance_Data")
if data_root.exists():
    shutil.rmtree(data_root)

print("=" * 60)
print("测试分类查询功能")
print("=" * 60)

# 初始化财务管理器
fm = FinanceManager()
admin_acc = fm.get_all_accounts()[0]

# 创建测试分类
fm.add_category(admin_acc.id, "工资")
fm.add_category(admin_acc.id, "房租")
fm.add_category(admin_acc.id, "食品")
print("\n✓ 创建分类: 工资, 房租, 食品")

# 创建测试交易
transactions_data = [
    ("2025-01-01", 5000, "工作所得", "工资", "1月工资"),
    ("2025-01-05", -1500, "房东", "房租", "1月房租"),
    ("2025-01-10", -300, "超市", "食品", "日常食品"),
    ("2025-01-15", 5000, "奖励", "工资", "绩效奖励"),
    ("2025-01-20", -200, "便利店", "食品", "零食"),
]

for date, amount, trader, category, notes in transactions_data:
    trans = Transaction(date=date, amount=amount, trader=trader, category=category, notes=notes)
    fm.add_transaction(admin_acc.id, trans)

print("✓ 创建5条交易记录")

# 测试按分类查询
print("\n[测试1] 查询 '工资' 分类")
results = fm.query_transactions(admin_acc.id, category="工资")
print(f"  结果: {len(results)} 条")
for t in results:
    print(f"    - {t.date} | {t.trader} | {t.category} | ¥{t.amount}")
assert len(results) == 2, "应该有2条工资交易"
assert all(t.category == "工资" for t in results), "所有交易应该是工资分类"
print("  ✓ 通过")

print("\n[测试2] 查询 '房租' 分类")
results = fm.query_transactions(admin_acc.id, category="房租")
print(f"  结果: {len(results)} 条")
for t in results:
    print(f"    - {t.date} | {t.trader} | {t.category} | ¥{t.amount}")
assert len(results) == 1, "应该有1条房租交易"
assert results[0].category == "房租"
print("  ✓ 通过")

print("\n[测试3] 查询 '食品' 分类")
results = fm.query_transactions(admin_acc.id, category="食品")
print(f"  结果: {len(results)} 条")
for t in results:
    print(f"    - {t.date} | {t.trader} | {t.category} | ¥{t.amount}")
assert len(results) == 2, "应该有2条食品交易"
assert all(t.category == "食品" for t in results), "所有交易应该是食品分类"
print("  ✓ 通过")

print("\n[测试4] 查询所有分类 (category=None)")
results = fm.query_transactions(admin_acc.id, category=None)
print(f"  结果: {len(results)} 条")
assert len(results) == 5, "应该返回所有5条交易"
print("  ✓ 通过")

print("\n[测试5] 按分类和金额范围查询")
results = fm.query_transactions(admin_acc.id, category="工资", amount_min=0)
print(f"  查询 '工资' 且金额>=0: {len(results)} 条")
assert len(results) == 2, "应该有2条正数的工资交易"
print("  ✓ 通过")

print("\n[测试6] 按分类和日期范围查询")
results = fm.query_transactions(admin_acc.id, category="食品", date_start="2025-01-15")
print(f"  查询 '食品' 且日期>=2025-01-15: {len(results)} 条")
for t in results:
    print(f"    - {t.date} | {t.trader}")
assert len(results) == 1, "应该有1条符合条件的食品交易"
print("  ✓ 通过")

print("\n" + "=" * 60)
print("所有分类查询测试都通过了！✓")
print("=" * 60)
