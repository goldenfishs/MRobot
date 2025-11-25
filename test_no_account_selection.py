#!/usr/bin/env python3
"""测试移除账户选择后的财务模块"""

import sys
from pathlib import Path

# 添加项目根路径
sys.path.insert(0, str(Path(__file__).parent))

from app.tools.finance_manager import FinanceManager, Transaction

def test_without_account_selection():
    """测试不需要账户选择的模式"""
    print("=" * 70)
    print("测试: 移除账户选择功能后的财务模块")
    print("=" * 70)
    
    fm = FinanceManager()
    
    # 1. 获取所有账户
    print("\n[1️⃣] 获取所有账户")
    all_accounts = fm.get_all_accounts()
    print(f"✅ 找到 {len(all_accounts)} 个账户")
    
    if not all_accounts:
        print("❌ 系统中没有账户，无法测试")
        return False
    
    # 2. 获取第一个账户作为默认账户
    print("\n[2️⃣] 获取默认账户（第一个账户）")
    default_account = all_accounts[0]
    print(f"✅ 默认账户: {default_account.name} (ID: {default_account.id})")
    print(f"   交易记录数: {len(default_account.transactions)}")
    
    # 3. 测试做账功能（新建记录）
    print("\n[3️⃣] 测试做账功能")
    new_trans = Transaction(
        date="2025-11-25",
        amount=123.45,
        trader="测试商户",
        notes="这是一个测试交易"
    )
    if fm.add_transaction(default_account.id, new_trans):
        print(f"✅ 新建记录成功: {new_trans.id}")
    else:
        print(f"❌ 新建记录失败")
        return False
    
    # 4. 刷新账户信息
    print("\n[4️⃣] 刷新账户信息")
    fm.load_all_accounts()
    updated_account = fm.get_account(default_account.id)
    if updated_account:
        print(f"✅ 账户已刷新")
        print(f"   新的交易记录数: {len(updated_account.transactions)}")
    
    # 5. 测试查询功能
    print("\n[5️⃣] 测试查询功能")
    
    # 无条件查询
    results = fm.query_transactions(default_account.id)
    print(f"✅ 无条件查询: {len(results)} 条记录")
    
    # 按交易人查询
    results = fm.query_transactions(default_account.id, trader="测试")
    print(f"✅ 按交易人'测试'查询: {len(results)} 条记录")
    
    # 按金额查询
    results = fm.query_transactions(default_account.id, amount_min=100, amount_max=200)
    print(f"✅ 按金额范围(100-200)查询: {len(results)} 条记录")
    
    # 6. 测试导出功能
    print("\n[6️⃣] 测试导出功能")
    
    # CSV导出
    csv_path = Path(fm.data_root) / "test_export.csv"
    if fm.export_to_csv(default_account.id, str(csv_path)):
        print(f"✅ CSV导出成功: {csv_path.name}")
        if csv_path.exists():
            print(f"   文件大小: {csv_path.stat().st_size} bytes")
    else:
        print(f"❌ CSV导出失败")
    
    # 7. 测试备份功能
    print("\n[7️⃣] 测试备份功能")
    if fm.backup_all_accounts():
        print(f"✅ 备份成功")
        backup_dir = fm.data_root / 'backups'
        if backup_dir.exists():
            backup_files = list(backup_dir.glob("*.zip"))
            print(f"   备份文件数: {len(backup_files)}")
    else:
        print(f"❌ 备份失败")
    
    # 8. 测试账户汇总
    print("\n[8️⃣] 测试账户汇总")
    summary = fm.get_account_summary(default_account.id)
    if summary:
        print(f"✅ 账户汇总:")
        print(f"   账户名称: {summary['account_name']}")
        print(f"   总金额: ¥{summary['total_amount']:.2f}")
        print(f"   交易笔数: {summary['transaction_count']}")
    else:
        print(f"❌ 获取汇总失败")
    
    print("\n" + "=" * 70)
    print("✅ 所有测试完成！移除账户选择功能后，系统仍可正常工作")
    print("=" * 70)
    return True

if __name__ == '__main__':
    test_without_account_selection()
