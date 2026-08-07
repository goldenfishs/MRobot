# MRobot / MCode 可持续架构

## 命名与职责

- **MRobot**：组织名、嵌入式框架名和整个生态的品牌。
- **MCode**：无界面的工程分析、包解析、代码生成和验证引擎。
- **mrobot-mcode**：Python 发布包名；导入名和命令统一为 `mcode`。
- GUI、CLI、VS Code 插件和 MCP/AI 工具都是前端，不拥有业务规则。

第一阶段只承诺 STM32CubeMX 工程。其他 MCU 平台必须通过 platform pack 接入，不能在 UI 中增加条件分支。

## 单一生成流水线

```mermaid
flowchart LR
    IOC["STM32CubeMX .ioc"] --> Parser["STM32CubeMXParser"]
    Parser --> Model["ProjectModel"]
    Config["mrobot.yaml"] --> Resolver["PackageResolver"]
    Model --> Resolver
    Resolver --> Plan["GenerationPlan"]
    Model --> Plan
    Plan --> Apply["Atomic apply"]
    Apply --> State[".mrobot/generated-state.json"]
    Apply --> Lock["mrobot.lock"]
    Model --> GUI
    Model --> CLI
    Model --> VSCode["VS Code extension"]
    Model --> MCP["MCP / AI"]
```

所有前端调用 `MCodeService.inspect/plan/generate/validate`。CLI 的 `--json` 是跨进程前端的首个稳定协议；以后可在不改变模型的前提下增加本地服务或 MCP 包装。

## BSP 分层

1. CubeMX/HAL：供应商生成层，由 CubeMX 管理。
2. `platform-stm32`：STM32 通用适配、家族差异和 CubeMX 能力映射。
3. `board-*`：板卡引脚、时钟、供电和板载器件定义。
4. `bsp-*`：CAN/UART/SPI/GPIO/PWM 等稳定抽象。
5. device/component/algorithm/module/task：只依赖能力或其他包，不依赖 GUI 目录。

芯片型号不对应一份复制的 BSP。芯片家族差异属于 platform pack，板卡差异属于 board pack，具体外设实例由 `.ioc` 和项目配置绑定。

## 文件所有权

| 策略 | 行为 | 适用内容 |
|---|---|---|
| `generated` | MCode 可重复生成；哈希不匹配则报冲突 | glue、注册表、CMake 清单、模型快照 |
| `scaffold` | 仅首次创建，之后完全归用户 | 业务任务、用户回调、应用入口 |
| CubeMX user sections | 仅作为旧工程兼容机制 | CubeMX 自有文件中的极少量接入代码 |

包源码视为不可变输入。实例配置和 glue 输出到 `User/MRobot/generated`，业务代码不再混入生成模板。生成先计划、后原子写入；失败回滚，绝不静默覆盖用户修改。

`mrobot.lock` 固定 MCU、`.ioc` 内容哈希以及包版本/内容哈希，适合进入版本控制；`.mrobot/generated-state.json` 只记录文件所有权和上次生成哈希，可按团队策略忽略。

## 仓库边界与命名

- `goldenfishs/MRobot`：桌面 GUI 与生态入口，逐步变薄。
- `goldenfishs/MCode`：独立的核心、CLI、schema 和前端协议。
- `goldenfishs/mrobot-platform-stm32`：STM32CubeMX 平台包。
- `goldenfishs/mrobot-board-<board>`：板卡包。
- `goldenfishs/mrobot-device-<name>`、`mrobot-component-<name>`、`mrobot-algorithm-<name>`、`mrobot-module-<name>`、`mrobot-task-<name>`：可独立发布的功能包。

不要一开始拆出所有旧目录。先选 STM32 平台包和 BMI088 设备包做端到端样板，验证版本、依赖、CI 和发布后，再按真实维护边界迁移。

## 渐进迁移

1. 在 MRobot 中建立 MCode 核心和兼容适配，冻结新的 GUI 内生成逻辑。
2. 独立发布 MCode；MRobot 改为依赖它。
3. 提取 `platform-stm32` 和一个设备包，建立包测试矩阵。
4. 将旧 assets 逐包迁移；迁移期允许 legacy adapter，但不允许两套解析器继续演化。
5. 增加 VS Code/MCP 前端；它们只消费 JSON/API。
6. 核心稳定后再新增 ESP32、CH32、HPM、MSPM0 等 platform pack。
