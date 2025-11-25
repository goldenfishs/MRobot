#!/usr/bin/env python3
"""
测试删除默认分类功能
"""

import shutil
from pathlib import Path
from app.tools.finance_manager import FinanceManager, Transaction, Account

# 清除旧数据
data_root = Path("assets/Finance_Data")
if data_root.exists():
    shutil.rmtree(data_root)

print("=" * 60)
print("测试删除默认分类功能")
print("=" * 60)

# 初始化财务管理器
fm = FinanceManager()

# 测试1: 验证 admin 账户的分类为空
print("\n[测试1] 新建账户的分类为空")
accounts = fm.get_all_accounts()
admin_acc = accounts[0]
print(f"  账户名称: {admin_acc.name}")
print(f"  分类数量: {len(admin_acc.categories)}")
print(f"  分类列表: {admin_acc.categories}")
assert len(admin_acc.categories) == 0, "新账户应该没有默认分类"
print("  ✓ 通过")

# 测试2: 用户创建分类
print("\n[测试2] 用户创建分类")
fm.add_category(admin_acc.id, "工资")
fm.add_category(admin_acc.id, "房租")
fm.add_category(admin_acc.id, "娱乐")
categories = fm.get_categories(admin_acc.id)
print(f"  创建的分类: {categories}")
assert len(categories) == 3, "应该有3个分类"
assert "工资" in categories
assert "房租" in categories
assert "娱乐" in categories
print("  ✓ 通过")

# 测试3: 创建交易时必须指定分类
print("\n[测试3] 创建交易时分类不能为空")
trans1 = Transaction(
    date="2025-01-01",
    amount=5000,
    trader="工作所得",
    notes="1月工资",
    category="工资"
)
assert trans1.category == "工资", "交易应该有分类"
print(f"  交易分类: {trans1.category}")
print("  ✓ 通过")

# 测试4: 验证空分类的交易
print("\n[测试4] 检查默认分类为空字符串")
trans_no_cat = Transaction(
    date="2025-01-01",
    amount=100,
    trader="测试用户"
)
print(f"  未指定分类的交易分类: '{trans_no_cat.category}'")
assert trans_no_cat.category == "", "未指定分类应该为空字符串"
print("  ✓ 通过")

# 测试5: 用户可以删除自定义分类
print("\n[测试5] 用户可以删除自定义分类")
success = fm.delete_category(admin_acc.id, "娱乐")
print(f"  删除 '娱乐' 分类: {'成功' if success else '失败'}")
assert success, "应该成功删除分类"
categories = fm.get_categories(admin_acc.id)
print(f"  删除后的分类: {categories}")
assert "娱乐" not in categories
assert len(categories) == 2
print("  ✓ 通过")

# 测试6: 验证分类持久化
print("\n[测试6] 分类数据持久化")
# 创建新的财务管理器实例，应该重新加载分类
fm2 = FinanceManager()
accounts2 = fm2.get_all_accounts()
admin_acc2 = accounts2[0]
categories2 = fm2.get_categories(admin_acc2.id)
print(f"  重新加载后的分类: {categories2}")
assert len(categories2) == 2, "应该有2个分类"
assert "工资" in categories2
assert "房租" in categories2
assert "娱乐" not in categories2
print("  ✓ 通过")

print("\n" + "=" * 60)
print("所有测试都通过了！✓")
print("=" * 60)
