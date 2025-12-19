#!/bin/bash

# MRobot 打包脚本
# 使用方法: chmod +x build.sh && ./build.sh

echo "=========================================="
echo "  MRobot 打包脚本"
echo "=========================================="
echo ""

# 清理旧的构建文件
echo "1. 清理旧的构建文件..."
rm -rf build dist *.spec

# 使用 PyInstaller 打包（onedir 模式）
echo ""
echo "2. 使用 PyInstaller 打包..."
pyinstaller MRobot.py \
    --onedir \
    --windowed \
    --icon=assets/logo/M.ico \
    --name=MRobot \
    --clean

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ PyInstaller 打包失败！"
    exit 1
fi

echo ""
echo "3. 检查打包结果..."
if [ ! -d "dist/MRobot" ]; then
    echo "❌ 未找到 dist/MRobot 目录！"
    exit 1
fi

if [ ! -f "dist/MRobot/MRobot.exe" ]; then
    echo "❌ 未找到 MRobot.exe！"
    exit 1
fi

echo ""
echo "✅ PyInstaller 打包完成！"
echo ""
echo "4. 下一步："
echo "   - 如果要创建安装程序，请运行 Inno Setup 编译 MRobot.iss"
echo "   - 或者直接使用 dist/MRobot 文件夹中的程序"
echo ""
echo "=========================================="
echo "  打包完成"
echo "=========================================="
