#!/usr/bin/env python3
"""
检查GitHub Releases API响应结构
"""

import requests
import json

def check_releases_structure():
    """检查GitHub releases的API响应结构"""
    try:
        url = "https://api.github.com/repos/goldenfishs/MRobot/releases/latest"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print("Release信息:")
            print(f"标签: {data.get('tag_name')}")
            print(f"名称: {data.get('name')}")
            print(f"发布时间: {data.get('published_at')}")
            print(f"是否为预发布: {data.get('prerelease')}")
            print(f"是否为草稿: {data.get('draft')}")
            
            print("\n可用的资源文件:")
            assets = data.get('assets', [])
            
            if not assets:
                print("❌ 没有找到任何资源文件")
                print("建议在GitHub Release中上传安装包文件")
            else:
                for i, asset in enumerate(assets):
                    print(f"  {i+1}. {asset['name']}")
                    print(f"     大小: {asset['size']} 字节")
                    print(f"     下载链接: {asset['browser_download_url']}")
                    print(f"     内容类型: {asset.get('content_type', 'unknown')}")
                    print()
            
            print(f"\n更新说明:\n{data.get('body', '无')}")
            
        else:
            print(f"❌ API请求失败，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    check_releases_structure()