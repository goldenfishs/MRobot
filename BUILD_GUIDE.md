# MRobot 打包说明

## 问题原因

之前使用 `--onefile` 模式和 `--add-data` 添加 assets 导致的问题：
1. `--onefile` 将所有文件打包进 exe，运行时解压到临时目录 `sys._MEIPASS`
2. 更新代码时下载到 `exe目录/assets`
3. 但读取时从 `sys._MEIPASS/assets` 读取（每次都是打包时的原始文件）
4. 结果：更新成功但读不到新文件

## 解决方案：使用 `--onedir` 模式

### 方法一：使用提供的脚本（推荐）

**macOS/Linux:**
```bash
./build.sh
```

**Windows:**
```cmd
build.bat
```

### 方法二：手动执行命令

```bash
# 清理旧文件
rm -rf build dist *.spec

# 打包（不要添加 --add-data）
pyinstaller MRobot.py \
    --onedir \
    --windowed \
    --icon=assets/logo/M.ico \
    --name=MRobot \
    --clean
```

### 创建安装程序

打包完成后，使用 Inno Setup 编译 `MRobot.iss` 创建安装程序。

## 打包模式对比

### `--onedir` 模式（推荐）✅
- **优点：**
  - assets 文件夹在 exe 同级目录，可以被更新覆盖
  - 更新代码库后能正确读取新文件
  - 文件结构清晰，便于调试
- **缺点：**
  - 需要分发整个文件夹（但可以用 Inno Setup 打包成单个安装程序）

### `--onefile` 模式（不推荐）❌
- **优点：**
  - 单个 exe 文件
- **缺点：**
  - 外部资源文件无法更新（因为每次都从 exe 内部解压）
  - 启动较慢（需要解压）
  - 不适合需要更新资源的应用

## 文件结构

### 打包后（onedir 模式）
```
dist/MRobot/
├── MRobot.exe          # 主程序
├── _internal/          # PyInstaller 依赖库
└── assets/             # 由 Inno Setup 安装时复制
    ├── logo/
    ├── User_code/
    └── mech_lib/
```

### 安装后
```
%APPDATA%\MRobot\       # 或 {userappdata}\MRobot
├── MRobot.exe
├── _internal/
└── assets/             # 可以被更新覆盖
    ├── logo/
    ├── User_code/      # 👈 更新代码库会更新这里
    └── mech_lib/
```

## 工作原理

1. **首次运行：**
   - 代码检测到 `exe目录/assets` 不存在
   - 从 `sys._MEIPASS/assets` 复制初始资源（如果存在）
   - 但在 onedir 模式下，Inno Setup 已经安装了 assets，所以直接使用

2. **更新代码库：**
   - 下载最新代码到 `exe目录/assets/User_code`
   - 清除缓存
   - 重新读取 `exe目录/assets/User_code`（能看到新模块如 oid）

3. **重新打开软件：**
   - 直接读取 `exe目录/assets`（包含更新后的文件）

## 注意事项

1. **不要使用 `--add-data "assets;assets"`**
   - 这会将 assets 打包进 exe，导致无法更新

2. **Inno Setup 负责安装 assets**
   - ISS 文件会将 assets 复制到安装目录
   - 这样 assets 就在 exe 同级目录，可以被更新

3. **代码已经优化**
   - `CodeGenerator.get_assets_dir()` 优先使用 `exe目录/assets`
   - 更新和读取使用相同路径
   - 首次运行时自动初始化（如果需要）

## 测试步骤

1. 运行 `build.bat` 或 `build.sh` 打包
2. 使用 Inno Setup 编译 `MRobot.iss` 创建安装程序
3. 安装并运行 MRobot
4. 点击"选择项目路径"，选择一个 CubeMX 项目
5. 点击"更新代码库"
6. 检查是否能看到新的模块（如 oid）
7. 关闭软件，重新打开
8. 再次进入项目，确认新模块仍然存在

## 版本更新

修改 `MRobot.iss` 中的版本号：
```ini
AppVersion=1.0.9  ; 更新这里
```
