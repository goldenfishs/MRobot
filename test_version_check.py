#!/usr/bin/env python3
"""
测试版本检查逻辑
"""

from packaging.version import parse as vparse

def test_version_comparison():
    """测试版本比较"""
    current_version = "1.0.2"
    
    # 测试不同的版本情况
    test_versions = ["1.0.1", "1.0.2", "1.0.3", "1.0.5", "1.1.0", "2.0.0"]
    
    print(f"当前版本: {current_version}")
    print("-" * 40)
    
    for version in test_versions:
        is_newer = vparse(version) > vparse(current_version)
        status = "有更新" if is_newer else "无更新"
        print(f"版本 {version}: {status}")


def simulate_check_update(local_version, remote_version):
    """模拟更新检查"""
    print(f"\n模拟检查: 本地版本 {local_version} vs 远程版本 {remote_version}")
    
    if vparse(remote_version) > vparse(local_version):
        print("✓ 发现新版本")
        return remote_version
    else:
        print("✗ 已是最新版本")
        return None


if __name__ == "__main__":
    test_version_comparison()
    
    # 模拟你遇到的情况
    print("\n" + "="*50)
    print("模拟实际情况:")
    simulate_check_update("1.0.2", "1.0.5")
    simulate_check_update("1.0.2", "1.0.2")
    simulate_check_update("1.0.2", "1.0.1")