# MRobot 项目 AI 交接说明

本文是没有历史上下文的编码 AI 进入本仓库时的第一份说明。开始工作前完整阅读本文，再按任务读取 `docs/architecture/` 和相关源码。架构、版本、测试方法或路线图发生变化时，同步更新本文。

## 1. 项目目标

MRobot 是组织名、机器人嵌入式框架名和生态品牌。当前重构目标是：

1. 优先把 STM32CubeMX 路径做稳定、简单、可验证。
2. GUI、CLI、VS Code、MCP/AI 只做前端，共享一套无界面核心接口。
3. 设备、组件、算法、任务、BSP、平台和板卡均可独立仓库、独立版本、独立发布。
4. 芯片差异、板卡差异和总线抽象分层，不再为每个芯片复制整套 BSP。
5. 代码生成必须可预览、可重复、安全保留用户代码，并拒绝静默覆盖冲突。
6. 最终支持多 MCU 平台，但不要以破坏 STM32 主路径为代价。

## 2. 命名和职责

- **MRobot**：框架、组织和生态总称；本仓库是桌面 GUI 与生态入口。
- **MCode**：代码生成核心；Python 包名 `mrobot-mcode`，导入名和命令名 `mcode`。
- **MCodeService**：唯一业务入口。解析、包解析、计划、生成、校验不能在 GUI、插件或 MCP 中重新实现。
- **mrobot-package.yaml**：独立模块包清单。
- **mrobot.yaml**：项目的声明式配置。
- **mrobot.lock**：MCU、输入和精确包内容锁定，应该进入版本控制。
- **.mrobot/generated-state.json**：生成文件所有权和内容哈希。

不要再把新的生成逻辑放进旧的 `app/tools/code_generator.py` 或各 GUI page。旧文件可能仍被其他界面引用，但代码生成主路径必须通过 MCode。

## 3. 仓库和当前发布基线

| 仓库 | 职责 | 当前基线 |
|---|---|---|
| `goldenfishs/MRobot` | GUI、生态入口、集成测试 | `v0.5.0`（待发布） |
| `goldenfishs/MCode` | 核心、CLI、schema、MCP | `v0.4.0` |
| `goldenfishs/mrobot-registry` | 官方包索引 | 64 个包 |
| `goldenfishs/mcode-vscode` | VS Code 薄前端 | `v0.3.0` |
| `goldenfishs/mcode-skill` | AI 操作工作流 | `v0.1.0` |
| `goldenfishs/mrobot-platform-stm32` | STM32 平台适配 | `v0.2.1` |
| `goldenfishs/mrobot-device-bmi088` | 可移植 BMI088 驱动 | `v0.2.0` |

另外已发布：

- `mrobot-platform-esp-idf@v0.2.0`
- `mrobot-platform-wch-ch32@v0.2.0`
- `mrobot-platform-hpm-sdk@v0.2.0`
- `mrobot-platform-ti-mspm0@v0.2.0`
- `mrobot-board-ctrboard-h7@v0.1.0`
- `mrobot-board-devc@v0.1.0`
- 独立的 BSP、device、component、algorithm、module、task 仓库

本仓库的 `mcode/` 是 Git 子模块，当前固定到 MCode `v0.4.0`。`pyproject.toml` 也固定远程依赖到相同版本。升级 MCode 时必须同时更新：

1. MCode 版本与 tag。
2. 本仓库 `mcode` 子模块指针。
3. `pyproject.toml` 的 MCode 依赖版本。
4. MRobot 集成测试、README 和发布版本。

## 4. 已完成的工作

### 4.1 统一核心

MCode 已从 GUI 中剥离，提供：

- Python `MCodeService`
- `mcode` CLI 和稳定 `--json` 输出
- `mcode-mcp` stdio 服务
- inspect、init/configure、plan、generate、validate
- 包搜索、安装、删除、创建、板卡包创建和清单校验
- build、flash/download、debug、clean 动作

动作在 `mrobot.yaml` 中使用 argv 数组，MCode 不通过 shell 执行，避免命令拼接。

### 4.2 GUI 接入

代码生成界面位于 `app/code_generate_interface.py`，当前主路径为：

1. `MCodeService.inspect()` 解析工程。
2. GUI 页面把用户选择转换为 package specs 和 bindings。
3. `MCodeService.configure()` 写入项目配置。
4. `MCodeService.validate()` 校验。
5. `MCodeService.generate()` 生成。

静态约束测试在 `tests/test_gui_unified.py`，用于防止 GUI 回退到旧的独立生成器。

### 4.3 STM32CubeMX

当前最完整的平台路径是 STM32CubeMX：

- 解析 `.ioc` 中的 MCU、家族、外设、GPIO label 和 FreeRTOS 能力。
- STM32 family 契约覆盖 F1、F4、H7、G4、L4、U5。
- 可从真实 `.ioc` 创建 board package。
- 可生成 CubeMX HAL 句柄绑定，例如 `hspi1`、`huart3`。
- 旧 UART、SPI、I2C、GPIO、PWM、CAN/FDCAN 模板已接入统一计划。

### 4.4 包和注册表

旧 `assets/User_code` 内容已迁移为独立包仓库。官方 registry 支持：

- SemVer 约束，包括 `^`、`~` 和比较约束。
- 递归依赖安装。
- `requires`/`provides` 能力解析。
- 项目包缓存和精确 lockfile。
- package、platform、board、BSP、device、component、algorithm、module、task 类型。

包格式见 `docs/architecture/PACKAGE_SPEC.md`。

### 4.5 安全生成

MCode 当前实现：

- 先 `plan`，后 `generate`。
- 原子写入。
- `generated` 文件使用哈希检测用户修改，冲突时拒绝覆盖。
- `scaffold` 文件只创建一次，之后归用户所有。
- `mrobot.lock` 固定输入和包版本/内容。
- `--adopt` 只迁移新旧文件都存在可识别 USER 区域的旧文件，并保留区域内容。
- 无 USER 标记的旧文件不会被隐式接管。

### 4.6 AI、VS Code 和 Issue #2

- VS Code 扩展提供 inspect、plan、generate、validate、build、flash、debug 命令。
- MCP 提供项目检查、计划、生成、校验、包搜索和动作执行工具。
- `mcode-skill` 规定 AI 的安全操作顺序和真机边界。
- MRobot Issue #2 已按 completed 关闭，并附交付链接。

### 4.7 桌面发布和自动更新

- GitHub Actions 在 macOS arm64、Windows x64、Linux x64 原生 runner 上分别构建。
- `app/update_service.py` 是 GUI、`mrobot-update` CLI 和未来插件共用的更新接口；前端不得重新实现平台选择、下载和校验。
- 程序启动后默认后台检查更新，“关于”页面可启用自动下载、安装和重启。
- `update.json` 内嵌每个安装包的 SHA-256，GitHub API 回退使用 Release asset digest；不再发布独立 `.sha256` 文件，缺少 digest 时更新器拒绝安装。
- `updates.qutmrobot.cn` 提供稳定版清单，`download.qutmrobot.cn` 提供版本化安装包；发布流水线同时生成香港源和 GitHub Release 清单，客户端失败时回退 GitHub 清单和旧版 API。
- macOS/Linux 使用退出后安装助手和失败回滚；Windows 自动更新只选择 Inno Setup `*-setup.exe`，ZIP 仅作便携包。
- 当前 macOS 仍为临时签名，正式公开分发前应配置 Developer ID、公证以及 Windows Authenticode 签名。

### 4.8 AI 工作台

- `app/ai/` 是 GUI 无关的 AI 核心，包含 Provider 配置、OpenAI-compatible 流式客户端、本地会话、MCode 只读工具和工具调用循环。
- `app/ai_interface.py` 只负责桌面交互；主导航直接提供“AI 工作台”，旧工具箱入口复用同一界面。
- 支持 OpenAI、DeepSeek、硅基流动、阿里云百炼、OpenRouter、Ollama 和自定义 OpenAI-compatible Base URL/模型 ID。
- Provider 配置和会话保存在系统应用数据目录，API Key 只从当前运行内存或用户指定环境变量读取，不能持久化到配置或历史。
- 工程工具只有 inspect、plan、validate、文件列表和受限文本读取；没有 generate、build、flash、debug、shell 或任意文件写入。
- 文件上下文拒绝工程外路径、目录穿越、密钥扩展名、`.env`、构建输出和超过 32 KiB 的单文件。
- 工具返回内容视为不可信数据，系统提示明确禁止遵循工程文件中伪装成指令的文本。

## 5. 真实能力边界：不要作错误声明

以下内容尚不能描述为“完整支持”：

1. **非 STM32 平台**：ESP-IDF、CH32、HPM SDK、MSPM0 当前是统一 `mrobot-project.json` 描述协议和 platform pack，不是完整原生 SDK 工程解析器。
2. **真机验证**：自动化测试和 C11 编译测试通过，但没有在所有真实板卡、探针和工具链上完成烧录/在线调试验收。
3. **构建系统修改**：MCode 可生成文件并调度用户配置的 build 命令，但不保证自动修改所有 CubeIDE `.cproject`、Keil、CMake、Makefile 工程元数据。
4. **GUI 包管理**：GUI 已走统一生成服务，但仍主要把旧页面选择映射为包，不是完整的远程 registry 浏览器、版本解析和冲突 UI。
5. **MCP 功能对齐**：MCP 尚未暴露 CLI/Service 的全部能力。初始化、configure、包安装/删除、`--adopt` 等仍需 CLI 或 Python API。
6. **VS Code 发布渠道**：扩展仓库和 tag 已发布，但不能假设已进入 VS Code Marketplace。
7. **硬件动作**：build/flash/debug 只是安全执行 `mrobot.yaml` 中配置的 argv；实际命令、工具链、固件路径和探针由项目提供。
8. **AI Provider**：当前只实现 OpenAI-compatible Chat Completions。没有原生 Anthropic Messages/OpenAI Responses adapter、外部 MCP 连接器、图片输入、成本账本或跨设备同步。
9. **AI 自主操作**：当前 AI 工具刻意只读，不能自行生成代码、构建、烧录、运行命令或修改工程。

## 6. 关键源码地图

### 本仓库

- `MRobot.py`：桌面程序入口。
- `app/main_window.py`：主窗口和页面装配。
- `app/ai/`：统一 AI Provider、会话、工具和 agent loop。
- `app/ai_interface.py`：AI 工作台 GUI 薄前端。
- `app/code_generate_interface.py`：GUI 代码生成集成入口。
- `app/code_page/`：旧 GUI 配置页面；只负责收集选择，不应拥有生成规则。
- `tests/test_generation.py`：生成、安全覆盖和集成测试。
- `tests/test_gui_unified.py`：GUI 必须调用 MCode 的架构守卫。
- `tests/test_packaging.py`：桌面依赖、版本和发布矩阵约束。
- `tests/test_updates.py`：平台选择、下载校验、安全解包和安装计划测试。
- `docs/architecture/MCODE_ARCHITECTURE.md`：目标架构。
- `docs/architecture/PACKAGE_SPEC.md`：包清单规范。
- `docs/architecture/AI_WORKBENCH.md`：AI Provider、会话、工具、安全边界和演进计划。
- `tools/migrate_legacy_packages.py`：旧模块迁移工具。
- `.github/workflows/test.yml`：主 CI。

### MCode 子模块

- `mcode/service.py`：统一服务入口。
- `mcode/cli.py`：CLI 参数和稳定 JSON 协议。
- `mcode/mcp_server.py`：MCP 薄适配层。
- `mcode/models.py`：统一模型和计划数据结构。
- `mcode/config.py`：`mrobot.yaml` 配置。
- `mcode/registry.py`：registry、SemVer、依赖和能力解析。
- `mcode/generator.py`：计划、写入、哈希和用户区保留。
- `mcode/stm32/`：CubeMX 解析和 STM32 绑定。
- `mcode/schemas/`：项目和包 schema。
- `mcode/tests/`：MCode 核心测试。

## 7. 本地开发和测试

要求 Python 3.10+，CI 使用 Python 3.12。

```bash
git submodule update --init --recursive
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ./mcode pytest PyYAML requests packaging
python -m pytest -q
python -m compileall -q app tools MRobot.py
```

当前预期：本仓库 49 项测试通过。

测试 MCode：

```bash
python -m pip install -e "./mcode[dev]"
(cd mcode && python -m pytest -q)
```

当前预期：MCode 13 项测试通过。

运行 GUI：

```bash
python -m pip install -e .
python MRobot.py
```

构建 Python 分发包：

```bash
python -m pip install build
python -m build
```

提交前至少运行与改动对应的测试；修改统一接口、schema、生成规则或包解析时，必须同时运行 MCode 和 MRobot 全部测试。

## 8. CubeMX 端到端验收流程

对临时工程而不是用户正式工程执行：

```bash
mcode inspect /path/to/project --json
mcode init /path/to/project
mcode package install mrobot.platform.stm32@^0.2.1 --project /path/to/project
mcode package install mrobot.device.bmi088@^0.2.0 --project /path/to/project
mcode plan /path/to/project --json
mcode generate /path/to/project
mcode validate /path/to/project --json
mcode plan /path/to/project --json
```

验收点：

- MCU、外设、GPIO label 和 FreeRTOS 识别正确。
- 首次 plan 只包含预期路径。
- 第二次 plan 无无意义变更。
- USER 区域在重复生成后保留。
- 手动修改 generated 文件后得到冲突而非覆盖。
- lockfile 固定包版本和内容哈希。
- 生成源文件能进入目标构建系统并完成交叉编译。
- 真机烧录和调试只能在明确的目标板、探针和工具链下声明通过。

## 9. 后续路线图

### P0：先把 STM32 主路径做到可交付

1. 增加真实 F4/H7/G4/L4/U5 CubeMX 工程 fixture 和交叉编译矩阵，而不仅是最小文本 `.ioc`。
2. 完成 CubeIDE、CMake、Makefile 至少三种工程的生成文件接入，避免用户手动添加源文件和 include 路径。
3. 在 GUI 中增加明确的 plan 预览、文件 diff、冲突说明和是否迁移旧 USER 区域的选择；不要默认隐藏 `adopt` 决策。
4. 把 registry 搜索、版本选择、依赖树、能力提供者和更新提示做成 GUI 包管理界面。
5. 为 STM32CubeProgrammer、OpenOCD、J-Link、ST-Link 增加可验证的 action profile，同时保留项目覆盖能力。
6. 用真实 CtrBoard-H7、DevC 或其他现有板卡完成构建、烧录、复位、串口输出和至少一个设备驱动的真机验收，并记录工具链版本。
7. 补齐 MCP 的 init/configure/package install/package remove/adopt 工具，使 MCP 与 CLI 核心能力对齐。
8. 为 AI 工作台补充原生 OpenAI Responses 和 Anthropic Messages adapter，并保持统一 Provider 接口。
9. 增加本地/远程 MCP 连接器管理、逐会话启停和逐工具权限；写操作必须显式确认且可预览。

### P1：提升模块生态和开发体验

1. 为迁移包逐个补充真正的单元测试、最小编译测试和示例，而不仅是清单验证。
2. 规范包 include 路径、公共 API、错误码、RTOS/裸机兼容和 C/C++ 互操作。
3. 增加 registry 发布校验：tag 与 manifest 版本一致、归档哈希、依赖闭环、能力冲突和许可证检查。
4. 给 board package 增加 MCU、晶振、引脚、板载器件和默认 binding schema。
5. 当前已发布 macOS arm64 DMG、Windows x64 安装版/ZIP 和 Linux x64 tar.gz；后续补充 macOS Intel、Linux AppImage 和可直接安装的 VSIX。
6. 配置 macOS Developer ID + notarization 与 Windows Authenticode，消除当前临时签名/未签名发行包的系统安全提示。
7. 增加从旧 MRobot 项目迁移的 dry-run 报告和回滚/备份说明。

### P2：多平台原生化

按实际用户需求逐个平台实现原生 importer，不要同时铺开：

1. 选择一个次优先平台，建议 ESP-IDF。
2. 解析真实 SDK 工程配置，转换为同一 `ProjectModel`。
3. platform pack 负责 SDK 差异，设备和算法包继续只依赖能力。
4. 建立真实工程 fixture、编译 CI 和板级 smoke test。
5. 稳定后再依次推进 CH32、HPM SDK、MSPM0。

## 10. 实施规则

1. 先读现有代码和测试，再修改；不要凭 README 猜实现。
2. 不在前端复制 MCode 规则。需要新能力时先扩展 `MCodeService`，再扩 CLI/MCP/GUI/VS Code。
3. 新生成行为必须先返回可检查的 `GenerationPlan`。
4. 不通过删除 lockfile、状态文件或用户文件绕过冲突。
5. package 源码是不可变输入；实例 glue 放 generated，业务入口使用 scaffold。
6. 新平台必须转换到统一模型，不能在 GUI 到处增加平台 `if/else`。
7. 修改 schema 时考虑向后兼容并添加迁移或清晰诊断。
8. 不要把“CI 通过”描述成“真机通过”。
9. 工作区可能有用户修改；不要清理、重置或覆盖无关改动。
10. 本文件提供项目上下文，不构成 push、发布、创建仓库、关闭 issue 或真机烧录的永久授权；按当前用户请求确认外部写操作范围。

## 11. 完成定义

一个功能只有同时满足以下条件才算完成：

- 通过统一服务实现，前端只是适配。
- 有针对成功、重复执行、错误和冲突的测试。
- plan 输出可解释且不会越出项目目录。
- 不丢失用户代码。
- 文档、schema、版本和示例保持一致。
- MCode 与 MRobot 集成测试通过。
- 相关仓库 CI 通过。
- 若涉及硬件，记录真实板卡、工具链、探针和执行结果；否则明确标记未做真机验证。

## 12. 新 AI 开始任务时的检查清单

1. 运行 `git status -sb`，保护现有用户改动。
2. 运行 `git submodule status`，确认 MCode 指针。
3. 阅读本文件、两份架构文档和任务涉及的测试。
4. 判断改动属于 MRobot 前端、MCode 核心、registry 还是独立 package，不要放错仓库。
5. 先复现或建立验收用例。
6. 实现最小闭环并运行对应测试。
7. 报告实际完成内容、测试证据、未验证的硬件边界和下一步。
