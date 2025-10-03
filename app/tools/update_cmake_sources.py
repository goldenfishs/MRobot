#!/usr/bin/env python3
"""
自动更新CMakeLists.txt中的User源文件列表
这个脚本会扫描User目录下的所有.c文件，并自动更新CMakeLists.txt中的target_sources部分
"""

import os
import re
from pathlib import Path

def find_user_c_files(user_dir):
    """查找User目录下的所有.c文件"""
    c_files = []
    user_path = Path(user_dir)
    
    if not user_path.exists():
        print(f"错误: User目录不存在: {user_dir}")
        return []
    
    # 递归查找所有.c文件
    for c_file in user_path.rglob("*.c"):
        # 获取相对于项目根目录的路径
        relative_path = c_file.relative_to(user_path.parent)
        # 使用正斜杠确保跨平台兼容性，避免转义字符问题
        c_files.append(str(relative_path).replace('\\', '/'))
    
    # 按目录和文件名排序
    c_files.sort()
    return c_files

def update_cmake_sources(cmake_file, c_files):
    """更新CMakeLists.txt中的源文件列表"""
    if not os.path.exists(cmake_file):
        print(f"错误: CMakeLists.txt文件不存在: {cmake_file}")
        return False
    
    # 读取CMakeLists.txt内容
    with open(cmake_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 构建新的源文件列表
    sources_section = "# Add sources to executable\ntarget_sources(${CMAKE_PROJECT_NAME} PRIVATE\n"
    sources_section += "    # Add user sources here\n"
    
    # 按目录分组
    current_dir = ""
    for c_file in c_files:
        # 确保路径使用正斜杠，避免转义字符问题
        normalized_file = c_file.replace('\\', '/')
        file_dir = str(Path(normalized_file).parent).replace('\\', '/')
        if file_dir != current_dir:
            if current_dir:  # 不是第一个目录，添加空行
                sources_section += "\n"
            sources_section += f"    # {file_dir} sources\n"
            current_dir = file_dir
        
        sources_section += f"    {normalized_file}\n"
    
    sources_section += ")"
    
    # 使用原始字符串避免转义问题，并使用更精确的正则表达式
    pattern = r'# Add sources to executable\s*\ntarget_sources\(\$\{CMAKE_PROJECT_NAME\}\s+PRIVATE\s*\n(?:.*?\n)*?\)'
    
    try:
        if re.search(pattern, content, re.DOTALL | re.MULTILINE):
            new_content = re.sub(pattern, sources_section, content, flags=re.DOTALL | re.MULTILINE)
            
            # 写回文件
            with open(cmake_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ 成功更新CMakeLists.txt中的源文件列表")
            return True
        else:
            print("❌ 错误: 在CMakeLists.txt中找不到target_sources部分")
            return False
    except re.error as e:
        print(f"❌ 正则表达式错误: {e}")
        return False
    
def update_cmake_includes(cmake_file, user_dir):
    """确保CMakeLists.txt中的include路径包含User"""
    if not os.path.exists(cmake_file):
        print(f"错误: CMakeLists.txt文件不存在: {cmake_file}")
        return False

    with open(cmake_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 构建新的include部分
    include_section = (
        "# Add include paths\n"
        "target_include_directories(${CMAKE_PROJECT_NAME} PRIVATE\n"
        "    # Add user defined include paths\n"
        "    User\n"
        ")"
    )

    # 使用更安全的正则表达式匹配include部分
    pattern = r'# Add include paths\s*\ntarget_include_directories\(\$\{CMAKE_PROJECT_NAME\}\s+PRIVATE\s*\n(?:.*?\n)*?\)'
    try:
        if re.search(pattern, content, re.DOTALL | re.MULTILINE):
            new_content = re.sub(pattern, include_section, content, flags=re.DOTALL | re.MULTILINE)
            with open(cmake_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("✅ 成功更新CMakeLists.txt中的include路径")
            return True
        else:
            print("❌ 错误: 在CMakeLists.txt中找不到target_include_directories部分")
            return False
    except re.error as e:
        print(f"❌ 正则表达式错误: {e}")
        return False

def main():
    """主函数"""
    script_dir = Path(__file__).parent
    project_root = script_dir
    
    user_dir = project_root / "User"
    cmake_file = project_root / "CMakeLists.txt"
    
    print("🔍 正在扫描User目录下的.c文件...")
    c_files = find_user_c_files(user_dir)
    
    if not c_files:
        print("⚠️  警告: 在User目录下没有找到.c文件")
        return
    
    print(f"📁 找到 {len(c_files)} 个.c文件:")
    for c_file in c_files:
        print(f"   - {c_file}")
    
    print(f"\n📝 正在更新 {cmake_file}...")
    success = update_cmake_sources(cmake_file, c_files)
    
    if success:
        print("🎉 更新完成！现在可以重新编译项目了。")
    else:
        print("💥 更新失败，请检查错误信息。")

if __name__ == "__main__":
    main()