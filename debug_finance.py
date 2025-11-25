#!/usr/bin/env python3
"""
财务模块调试脚本
用于测试财务管理器的基本功能
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.tools.finance_manager import FinanceManager, Transaction

def main():
    print("=" * 60)
    print("财务模块调试")
    print("=" * 60)
    
    # 1. 初始化财务管理器
    print("\n1. 初始化财务管理器...")
    try:
        fm = FinanceManager()
        print(f"✅ 初始化成功")
        print(f"   数据目录: {fm.data_root}")
        print(f"   目录存在: {fm.data_root.exists()}")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    # 2. 获取现有账户
    print("\n2. 获取现有账户...")
    try:
        accounts = fm.get_all_accounts()
        print(f"✅ 获取成功")
        print(f"   账户数: {len(accounts)}")
        for acc in accounts:
            print(f"   - {acc.name} (ID: {acc.id})")
    except Exception as e:
        print(f"❌ 获取失败: {e}")
        return
    
    # 3. 创建测试账户
    print("\n3. 创建测试账户...")
    try:
        account = fm.create_account(
            account_name="测试账户",
            description="用于调试的测试账户"
        )
        print(f"✅ 创建成功")
        print(f"   账户ID: {account.id}")
        print(f"   账户名: {account.name}")
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        return
    
    # 4. 添加交易记录
    print("\n4. 添加交易记录...")
    try:
        transaction = Transaction(
            date="2024-11-25",
            amount=100.0,
            trader="测试商家",
            notes="测试交易记录"
        )
        fm.add_transaction(account.id, transaction)
        print(f"✅ 添加成功")
        print(f"   交易ID: {transaction.id}")
        print(f"   日期: {transaction.date}")
        print(f"   金额: ¥{transaction.amount}")
    except Exception as e:
        print(f"❌ 添加失败: {e}")
        return
    
    # 5. 查询账户
    print("\n5. 查询账户信息...")
    try:
        acc = fm.get_account(account.id)
        print(f"✅ 查询成功")
        print(f"   账户名: {acc.name}")
        print(f"   记录数: {len(acc.transactions)}")
        
        for trans in acc.transactions:
            print(f"   - {trans.date}: {trans.trader} ¥{trans.amount}")
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return
    
    # 6. 获取账户汇总
    print("\n6. 获取账户汇总...")
    try:
        summary = fm.get_account_summary(account.id)
        print(f"✅ 获取成功")
        print(f"   账户名: {summary['account_name']}")
        print(f"   总额: ¥{summary['total_amount']:.2f}")
        print(f"   记录数: {summary['transaction_count']}")
    except Exception as e:
        print(f"❌ 获取失败: {e}")
        return
    
    # 7. 查询功能
    print("\n7. 测试查询功能...")
    try:
        results = fm.query_transactions(
            account.id,
            date_start="2024-01-01",
            date_end="2024-12-31"
        )
        print(f"✅ 查询成功")
        print(f"   查询结果: {len(results)} 条记录")
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return
    
    # 8. 备份功能
    print("\n8. 测试备份功能...")
    try:
        success = fm.backup_all_accounts()
        if success:
            print(f"✅ 备份成功")
            backup_dir = fm.data_root / "backups"
            if backup_dir.exists():
                backups = list(backup_dir.glob("*.zip"))
                print(f"   备份文件数: {len(backups)}")
                if backups:
                    print(f"   最新备份: {backups[-1].name}")
        else:
            print(f"❌ 备份失败")
    except Exception as e:
        print(f"❌ 备份失败: {e}")
    
    print("\n" + "=" * 60)
    print("调试完成！所有功能正常运行 ✅")
    print("=" * 60)

if __name__ == "__main__":
    main()
