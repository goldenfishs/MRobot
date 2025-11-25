#!/usr/bin/env python3
"""
测试查询页面分类下拉框动态更新功能
"""

import shutil
from pathlib import Path
from app.tools.finance_manager import FinanceManager, Transaction

# 清除旧数据
data_root = Path("assets/Finance_Data")
if data_root.exists():
    shutil.rmtree(data_root)

print("=" * 60)
print("测试查询页面分类下拉框动态更新")
print("=" * 60)

# 初始化财务管理器
fm = FinanceManager()
admin_acc = fm.get_all_accounts()[0]

print("\n[初始状态] 检查初始分类列表")
categories = fm.get_categories(admin_acc.id)
print(f"  初始分类数: {len(categories)}")
print(f"  初始分类: {categories}")
assert len(categories) == 0, "初始应该没有分类"
print("  ✓ 通过")

print("\n[测试1] 创建第一个分类")
success = fm.add_category(admin_acc.id, "工资")
print(f"  添加 '工资': {'成功' if success else '失败'}")
assert success, "应该成功添加分类"
categories = fm.get_categories(admin_acc.id)
print(f"  当前分类: {categories}")
assert "工资" in categories
print("  ✓ 通过")

print("\n[测试2] 创建第二个分类")
success = fm.add_category(admin_acc.id, "房租")
print(f"  添加 '房租': {'成功' if success else '失败'}")
assert success
categories = fm.get_categories(admin_acc.id)
print(f"  当前分类: {categories}")
assert len(categories) == 2
assert "工资" in categories and "房租" in categories
print("  ✓ 通过")

print("\n[测试3] 创建第三个分类")
success = fm.add_category(admin_acc.id, "食品")
print(f"  添加 '食品': {'成功' if success else '失败'}")
assert success
categories = fm.get_categories(admin_acc.id)
print(f"  当前分类: {categories}")
assert len(categories) == 3
print("  ✓ 通过")

print("\n[测试4] 验证分类持久化")
# 重新加载账户
fm2 = FinanceManager()
admin_acc2 = None
for acc in fm2.get_all_accounts():
    if acc.name == "admin":
        admin_acc2 = acc
        break

assert admin_acc2 is not None
categories2 = fm2.get_categories(admin_acc2.id)
print(f"  重新加载后的分类: {categories2}")
assert len(categories2) == 3
assert set(categories2) == {"工资", "房租", "食品"}
print("  ✓ 通过")

print("\n[测试5] 创建交易并按分类查询")
# 创建测试交易
trans_data = [
    ("2025-01-01", 5000, "工作", "工资", "1月工资"),
    ("2025-01-05", -1500, "房东", "房租", "房租"),
    ("2025-01-10", -200, "超市", "食品", "食材"),
]

for date, amount, trader, category, notes in trans_data:
    trans = Transaction(date=date, amount=amount, trader=trader, category=category, notes=notes)
    fm2.add_transaction(admin_acc2.id, trans)

print(f"  创建了 {len(trans_data)} 条交易")

# 按各分类查询
for cat in categories2:
    results = fm2.query_transactions(admin_acc2.id, category=cat)
    print(f"  查询 '{cat}' 分类: {len(results)} 条")
    assert len(results) == 1, f"应该有1条 {cat} 分类的交易"

print("  ✓ 通过")

print("\n" + "=" * 60)
print("所有动态分类测试都通过了！✓")
print("=" * 60)
print("\n说明:")
print("1. 新建的分类可以立即在下拉框中选择")
print("2. 分类数据会被正确保存和加载")
print("3. 创建的交易可以按分类进行查询")
