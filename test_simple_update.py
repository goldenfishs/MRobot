#!/usr/bin/env python3
"""
测试简化的自动更新对话框
确保稳定性和兼容性
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_simple_dialog():
    """测试简化对话框"""
    from PyQt5.QtWidgets import QApplication
    from qfluentwidgets import setThemeColor, Theme, setTheme
    from app.tools.simple_update_dialog import SimpleUpdateDialog
    
    app = QApplication(sys.argv)
    
    # 设置主题
    setThemeColor('#f18cb9')
    setTheme(Theme.AUTO)
    
    # 创建对话框
    dialog = SimpleUpdateDialog("1.0.0")  # 使用较低版本触发更新
    dialog.show()
    
    sys.exit(app.exec_())

def test_imports():
    """测试导入"""
    try:
        from app.tools.simple_update_dialog import SimpleUpdateDialog, QuickNotifier
        print("✅ 简化更新对话框导入成功")
        
        from app.tools.auto_updater import AutoUpdater, check_update_availability
        print("✅ 自动更新器导入成功")
        
        from qfluentwidgets import (
            CardWidget, PrimaryPushButton, ProgressBar,
            SubtitleLabel, BodyLabel, InfoBar, FluentIcon
        )
        print("✅ QFluentWidgets基础组件导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_update_check():
    """测试更新检查"""
    try:
        from app.tools.auto_updater import check_update_availability
        
        result = check_update_availability("1.0.0")
        if result:
            print(f"✅ 检测到更新: v{result['version']}")
        else:
            print("ℹ️  当前已是最新版本")
        
        return True
        
    except Exception as e:
        print(f"❌ 更新检查失败: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="简化更新对话框测试")
    parser.add_argument("--mode", choices=["dialog", "imports", "check"], 
                       default="imports", help="测试模式")
    
    args = parser.parse_args()
    
    print("🧪 简化自动更新对话框测试")
    print("=" * 40)
    
    if args.mode == "dialog":
        print("启动对话框测试...")
        test_simple_dialog()
    elif args.mode == "imports":
        test_imports()
    elif args.mode == "check":
        test_update_check()
    
    print("测试完成！")