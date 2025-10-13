#!/usr/bin/env python3
"""
自动更新功能演示
展示如何使用自动更新功能的完整示例
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt

def demo_auto_update():
    """演示自动更新功能"""
    from app.tools.update_dialog import UpdateDialog
    
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = QWidget()
    window.setWindowTitle("自动更新演示")
    window.setFixedSize(300, 200)
    
    layout = QVBoxLayout(window)
    
    # 标题
    title = QLabel("MRobot 自动更新演示")
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 20px;")
    layout.addWidget(title)
    
    # 当前版本显示
    version_label = QLabel("当前版本: v1.0.0")
    version_label.setAlignment(Qt.AlignCenter)
    layout.addWidget(version_label)
    
    # 更新按钮
    update_btn = QPushButton("检查并更新")
    update_btn.clicked.connect(lambda: show_update_dialog(window))
    layout.addWidget(update_btn)
    
    # 说明
    info_label = QLabel("点击按钮体验自动更新功能")
    info_label.setAlignment(Qt.AlignCenter)
    info_label.setStyleSheet("color: gray; font-size: 12px;")
    layout.addWidget(info_label)
    
    window.show()
    
    def show_update_dialog(parent):
        """显示更新对话框"""
        dialog = UpdateDialog("1.0.0", parent)
        dialog.exec_()
    
    sys.exit(app.exec_())

def demo_quick_check():
    """演示快速更新检查"""
    from app.tools.update_dialog import QuickUpdateChecker
    
    print("演示快速更新检查功能...")
    
    # 检查更新但不显示对话框
    result = QuickUpdateChecker.check_and_notify("1.0.0", None, auto_show_dialog=False)
    
    if result:
        print("✅ 发现更新并显示了通知")
    else:
        print("ℹ️  当前已是最新版本或检查失败")

def demo_api_usage():
    """演示API使用方法"""
    from app.tools.auto_updater import check_update_availability
    
    print("\n演示API使用方法...")
    
    # 检查更新
    current_version = "1.0.0"
    update_info = check_update_availability(current_version)
    
    if update_info:
        print("📦 发现新版本！")
        print(f"   版本号: {update_info['version']}")
        print(f"   下载链接: {update_info['download_url']}")
        print(f"   文件名: {update_info['asset_name']}")
        print(f"   发布日期: {update_info['release_date']}")
        print(f"   更新说明: {update_info['release_notes'][:100]}...")
    else:
        print("ℹ️  当前已是最新版本")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MRobot 自动更新功能演示")
    parser.add_argument("--mode", choices=["ui", "quick", "api"], default="ui",
                       help="演示模式: ui=图形界面, quick=快速检查, api=API演示")
    
    args = parser.parse_args()
    
    print("🚀 MRobot 自动更新功能演示")
    print("="*40)
    
    if args.mode == "ui":
        print("启动图形界面演示...")
        demo_auto_update()
    elif args.mode == "quick":
        demo_quick_check()
    elif args.mode == "api":
        demo_api_usage()
    
    print("\n演示完成！")