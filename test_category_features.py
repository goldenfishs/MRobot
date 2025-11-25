#!/usr/bin/env python3
"""
测试财务模块的分类功能完整流程
"""

import shutil
from pathlib import Path
from app.tools.finance_manager import FinanceManager, Transaction

# 清除旧数据
data_root = Path("assets/Finance_Data")
if data_root.exists():
    shutil.rmtree(data_root)

print("=" * 60)
print("财务模块分类功能测试")
print("=" * 60)

# 初始化财务管理器
fm = FinanceManager()

# 测试1: 验证 admin 账户自动创建
print("\n[测试1] admin 账户自动创建")
accounts = fm.get_all_accounts()
print(f"  账户数量: {len(accounts)}")
assert len(accounts) == 1, "应该有1个账户"
admin_acc = accounts[0]
print(f"  账户名称: {admin_acc.name}")
assert admin_acc.name == "admin", "账户名称应该是 'admin'"
print("  ✓ 通过")

# 测试2: 验证默认分类
print("\n[测试2] 默认分类")
print(f"  分类数量: {len(admin_acc.categories)}")
print(f"  分类列表: {admin_acc.categories}")
assert len(admin_acc.categories) > 0, "应该有默认分类"
print("  ✓ 通过")

# 测试3: 添加新分类
print("\n[测试3] 添加新分类")
result = fm.add_category(admin_acc.id, "房租")
print(f"  添加 '房租' 分类: {'成功' if result else '失败'}")
assert result, "应该成功添加分类"
categories = fm.get_categories(admin_acc.id)
print(f"  分类数量: {len(categories)}")
assert "房租" in categories, "应该包含 '房租' 分类"
print("  ✓ 通过")

# 测试4: 创建带分类的交易记录
print("\n[测试4] 创建带分类的交易记录")
trans1 = Transaction(
    date="2025-01-01",
    amount=5000,
    trader="工作所得",
    notes="1月工资",
    category="工资"
)
fm.add_transaction(admin_acc.id, trans1)
print(f"  交易1: {trans1.date} | {trans1.trader} | {trans1.category} | ¥{trans1.amount}")

trans2 = Transaction(
    date="2025-01-05",
    amount=-1500,
    trader="房东",
    notes="1月房租",
    category="房租"
)
fm.add_transaction(admin_acc.id, trans2)
print(f"  交易2: {trans2.date} | {trans2.trader} | {trans2.category} | ¥{trans2.amount}")

# 重新加载以验证保存
fm.load_all_accounts()
admin_acc = fm.get_account(admin_acc.id)
print(f"  账户交易总数: {len(admin_acc.transactions)}")
assert len(admin_acc.transactions) == 2, "应该有2个交易"
print("  ✓ 通过")

# 测试5: 按分类查询
print("\n[测试5] 按分类查询")
results_salary = fm.query_transactions(admin_acc.id, category="工资")
print(f"  '工salary' 分类的交易: {len(results_salary)} 条")
assert len(results_salary) == 1, "应该有1个工资交易"
assert results_salary[0].amount == 5000

results_rent = fm.query_transactions(admin_acc.id, category="房租")
print(f"  '房租' 分类的交易: {len(results_rent)} 条")
assert len(results_rent) == 1, "应该有1个房租交易"
assert results_rent[0].amount == -1500

results_all = fm.query_transactions(admin_acc.id)
print(f"  全部分类的交易: {len(results_all)} 条")
assert len(results_all) == 2, "应该有2个交易"
print("  ✓ 通过")

# 测试6: 更新交易分类
print("\n[测试6] 更新交易分类")
fm.update_transaction(admin_acc.id, trans1.id, category="奖金")
fm.load_all_accounts()
admin_acc = fm.get_account(admin_acc.id)
updated_trans = fm.get_transaction(admin_acc.id, trans1.id)
print(f"  更新后的分类: {updated_trans.category}")
assert updated_trans.category == "奖金", "分类应该更新为 '奖金'"
print("  ✓ 通过")

# 测试7: CSV导出包含分类
print("\n[测试7] CSV导出包含分类")
csv_path = "/tmp/test_export.csv"
result = fm.export_to_csv(admin_acc.id, csv_path)
print(f"  导出结果: {'成功' if result else '失败'}")
assert result, "应该成功导出CSV"
# 验证CSV内容
with open(csv_path, 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()
    print(f"  CSV行数: {len(lines)}")
    print(f"  标题行: {lines[0].strip()}")
    assert "分类" in lines[0], "CSV应该包含 '分类' 列"
    print(f"  数据行1: {lines[1].strip()}")
    print(f"  数据行2: {lines[2].strip()}")
print("  ✓ 通过")

print("\n" + "=" * 60)
print("所有测试都通过了！✓")
print("=" * 60)
