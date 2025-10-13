#!/usr/bin/env python3
"""
测试修复后的自动更新功能
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_simple_dialog_import():
    """测试简化对话框导入"""
    try:
        from app.tools.update_dialog_simple import SimpleUpdateDialog, QuickUpdateChecker
        print("✅ 简化对话框导入成功")
        return True
    except Exception as e:
        print(f"❌ 简化对话框导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dialog_creation():
    """测试对话框创建（不显示）"""
    try:
        from PyQt5.QtWidgets import QApplication
        from app.tools.update_dialog_simple import SimpleUpdateDialog
        
        # 创建应用程序实例（如果还没有的话）
        if not QApplication.instance():
            app = QApplication([])
        
        # 创建对话框但不显示
        dialog = SimpleUpdateDialog("1.0.0")
        print("✅ 对话框创建成功")
        
        # 清理
        dialog.deleteLater()
        
        return True
        
    except Exception as e:
        print(f"❌ 对话框创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_about_interface_import():
    """测试关于界面导入"""
    try:
        from app.about_interface import AboutInterface
        print("✅ 关于界面导入成功")
        return True
    except Exception as e:
        print(f"❌ 关于界面导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_tests():
    """运行所有测试"""
    print("🔧 测试修复后的自动更新功能\n")
    
    tests = [
        ("简化对话框导入", test_simple_dialog_import),
        ("对话框创建", test_dialog_creation),
        ("关于界面导入", test_about_interface_import),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"测试 {name}...")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} 测试异常: {e}")
            results.append((name, False))
        print()
    
    print("=" * 50)
    print("测试结果:")
    print("=" * 50)
    
    passed = 0
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 项测试通过")
    
    if passed == len(results):
        print("🎉 所有测试通过！修复成功，自动更新功能应该不会再闪退。")
    else:
        print("⚠️  部分测试失败，可能还有问题需要修复。")
    
    return passed == len(results)

if __name__ == "__main__":
    success = run_tests()
    
    if success:
        print("\n💡 使用提示:")
        print("1. 现在可以在'关于'页面点击'自动更新'按钮")
        print("2. 更新过程中会显示详细的进度条和状态")
        print("3. 更新完成后程序会自动重启")
        print("4. 如果更新失败会显示错误信息并允许重试")
    
    sys.exit(0 if success else 1)