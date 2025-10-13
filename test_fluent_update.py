#!/usr/bin/env python3
"""
测试基于QFluentWidgets的自动更新对话框
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

def test_fluent_update_dialog():
    """测试Fluent风格更新对话框"""
    from qfluentwidgets import setThemeColor, Theme, setTheme
    from app.tools.fluent_update_dialog import FluentUpdateDialog
    
    app = QApplication(sys.argv)
    
    # 设置主题
    setThemeColor('#f18cb9')
    setTheme(Theme.AUTO)
    
    # 创建对话框
    dialog = FluentUpdateDialog("1.0.0")  # 使用较低版本来触发更新
    
    # 显示对话框
    dialog.show()
    
    sys.exit(app.exec_())

def test_import():
    """测试导入"""
    try:
        from app.tools.fluent_update_dialog import FluentUpdateDialog, QuickUpdateNotification
        print("✅ Fluent更新对话框导入成功")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_components():
    """测试组件"""
    try:
        from qfluentwidgets import (
            CardWidget, PrimaryPushButton, ProgressBar, 
            SubtitleLabel, BodyLabel, InfoBar, FluentIcon
        )
        print("✅ QFluentWidgets组件导入成功")
        return True
    except Exception as e:
        print(f"❌ QFluentWidgets组件导入失败: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="测试Fluent风格更新对话框")
    parser.add_argument("--mode", choices=["import", "components", "dialog"], 
                       default="import", help="测试模式")
    
    args = parser.parse_args()
    
    if args.mode == "import":
        test_import()
    elif args.mode == "components":
        test_components()
    elif args.mode == "dialog":
        test_fluent_update_dialog()