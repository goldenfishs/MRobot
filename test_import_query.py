#!/usr/bin/env python3
"""测试导入账户后查询功能"""

import sys
import os
from pathlib import Path
import json
import shutil

# 添加项目根路径
sys.path.insert(0, str(Path(__file__).parent))

from app.tools.finance_manager import FinanceManager

def test_import_and_query():
    """测试导入和查询流程"""
    fm = FinanceManager()
    
    print("=" * 70)
    print("测试: 导入账户后查询数据")
    print("=" * 70)
    
    # 1. 获取现有账户
    print("\n[步骤1] 获取现有账户")
    all_accounts = fm.get_all_accounts()
    print(f"当前有 {len(all_accounts)} 个账户")
    
    if all_accounts:
        # 找到有数据的账户
        test_account = None
        for account in all_accounts:
            if account.transactions:
                test_account = account
                break
        
        if test_account:
            print(f"\n✅ 找到有数据的测试账户: '{test_account.name}'")
            print(f"   账户ID: {test_account.id}")
            print(f"   交易数: {len(test_account.transactions)}")
            
            # 2. 创建ZIP压缩包进行模拟导出/导入
            print("\n[步骤2] 导出账户为ZIP包")
            export_dir = Path(fm.data_root) / "temp_export"
            export_dir.mkdir(exist_ok=True)
            
            success = fm.export_account_package(test_account.id, str(export_dir))
            if success:
                print(f"✅ 导出成功")
                
                # 找到生成的ZIP文件
                zip_files = list(export_dir.glob("*.zip"))
                if zip_files:
                    zip_file = zip_files[0]
                    print(f"   ZIP文件: {zip_file.name}")
                    print(f"   文件大小: {zip_file.stat().st_size} bytes")
                    
                    # 3. 导入账户
                    print("\n[步骤3] 导入账户")
                    imported_id = fm.import_account_package(str(zip_file))
                    if imported_id:
                        print(f"✅ 导入成功")
                        print(f"   新账户ID: {imported_id}")
                        
                        # 4. 验证导入的账户
                        print("\n[步骤4] 验证导入的账户")
                        imported_account = fm.get_account(imported_id)
                        if imported_account:
                            print(f"✅ 导入的账户信息:")
                            print(f"   名称: {imported_account.name}")
                            print(f"   交易数: {len(imported_account.transactions)}")
                            
                            # 5. 测试查询导入的账户
                            print("\n[步骤5] 测试查询导入的账户")
                            
                            # 无条件查询
                            results = fm.query_transactions(imported_id)
                            print(f"✅ 无条件查询: {len(results)} 条记录")
                            
                            if results:
                                print(f"\n   查询结果样本:")
                                for i, trans in enumerate(results[:3], 1):
                                    print(f"   [{i}] {trans.date} | {trans.trader} | ¥{trans.amount:.2f}")
                            
                            # 按交易人查询
                            if imported_account.transactions:
                                trader_name = imported_account.transactions[0].trader
                                results = fm.query_transactions(imported_id, trader=trader_name)
                                print(f"\n✅ 按交易人'{trader_name}'查询: {len(results)} 条记录")
                        else:
                            print(f"❌ 无法获取导入的账户")
                    else:
                        print(f"❌ 导入失败")
                    
                    # 清理临时文件
                    print("\n[步骤6] 清理临时文件")
                    shutil.rmtree(export_dir)
                    print("✅ 临时文件已清理")
            else:
                print(f"❌ 导出失败")
        else:
            print(f"❌ 没有找到有数据的账户用于测试")
            print(f"   现有账户:")
            for account in all_accounts:
                print(f"   - {account.name}: {len(account.transactions)} 条交易")
    else:
        print(f"❌ 系统中没有账户")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)

if __name__ == '__main__':
    test_import_and_query()
