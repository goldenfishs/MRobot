#!/usr/bin/env python3
"""
测试修复后的更新功能
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_dialog_creation():
    """测试对话框创建"""
    print("测试对话框创建...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv if len(sys.argv) > 1 else ['test'])
        
        from app.tools.update_dialog import UpdateDialog
        
        # 创建对话框（但不显示）
        dialog = UpdateDialog("1.0.0")
        print("✅ 对话框创建成功")
        
        # 测试基本方法
        dialog.check_for_updates()
        print("✅ 检查更新功能正常")
        
        # 清理
        dialog.close()
        app.quit()
        
        return True
        
    except Exception as e:
        print(f"❌ 对话框测试失败: {e}")
        return False

def test_imports():
    """测试导入"""
    print("测试模块导入...")
    
    try:
        from app.tools.update_dialog import UpdateDialog, QuickUpdateChecker
        from app.tools.auto_updater import AutoUpdater, check_update_availability
        print("✅ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 测试修复后的更新功能\n")
    
    tests = [
        ("模块导入", test_imports),
        ("对话框创建", test_dialog_creation),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"🔍 {name}...")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name}异常: {e}")
            results.append((name, False))
        print()
    
    print("="*40)
    print("测试结果:")
    passed = 0
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 项测试通过")
    
    if passed == len(results):
        print("🎉 修复成功！可以运行主程序了。")
    else:
        print("⚠️  仍有问题需要解决。")

if __name__ == "__main__":
    main()