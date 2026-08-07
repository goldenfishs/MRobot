# MRobot package manifest v1

每个可发布包是独立仓库，仓库根目录必须有 `mrobot-package.yaml`。该文件既可写 YAML，也可写 JSON；JSON 本身是合法 YAML，并能让无第三方依赖的 MCode 启动。

```json
{
  "$schema": "https://raw.githubusercontent.com/goldenfishs/MCode/main/schemas/package.schema.json",
  "schema_version": 1,
  "package": {
    "id": "mrobot.device.bmi088",
    "name": "BMI088",
    "type": "device",
    "version": "0.1.0",
    "description": "BMI088 IMU driver"
  },
  "dependencies": [
    { "id": "mrobot.component.user-math", "version": "^0.1.0" }
  ],
  "requires": ["bsp.spi", "bsp.gpio"],
  "provides": ["device.imu.bmi088"],
  "files": [
    { "source": "src/bmi088.c", "destination": "User/MRobot/packages/bmi088/bmi088.c", "policy": "generated" },
    { "source": "include/bmi088.h", "destination": "User/MRobot/packages/bmi088/bmi088.h", "policy": "generated" },
    { "source": "templates/bmi088_config.h", "destination": "User/MRobot/config/bmi088_config.h", "policy": "scaffold" }
  ]
}
```

包通过 `requires` 声明能力，通过 `provides` 暴露能力。能力名称描述语义，例如 `bsp.spi`，不能是 `../../bsp/spi.h` 一类文件路径。

官方索引位于 `goldenfishs/mrobot-registry`。MCode 支持搜索、SemVer 约束、递归依赖/能力提供者安装、项目级缓存和 lockfile：

```bash
mcode package search imu
mcode package install mrobot.device.bmi088@^0.2.0 --project .
mcode package remove mrobot.device.bmi088 --project .
```
