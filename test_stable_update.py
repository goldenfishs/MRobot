#!/usr/bin/env python3
"""
测试稳定的更新对话框
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_stable_imports():
    """测试稳定组件导入"""
    try:
        from app.tools.simple_update_components import (
            SimpleUpdateStatusCard, SimpleVersionCard, SimpleActionButtons
        )
        print("✅ 简化组件导入成功")
        
        from app.tools.stable_update_dialog import StableUpdateDialog, SimpleUpdateNotifier
        print("✅ 稳定对话框导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_stable_dialog():
    """测试稳定对话框"""
    from PyQt5.QtWidgets import QApplication
    from qfluentwidgets import setThemeColor, Theme, setTheme
    from app.tools.stable_update_dialog import StableUpdateDialog
    
    app = QApplication(sys.argv)
    
    # 设置主题
    setThemeColor('#f18cb9')
    setTheme(Theme.AUTO)
    
    # 创建对话框
    dialog = StableUpdateDialog("1.0.0")  # 使用较低版本来触发更新
    
    # 显示对话框
    dialog.show()
    
    sys.exit(app.exec_())

def test_about_interface():
    """测试关于页面集成"""
    try:
        from app.about_interface import AboutInterface
        print("✅ 关于页面导入成功")
        return True
    except Exception as e:
        print(f"❌ 关于页面导入失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("🧪 测试稳定的更新功能\n")
    
    tests = [
        ("稳定组件导入", test_stable_imports),
        ("关于页面集成", test_about_interface),
    ]
    
    passed = 0
    for name, test_func in tests:
        try:
            if test_func():
                print(f"✅ {name}: 通过")
                passed += 1
            else:
                print(f"❌ {name}: 失败")
        except Exception as e:
            print(f"❌ {name}: 异常 - {e}")
    
    print(f"\n📊 测试结果: {passed}/{len(tests)} 通过")
    return passed == len(tests)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="测试稳定更新对话框")
    parser.add_argument("--mode", choices=["test", "dialog"], 
                       default="test", help="运行模式")
    
    args = parser.parse_args()
    
    if args.mode == "test":
        success = run_all_tests()
        sys.exit(0 if success else 1)
    elif args.mode == "dialog":
        test_stable_dialog()