# Flash BSP 自动配置说明

## 功能特性

Flash BSP模块能够自动识别STM32芯片型号并生成对应的Flash配置代码。

### 支持的芯片系列

#### STM32F1 系列
- 使用**Page**组织方式（而非Sector）
- 自动检测Flash容量（16KB - 1MB）
- 小/中容量设备：1KB/页
- 大容量/互联型设备：2KB/页

#### STM32F4 系列
- 使用**Sector**组织方式
- 自动检测Flash容量（256KB/512KB/1MB/2MB）
- 自动配置单Bank或双Bank模式
- 不同大小的Sector（16KB/64KB/128KB）

#### STM32H7 系列
- 使用**Sector**组织方式
- 每个Sector固定128KB
- 自动检测Flash容量（128KB/1MB/2MB）
- 自动配置单Bank或双Bank模式

### Flash容量识别规则

根据STM32命名规则中的第9位字符识别Flash容量：

**STM32F1系列:**
- **4**: 16KB (16 pages × 1KB)
- **6**: 32KB (32 pages × 1KB)
- **8**: 64KB (64 pages × 1KB)
- **B**: 128KB (128 pages × 1KB)
- **C**: 256KB (128 pages × 2KB)
- **D**: 384KB (192 pages × 2KB)
- **E**: 512KB (256 pages × 2KB)
- **F**: 768KB (384 pages × 2KB, 互联型)
- **G**: 1MB (512 pages × 2KB, 互联型)

**STM32F4系列:**
- **C**: 256KB (单Bank, Sector 0-7)
- **E**: 512KB (单Bank, Sector 0-9)
- **G**: 1MB (单Bank, Sector 0-11)
- **I**: 2MB (双Bank, Sector 0-23)

**STM32H7系列:**
- **B**: 128KB (1个Sector, 单Bank)
- **G**: 1MB (8个Sector, 单Bank)
- **I**: 2MB (16个Sector, 双Bank)

例如：
- `STM32F103C8T6` → 64KB Flash (64 pages × 1KB)
- `STM32F103RCT6` → 256KB Flash (128 pages × 2KB)
- `STM32F103ZET6` → 512KB Flash (256 pages × 2KB)
- `STM32F407VGT6` → 1MB Flash (Sector 0-11)
- `STM32F407IGH6` → 2MB Flash (Sector 0-23, 双Bank)
- `STM32F405RGT6` → 1MB Flash (Sector 0-11)
- `STM32H743VIT6` → 2MB Flash (16 sectors × 128KB, 双Bank)
- `STM32H750VBT6` → 128KB Flash (1 sector × 128KB)

## Flash布局

### STM32F1 Page模式 (16KB - 1MB)
```
小/中容量 (≤128KB): 每页1KB
  Page 0:  0x08000000 - 0x080003FF (1KB)
  Page 1:  0x08000400 - 0x080007FF (1KB)
  ...

大容量/互联型 (>128KB): 每页2KB
  Page 0:  0x08000000 - 0x080007FF (2KB)
  Page 1:  0x08000800 - 0x08000FFF (2KB)
  ...
```

### STM32F4 单Bank模式 (256KB - 1MB)
```
Sector 0-3:  16KB  each  (0x08000000 - 0x0800FFFF)
Sector 4:    64KB        (0x08010000 - 0x0801FFFF)
Sector 5-11: 128KB each  (0x08020000 - 0x080FFFFF)
```

### STM32F4 双Bank模式 (2MB)
```
Bank 1:
  Sector 0-3:  16KB  each  (0x08000000 - 0x0800FFFF)
  Sector 4:    64KB        (0x08010000 - 0x0801FFFF)
  Sector 5-11: 128KB each  (0x08020000 - 0x080FFFFF)

Bank 2:
  Sector 12-15: 16KB  each  (0x08100000 - 0x0810FFFF)
  Sector 16:    64KB        (0x08110000 - 0x0811FFFF)
  Sector 17-23: 128KB each  (0x08120000 - 0x081FFFFF)
```

### STM32H7 Sector模式
```
单Bank (1MB):
  Sector 0-7: 128KB each (0x08000000 - 0x080FFFFF)

双Bank (2MB):
  Bank 1:
    Sector 0-7:  128KB each (0x08000000 - 0x080FFFFF)
  Bank 2:
    Sector 8-15: 128KB each (0x08100000 - 0x081FFFFF)
```

## 使用方法

### 1. 在BSP配置界面启用Flash
在代码生成界面的BSP标签中，勾选"生成 Flash 代码"选项。

### 2. 自动检测
系统会自动：
- 读取项目中的`.ioc`文件
- 提取MCU型号信息
- 计算Flash扇区配置
- 生成对应的宏定义

### 3. 生成的代码示例

**STM32F1系列** (以STM32F103RCT6为例 - 256KB):
```c
// flash.h
#define ADDR_FLASH_PAGE_0 ((uint32_t)0x08000000)
/* Base address of Page 0, 2 Kbytes */
#define ADDR_FLASH_PAGE_1 ((uint32_t)0x08000800)
/* Base address of Page 1, 2 Kbytes */
...
#define ADDR_FLASH_PAGE_127 ((uint32_t)0x0803F800)
/* Base address of Page 127, 2 Kbytes */
#define ADDR_FLASH_END ((uint32_t)0x08040000)

// flash.c
#define BSP_FLASH_MAX_PAGE 127
if (page >= 0 && page <= 127) {
  // 擦除代码...
}
```

**STM32F4系列** (以STM32F407IGH6为例 - 2MB):
```c
// flash.h
#define ADDR_FLASH_SECTOR_0 ((uint32_t)0x08000000)
/* Base address of Sector 0, 16 Kbytes */
...
#define ADDR_FLASH_SECTOR_23 ((uint32_t)0x081E0000)
/* Base address of Sector 23, 128 Kbytes */

#define ADDR_FLASH_END ((uint32_t)0x08200000)
/* End address for flash */
```

**flash.c**:
```c
#define BSP_FLASH_MAX_SECTOR 23

void BSP_Flash_EraseSector(uint32_t sector) {
  if (sector > 0 && sector <= 23) {
    // 擦除代码...
  }
}
```

**STM32H7系列** (以STM32H743VIT6为例 - 2MB):
```c
// flash.h
#define ADDR_FLASH_SECTOR_0 ((uint32_t)0x08000000)
/* Base address of Sector 0, 128 Kbytes */
...
#define ADDR_FLASH_SECTOR_15 ((uint32_t)0x081E0000)
/* Base address of Sector 15, 128 Kbytes */

#define ADDR_FLASH_END ((uint32_t)0x08200000)

// flash.c
#define BSP_FLASH_MAX_SECTOR 15
if (sector > 0 && sector <= 15) {
  // 擦除代码...
}
```

## API接口

### BSP_Flash_EraseSector (F4/H7) / BSP_Flash_ErasePage (F1)
擦除指定扇区或页
```c
// F4/H7系列
void BSP_Flash_EraseSector(uint32_t sector);
// F1系列
void BSP_Flash_ErasePage(uint32_t page);
```
- **参数**: 
  - sector/page - 扇区号或页号
  - F1: 0 到 (页数-1)
  - F4: 0-11 或 0-23（根据芯片型号）
  - H7: 0-7 或 0-15（根据芯片型号）

### BSP_Flash_WriteBytes
写入数据到Flash
```c
void BSP_Flash_WriteBytes(uint32_t address, const uint8_t *buf, size_t len);
```
- **参数**: 
  - address - Flash地址
  - buf - 数据缓冲区
  - len - 数据长度

### BSP_Flash_ReadBytes
从Flash读取数据
```c
void BSP_Flash_ReadBytes(uint32_t address, void *buf, size_t len);
```
- **参数**: 
  - address - Flash地址
  - buf - 接收缓冲区
  - len - 读取长度

## 使用示例

### STM32F1系列示例
```c
#include "bsp/flash.h"

void save_config_f1(void) {
    // 擦除Page 127 (最后一页，通常用于存储用户数据)
    BSP_Flash_ErasePage(127);
    
    // 写入配置数据
    uint8_t config[100] = {/* 配置数据 */};
    BSP_Flash_WriteBytes(ADDR_FLASH_PAGE_127, config, sizeof(config));
}

void load_config_f1(void) {
    // 读取配置数据
    uint8_t config[100];
    BSP_Flash_ReadBytes(ADDR_FLASH_PAGE_127, config, sizeof(config));
}
```

### STM32F4系列示例
```c
#include "bsp/flash.h"

void save_config_f4(void) {
    // 擦除Sector 11 (通常用于存储用户数据)
    BSP_Flash_EraseSector(11);
    
    // 写入配置数据
    uint8_t config[100] = {/* 配置数据 */};
    BSP_Flash_WriteBytes(ADDR_FLASH_SECTOR_11, config, sizeof(config));
}

void load_config_f4(void) {
    // 读取配置数据
    uint8_t config[100];
    BSP_Flash_ReadBytes(ADDR_FLASH_SECTOR_11, config, sizeof(config));
}
```

### STM32H7系列示例

### STM32H7系列示例
```c
#include "bsp/flash.h"

void save_config(void) {
    // 擦除Sector 11 (通常用于存储用户数据)
    BSP_Flash_EraseSector(11);
    
    // 写入配置数据
    uint8_t config[100] = {/* 配置数据 */};
    BSP_Flash_WriteBytes(ADDR_FLASH_SECTOR_11, config, sizeof(config));
}

void load_config(void) {
    // 读取配置数据
    uint8_t config[100];
    BSP_Flash_ReadBytes(ADDR_FLASH_SECTOR_11, config, sizeof(config));
}
```

## 注意事项

1. **擦除时间**: Flash擦除需要一定时间，注意不要在中断中执行
   - F1 Page擦除: ~20ms
   - F4 Sector擦除: 16KB~100ms, 64KB~300ms, 128KB~500ms
   - H7 Sector擦除: ~200ms
2. **写入前擦除**: 
   - F1: 必须先擦除整页才能写入
   - F4/H7: 必须先擦除整个扇区才能写入
3. **区域选择**: 避免擦除包含程序代码的扇区/页
   - F1: 通常最后几页用于存储数据
   - F4: Sector 11 或 23 常用于存储数据
   - H7: Sector 7 或 15 常用于存储数据
4. **写入对齐**: 建议按字节写入，HAL库会处理对齐
5. **断电保护**: 写入过程中断电可能导致数据丢失
6. **擦写次数限制**: 
   - F1: 典型10,000次
   - F4/H7: 典型10,000-100,000次

## 配置文件

配置信息保存在 `bsp_config.yaml`:

**STM32F1:**
```yaml
flash:
  enabled: true
  mcu_name: STM32F103RCT6
  dual_bank: false
  sectors: 128  # 实际是128个页
  type: page
  page_size: 2
```

**STM32F4:**
```yaml
flash:
  enabled: true
  mcu_name: STM32F407IGHx
  dual_bank: true
  sectors: 24
  type: sector
```

**STM32H7:**
```yaml
flash:
  enabled: true
  mcu_name: STM32H743VIT6
  dual_bank: true
  sectors: 16
  type: sector
```

## 扩展支持

当前支持的系列：
- ✅ STM32F1 (Page模式)
- ✅ STM32F4 (Sector模式)
- ✅ STM32H7 (Sector模式)

如需支持其他STM32系列（如F2/F3/L4/G4等），可在 `analyzing_ioc.py` 的 `get_flash_config_from_mcu()` 函数中添加相应的配置规则。
