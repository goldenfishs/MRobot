#!/usr/bin/env python3
"""调试导入后查询无法显示的问题"""

import sys
import os
from pathlib import Path

# 添加项目根路径
sys.path.insert(0, str(Path(__file__).parent))

from app.tools.finance_manager import FinanceManager

def debug_import_issue():
    """调试导入问题"""
    fm = FinanceManager()
    
    print("=" * 60)
    print("财务模块 - 导入查询调试")
    print("=" * 60)
    
    # 1. 显示当前所有账户
    print("\n1️⃣ 当前所有账户:")
    all_accounts = fm.get_all_accounts()
    for i, account in enumerate(all_accounts, 1):
        print(f"  [{i}] {account.name} (ID: {account.id})")
        print(f"      交易数: {len(account.transactions)}")
        if account.transactions:
            for j, trans in enumerate(account.transactions[:3], 1):
                print(f"      - [{j}] {trans.date} | {trans.trader} | ¥{trans.amount:.2f}")
            if len(account.transactions) > 3:
                print(f"      ... 还有 {len(account.transactions) - 3} 条记录")
    
    if not all_accounts:
        print("  ❌ 没有账户")
        return
    
    # 2. 针对每个账户进行详细检查
    for account in all_accounts:
        print(f"\n2️⃣ 账户 '{account.name}' 的详细信息:")
        print(f"  - 账户 ID: {account.id}")
        print(f"  - 创建时间: {account.created_at}")
        print(f"  - 交易总数: {len(account.transactions)}")
        
        if account.transactions:
            print(f"  - 金额范围: ¥{min(t.amount for t in account.transactions):.2f} ~ ¥{max(t.amount for t in account.transactions):.2f}")
            
            # 按日期排序显示
            sorted_trans = sorted(account.transactions, key=lambda x: x.date)
            print(f"  - 日期范围: {sorted_trans[0].date} ~ {sorted_trans[-1].date}")
            
            # 显示样本交易
            print(f"\n  📋 交易样本 (前5条):")
            for i, trans in enumerate(sorted_trans[:5], 1):
                print(f"    [{i}] 日期: {trans.date}")
                print(f"        交易人: {trans.trader}")
                print(f"        金额: ¥{trans.amount:.2f}")
                print(f"        备注: {trans.notes or '(无)'}")
                print(f"        ID: {trans.id}")
    
    # 3. 测试查询功能
    print("\n3️⃣ 测试查询功能:")
    if all_accounts:
        test_account = all_accounts[0]
        print(f"  使用账户: '{test_account.name}'")
        
        # 无条件查询
        print(f"\n  a) 无条件查询:")
        results = fm.query_transactions(test_account.id)
        print(f"     结果数: {len(results)} 条")
        
        # 有条件查询
        if test_account.transactions:
            first_trans = sorted(test_account.transactions, key=lambda x: x.date)[0]
            print(f"\n  b) 按日期查询 (>= {first_trans.date}):")
            results = fm.query_transactions(test_account.id, date_start=first_trans.date)
            print(f"     结果数: {len(results)} 条")
            
            # 金额查询
            min_amount = min(t.amount for t in test_account.transactions)
            print(f"\n  c) 按金额查询 (>= ¥{min_amount:.2f}):")
            results = fm.query_transactions(test_account.id, amount_min=min_amount)
            print(f"     结果数: {len(results)} 条")
    
    # 4. 检查数据文件
    print("\n4️⃣ 检查数据文件位置:")
    data_root = fm.data_root
    print(f"  数据根目录: {data_root}")
    
    accounts_dir = data_root / 'accounts'
    if accounts_dir.exists():
        print(f"  账户目录存在: ✅")
        account_dirs = list(accounts_dir.iterdir())
        print(f"  账户文件夹数: {len(account_dirs)}")
        for acc_dir in account_dirs[:3]:
            print(f"    - {acc_dir.name}/")
            metadata_file = acc_dir / 'metadata.json'
            if metadata_file.exists():
                print(f"      metadata.json: ✅")
    else:
        print(f"  账户目录不存在: ❌")
    
    print("\n" + "=" * 60)
    print("调试完成！")
    print("=" * 60)

if __name__ == '__main__':
    debug_import_issue()
