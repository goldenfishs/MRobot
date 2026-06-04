/**
  ******************************************************************************
  * @file    mrlink_lite.hpp
  * @brief   Zero-std::function C++ wrapper for mrlink.
  *
  * This header is intended for STM32 paths where deterministic memory use is
  * more important than captured-lambda ergonomics. It keeps the public shape
  * close to mrlink.hpp while storing only function pointers and caller contexts.
  ******************************************************************************
  */

#pragma once

#include <cstdint>
#include <cstring>
#include <type_traits>

#include "device/mrlink/mrlink.h"
#include "device/mrlink/mrlink_channel.h"

namespace mr {
namespace link {
namespace lite {

using Topic = uint8_t;
using Writer = bool (*)(uint8_t* frame, uint16_t frame_len, void* ctx);
using ErrorHandler = void (*)(const MrLink_ErrorInfo_t& info, void* ctx);
using EmptyHandler = void (*)(void* ctx);

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
    return static_cast<Topic>(MessageTraits<T>::topic);
  }
};

template <typename T>
struct TopicResolver<T, true, true> {
  static constexpr Topic Value() {
    return static_cast<Topic>(MessageTraits<T>::topic);
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
                  "mr::link::lite::TopicOf<T>: add T::topic or specialize "
                  "mr::link::lite::MessageTraits<T>");
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

#define MRLINK_LITE_TOPIC(PayloadType, TopicValue)                  \
  namespace mr { namespace link { namespace lite {                  \
  template <>                                                       \
  struct MessageTraits<PayloadType> {                               \
    static constexpr Topic topic = static_cast<Topic>(TopicValue);  \
  };                                                               \
  } } }

#define MRLINK_LITE_MESSAGE(PayloadType, TopicValue) \
  MRLINK_LITE_TOPIC(PayloadType, TopicValue)

template <uint8_t MaxHandlers = 16u>
class Instance {
 public:
  Instance() = default;
  Instance(const Instance&) = delete;
  Instance& operator=(const Instance&) = delete;

  int8_t Init(const MrLink_Config_t* cfg,
              uint8_t* rx_buf, uint16_t rx_buf_size,
              uint8_t* tx_buf, uint16_t tx_buf_size) {
    tx_buf_ = tx_buf;
    tx_buf_size_ = tx_buf_size;
    ClearSlots();
    return MrLink_Init(&proto_, cfg, rx_buf, rx_buf_size,
                       tx_buf, tx_buf_size);
  }

  void Reset() {
    MrLink_Reset(&proto_);
    ClearSlots();
  }

  int8_t PushBytes(const uint8_t* data, uint16_t len) {
    return MrLink_PushBytes(&proto_, data, len);
  }

  int8_t Dispatch() {
    return MrLink_Dispatch(&proto_);
  }

  int8_t FeedBytes(const uint8_t* data, uint16_t len) {
    return MrLink_FeedBytes(&proto_, data, len);
  }

  int8_t Parse(uint8_t* out_cmd,
               const uint8_t** out_payload,
               uint16_t* out_payload_len) {
    return MrLink_Parse(&proto_, out_cmd, out_payload, out_payload_len);
  }

  uint16_t Build(Topic topic, const uint8_t* payload, uint16_t payload_len) {
    return MrLink_Build(&proto_, topic, payload, payload_len);
  }

  uint16_t BuildEmpty(Topic topic) {
    return MrLink_Build(&proto_, topic, nullptr, 0u);
  }

  template <typename T>
  uint16_t Build(Topic topic, const T& payload) {
    static_assert(std::is_trivially_copyable<T>::value,
                  "mr::link::lite::Instance::Build<T>: T must be trivially copyable");
    return MrLink_Build(&proto_, topic,
                        reinterpret_cast<const uint8_t*>(&payload), sizeof(T));
  }

  template <typename T>
  uint16_t Build(const T& payload) {
    return Build(TopicOf<T>(), payload);
  }

  bool PublishEmpty(Topic topic) {
    return WriteBuiltFrame(BuildEmpty(topic));
  }

  template <typename T>
  bool Publish(Topic topic, const T& payload) {
    static_assert(std::is_trivially_copyable<T>::value,
                  "mr::link::lite::Instance::Publish<T>: T must be trivially copyable");
    return WriteBuiltFrame(Build(topic, payload));
  }

  template <typename T>
  bool Publish(const T& payload) {
    return Publish(TopicOf<T>(), payload);
  }

  const uint8_t* TxBuffer() const {
    return tx_buf_;
  }

  void SetWriter(Writer writer, void* ctx = nullptr) {
    channel_ = nullptr;
    writer_ = writer;
    writer_ctx_ = ctx;
  }

  void ClearWriter() {
    channel_ = nullptr;
    writer_ = nullptr;
    writer_ctx_ = nullptr;
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
    writer_ = &Instance::ChannelWriter;
    writer_ctx_ = const_cast<MrLink_Channel_t*>(channel);
    return MRLINK_CHANNEL_OK;
  }

  void ClearChannel() {
    channel_ = nullptr;
    writer_ = nullptr;
    writer_ctx_ = nullptr;
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
      (void)PushBytes(scratch, len);
      if (dispatch) {
        (void)Dispatch();
      }
    }
    return len;
  }

  int8_t OnError(ErrorHandler handler, void* ctx = nullptr) {
    error_handler_ = handler;
    error_ctx_ = ctx;
    return MrLink_SetErrorHandler(&proto_,
                                  error_handler_ != nullptr
                                      ? &Instance::ErrorTrampoline
                                      : nullptr,
                                  this);
  }

  void ClearErrorHandler() {
    error_handler_ = nullptr;
    error_ctx_ = nullptr;
    (void)MrLink_SetErrorHandler(&proto_, nullptr, nullptr);
  }

  int8_t On(Topic topic, EmptyHandler handler, void* ctx = nullptr) {
    if (handler == nullptr) {
      return Off(topic);
    }

    Slot* slot = FindOrAllocSlot(topic);
    if (slot == nullptr) {
      return MRLINK_ERR_ARGS;
    }

    slot->used = true;
    slot->topic = topic;
    slot->kind = SlotKind::Empty;
    slot->empty = handler;
    slot->typed = nullptr;
    slot->invoke = nullptr;
    slot->user_ctx = ctx;
    return MrLink_RegisterHandler(&proto_, topic,
                                  &Instance::EmptyTrampoline, slot);
  }

  int8_t Subscribe(Topic topic, EmptyHandler handler, void* ctx = nullptr) {
    return On(topic, handler, ctx);
  }

  template <typename T>
  int8_t On(Topic topic, void (*handler)(const T&, void*),
            void* ctx = nullptr) {
    static_assert(std::is_trivially_copyable<T>::value,
                  "mr::link::lite::Instance::On<T>: T must be trivially copyable");
    if (handler == nullptr) {
      return Off(topic);
    }

    Slot* slot = FindOrAllocSlot(topic);
    if (slot == nullptr) {
      return MRLINK_ERR_ARGS;
    }

    slot->used = true;
    slot->topic = topic;
    slot->kind = SlotKind::Typed;
    slot->empty = nullptr;
    slot->typed = reinterpret_cast<ErasedFunction>(handler);
    slot->invoke = &Instance::InvokeTyped<T>;
    slot->user_ctx = ctx;
    return MrLink_RegisterTypedHandler(&proto_, topic, sizeof(T),
                                       &Instance::TypedTrampoline, slot);
  }

  template <typename T>
  int8_t On(void (*handler)(const T&, void*), void* ctx = nullptr) {
    return On<T>(TopicOf<T>(), handler, ctx);
  }

  template <typename T>
  int8_t Subscribe(Topic topic, void (*handler)(const T&, void*),
                   void* ctx = nullptr) {
    return On<T>(topic, handler, ctx);
  }

  template <typename T>
  int8_t Subscribe(void (*handler)(const T&, void*), void* ctx = nullptr) {
    return On<T>(handler, ctx);
  }

  int8_t Off(Topic topic) {
    Slot* slot = FindSlot(topic);
    if (slot == nullptr) {
      return MRLINK_ERR_ARGS;
    }
    *slot = Slot{};
    return MrLink_RegisterHandler(&proto_, topic, nullptr, nullptr);
  }

  const MrLink_Stats_t* GetStats() const {
    return MrLink_GetStats(&proto_);
  }

 protected:
  MrLink_t* Proto() {
    return &proto_;
  }

  const MrLink_t* Proto() const {
    return &proto_;
  }

 private:
  enum class SlotKind : uint8_t {
    Empty,
    Typed,
  };

  using ErasedFunction = void (*)();

  struct Slot;
  using TypedInvoker = void (*)(const void* data, Slot* slot);

  struct Slot {
    bool used = false;
    Topic topic = 0u;
    SlotKind kind = SlotKind::Empty;
    EmptyHandler empty = nullptr;
    ErasedFunction typed = nullptr;
    TypedInvoker invoke = nullptr;
    void* user_ctx = nullptr;
  };

  static bool ChannelWriter(uint8_t* frame, uint16_t frame_len, void* ctx) {
    return MrLink_Channel_Send(static_cast<const MrLink_Channel_t*>(ctx),
                               frame, frame_len) == MRLINK_CHANNEL_OK;
  }

  static int8_t EmptyTrampoline(uint8_t cmd, const uint8_t* payload,
                                uint16_t payload_len, void* ctx) {
    (void)cmd;
    (void)payload;
    Slot* slot = static_cast<Slot*>(ctx);
    if (slot == nullptr || slot->kind != SlotKind::Empty ||
        payload_len != 0u) {
      return MRLINK_ERR_ARGS;
    }
    if (slot->empty != nullptr) {
      slot->empty(slot->user_ctx);
    }
    return MRLINK_OK;
  }

  static int8_t TypedTrampoline(uint8_t cmd, const void* data,
                                uint16_t size, void* ctx) {
    (void)cmd;
    (void)size;
    Slot* slot = static_cast<Slot*>(ctx);
    if (slot == nullptr || slot->kind != SlotKind::Typed ||
        slot->invoke == nullptr) {
      return MRLINK_ERR_ARGS;
    }
    slot->invoke(data, slot);
    return MRLINK_OK;
  }

  template <typename T>
  static void InvokeTyped(const void* data, Slot* slot) {
    using Handler = void (*)(const T&, void*);
    Handler handler = reinterpret_cast<Handler>(slot->typed);
    if (handler == nullptr || data == nullptr) {
      return;
    }
    T value;
    std::memcpy(&value, data, sizeof(T));
    handler(value, slot->user_ctx);
  }

  static void ErrorTrampoline(const MrLink_ErrorInfo_t* info, void* ctx) {
    if (info == nullptr || ctx == nullptr) {
      return;
    }
    auto* self = static_cast<Instance*>(ctx);
    if (self->error_handler_ != nullptr) {
      self->error_handler_(*info, self->error_ctx_);
    }
  }

  Slot* FindSlot(Topic topic) {
    for (auto& slot : slots_) {
      if (slot.used && slot.topic == topic) {
        return &slot;
      }
    }
    return nullptr;
  }

  Slot* FindOrAllocSlot(Topic topic) {
    if (Slot* existing = FindSlot(topic)) {
      return existing;
    }
    for (auto& slot : slots_) {
      if (!slot.used) {
        return &slot;
      }
    }
    return nullptr;
  }

  void ClearSlots() {
    for (auto& slot : slots_) {
      slot = Slot{};
    }
  }

  bool WriteBuiltFrame(uint16_t frame_len) {
    if (frame_len == 0u || tx_buf_ == nullptr || frame_len > tx_buf_size_ ||
        writer_ == nullptr) {
      return false;
    }
    return writer_(tx_buf_, frame_len, writer_ctx_);
  }

  MrLink_t proto_{};
  Slot slots_[MaxHandlers]{};
  uint8_t* tx_buf_ = nullptr;
  uint16_t tx_buf_size_ = 0u;
  const MrLink_Channel_t* channel_ = nullptr;
  Writer writer_ = nullptr;
  void* writer_ctx_ = nullptr;
  ErrorHandler error_handler_ = nullptr;
  void* error_ctx_ = nullptr;
};

template <uint16_t RxBufSize = 256u,
          uint16_t TxBufSize = MRLINK_MAX_FRAME_SIZE,
          uint16_t PollBufSize = MRLINK_MAX_FRAME_SIZE,
          uint8_t MaxHandlers = 16u,
          uint8_t UartRxSlotCount = 4u,
          uint16_t UartRxSlotSize = PollBufSize>
class StaticInstance : public Instance<MaxHandlers> {
 public:
  StaticInstance() = default;
  StaticInstance(const StaticInstance&) = delete;
  StaticInstance& operator=(const StaticInstance&) = delete;

  int8_t Begin(const MrLink_Config_t* config = nullptr) {
    return this->Init(config, rx_buf_, RxBufSize, tx_buf_, TxBufSize);
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
    result = this->BindChannel(&channel_);
    if (result != MRLINK_CHANNEL_OK) {
      return result;
    }
    return this->StartChannelRx();
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
    result = this->BindChannel(&channel_);
    if (result != MRLINK_CHANNEL_OK) {
      return result;
    }
    return this->StartChannelRx();
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
    result = this->BindChannel(&channel_);
    if (result != MRLINK_CHANNEL_OK) {
      return result;
    }
    return this->StartChannelRx();
  }

  uint16_t Poll() {
    return this->PollChannelRx(poll_buf_, PollBufSize, true);
  }

  uint16_t PollRx() {
    return this->PollChannelRx(poll_buf_, PollBufSize, false);
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
  static_assert(RxBufSize >= MRLINK_HEADER_LEN + MRLINK_LEN_FIELD_LEN +
                                 MRLINK_CMD_FIELD_LEN,
                "mr::link::lite::StaticInstance: RxBufSize too small");
  static_assert(TxBufSize >= MRLINK_HEADER_LEN + MRLINK_LEN_FIELD_LEN +
                                 MRLINK_CMD_FIELD_LEN,
                "mr::link::lite::StaticInstance: TxBufSize too small");
  static_assert(PollBufSize > 0u,
                "mr::link::lite::StaticInstance: PollBufSize must be > 0");
  static_assert(UartRxSlotCount >= 2u,
                "mr::link::lite::StaticInstance: UartRxSlotCount must be >= 2");
  static_assert(UartRxSlotSize > 0u,
                "mr::link::lite::StaticInstance: UartRxSlotSize must be > 0");

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
          uint8_t MaxHandlers = 16u,
          uint8_t UartRxSlotCount = 4u,
          uint16_t UartRxSlotSize = PollBufSize>
using Bus = StaticInstance<RxBufSize, TxBufSize, PollBufSize,
                           MaxHandlers, UartRxSlotCount, UartRxSlotSize>;

}  // namespace lite
}  // namespace link
}  // namespace mr
