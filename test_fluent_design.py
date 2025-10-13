#!/usr/bin/env python3
"""
测试基于Fluent Design的现代化更新对话框
完全遵循qfluentwidgets设计规范，支持明暗主题
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt

def test_fluent_dialog():
    """测试Fluent Design更新对话框"""
    from qfluentwidgets import (
        setThemeColor, Theme, setTheme, 
        PrimaryPushButton, PushButton, BodyLabel, SubtitleLabel,
        CardWidget, VBoxLayout, HBoxLayout, isDarkTheme
    )
    from app.tools.fluent_design_update import FluentUpdateDialog
    
    app = QApplication(sys.argv)
    
    # 设置主题
    setThemeColor('#f18cb9')
    setTheme(Theme.AUTO)
    
    # 创建测试窗口
    window = QWidget()
    window.setWindowTitle("Fluent Design 更新对话框测试")
    window.setFixedSize(500, 400)
    
    # 应用主题样式
    if isDarkTheme():
        window.setStyleSheet("background-color: #202020; color: white;")
    else:
        window.setStyleSheet("background-color: #FAFAFA; color: black;")
    
    layout = VBoxLayout(window)
    layout.setContentsMargins(40, 40, 40, 40)
    layout.setSpacing(24)
    
    # 创建测试卡片
    test_card = CardWidget()
    test_card.setFixedHeight(280)
    
    card_layout = VBoxLayout(test_card)
    card_layout.setContentsMargins(32, 24, 32, 24)
    card_layout.setSpacing(20)
    
    # 标题
    title = SubtitleLabel("MRobot 现代化更新测试")
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    card_layout.addWidget(title)
    
    # 说明
    info = BodyLabel("这是基于QFluentWidgets设计系统的现代化自动更新界面测试。\n\n"
                    "新界面特点：\n"
                    "• 完全遵循Fluent Design规范\n"
                    "• 自动适应明暗主题\n"
                    "• 流畅的动画效果\n"
                    "• 现代化的卡片设计\n"
                    "• 清晰的视觉层次")
    info.setWordWrap(True)
    card_layout.addWidget(info)
    
    # 主题切换提示
    theme_info = BodyLabel(f"当前主题: {'暗色模式' if isDarkTheme() else '亮色模式'}")
    theme_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
    card_layout.addWidget(theme_info)
    
    layout.addWidget(test_card)
    
    # 按钮区域
    btn_layout = HBoxLayout()
    
    test_btn = PrimaryPushButton("测试更新对话框")
    test_btn.clicked.connect(lambda: show_update_dialog(window))
    
    theme_btn = PushButton("切换主题")
    theme_btn.clicked.connect(lambda: toggle_theme_and_refresh(window, theme_info))
    
    btn_layout.addWidget(theme_btn)
    btn_layout.addStretch()
    btn_layout.addWidget(test_btn)
    
    layout.addLayout(btn_layout)
    
    def show_update_dialog(parent):
        """显示更新对话框"""
        dialog = FluentUpdateDialog("1.0.0", parent)  # 使用低版本触发更新
        dialog.exec_()
    
    def toggle_theme_and_refresh(window, label):
        """切换主题并刷新"""
        from qfluentwidgets import toggleTheme, isDarkTheme
        toggleTheme()
        
        # 更新窗口样式
        if isDarkTheme():
            window.setStyleSheet("background-color: #202020; color: white;")
            label.setText("当前主题: 暗色模式")
        else:
            window.setStyleSheet("background-color: #FAFAFA; color: black;")
            label.setText("当前主题: 亮色模式")
    
    window.show()
    sys.exit(app.exec_())

def test_components():
    """测试组件导入"""
    tests = [
        ("Fluent Design更新对话框", lambda: __import__('app.tools.fluent_design_update')),
        ("qfluentwidgets组件", test_qfluentwidgets_components),
        ("自动更新器", lambda: __import__('app.tools.auto_updater')),
    ]
    
    print("🎨 测试Fluent Design组件...")
    print("-" * 50)
    
    for name, test_func in tests:
        try:
            test_func()
            print(f"✅ {name}: 导入成功")
        except Exception as e:
            print(f"❌ {name}: 导入失败 - {e}")
    
    print("-" * 50)
    print("测试完成！")

def test_qfluentwidgets_components():
    """测试qfluentwidgets组件"""
    from qfluentwidgets import (
        Dialog, CardWidget, SimpleCardWidget, ElevatedCardWidget,
        PrimaryPushButton, PushButton, TransparentPushButton,
        ProgressBar, ProgressRing, IndeterminateProgressBar,
        SubtitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel, DisplayLabel,
        FluentIcon, InfoBar, ScrollArea, VBoxLayout, HBoxLayout,
        setTheme, Theme, isDarkTheme, toggleTheme
    )
    return True

def test_theme_switching():
    """测试主题切换"""
    from qfluentwidgets import setTheme, Theme, isDarkTheme, toggleTheme
    
    print("🌓 测试主题切换...")
    
    # 测试设置主题
    setTheme(Theme.LIGHT)
    print(f"设置亮色主题 - 当前是否暗色: {isDarkTheme()}")
    
    setTheme(Theme.DARK)
    print(f"设置暗色主题 - 当前是否暗色: {isDarkTheme()}")
    
    setTheme(Theme.AUTO)
    print(f"设置自动主题 - 当前是否暗色: {isDarkTheme()}")
    
    print("主题切换测试完成！")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fluent Design更新对话框测试")
    parser.add_argument("--mode", choices=["dialog", "components", "theme"], 
                       default="components", help="测试模式")
    
    args = parser.parse_args()
    
    print("🎨 Fluent Design 现代化更新对话框测试")
    print("=" * 60)
    
    if args.mode == "dialog":
        print("启动图形界面测试...")
        test_fluent_dialog()
    elif args.mode == "components":
        test_components()
    elif args.mode == "theme":
        test_theme_switching()