@echo off
chcp 65001 > nul
echo ==========================================
echo   MRobot 打包脚本
echo ==========================================
echo.

REM 清理旧的构建文件
echo 1. 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist MRobot.spec del /f /q MRobot.spec

REM 使用 PyInstaller 打包（onedir 模式）
echo.
echo 2. 使用 PyInstaller 打包...
pyinstaller MRobot.py --onedir --windowed --icon=assets\logo\M.ico --name=MRobot --clean

if %errorlevel% neq 0 (
    echo.
    echo ❌ PyInstaller 打包失败！
    pause
    exit /b 1
)

echo.
echo 3. 检查打包结果...
if not exist "dist\MRobot" (
    echo ❌ 未找到 dist\MRobot 目录！
    pause
    exit /b 1
)

if not exist "dist\MRobot\MRobot.exe" (
    echo ❌ 未找到 MRobot.exe！
    pause
    exit /b 1
)

echo.
echo ✅ PyInstaller 打包完成！
echo.
echo 4. 下一步：
echo    - 如果要创建安装程序，请运行 Inno Setup 编译 MRobot.iss
echo    - 或者直接使用 dist\MRobot 文件夹中的程序
echo.
echo ==========================================
echo   打包完成
echo ==========================================
echo.
pause
