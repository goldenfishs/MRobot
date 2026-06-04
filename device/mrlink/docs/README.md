# mrlink 通用通信协议库

轻量级 byte-stream 帧协议库，面向 STM32 / 嵌入式 MCU。协议帧头 `{0x4D, 0x52}` = ASCII "MR"。

## 文件分层

`mrlink/` 根目录只保留公开 `.h/.hpp` API；实现、内部头文件和文档都放入子目录。

| 层级 | 文件 | 作用 |
|---|---|---|
| Public API | `mrlink.h` | 通用 frame 协议 (32 槽 cmd 派发) |
| Public API | `mrlink_channel.h` | 面向业务的通信通道 API，初始化时绑定 UART / USB / FDCAN |
| Public API | `mrlink.hpp` | OneMessage-style typed 注册 API (namespace `mr::link`) |
| Public API | `mrlink_lite.hpp` | Zero-`std::function` typed API for STM32 real-time / small-memory paths |
| Main impl | `src/mrlink.c` | frame 协议实现 |
| Main impl | `src/mrlink_channel.c` | channel 主实现，只做 init 入口和 backend ops 分发 |
| Internal impl | `internal/mrlink_channel_internal.h` | 内部 backend ops，不给业务 include |
| Internal impl | `internal/mrlink_channel_uart.c` | UART DMA ReceiveToIdle backend |
| Internal impl | `internal/mrlink_channel_fdcan.c` | FDCAN 单帧 CAN FD backend |
| Internal impl | `internal/mrlink_channel_usb.c` | USB byte-stream callback backend |
| Shared component | `component/container/spsc_ringbuf.h/.c` | 通用 SPSC 字节环形缓冲，供 mrlink RX stream 使用 |

## 特性

- **帧头** `{0x4D, 0x52}` = ASCII "MR"（项目标识）
- **CRC16-CCITT-FALSE** 可选（`MrLink_Config.use_crc16`）
- **32 槽** cmd 派发表，O(N) 线性扫描
- **零 OS 依赖**（除 `cmsis_compiler.h` 用于 ISR 临界区）
- **加新命令 = 0 库代码修改**：写 handler + 1 行 `MrLink_RegisterHandler`
- **C 库 typed API**（`MrLink_RegisterTypedHandler`）：库内自动 length check + memcpy
- **C++ typed wrapper**（`mrlink.hpp`）：每条命令 1 行 lambda，库内自动 length check + memcpy
- **C++ latest cache**：`SubscribeLatest<T>()` 自动缓存；`Latest<T>()` 返回内部指针，跨任务/ISR 读取推荐 `CopyLatest<T>()`
- **错误事件**：`MrLink_SetErrorHandler()` / `Instance::OnError()` 可记录 CRC、超长、未知 cmd、丢字节等错误
- **RX 分层**：`MrLink_PushBytes()` 只入队，`MrLink_Dispatch()` 在任务上下文派发 handler
- **无拷贝丢弃**：parser 使用 `SpscRingBuf_Drop()` 丢弃已消费字节
- **channel 绑定硬件**：一个通信对象初始化时选择 UART / USB / FDCAN，后续所有命令都走该通道
- **清晰分层**：业务只 include `mrlink_channel.h`，UART / FDCAN / USB 后端放在 `internal/`
- **底层收发内聚**：UART DMA、FDCAN 单帧、USB 回调适配等细节都收在 channel 内部
- **C++ 命名空间**：`mr::link::Instance`

## 帧格式

```
use_crc16 = true:  [0x4D][0x52][len][cmd][payload...][CRC_lo][CRC_hi]
use_crc16 = false: [0x4D][0x52][len][cmd][payload...]
```

| 字段 | 长度 | 说明 |
|---|---|---|
| header | 2B | 写死 `{0x4D, 0x52}` = "MR" |
| length | 1B | payload 字节数 (0~max_payload_size) |
| cmd | 1B | 命令字，库不解释 |
| payload | 0~max_payload_size（默认 64B） | 业务数据 |
| CRC16 | 0 或 2B | CCITT-FALSE, init=0xFFFF, poly=0x1021, 小端写 |

**最大帧长**：6 + max_payload（默认 70 字节）

当前实现限制：parser / typed handler 内部 frame buffer 以编译期 `MRLINK_MAX_FRAME_SIZE` 为上限；默认配置与 `max_payload_size=64`、CRC 开启时的 70B 完整帧对齐。未来若支持分片或更大 payload，需同步重审 `MRLINK_MAX_FRAME_SIZE`、`MrLink_t` opaque storage、RX/TX/Poll buffer 以及 UART / FDCAN / USB channel 的 `max_frame_size`。

## 内存开销

| 组件 | 大小 / 实例 |
|---|---|
| `SpscRingBuf_t` | 约 12 字节 (head/tail + 指针，32-bit MCU) |
| `MrLink_t` (32 槽 + frame_buf) | ~456 字节 (含 70B typed 内部 buffer) |
| `mr::link::Instance` (默认 16 typed + 16 latest slot) | ~2 KB 级别 (含 std::function 与 latest payload 缓存) |

可通过编译宏调整 C++ wrapper 容量：

```cpp
#define MRLINK_CPP_MAX_TYPED_HANDLERS  16u
#define MRLINK_CPP_MAX_LATEST_MESSAGES 16u
```

## 最小示例 — C 风格

```c
#include "mrlink/mrlink.h"

static uint8_t s_rx[256], s_tx[80];
static MrLink_t s_link;

static int8_t OnHeartbeat(uint8_t cmd, const uint8_t* pl, uint16_t len, void* ctx) {
    (void)cmd; (void)pl; (void)len; (void)ctx;
    // ... 业务 (需要自己 memcpy payload)
    return MRLINK_OK;
}

void MyDev_Init(void) {
    MrLink_Config_t cfg = { .max_payload_size = 64, .use_crc16 = true };
    MrLink_Init(&s_link, &cfg, s_rx, sizeof(s_rx), s_tx, sizeof(s_tx));
    MrLink_RegisterHandler(&s_link, 0x01, OnHeartbeat, NULL);
}

void USARTx_IRQHandler_RX(void) {
    if (RX_done) MrLink_PushBytes(&s_link, rx_buf, rx_len);
}

void MyDev_Process(void) {
    (void)MrLink_Dispatch(&s_link);
}

void SendHeartbeat(void) {
    uint16_t n = MrLink_Build(&s_link, 0x01, NULL, 0);
    if (n > 0u) BSP_UART_Transmit(BSP_UART_PC, s_tx, n, true);
}
```

## 最小示例 — C 风格 + typed handler

C 库提供 `MrLink_RegisterTypedHandler`，库内自动做 length check + memcpy 到内部 buffer，handler 拿到 `const void*`（业务 cast 成自己的类型）：

```c
#include "mrlink/mrlink.h"

typedef struct { float vx, vy, wz; } ChassisCmd_t;   // 12 字节

static int8_t OnChassisCmd(uint8_t cmd, const void* data,
                            uint16_t size, void* ctx) {
    (void)cmd; (void)ctx;
    if (size != sizeof(ChassisCmd_t)) return MRLINK_ERR_ARGS;
    const ChassisCmd_t* c = (const ChassisCmd_t*)data;
    Chassis_ApplyRemoteCmd(c);
    return MRLINK_OK;
}

void MyDev_Init(void) {
    // ... 同上
    MrLink_RegisterTypedHandler(&s_link, 0x10,
                                 sizeof(ChassisCmd_t),
                                 OnChassisCmd, NULL);
}
```

**对比**：

| 维度 | C 风格 (`MrLink_RegisterHandler`) | C typed 风格 (`MrLink_RegisterTypedHandler`) |
|---|---|---|
| handler 签名 | `(cmd, pl, len, ctx)` | `(cmd, data, size, ctx)` |
| length check | 业务手写 | **库自动** |
| memcpy | 业务手写 | **库自动** (到 frame_buf) |
| handler 拿到的 | `const uint8_t*` | `const void*` (typed by convention) |
| 加新命令代码 | 6-7 行 | **3-4 行**（仅 cast + dispatch）|

## 最小示例 — C++ OneMessage 风格

```cpp
#include "mrlink/mrlink.hpp"

struct ChassisCmd {
    static constexpr mr::link::Topic topic = 0x10;
    float vx;
    float vy;
    float wz;
};

struct ChassisFeedback {
    static constexpr mr::link::Topic topic = 0x20;
    float vx;
    float vy;
    float wz;
};

static mr::link::Bus<> s_link;

void MyDev_Init() {
    s_link.BeginUart(BSP_UART_PC);

    // ★ 1 行 1 命令, 0 行 boilerplate
    s_link.OnLatest<ChassisCmd>([](const ChassisCmd& c) {
        // 自动 length check + memcpy
    });
}

void MyDev_Process() {
    s_link.Poll();

    ChassisCmd latest{};
    if (s_link.CopyLatest(&latest)) {
        // 拿到最新命令快照
    }
}

void MyDev_SendFeedback() {
    s_link.Publish(ChassisFeedback{1.0f, 0.0f, 0.0f});
}
```

如果你的消息类型已经在别处定义，不能往结构体里加 `topic`，也可以保留外部声明：

```cpp
MRLINK_TOPIC(ChassisCmd, 0x10);
MRLINK_TOPIC(ChassisFeedback, 0x20);
```

## 集成到 STM32 工程

把以下源文件加入 `CMakeLists.txt`（或 `.mxproject`）：

```cmake
target_sources(${PROJECT_NAME} PRIVATE
    User/component/container/spsc_ringbuf.c
    User/device/mrlink/src/mrlink.c
    User/device/mrlink/src/mrlink_channel.c
    User/device/mrlink/internal/mrlink_channel_uart.c
    User/device/mrlink/internal/mrlink_channel_fdcan.c
    User/device/mrlink/internal/mrlink_channel_usb.c
)
```

链接时确保以下头文件路径在 include 列表：

```
User/device
User/device/mrlink
User/component     # crc16.h
Drivers/CMSIS/Include   # cmsis_compiler.h
```

## Channel 通信对象绑定

推荐业务层使用 `MrLink_Channel_t`：一个通信对象初始化时绑定一次硬件，后续该对象所有 RX/TX 都走同一个 channel。`mrlink` core 仍只负责 frame build / parse / dispatch，不直接 include UART、FDCAN、USB 等 BSP。

```c
static MrLink_Channel_t s_pc_channel;
static uint8_t s_pc_rx_dma_buf[4][256];
static volatile uint16_t s_pc_rx_len[4];

MrLink_ChannelUartConfig_t pc_uart = {
    .uart = BSP_UART_PC,
    .rx_slots = &s_pc_rx_dma_buf[0][0],
    .rx_slot_size = 256,
    .rx_slot_count = 4,
    .rx_len_storage = s_pc_rx_len,
    .rx_ready = OnPcRxReady,
};

MrLink_Channel_InitUart(&s_pc_channel, &pc_uart);
MrLink_Channel_StartRx(&s_pc_channel);

uint16_t rx_len = MrLink_Channel_PopRx(&s_pc_channel, rx_buf, sizeof(rx_buf));
if (rx_len > 0u) {
    MrLink_PushBytes(&link, rx_buf, rx_len);
    MrLink_Dispatch(&link);
}

uint16_t tx_len = MrLink_Build(&link, 0x01, NULL, 0);
if (tx_len > 0u) {
    MrLink_Channel_Send(&s_pc_channel, tx_buf, tx_len);
}
```

C++ 推荐优先用 `Bus<>`，自动持有 protocol buffer、channel、UART RX slots 和 poll buffer：

```cpp
static mr::link::Bus<> s_link;

s_link.BeginUart(BSP_UART_PC);

void PcComm_Process() {
    s_link.Poll();
}
```

需要完全手动管理 buffer 或复用已有 `MrLink_Channel_t` 时，再使用底层 `Instance` + `BindChannel()`。

当前已落地 UART / FDCAN / USB channel：
- `MrLink_Channel_InitUart()`：通信对象绑定 `BSP_UART_t`、RX slot buffer、RX ready callback；当前 UART backend 每个 `BSP_UART_t` 只能绑定一个 channel。
- `MrLink_Channel_InitFdcan()`：通信对象绑定 `BSP_FDCAN_t`、TX/RX CAN ID，单帧 CAN FD 收发。
- `MrLink_Channel_InitUsb()`：通信对象绑定 USB byte-stream 回调，适配后续 USB CDC/BSP。
- `MrLink_Channel_StartRx()`：启动底层 RX。
- `MrLink_Channel_PopRx()`：从通道取出一段连续字节流。
- `MrLink_Channel_Send()`：通过该通道发送完整 frame。
- `MrLink_Channel_RegisterTxCallbacks()`：注册 TX done / error 通知。

业务模块只持有 `MrLink_Channel_t`，不要 include `mrlink/internal/*`。

### FDCAN 单帧示例

FDCAN backend 当前不做分片，要求完整 MrLink frame 不超过 channel 的 `max_frame_size`（默认 CAN FD 单帧 64B）。默认 MrLink 最大帧是 70B，因此 FDCAN 通道建议把 `max_payload_size <= 58`。

C++ `Bus<>::BeginFdcan()` / `StaticInstance::BeginFdcan()` 会按 `MrLink_MaxFrameSizeForConfig(config)` 计算完整帧长度，并与有效 `max_frame_size`（`channel_config.max_frame_size` 或默认 CAN FD 上限）检查，不满足时返回 `MRLINK_ERR_ARGS`。底层 C 手动组合 `MrLink_Channel_InitFdcan()`、`MrLink_Build()`、`MrLink_Channel_Send()` 时，调用方仍需在配置阶段保证完整 MrLink frame `<= max_frame_size`，否则不属于当前单帧 FDCAN backend 支持范围。

```c
static MrLink_Channel_t s_can_channel;

MrLink_ChannelFdcanConfig_t can_cfg = {
    .fdcan = BSP_FDCAN_1,
    .tx_format = BSP_FDCAN_FORMAT_STD_DATA,
    .tx_id = 0x321,
    .rx_id = 0x123,
    .rx_queue_size = 4,
    .max_frame_size = MRLINK_CHANNEL_FDCAN_MAX_FRAME_SIZE,
};

MrLink_Channel_InitFdcan(&s_can_channel, &can_cfg);
```

### USB 回调示例

当前工程未包含 USB CDC Device 栈，USB backend 先采用回调适配。等 `CDC_Transmit` / USB BSP 到位后，只需要把回调接进去，业务层仍使用同一个 `MrLink_Channel_t`。

```c
static MrLink_Channel_t s_usb_channel;

MrLink_ChannelUsbConfig_t usb_cfg = {
    .ctx = user_usb_ctx,
    .start_rx = UserUsbStartRx,
    .pop_rx = UserUsbPopRx,
    .send = UserUsbSend,
    .register_tx_callbacks = UserUsbRegisterTxCallbacks,
    .is_rx_active = UserUsbIsRxActive,
};

MrLink_Channel_InitUsb(&s_usb_channel, &usb_cfg);
```

注意：FDCAN 不是 byte-stream，CAN FD 单帧 64B 小于默认 mrlink 最大帧 70B，若不做分片应限制 `max_payload_size <= 58`。

## 适用场景 vs 不适用

**适用**：
- 跨 MCU 通信（板内 / 板间）
- UART / SPI / FDCAN / TCP 字节流
- 需要 5~30 种命令的小型总线

**不适用**：
- 大量 topic (>30)：用 OneMessage 原版（topic ID 是 2B）
- 主从/请求-响应时序：库**不**管，调用方自己实现
- 经典 CAN 8 字节：FDCAN (64 字节) 已普及
