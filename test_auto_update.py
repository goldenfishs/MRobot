#!/usr/bin/env python3
"""
自动更新功能测试脚本
用于测试自动更新功能的各个组件
"""

import sys
import os

# 添加项目路径到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_update_check():
    """测试更新检查功能"""
    print("测试更新检查功能...")
    
    try:
        from app.tools.auto_updater import check_update_availability
        
        current_version = "1.0.0"  # 使用一个较低的版本号来测试
        result = check_update_availability(current_version)
        
        if result:
            print(f"✅ 发现新版本: {result['version']}")
            print(f"   下载链接: {result['download_url']}")
            print(f"   文件名: {result['asset_name']}")
            return True
        else:
            print("ℹ️  当前已是最新版本")
            return True
            
    except Exception as e:
        print(f"❌ 更新检查失败: {e}")
        return False

def test_updater_creation():
    """测试更新器创建"""
    print("\n测试更新器创建...")
    
    try:
        from app.tools.auto_updater import AutoUpdater
        
        updater = AutoUpdater("1.0.0")
        print(f"✅ 更新器创建成功")
        print(f"   应用目录: {updater.app_dir}")
        print(f"   是否打包: {updater.is_frozen}")
        return True
        
    except Exception as e:
        print(f"❌ 更新器创建失败: {e}")
        return False

def test_dialog_import():
    """测试对话框导入"""
    print("\n测试对话框导入...")
    
    try:
        from app.tools.update_dialog import UpdateDialog, QuickUpdateChecker
        print("✅ 更新对话框模块导入成功")
        return True
        
    except Exception as e:
        print(f"❌ 更新对话框导入失败: {e}")
        return False

def test_config_import():
    """测试配置导入"""
    print("\n测试配置导入...")
    
    try:
        from app.tools import update_config
        print("✅ 更新配置模块导入成功")
        print(f"   自动更新启用: {update_config.AUTO_UPDATE_ENABLED}")
        print(f"   GitHub仓库: {update_config.GITHUB_REPO}")
        return True
        
    except Exception as e:
        print(f"❌ 更新配置导入失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始自动更新功能测试\n")
    
    tests = [
        ("配置导入", test_config_import),
        ("更新器创建", test_updater_creation), 
        ("对话框导入", test_dialog_import),
        ("更新检查", test_update_check),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name}测试出现异常: {e}")
            results.append((name, False))
    
    print("\n" + "="*50)
    print("测试结果总结:")
    print("="*50)
    
    passed = 0
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 项测试通过")
    
    if passed == len(results):
        print("🎉 所有测试通过！自动更新功能可以正常使用。")
    else:
        print("⚠️  部分测试失败，请检查相关模块。")
    
    return passed == len(results)

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)