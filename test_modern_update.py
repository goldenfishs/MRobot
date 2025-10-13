#!/usr/bin/env python3
"""
测试现代化QFluentWidgets自动更新对话框
展示完整的Fluent Design风格界面
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt

def test_modern_dialog():
    """测试现代化更新对话框"""
    from qfluentwidgets import setThemeColor, Theme, setTheme, PrimaryPushButton, BodyLabel
    from app.tools.modern_update_dialog import ModernUpdateDialog
    
    app = QApplication(sys.argv)
    
    # 设置主题
    setThemeColor('#f18cb9')
    setTheme(Theme.AUTO)
    
    # 创建测试窗口
    window = QWidget()
    window.setWindowTitle("现代化更新对话框测试")
    window.setFixedSize(400, 300)
    
    layout = QVBoxLayout(window)
    layout.setSpacing(20)
    layout.setContentsMargins(40, 40, 40, 40)
    
    # 标题
    title = BodyLabel("MRobot 现代化更新测试")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title.setStyleSheet("font-size: 18px; font-weight: bold;")
    layout.addWidget(title)
    
    # 说明
    info = BodyLabel("点击下方按钮测试基于QFluentWidgets的现代化更新界面")
    info.setAlignment(Qt.AlignmentFlag.AlignCenter)
    info.setWordWrap(True)
    layout.addWidget(info)
    
    # 测试按钮
    test_btn = PrimaryPushButton("打开更新对话框")
    test_btn.clicked.connect(lambda: show_update_dialog(window))
    layout.addWidget(test_btn)
    
    layout.addStretch()
    
    def show_update_dialog(parent):
        dialog = ModernUpdateDialog("1.0.0", parent)  # 使用低版本触发更新
        dialog.exec_()
    
    window.show()
    sys.exit(app.exec_())

def test_components():
    """测试组件导入"""
    tests = [
        ("现代化对话框", lambda: __import__('app.tools.modern_update_dialog')),
        ("Fluent组件", lambda: __import__('app.tools.fluent_components')),
        ("自动更新器", lambda: __import__('app.tools.auto_updater')),
    ]
    
    print("🧪 测试组件导入...")
    print("-" * 40)
    
    for name, test_func in tests:
        try:
            test_func()
            print(f"✅ {name}: 导入成功")
        except Exception as e:
            print(f"❌ {name}: 导入失败 - {e}")
    
    print("-" * 40)
    print("测试完成！")

def test_qfluentwidgets():
    """测试QFluentWidgets组件"""
    try:
        from qfluentwidgets import (
            Dialog, CardWidget, PrimaryPushButton, ProgressBar,
            SubtitleLabel, BodyLabel, InfoBar, FluentIcon,
            ElevatedCardWidget, SimpleCardWidget, HeaderCardWidget,
            TransparentToolButton, ProgressRing, PillPushButton
        )
        print("✅ QFluentWidgets高级组件导入成功")
        return True
    except Exception as e:
        print(f"❌ QFluentWidgets组件导入失败: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="现代化更新对话框测试")
    parser.add_argument("--mode", choices=["dialog", "components", "qfw"], 
                       default="components", help="测试模式")
    
    args = parser.parse_args()
    
    print("🚀 现代化自动更新对话框测试")
    print("=" * 50)
    
    if args.mode == "dialog":
        print("启动图形界面测试...")
        test_modern_dialog()
    elif args.mode == "components":
        test_components()
    elif args.mode == "qfw":
        test_qfluentwidgets()