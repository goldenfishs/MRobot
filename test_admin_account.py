#!/usr/bin/env python3
"""
测试 admin 账户自动创建功能
"""

import shutil
from pathlib import Path
from app.tools.finance_manager import FinanceManager

# 清除旧数据
data_root = Path("assets/Finance_Data")
if data_root.exists():
    shutil.rmtree(data_root)

# 测试1: 第一次初始化，应该创建 admin 账户
print("测试1: 第一次初始化（应该创建 admin 账户）")
fm1 = FinanceManager()
accounts1 = fm1.get_all_accounts()
print(f"  账户数量: {len(accounts1)}")
if accounts1:
    print(f"  第一个账户: 名称={accounts1[0].name}, ID={accounts1[0].id}")
    print(f"  是否为 admin: {accounts1[0].name == 'admin'}")
assert len(accounts1) == 1, "应该有1个账户"
assert accounts1[0].name == "admin", "账户名称应该是 'admin'"
print("  ✓ 通过！\n")

# 测试2: 再次初始化，应该加载现有的 admin 账户
print("测试2: 再次初始化（应该加载现有的 admin 账户）")
fm2 = FinanceManager()
accounts2 = fm2.get_all_accounts()
print(f"  账户数量: {len(accounts2)}")
if accounts2:
    print(f"  第一个账户: 名称={accounts2[0].name}, ID={accounts2[0].id}")
    print(f"  账户ID是否相同: {accounts1[0].id == accounts2[0].id}")
assert len(accounts2) == 1, "应该有1个账户"
assert accounts2[0].name == "admin", "账户名称应该是 'admin'"
assert accounts1[0].id == accounts2[0].id, "账户ID应该相同"
print("  ✓ 通过！\n")

# 测试3: 添加新账户后，应该仍然能找到 admin 账户
print("测试3: 添加新账户后，应该仍然能找到 admin 账户")
fm2.create_account("test", "测试账户")
accounts3 = fm2.get_all_accounts()
print(f"  账户数量: {len(accounts3)}")
admin_found = False
for acc in accounts3:
    print(f"  - {acc.name}")
    if acc.name == "admin":
        admin_found = True
assert len(accounts3) == 2, "应该有2个账户"
assert admin_found, "应该找到 admin 账户"
print("  ✓ 通过！\n")

# 测试4: 测试 admin 账户的分类
print("测试4: 测试 admin 账户的分类")
admin_acc = None
for acc in accounts3:
    if acc.name == "admin":
        admin_acc = acc
        break
assert admin_acc is not None
print(f"  默认分类: {admin_acc.categories}")
assert len(admin_acc.categories) > 0, "应该有默认分类"
print("  ✓ 通过！\n")

print("所有测试都通过了！✓")
