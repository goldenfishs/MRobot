#!/usr/bin/env python3
"""
分类管理功能测试脚本
测试新增、重命名、删除分类的功能
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 添加app目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.tools.finance_manager import FinanceManager, Transaction


def test_rename_category():
    """测试重命名分类"""
    print("=== 测试重命名分类 ===")
    
    # 创建测试用的FinanceManager
    test_data_root = Path("/tmp/test_finance_data_rename")
    fm = FinanceManager(str(test_data_root))
    
    # 获取admin账户或创建一个测试账户
    account_ids = list(fm.accounts.keys())
    if not account_ids:
        account_id = fm.create_account("test_account", "测试账户")
    else:
        account_id = account_ids[0]
    
    print(f"使用账户: {account_id}")
    
    # 添加分类
    print("添加分类: 食品、交通、娱乐")
    assert fm.add_category(account_id, "食品"), "添加分类'食品'失败"
    assert fm.add_category(account_id, "交通"), "添加分类'交通'失败"
    assert fm.add_category(account_id, "娱乐"), "添加分类'娱乐'失败"
    
    categories = fm.get_categories(account_id)
    print(f"当前分类: {categories}")
    assert len(categories) == 3, f"期望3个分类，实际{len(categories)}个"
    
    # 添加一个使用"食品"分类的交易
    trans = Transaction(
        date="2024-01-01",
        amount=100.0,
        trader="超市",
        notes="购买食品",
        category="食品"
    )
    fm.add_transaction(account_id, trans)
    print(f"添加交易，分类为'食品': {trans.id}")
    
    # 重命名分类
    print("重命名分类: 食品 -> 饮食")
    assert fm.rename_category(account_id, "食品", "饮食"), "重命名分类失败"
    
    categories = fm.get_categories(account_id)
    print(f"重命名后分类: {categories}")
    assert "饮食" in categories, "重命名后分类中没有'饮食'"
    assert "食品" not in categories, "重命名后分类中仍有'食品'"
    
    # 验证交易的分类也被更新了
    # 需要重新加载账户数据
    fm.load_all_accounts()
    account = fm.accounts[account_id]
    for t in account.transactions:
        if t.id == trans.id:
            print(f"交易分类已更新为: {t.category}")
            assert t.category == "饮食", f"交易分类应该是'饮食'，实际是'{t.category}'"
            break
    
    # 测试重命名失败的情况：新分类名已存在
    print("测试重命名失败情况: 新分类名'交通'已存在")
    assert not fm.rename_category(account_id, "饮食", "交通"), "应该重命名失败"
    
    print("✓ 重命名分类测试通过\n")


def test_delete_category():
    """测试删除分类"""
    print("=== 测试删除分类 ===")
    
    test_data_root = Path("/tmp/test_finance_data_delete")
    fm = FinanceManager(str(test_data_root))
    
    account_ids = list(fm.accounts.keys())
    if not account_ids:
        account_id = fm.create_account("test_account", "测试账户")
    else:
        account_id = account_ids[0]
    
    print(f"使用账户: {account_id}")
    
    # 添加分类
    print("添加分类: 食品、交通、娱乐")
    fm.add_category(account_id, "食品")
    fm.add_category(account_id, "交通")
    fm.add_category(account_id, "娱乐")
    
    # 添加使用"食品"分类的交易
    trans1 = Transaction(
        date="2024-01-01",
        amount=100.0,
        trader="超市",
        notes="购买食品",
        category="食品"
    )
    trans2 = Transaction(
        date="2024-01-02",
        amount=50.0,
        trader="出租车",
        notes="交通费用",
        category="交通"
    )
    
    fm.add_transaction(account_id, trans1)
    fm.add_transaction(account_id, trans2)
    
    print(f"添加交易1（分类'食品'）: {trans1.id}")
    print(f"添加交易2（分类'交通'）: {trans2.id}")
    
    # 删除"食品"分类
    print("删除分类: 食品")
    assert fm.delete_category(account_id, "食品"), "删除分类失败"
    
    categories = fm.get_categories(account_id)
    print(f"删除后分类: {categories}")
    assert "食品" not in categories, "删除后分类中仍有'食品'"
    
    # 验证使用"食品"分类的交易分类被清空了
    fm.load_all_accounts()
    account = fm.accounts[account_id]
    for t in account.transactions:
        if t.id == trans1.id:
            print(f"使用已删除分类的交易，其分类现在为: '{t.category}'")
            assert t.category == "", f"交易分类应该被清空，实际是'{t.category}'"
        elif t.id == trans2.id:
            print(f"使用'交通'分类的交易，其分类仍为: '{t.category}'")
            assert t.category == "交通", f"交易分类应该保持'交通'，实际是'{t.category}'"
    
    print("✓ 删除分类测试通过\n")


def test_add_category():
    """测试添加分类"""
    print("=== 测试添加分类 ===")
    
    test_data_root = Path("/tmp/test_finance_data_add")
    fm = FinanceManager(str(test_data_root))
    
    account_ids = list(fm.accounts.keys())
    if not account_ids:
        account_id = fm.create_account("test_account", "测试账户")
    else:
        account_id = account_ids[0]
    
    print(f"使用账户: {account_id}")
    
    # 初始应该没有分类
    categories = fm.get_categories(account_id)
    print(f"初始分类: {categories}")
    
    # 添加分类
    print("添加分类: 食品")
    assert fm.add_category(account_id, "食品"), "添加分类失败"
    
    categories = fm.get_categories(account_id)
    print(f"添加后分类: {categories}")
    assert "食品" in categories, "分类中没有'食品'"
    
    # 测试添加重复分类
    print("测试添加重复分类")
    assert not fm.add_category(account_id, "食品"), "应该返回False"
    
    categories = fm.get_categories(account_id)
    assert len(categories) == 1, f"应该只有1个分类，实际{len(categories)}个"
    
    print("✓ 添加分类测试通过\n")


def main():
    """运行所有测试"""
    print("开始测试分类管理功能...\n")
    
    try:
        test_add_category()
        test_rename_category()
        test_delete_category()
        
        print("=" * 50)
        print("✓ 所有测试通过！")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
