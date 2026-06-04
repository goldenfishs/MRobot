/**
  ******************************************************************************
  * @file    mrlink.hpp
  * @brief   C++ OneMessage-style typed wrapper over mrlink C library.
  *
  * 在 C 库 `mrlink` 之上提供类型安全的 topic 注册 API:
  *   - s_link.On<T>(cmd, [](const T&) { ... });
  * 库内自动完成 length check + memcpy, 业务 handler 直接拿到 `const T&`。
  *
  * 要求 / Requirements:
  *   - C++14 及以上 (auto / std::function / lambda)
  *   - 链接 src/mrlink.c (本文件不重写协议层, 仅做 typed 包装)
  *
  * 内存 / Memory (per Instance):
  *   - MrLink_t 内部: ~384 字节 (32 槽 raw handler)
  *   - 本 wrapper: 16 槽 typed slot × ~40 字节 (std::function) ≈ 640 字节
  *   - 合计 ~1 KB / 实例
  *
  * 限制 / Limits:
  *   - 当前 C core parser 与内部 frame buffer 以编译期 MRLINK_MAX_FRAME_SIZE
  *     为上限；未来支持分片或更大 payload 时，需同步重审 protocol buffer、
  *     StaticInstance TX/Poll buffer 与各 channel 的 max_frame_size。
  *
  * Quick start:
  *   ```cpp
  *   #include "device/mrlink/mrlink.hpp"
  *
  *   struct ChassisCmd { float vx, vy, wz; };
  *   MRLINK_TOPIC(ChassisCmd, 0x10);
  *
  *   static mr::link::Bus<> s_link;
  *
  *   s_link.BeginUart(BSP_UART_PC);
  *   s_link.OnLatest<ChassisCmd>([](const ChassisCmd& cmd) {});
  *   ```
  ******************************************************************************
  */

#pragma once

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <functional>
#include <type_traits>

#include "device/mrlink/mrlink_channel.h"
#include "device/mrlink/mrlink.h"

namespace mr::link {

using Topic = uint8_t;
using Writer = std::function<bool(uint8_t* frame, uint16_t frame_len)>;
using ErrorHandler = std::function<void(const MrLink_ErrorInfo_t& info)>;

#ifndef MRLINK_CPP_MAX_TYPED_HANDLERS
#define MRLINK_CPP_MAX_TYPED_HANDLERS (16u)
#endif

#ifndef MRLINK_CPP_MAX_LATEST_MESSAGES
#define MRLINK_CPP_MAX_LATEST_MESSAGES (16u)
#endif

template <typename T>
struct MessageTraits;

namespace detail {

template <typename...>
using VoidT = void;

template <typename T, typename = void>
struct HasMessageTraits : std::false_type {};

template <typename T>
struct HasMessageTraits<T, VoidT<decltype(MessageTraits<T>::topic)>>
    : std::true_type {};

template <typename T, typename = void>
struct HasStaticTopic : std::false_type {};

template <typename T>
struct HasStaticTopic<T, VoidT<decltype(T::topic)>> : std::true_type {};

template <typename T, bool HasTraits, bool HasTypeTopic>
struct TopicResolver;

template <typename T>
struct TopicResolver<T, true, false> {
  static constexpr Topic Value() {
    return MessageTraits<T>::topic;
  }
};

template <typename T>
struct TopicResolver<T, true, true> {
  static constexpr Topic Value() {
    return MessageTraits<T>::topic;
  }
};

template <typename T>
struct TopicResolver<T, false, true> {
  static constexpr Topic Value() {
    return static_cast<Topic>(T::topic);
  }
};

template <typename T>
struct TopicResolver<T, false, false> {
  static constexpr Topic Value() {
    static_assert(HasMessageTraits<T>::value,
                  "mr::link::TopicOf<T>: add static constexpr topic to T or specialize MessageTraits<T>");
    return 0u;
  }
};

}  // namespace detail

template <typename T>
constexpr Topic TopicOf() {
  using Payload = typename std::remove_cv<
      typename std::remove_reference<T>::type>::type;
  return detail::TopicResolver<Payload,
                               detail::HasMessageTraits<Payload>::value,
                               detail::HasStaticTopic<Payload>::value>::Value();
}

#define MRLINK_TOPIC(PayloadType, TopicValue)                 \
  namespace mr::link {                                        \
  template <>                                                  \
  struct MessageTraits<PayloadType> {                          \
    static constexpr Topic topic = static_cast<Topic>(TopicValue); \
  };                                                           \
  }

#define MRLINK_MESSAGE(PayloadType, TopicValue) \
  MRLINK_TOPIC(PayloadType, TopicValue)

/** Per-instance typed handler pool size. */
inline constexpr uint8_t MAX_TYPED_HANDLERS = MRLINK_CPP_MAX_TYPED_HANDLERS;
inline constexpr uint8_t MAX_LATEST_MESSAGES = MRLINK_CPP_MAX_LATEST_MESSAGES;

static_assert(MRLINK_CPP_MAX_TYPED_HANDLERS <= MRLINK_MAX_HANDLERS,
              "MRLINK_CPP_MAX_TYPED_HANDLERS must not exceed MRLINK_MAX_HANDLERS");
static_assert(MRLINK_CPP_MAX_LATEST_MESSAGES > 0u,
              "MRLINK_CPP_MAX_LATEST_MESSAGES must be > 0");

/**
 * @brief 类型安全的 mrlink 实例包装 / Type-safe mrlink instance wrapper.
 *
 * 一个 Instance 对应一条物理通道 (UART / SPI / FDCAN 之一)。
 * 同实例**不建议**同时混用 C 库原生 RegisterHandler 与本 wrapper 的 On<T>,
 * 否则 typed slot 与 raw slot 互不感知, 可能产生意外行为。
 */
class Instance {
 public:
  Instance() = default;

  // 不允许拷贝: 内含 C 库 opaque 状态, 拷贝会破坏内部一致性
  Instance(const Instance&) = delete;
  Instance& operator=(const Instance&) = delete;

  /**
   * @brief 析构: 注销所有已注册 handler, 防止 C 库持有野指针.
   */
  ~Instance() {
    for (uint8_t i = 0u; i < MAX_TYPED_HANDLERS; i++) {
      if (slots_[i].used) {
        (void)MrLink_RegisterHandler(&proto_, slots_[i].cmd,
                                     nullptr, nullptr);
        slots_[i].used = false;
      }
    }
  }

  /**
   * @brief 初始化 / Initialize.
   *
   * @param cfg          C 库 config (NULL 则用默认: max_payload=64, use_crc16=true)
   * @param rx_buf       RX 流缓冲 (外部提供, ≥ 4 字节)
   * @param rx_buf_size
   * @param tx_buf       TX 缓冲 (外部提供, ≥ 4 + max_payload)
   * @param tx_buf_size
   * @return MRLINK_OK / ERR_NULL / ERR_ARGS
   */
  int8_t Init(const MrLink_Config_t* cfg,
              uint8_t* rx_buf, uint16_t rx_buf_size,
              uint8_t* tx_buf, uint16_t tx_buf_size) {
    tx_buf_ = tx_buf;
    tx_buf_size_ = tx_buf_size;
    return MrLink_Init(&proto_, cfg, rx_buf, rx_buf_size, tx_buf, tx_buf_size);
  }

  /** 重置 (清空 RX 缓冲 + stats + handlers) / Reset. */
  void Reset() {
    MrLink_Reset(&proto_);
    for (auto& s : slots_) {
      s.used = false;
      s.cmd = 0u;
      s.typed = nullptr;
      s.empty = nullptr;
    }
    for (auto& s : latest_slots_) {
      s.used = false;
      s.topic = 0u;
      s.size = 0u;
      s.sequence = 0u;
    }
  }

  /** 喂入接收到的字节 / Feed received bytes (ISR / 任务均可调用). */
  int8_t PushBytes(const uint8_t* data, uint16_t len) {
    return MrLink_PushBytes(&proto_, data, len);
  }

  int8_t Dispatch() {
    return MrLink_Dispatch(&proto_);
  }

  int8_t FeedBytes(const uint8_t* data, uint16_t len) {
    return MrLink_FeedBytes(&proto_, data, len);
  }

  /** 拉取一帧 (任务上下文) / Pull one frame. */
  int8_t Parse(uint8_t* out_cmd,
               const uint8_t** out_payload,
               uint16_t* out_payload_len) {
    return MrLink_Parse(&proto_, out_cmd, out_payload, out_payload_len);
  }

  /** 构造一帧到 tx_buf / Build one frame into tx_buf. 返回写入字节数 (0=失败). */
  uint16_t Build(uint8_t cmd, const uint8_t* payload, uint16_t payload_len) {
    return MrLink_Build(&proto_, cmd, payload, payload_len);
  }

  uint16_t BuildEmpty(Topic topic) {
    return MrLink_Build(&proto_, topic, nullptr, 0u);
  }

  bool PublishEmpty(Topic topic) {
    return WriteBuiltFrame(BuildEmpty(topic));
  }

  template <typename T>
  uint16_t Build(Topic topic, const T& payload) {
    static_assert(std::is_trivially_copyable<T>::value,
                  "mr::link::Instance::Build<T>: T must be trivially copyable");
    return MrLink_Build(&proto_, topic,
                        reinterpret_cast<const uint8_t*>(&payload), sizeof(T));
  }

  template <typename T>
  uint16_t Build(const T& payload) {
    return Build(TopicOf<T>(), payload);
  }

  template <typename T>
  bool Publish(Topic topic, const T& payload) {
    static_assert(std::is_trivially_copyable<T>::value,
                  "mr::link::Instance::Publish<T>: T must be trivially copyable");
    const uint16_t frame_len = Build(topic, payload);
    return WriteBuiltFrame(frame_len);
  }

  template <typename T>
  bool Publish(const T& payload) {
    return Publish(TopicOf<T>(), payload);
  }

  uint16_t PublishEmpty(Topic topic, uint8_t* out_buf, uint16_t out_buf_size) {
    const uint16_t frame_len = BuildEmpty(topic);
    return CopyBuiltFrame(out_buf, out_buf_size, frame_len);
  }

  template <typename T>
  uint16_t Publish(Topic topic, const T& payload,
                   uint8_t* out_buf, uint16_t out_buf_size) {
    static_assert(std::is_trivially_copyable<T>::value,
                  "mr::link::Instance::Publish<T>: T must be trivially copyable");
    const uint16_t frame_len = Build(topic, payload);
    return CopyBuiltFrame(out_buf, out_buf_size, frame_len);
  }

  template <typename T>
  uint16_t Publish(const T& payload, uint8_t* out_buf, uint16_t out_buf_size) {
    return Publish(TopicOf<T>(), payload, out_buf, out_buf_size);
  }

  const uint8_t* TxBuffer() const {
    return tx_buf_;
  }

  void SetWriter(Writer writer) {
    channel_ = nullptr;
    writer_ = writer;
  }

  void ClearWriter() {
    channel_ = nullptr;
    writer_ = nullptr;
  }

  bool HasWriter() const {
    return writer_ != nullptr;
  }

  int8_t BindChannel(const MrLink_Channel_t* channel) {
    if (channel == nullptr) {
      ClearChannel();
      return MRLINK_CHANNEL_ERR_NULL;
    }
    channel_ = channel;
    writer_ = [channel](uint8_t* frame, uint16_t frame_len) {
      return MrLink_Channel_Send(channel, frame, frame_len) == MRLINK_CHANNEL_OK;
    };
    return MRLINK_CHANNEL_OK;
  }

  void ClearChannel() {
    channel_ = nullptr;
    writer_ = nullptr;
  }

  bool HasChannel() const {
    return channel_ != nullptr;
  }

  int8_t StartChannelRx() const {
    return (channel_ != nullptr) ? MrLink_Channel_StartRx(channel_)
                                 : MRLINK_CHANNEL_ERR_NULL;
  }

  uint16_t PollChannelRx(uint8_t* scratch, uint16_t scratch_size,
                         bool dispatch = true) {
    if (channel_ == nullptr || scratch == nullptr || scratch_size == 0u) {
      return 0u;
    }
    const uint16_t len = MrLink_Channel_PopRx(channel_, scratch, scratch_size);
    if (len > 0u) {
      if (dispatch) {
        (void)FeedBytes(scratch, len);
      } else {
        (void)PushBytes(scratch, len);
      }
    }
    return len;
  }

  int8_t OnError(ErrorHandler handler) {
    error_handler_ = handler;
    return MrLink_SetErrorHandler(&proto_, error_handler_ != nullptr
                                               ? &Instance::ErrorTrampoline
                                               : nullptr,
                                  this);
  }

  void ClearErrorHandler() {
    error_handler_ = nullptr;
    (void)MrLink_SetErrorHandler(&proto_, nullptr, nullptr);
  }

  /**
   * @brief 注册空 payload handler / Register empty-payload handler.
   *
   * 适用于 heartbeat 等 length=0 的命令。收到匹配 cmd 且 payload_len=0
   * 时调用 handler；若长度非 0，则计入 stats.frame_rx_size_mismatch。
   */
  int8_t On(uint8_t cmd, std::function<void()> handler) {
    if (handler == nullptr) {
      return Off(cmd);
    }

    int slot = FindSlot(cmd);
    if (slot < 0) {
      slot = AllocSlot();
      if (slot < 0) {
        return MRLINK_ERR_ARGS;
      }
    }

    slots_[slot].used = true;
    slots_[slot].cmd = cmd;
    slots_[slot].typed = nullptr;
    slots_[slot].empty = handler;

    return MrLink_RegisterHandler(&proto_, cmd,
                                  &Instance::EmptyTrampoline,
                                  &slots_[slot]);
  }

  int8_t Subscribe(Topic topic, std::function<void()> handler) {
    return On(topic, handler);
  }

  /** 获取运行统计 / Get runtime stats. */
  const MrLink_Stats_t* GetStats() const {
    return MrLink_GetStats(&proto_);
  }

  /**
   * @brief 注册类型化 handler / Register typed handler (OneMessage-style).
   *
   * 收到匹配 cmd 的帧时, 库内自动:
   *   1. 校验 len == sizeof(T), 不匹配则记入 stats.frame_rx_unknown_cmd
   *   2. memcpy payload 到栈上 T 变量
   *   3. 调用 handler, 传入 `const T&`
   *
   * @tparam T       payload 类型, 必须是 trivially copyable (POD 风格)
   * @param cmd      命令字 (0x00~0xFF)
   * @param handler  std::function, 支持 lambda 捕获
   * @return MRLINK_OK / ERR_NULL / ERR_ARGS (typed slot 已满)
   *
   * 重复注册同 cmd 会**覆盖**旧 handler。
   * handler = nullptr 等价于 Off(cmd)。
   */
  template <typename T>
  int8_t On(uint8_t cmd, std::function<void(const T&)> handler) {
    static_assert(std::is_trivially_copyable<T>::value,
                  "mr::link::Instance::On<T>: T must be trivially copyable "
                  "(POD-style struct). No std::string, std::vector, etc.");
    if (handler == nullptr) {
      return Off(cmd);
    }

    int slot = FindSlot(cmd);
    if (slot < 0) {
      slot = AllocSlot();
      if (slot < 0) {
        return MRLINK_ERR_ARGS;  // typed pool 满
      }
    }

    slots_[slot].used = true;
    slots_[slot].cmd = cmd;
    slots_[slot].empty = nullptr;
    slots_[slot].typed = [handler](const uint8_t* pl) {
      T value;
      std::memcpy(&value, pl, sizeof(T));
      handler(value);
    };

    /* 长度校验 + memcpy 由 C 库 MrLink_RegisterTypedHandler 负责 */
    return MrLink_RegisterTypedHandler(&proto_, cmd, sizeof(T),
                                           &Instance::Trampoline,
                                           &slots_[slot]);
  }

  template <typename T>
  int8_t On(std::function<void(const T&)> handler) {
    return On<T>(TopicOf<T>(), handler);
  }

  template <typename T>
  int8_t Subscribe(Topic topic, std::function<void(const T&)> handler) {
    return On<T>(topic, handler);
  }

  template <typename T>
  int8_t Subscribe(std::function<void(const T&)> handler) {
    return On<T>(handler);
  }

  template <typename T>
  int8_t OnLatest(Topic topic,
                  std::function<void(const T&)> handler = nullptr) {
    static_assert(std::is_trivially_copyable<T>::value,
                  "mr::link::Instance::OnLatest<T>: T must be trivially copyable");
    static_assert(sizeof(T) <= MRLINK_MAX_PAYLOAD_DEFAULT,
                  "mr::link::Instance::OnLatest<T>: T exceeds latest payload storage");
    return On<T>(topic, [this, topic, handler](const T& payload) {
      StoreLatest(topic, payload);
      if (handler != nullptr) {
        handler(payload);
      }
    });
  }

  template <typename T>
  int8_t OnLatest(std::function<void(const T&)> handler = nullptr) {
    return OnLatest<T>(TopicOf<T>(), handler);
  }

  template <typename T>
  int8_t SubscribeLatest(Topic topic,
                         std::function<void(const T&)> handler = nullptr) {
    return OnLatest<T>(topic, handler);
  }

  template <typename T>
  int8_t SubscribeLatest(std::function<void(const T&)> handler = nullptr) {
    return OnLatest<T>(handler);
  }

  template <typename T>
  bool StoreLatest(Topic topic, const T& payload) {
    static_assert(std::is_trivially_copyable<T>::value,
                  "mr::link::Instance::StoreLatest<T>: T must be trivially copyable");
    static_assert(sizeof(T) <= MRLINK_MAX_PAYLOAD_DEFAULT,
                  "mr::link::Instance::StoreLatest<T>: T exceeds latest payload storage");
    ScopedIrqLock lock;
    LatestSlot* slot = FindOrAllocLatestSlot(topic);
    if (slot == nullptr) {
      return false;
    }
    slot->used = true;
    slot->topic = topic;
    slot->size = sizeof(T);
    slot->sequence++;
    std::memcpy(slot->payload, &payload, sizeof(T));
    return true;
  }

  template <typename T>
  bool StoreLatest(const T& payload) {
    return StoreLatest(TopicOf<T>(), payload);
  }

  /**
   * @brief 返回 latest cache 中指定 topic 的内部指针 / Get internal latest pointer.
   *
   * 返回值直接指向 Instance 内部缓存，不做拷贝，也不持有临界区。
   * 当其他任务或 ISR 可能通过 OnLatest()/StoreLatest() 更新同一 topic 时，
   * 该指针不是并发安全快照。跨任务/ISR 读取或需要稳定数据时，请使用
   * CopyLatest<T>()。
   */
  template <typename T>
  const T* Latest(Topic topic) const {
    static_assert(std::is_trivially_copyable<T>::value,
                  "mr::link::Instance::Latest<T>: T must be trivially copyable");
    const LatestSlot* slot = FindLatestSlot(topic);
    if (slot == nullptr || slot->size != sizeof(T)) {
      return nullptr;
    }
    return reinterpret_cast<const T*>(slot->payload);
  }

  template <typename T>
  const T* Latest() const {
    return Latest<T>(TopicOf<T>());
  }

  struct LatestMetadata {
    Topic topic = 0u;
    uint16_t size = 0u;
    uint32_t sequence = 0u;
  };

  bool LatestMetadataFor(Topic topic, LatestMetadata* out) const {
    if (out == nullptr) {
      return false;
    }
    ScopedIrqLock lock;
    const LatestSlot* slot = FindLatestSlot(topic);
    if (slot == nullptr) {
      return false;
    }
    out->topic = slot->topic;
    out->size = slot->size;
    out->sequence = slot->sequence;
    return true;
  }

  template <typename T>
  bool LatestMetadataFor(LatestMetadata* out) const {
    return LatestMetadataFor(TopicOf<T>(), out);
  }

  /**
   * @brief 在短临界区内拷贝 latest cache / Copy latest cache snapshot.
   *
   * 推荐用于跨任务/ISR 读取；成功时 out 获得一份稳定快照，sequence 可选返回
   * 对应缓存的更新序号。
   */
  template <typename T>
  bool CopyLatest(Topic topic, T* out, uint32_t* sequence = nullptr) const {
    static_assert(std::is_trivially_copyable<T>::value,
                  "mr::link::Instance::CopyLatest<T>: T must be trivially copyable");
    if (out == nullptr) {
      return false;
    }
    ScopedIrqLock lock;
    const LatestSlot* slot = FindLatestSlot(topic);
    if (slot == nullptr || slot->size != sizeof(T)) {
      return false;
    }
    std::memcpy(out, slot->payload, sizeof(T));
    if (sequence != nullptr) {
      *sequence = slot->sequence;
    }
    return true;
  }

  template <typename T>
  bool CopyLatest(T* out, uint32_t* sequence = nullptr) const {
    return CopyLatest(TopicOf<T>(), out, sequence);
  }

  /**
   * @brief 注销指定 cmd 的 handler / Unregister handler for cmd.
   */
  int8_t Off(uint8_t cmd) {
    int slot = FindSlot(cmd);
    if (slot < 0) {
      return MRLINK_ERR;  // 没找到
    }
    slots_[slot].used = false;
    slots_[slot].typed = nullptr;
    slots_[slot].empty = nullptr;
    return MrLink_RegisterHandler(&proto_, cmd, nullptr, nullptr);
  }

 private:
  class ScopedIrqLock {
   public:
    ScopedIrqLock() : primask_(MrLink_EnterCritical()) {}

    ~ScopedIrqLock() {
      MrLink_ExitCritical(primask_);
    }

    ScopedIrqLock(const ScopedIrqLock&) = delete;
    ScopedIrqLock& operator=(const ScopedIrqLock&) = delete;

   private:
    uint32_t primask_;
  };

  /** Type-erased typed slot: 1 entry per registered cmd. */
  struct Slot {
    bool used = false;
    uint8_t cmd = 0u;
    std::function<void(const uint8_t*)> typed;  // type-erased
    std::function<void()> empty;
  };

  struct LatestSlot {
    bool used = false;
    Topic topic = 0u;
    uint16_t size = 0u;
    uint32_t sequence = 0u;
    alignas(std::max_align_t) uint8_t payload[MRLINK_MAX_PAYLOAD_DEFAULT]{};
  };

  MrLink_t proto_{};
  Slot slots_[MAX_TYPED_HANDLERS]{};
  LatestSlot latest_slots_[MAX_LATEST_MESSAGES]{};
  uint8_t* tx_buf_ = nullptr;
  uint16_t tx_buf_size_ = 0u;
  const MrLink_Channel_t* channel_ = nullptr;
  Writer writer_;
  ErrorHandler error_handler_;

  /**
   * @brief C 库 → typed slot 的桥 / Trampoline from C library to typed slot.
   *
   * C 库已做完 length 校验 + memcpy 到 frame_buf, 此处仅 cast + 调 type-erased handler。
   */
  static int8_t Trampoline(uint8_t cmd, const void* data,
                           uint16_t size, void* ctx) {
    (void)cmd; (void)size;
    const auto* slot = static_cast<const Slot*>(ctx);
    if (slot->typed) {
      slot->typed(static_cast<const uint8_t*>(data));
    }
    return MRLINK_OK;
  }

  static int8_t EmptyTrampoline(uint8_t cmd, const uint8_t* payload,
                                uint16_t payload_len, void* ctx) {
    (void)cmd; (void)payload;
    const auto* slot = static_cast<const Slot*>(ctx);
    if (payload_len != 0u) {
      return MRLINK_ERR_ARGS;
    }
    if (slot->empty) {
      slot->empty();
    }
    return MRLINK_OK;
  }

  static void ErrorTrampoline(const MrLink_ErrorInfo_t* info, void* ctx) {
    if (info == nullptr || ctx == nullptr) {
      return;
    }
    auto* self = static_cast<Instance*>(ctx);
    if (self->error_handler_ != nullptr) {
      self->error_handler_(*info);
    }
  }

  int FindSlot(uint8_t cmd) const {
    for (int i = 0; i < MAX_TYPED_HANDLERS; i++) {
      if (slots_[i].used && slots_[i].cmd == cmd) {
        return i;
      }
    }
    return -1;
  }

  int AllocSlot() {
    for (int i = 0; i < MAX_TYPED_HANDLERS; i++) {
      if (!slots_[i].used) {
        return i;
      }
    }
    return -1;
  }

  LatestSlot* FindOrAllocLatestSlot(Topic topic) {
    LatestSlot* free_slot = nullptr;
    for (auto& slot : latest_slots_) {
      if (slot.used && slot.topic == topic) {
        return &slot;
      }
      if (!slot.used && free_slot == nullptr) {
        free_slot = &slot;
      }
    }
    return free_slot;
  }

  const LatestSlot* FindLatestSlot(Topic topic) const {
    for (const auto& slot : latest_slots_) {
      if (slot.used && slot.topic == topic) {
        return &slot;
      }
    }
    return nullptr;
  }

  uint16_t CopyBuiltFrame(uint8_t* out_buf, uint16_t out_buf_size,
                          uint16_t frame_len) const {
    if (frame_len == 0u || tx_buf_ == nullptr || frame_len > tx_buf_size_) {
      return 0u;
    }
    if (out_buf == nullptr || frame_len > out_buf_size) {
      return 0u;
    }
    std::memcpy(out_buf, tx_buf_, frame_len);
    return frame_len;
  }

  bool WriteBuiltFrame(uint16_t frame_len) {
    if (frame_len == 0u || tx_buf_ == nullptr || frame_len > tx_buf_size_ ||
        writer_ == nullptr) {
      return false;
    }
    return writer_(tx_buf_, frame_len);
  }
};

template <uint16_t RxBufSize = 256u,
          uint16_t TxBufSize = MRLINK_MAX_FRAME_SIZE,
          uint16_t PollBufSize = MRLINK_MAX_FRAME_SIZE,
          uint8_t UartRxSlotCount = 4u,
          uint16_t UartRxSlotSize = PollBufSize>
class StaticInstance : public Instance {
 public:
  StaticInstance() = default;
  StaticInstance(const StaticInstance&) = delete;
  StaticInstance& operator=(const StaticInstance&) = delete;

  int8_t Begin(const MrLink_Config_t* config = nullptr) {
    return Init(config, rx_buf_, RxBufSize, tx_buf_, TxBufSize);
  }

  int8_t BeginUart(BSP_UART_t uart,
                   const MrLink_Config_t* config = nullptr,
                   MrLink_ChannelNotify_t rx_ready = nullptr,
                   void* rx_ready_ctx = nullptr) {
    int8_t result = Begin(config);
    if (result != MRLINK_OK) {
      return result;
    }

    MrLink_ChannelUartConfig_t uart_config = {};
    uart_config.uart = uart;
    uart_config.rx_slots = &uart_rx_slots_[0][0];
    uart_config.rx_slot_size = UartRxSlotSize;
    uart_config.rx_slot_count = UartRxSlotCount;
    uart_config.rx_len_storage = uart_rx_len_;
    uart_config.rx_ready = rx_ready;
    uart_config.rx_ready_ctx = rx_ready_ctx;

    result = MrLink_Channel_InitUart(&channel_, &uart_config);
    if (result != MRLINK_CHANNEL_OK) {
      return result;
    }
    result = BindChannel(&channel_);
    if (result != MRLINK_CHANNEL_OK) {
      return result;
    }
    return StartChannelRx();
  }

  int8_t BeginFdcan(const MrLink_ChannelFdcanConfig_t& channel_config,
                    const MrLink_Config_t* config = nullptr) {
    const uint16_t max_frame_size = MrLink_MaxFrameSizeForConfig(config);
    const uint8_t channel_max_frame_size =
        (channel_config.max_frame_size > 0u)
            ? channel_config.max_frame_size
            : MRLINK_CHANNEL_FDCAN_MAX_FRAME_SIZE;
    if (max_frame_size == 0u || max_frame_size > channel_max_frame_size) {
      return MRLINK_ERR_ARGS;
    }

    int8_t result = Begin(config);
    if (result != MRLINK_OK) {
      return result;
    }
    result = MrLink_Channel_InitFdcan(&channel_, &channel_config);
    if (result != MRLINK_CHANNEL_OK) {
      return result;
    }
    result = BindChannel(&channel_);
    if (result != MRLINK_CHANNEL_OK) {
      return result;
    }
    return StartChannelRx();
  }

  int8_t BeginUsb(const MrLink_ChannelUsbConfig_t& channel_config,
                  const MrLink_Config_t* config = nullptr) {
    int8_t result = Begin(config);
    if (result != MRLINK_OK) {
      return result;
    }
    result = MrLink_Channel_InitUsb(&channel_, &channel_config);
    if (result != MRLINK_CHANNEL_OK) {
      return result;
    }
    result = BindChannel(&channel_);
    if (result != MRLINK_CHANNEL_OK) {
      return result;
    }
    return StartChannelRx();
  }

  uint16_t Poll() {
    return PollChannelRx(poll_buf_, PollBufSize, true);
  }

  uint16_t PollRx() {
    return PollChannelRx(poll_buf_, PollBufSize, false);
  }

  uint16_t PollAndDispatch() {
    return Poll();
  }

  MrLink_Channel_t* Channel() {
    return &channel_;
  }

  const MrLink_Channel_t* Channel() const {
    return &channel_;
  }

 private:
  static_assert(RxBufSize >= 4u, "mr::link::StaticInstance: RxBufSize too small");
  static_assert(TxBufSize >= MRLINK_HEADER_LEN + MRLINK_LEN_FIELD_LEN +
                                 MRLINK_CMD_FIELD_LEN,
                "mr::link::StaticInstance: TxBufSize too small");
  static_assert(PollBufSize > 0u, "mr::link::StaticInstance: PollBufSize must be > 0");
  static_assert(UartRxSlotCount > 0u,
                "mr::link::StaticInstance: UartRxSlotCount must be > 0");
  static_assert(UartRxSlotSize > 0u,
                "mr::link::StaticInstance: UartRxSlotSize must be > 0");

  MrLink_Channel_t channel_{};
  uint8_t rx_buf_[RxBufSize]{};
  uint8_t tx_buf_[TxBufSize]{};
  uint8_t poll_buf_[PollBufSize]{};
  uint8_t uart_rx_slots_[UartRxSlotCount][UartRxSlotSize]{};
  volatile uint16_t uart_rx_len_[UartRxSlotCount]{};
};

template <uint16_t RxBufSize = 256u,
          uint16_t TxBufSize = MRLINK_MAX_FRAME_SIZE,
          uint16_t PollBufSize = MRLINK_MAX_FRAME_SIZE,
          uint8_t UartRxSlotCount = 4u,
          uint16_t UartRxSlotSize = PollBufSize>
using Bus = StaticInstance<RxBufSize, TxBufSize, PollBufSize,
                           UartRxSlotCount, UartRxSlotSize>;

}  // namespace mr::link
