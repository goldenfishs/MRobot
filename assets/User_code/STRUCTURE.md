# User_code 目录结构说明

## 新的文件夹结构

所有外设、组件和设备的文件现在都存放在独立的子文件夹中，便于管理和维护。

### BSP (板级支持包)
```
bsp/
├── bsp.h                 # BSP 总头文件
├── describe.csv          # 外设描述文件
├── .gitkeep
├── can/
│   ├── can.c
│   └── can.h
├── fdcan/
│   ├── fdcan.c
│   └── fdcan.h
├── uart/
│   ├── uart.c
│   └── uart.h
├── spi/
│   ├── spi.c
│   └── spi.h
├── i2c/
│   ├── i2c.c
│   └── i2c.h
├── gpio/
│   ├── gpio.c
│   └── gpio.h
├── pwm/
│   ├── pwm.c
│   └── pwm.h
├── time/
│   ├── time.c
│   └── time.h
├── dwt/
│   ├── dwt.c
│   └── dwt.h
└── mm/
    ├── mm.c
    └── mm.h
```

### Component (组件)
```
component/
├── describe.csv          # 组件描述文件
├── dependencies.csv      # 组件依赖关系
├── .gitkeep
├── ahrs/
├── capacity/
├── cmd/
├── crc16/
├── crc8/
├── error_detect/
├── filter/
├── freertos_cli/
├── limiter/
├── mixer/
├── pid/
├── ui/
└── user_math/
```

### Device (设备)
```
device/
├── device.h              # Device 总头文件
├── config.yaml           # 设备配置文件
├── .gitkeep
├── bmi088/
├── buzzer/
├── dm_imu/
├── dr16/
├── ist8310/
├── led/
├── motor/
├── motor_dm/
├── motor_lk/
├── motor_lz/
├── motor_odrive/
├── motor_rm/
├── motor_vesc/
├── oid/
├── ops9/
├── rc_can/
├── servo/
├── vofa/
├── ws2812/
└── lcd_driver/          # LCD 驱动（原有结构）
```

## 代码生成逻辑

代码生成器会：
1. 首先尝试从子文件夹加载模板（如 `bsp/can/can.c`）
2. 如果子文件夹不存在，回退到根目录加载（向后兼容）
3. 生成时将文件展开到项目的扁平目录结构中（如 `User/bsp/can.c`）

## 优势

✅ **更好的组织**: 每个外设/组件的文件都在独立文件夹中
✅ **便于管理**: 添加、删除、修改模板更加方便
✅ **向后兼容**: 现有的扁平结构仍然可以正常工作
✅ **清晰的结构**: 一目了然地看到所有可用的外设/组件

## 迁移说明

如果你添加新的外设/组件/设备：
1. 在对应目录下创建新的子文件夹（小写命名）
2. 将 .c 和 .h 文件放入子文件夹
3. 代码生成器会自动识别并使用
