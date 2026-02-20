# MRobot

<div align="center">
  <img src="assets/logo/MRobot.png" height="80" alt="MRobot Logo">
  
  **更加高效快捷的机器人开发工具**
  
  诞生于 Robocon 和 Robomaster，但绝不仅限于此
  
  <p>
    <a href="https://github.com/goldenfishs/MRobot/blob/master/LICENSE">
      <img src="https://img.shields.io/github/license/goldenfishs/MRobot.svg" alt="License">
    </a>
    <a href="https://github.com/goldenfishs/MRobot">
      <img src="https://img.shields.io/github/repo-size/goldenfishs/MRobot.svg" alt="Repo Size">
    </a>
    <a href="https://github.com/goldenfishs/MRobot/commits/master">
      <img src="https://img.shields.io/github/last-commit/goldenfishs/MRobot.svg" alt="Last Commit">
    </a>
    <img src="https://img.shields.io/badge/language-Python-blue.svg" alt="Language">
    <img src="https://img.shields.io/badge/PyQt-6.x-green.svg" alt="PyQt">
    <img src="https://img.shields.io/badge/STM32-supported-orange.svg" alt="STM32">
  </p>
</div>

---

## 📖 简介

提起嵌入式开发，大多数开发者都会感到每次繁琐的配置和查阅各种文档的枯燥。对于小型项目，创建优雅的架构又比较费时。有没有办法快速完成基础环境搭建后直接开始写逻辑代码呢？

这就是 **MRobot** —— 一个功能完善的机器人工程辅助平台，通过可视化界面简化嵌入式开发流程，帮助开发者高效管理代码、配置和资源，让开发更专注于核心逻辑。

### ✨ 核心优势

- 🚀 **快速开发**: 自动化代码生成，从.ioc配置直接生成完整代码框架
- 🎯 **模块化设计**: 清晰的分层架构，支持高度模块化和可扩展性
- 🛡️ **用户代码保护**: 智能识别并保留用户自定义代码区域
- 🎨 **现代化界面**: 基于QFluentWidgets的现代化UI设计
- 📦 **丰富的组件库**: 内置大量常用的BSP、组件、设备驱动和功能模块

---

## 🌟 主要特性

### 💻 代码生成系统
- **智能配置解析**: 自动解析STM32CubeMX的.ioc文件，提取硬件配置信息
- **模板驱动生成**: 基于模板的代码生成机制，支持自定义模板
- **依赖关系管理**: 自动处理组件和设备之间的依赖关系
- **用户代码保留**: 使用`/* USER ... BEGIN */ ... /* USER ... END */`标记保护用户代码
- **分层代码生成**: 支持BSP→Component→Device→Module的完整代码生成流程

### 🎨 界面功能
- **代码生成**: 可视化配置界面，快速生成项目代码
- **数据管理**: 数据可视化和分析工具
- **财务管理**: 项目财务管理功能
- **AI辅助**: 集成AI接口，提供智能辅助
- **机械设计**: 零件库管理、批量导出等工具
- **函数拟合**: 数据拟合和分析工具
- **小工具集合**: 实用的小型工具集
- **串口终端**: 串口通信和调试工具
- **零件库**: 机械零件库管理

### 🔧 硬件支持
- **MCU系列**: STM32F1、STM32F4、STM32H7系列
- **RTOS**: FreeRTOS完整支持
- **外设接口**:
  - CAN/FDCAN 总线通信
  - UART/USART 串口通信
  - I2C/SPI 通信接口
  - GPIO 数字输入输出
  - PWM 脉宽调制输出
  - Flash 存储读写
  - DWT 高精度计时

### 📦 组件库

#### BSP层（板级支持包）
- `can`: CAN/FDCAN总线驱动
- `gpio`: GPIO驱动（支持中断回调）
- `uart`: UART/USART驱动（支持DMA和多种回调）
- `i2c`: I2C通信驱动
- `spi`: SPI通信驱动
- `pwm`: PWM输出驱动
- `dwt`: DWT计时器
- `mm`: 内存管理
- `time`: 时间管理
- `flash`: Flash读写驱动

#### Component层（通用组件）
- `pid`: PID控制器（支持多种模式）
- `filter`: 滤波器库
- `kalman_filter`: 卡尔曼滤波
- `ahrs`: 姿态解算算法
- `mixer`: 混合控制器
- `limiter`: 限幅器
- `capacity`: 容量计算
- `crc8/crc16`: 循环冗余校验
- `error_detect`: 错误检测
- `cmd`: 命令处理
- `freertos_cli`: FreeRTOS命令行接口
- `ui`: UI组件
- `user_math`: 数学工具库

#### Device层（设备驱动）
- **电机驱动**:
  - `motor_rm`: RoboMaster电机（M2006, M3508, GM6020）
  - `motor_dm`: 大疆电机
  - `motor_lk`: 雷克电机
  - `motor_lz`: 雷智电机
  - `motor_vesc`: VESC电机
  - `motor_odrive`: ODrive电机
- **传感器**:
  - `bmi088`: BMI088 IMU
  - `ist8310`: IST8310磁力计
  - `dm_imu`: 大疆IMU
- **通信**:
  - `dr16`: DR16遥控器接收
  - `rc_can`: CAN遥控
  - `vofa`: VOFA+通信协议
- **执行器**:
  - `servo`: 舵机控制
  - `buzzer`: 蜂鸣器
  - `led`: LED灯控制
  - `ws2812`: WS2812灯带控制
- **其他**:
  - `ops9`: OPS9设备
  - `oid`: OID识别
  - `lcd_driver`: LCD显示驱动
  - `mrobot`: MRobot专用设备

#### Module层（功能模块）
- `config`: 配置管理
- `cmd`: 命令处理模块
- `gimbal`: 云台控制模块
- `shoot`: 发射机构控制模块

---

## 🏗️ 项目架构

### 系统架构图

```
MRobot
├── 应用层
│   ├── 主界面
│   ├── 代码生成界面
│   ├── 数据管理界面
│   ├── 财务管理界面
│   └── 工具集界面
├── 工具层
│   ├── 代码生成器
│   ├── IOC解析器
│   ├── 配置管理器
│   └── 更新管理器
├── 资源层
│   ├── 用户代码库
│   ├── 配置文件
│   └── 资源文件
└── 配置层
    └── 应用配置
```

### 用户代码架构

```
User_code/
├── BSP层 (板级支持包)
│   ├── 硬件抽象接口
│   └── 外设驱动
├── Component层 (通用组件)
│   ├── 算法库
│   └── 工具函数
├── Device层 (设备驱动)
│   ├── 传感器驱动
│   ├── 执行器驱动
│   └── 通信设备驱动
├── Module层 (功能模块)
│   ├── 业务逻辑
│   └── 功能集成
└── Task层 (任务模板)
    └── 任务框架
```

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.8 或更高版本
- **操作系统**: Windows / macOS / Linux
- **依赖库**: 
  - PyQt6
  - QFluentWidgets
  - PyYAML
  - PyInstaller（用于打包）
  

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/goldenfishs/MRobot.git
cd MRobot
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行程序**
```bash
python MRobot.py
```

### 构建可执行文件


使用PyInstaller将程序打包为单个可执行文件：

```bash
pyinstaller MRobot.py --onefile --windowed --add-data "assets/logo;assets/logo" --add-data "app;app" --add-data "app/tools;app/tools"
```
```

构建完成后，可执行文件位于 `dist/MRobot.exe`。

---

## 📖 使用指南

### 代码生成流程

1. **准备.ioc文件**
   - 使用STM32CubeMX配置硬件
   - 保存.ioc文件到`assets/User_code/ioc/`目录

2. **配置代码生成**
   - 打开代码生成界面
   - 选择.ioc文件
   - 配置BSP、Component、Device、Module

3. **生成代码**
   - 点击生成按钮
   - 系统自动解析.ioc配置
   - 生成完整的代码框架

4. **导出代码**
   - 将生成的代码导出到目标项目
   - 开始编写业务逻辑

### 用户代码保护

在生成的代码中，使用以下标记来保护您的自定义代码：

```c
/* USER INCLUDE BEGIN */
// 您的自定义头文件
#include "my_custom_header.h"
/* USER INCLUDE END */

/* USER CODE BEGIN */
// 您的自定义代码
void my_custom_function(void) {
    // 您的代码逻辑
}
/* USER CODE END */
```

当重新生成代码时，这些区域内的内容将被保留。

### 配置文件说明

- **config.csv**: 组件和设备配置列表
- **device/config.yaml**: 设备详细配置
- **bsp/describe.csv**: BSP描述信息
- **component/describe.csv**: 组件描述信息
- **component/dependencies.csv**: 组件依赖关系
- **module/describe.csv**: 模块描述信息

---

## 🎯 应用案例

### Robomaster
- 全向轮步兵机器人
- 英雄机器人
- 哨兵机器人

### Robocon
- 各类竞赛机器人项目

### 其他应用
- 教育机器人
- 科研项目原型
- 个人DIY项目

---

## 🔬 技术细节

### 代码生成原理

1. **配置解析**: `analyzing_ioc.py`解析.ioc文件，提取硬件配置
2. **模板处理**: `code_generator.py`加载模板并执行替换
3. **依赖处理**: 根据依赖关系自动添加必要的文件
4. **代码保护**: 使用正则表达式识别并保留用户代码区域

### 支持的MCU系列

| 系列 | 示例型号 | Flash | RAM | 特性 |
|------|---------|-------|-----|------|
| STM32F1 | STM32F103C8T6 | 64KB | 20KB | Cortex-M3 |
| STM32F4 | STM32F407IGHx | 1MB | 192KB | Cortex-M4, FPU |
| STM32H7 | STM32H723VGT6 | 1MB | 1MB | Cortex-M7, 双精度FPU |

### 外设配置示例

#### CAN配置
- 支持标准CAN和FDCAN
- 自动识别CAN总线和波特率
- 支持多CAN总线管理

#### UART配置
- 支持DMA传输
- 多种回调类型（发送完成、接收完成、空闲检测等）
- 自动处理中断向量表

#### GPIO配置
- 支持输入、输出、外部中断模式
- 自动生成中断回调函数
- 支持多个GPIO实例

---

## 🛠️ 开发指南

### 添加新的BSP驱动

1. 在`assets/User_code/bsp/`创建新目录
2. 实现驱动代码（.c和.h文件）
3. 在`bsp/describe.csv`添加描述
4. 在`config.csv`注册新BSP

### 添加新的组件

1. 在`assets/User_code/component/`创建新目录
2. 实现组件代码
3. 在`component/describe.csv`添加描述
4. 在`component/dependencies.csv`声明依赖
5. 在`config.csv`注册新组件

### 添加新的设备驱动

1. 在`assets/User_code/device/`创建新目录
2. 实现设备驱动
3. 在`device/config.yaml`添加配置
4. 在`config.csv`注册新设备

### 自定义模板

1. 创建模板文件，使用`/* MARKER */`标记替换位置
2. 在代码生成器中注册模板路径
3. 定义替换规则

---

## 📝 配置说明

### 应用配置

位于`config/config.json`:

```json
{
    "QFluentWidgets": {
        "ThemeColor": "#fff18cb9",
        "ThemeMode": "Dark"
    }
}
```

### IOC配置

将STM32CubeMX生成的.ioc文件放置在`assets/User_code/ioc/`目录。

### 设备配置

位于`assets/User_code/device/config.yaml`，使用YAML格式定义设备参数。

---

## 🤝 贡献指南

我们欢迎任何形式的贡献！

### 如何贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 贡献类型

- 🐛 Bug修复
- ✨ 新功能
- 📝 文档改进
- 🎨 代码优化
- ⚡ 性能提升
- ✅ 测试用例

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- **PyQt6**: 用于构建现代化GUI界面
- **QFluentWidgets**: 提供现代化的UI组件
- **STM32CubeMX**: 硬件配置工具
- **FreeRTOS**: 实时操作系统
- **RoboMaster社区**: 提供的技术支持和灵感

---

## 📮 联系方式

- **项目主页**: [https://github.com/goldenfishs/MRobot](https://github.com/goldenfishs/MRobot)
- **问题反馈**: [GitHub Issues](https://github.com/goldenfishs/MRobot/issues)
- **讨论区**: [GitHub Discussions](https://github.com/goldenfishs/MRobot/discussions)

---

## 📊 项目统计

<div align="center">
  <img src="https://img.shields.io/badge/code_style-pep8-blue.svg" alt="Code Style">
  <img src="https://img.shields.io/badge/version-v1.0.0-green.svg" alt="Version">
</div>

---

<div align="center">
  <p>
    <b>Made with ❤️ by the MRobot Team</b>
  </p>
  <p>
    让机器人开发更简单、更高效
  </p>
</div>