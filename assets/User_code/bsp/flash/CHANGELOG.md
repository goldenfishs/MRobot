# Flash BSP 更新日志

## v2.0 - 2026-01-01

### 新增功能
✨ **多系列MCU支持**
- 新增 STM32F1 系列支持（Page模式）
- 新增 STM32H7 系列支持（Sector模式）
- 保持 STM32F4 系列支持（Sector模式）

### STM32F1系列详情
- **Flash组织**: Page模式（页）
- **页大小**: 
  - 小/中容量（≤128KB）: 1KB/页
  - 大容量/互联型（>128KB）: 2KB/页
- **容量支持**: 16KB - 1MB
- **容量代码**: 4/6/8/B/C/D/E/F/G
- **生成宏**: `ADDR_FLASH_PAGE_X`

### STM32H7系列详情
- **Flash组织**: Sector模式（扇区）
- **扇区大小**: 固定128KB
- **容量支持**: 128KB - 2MB
- **容量代码**: B/G/I
- **Bank支持**: 
  - 单Bank: 1MB (8个Sector)
  - 双Bank: 2MB (16个Sector)
- **生成宏**: `ADDR_FLASH_SECTOR_X`

### 技术改进
- 重构 `get_flash_config_from_mcu()` 函数为多系列架构
- 新增 `_get_stm32f1_flash_config()` - F1系列专用配置
- 新增 `_get_stm32f4_flash_config()` - F4系列专用配置  
- 新增 `_get_stm32h7_flash_config()` - H7系列专用配置
- 配置中新增 `type` 字段区分 'page' 和 'sector' 模式
- 界面自动识别并显示Page或Sector模式
- 代码生成支持Page和Sector两种宏定义

### 示例支持的芯片型号
**STM32F1:**
- STM32F103C8T6 → 64KB (64 pages × 1KB)
- STM32F103RCT6 → 256KB (128 pages × 2KB)
- STM32F103ZET6 → 512KB (256 pages × 2KB)

**STM32F4:**
- STM32F407VGT6 → 1MB (Sector 0-11)
- STM32F407IGH6 → 2MB (Sector 0-23, 双Bank)
- STM32F405RGT6 → 1MB (Sector 0-11)

**STM32H7:**
- STM32H750VBT6 → 128KB (1 sector)
- STM32H743VGT6 → 1MB (8 sectors)
- STM32H743VIT6 → 2MB (16 sectors, 双Bank)

### 配置文件变化
```yaml
# 新增字段
flash:
  type: page  # 或 sector
  page_size: 2  # 仅F1系列有此字段
```

### 文档更新
- 更新 README.md 包含三个系列的完整说明
- 新增各系列的Flash布局图
- 新增各系列的使用示例
- 更新注意事项包含擦除时间和寿命信息

---

## v1.0 - 初始版本

### 初始功能
- STM32F4 系列支持
- 自动识别芯片型号
- 单Bank/双Bank配置
- 基础API（擦除、读、写）
