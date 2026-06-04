#pragma once

/**
 * @file spsc_ringbuf.hpp
 * @brief C++ 包装：SpscRingBufView（外部存储）和 StaticSpscRingBuf<N>（内嵌存储）。
 *
 * @section usage_cpp 用法示例
 *
 * @subsection view SpscRingBufView —— 存储由调用方管理
 *
 * @code
 *   // 多个独立实例，零模块级状态
 *   static uint8_t sensor_a_storage[256];
 *   static uint8_t sensor_b_storage[512];
 *
 *   static mr::comp::SpscRingBufView sensor_a_rb(sensor_a_storage,
 *                                                sizeof(sensor_a_storage));
 *   static mr::comp::SpscRingBufView sensor_b_rb(sensor_b_storage,
 *                                                sizeof(sensor_b_storage));
 *
 *   // 生产者
 *   sensor_a_rb.TryPushObject(SensorSample{ /* ... *\/ });
 *
 *   // 消费者
 *   SensorSample s;
 *   if (sensor_a_rb.TryPopObject(&s)) {
 *     // 处理 s
 *   }
 * @endcode
 *
 * @subsection static StaticSpscRingBuf<N> —— 存储随对象一起静态分配
 *
 * @code
 *   // 容量在编译期确定；对象是 trivially-copyable，可放全局/静态
 *   static mr::comp::StaticSpscRingBuf<1024> log_rb;
 *
 *   // 推一条强类型记录
 *   LogEntry e{ /* ... *\/ };
 *   if (!log_rb.TryPushObject(e)) {
 *     // 队列满
 *   }
 *
 *   // 类型化弹出
 *   LogEntry out;
 *   if (log_rb.TryPopObject(&out)) {
 *     // 处理 out
 *   }
 *
 *   // 也可继续走原始字节接口
 *   uint8_t buf[64];
 *   uint16_t got = log_rb.Pop(buf, sizeof(buf));
 * @endcode
 *
 * @section api_cpp 可用 API（C++ 接口）
 *
 * 两个包装类共用一套方法名（StaticSpscRingBuf 内部委托给 View）：
 *
 * 生命周期：
 *   - Init(storage, size)                 // 绑定外部存储并清零 head/tail
 *   - Reset()                             // 丢弃所有数据
 *
 * 字节级读写（Push/Pop 是"尽力而为"，TryPush/TryPop 是"全或无"）：
 *   - Push(data, len)        -> uint16_t  // 实际写入字节数
 *   - TryPush(data, len)     -> bool      // 全部写入返回 true
 *   - Pop(dst, len)          -> uint16_t  // 实际读出字节数
 *   - TryPop(dst, len)       -> bool      // 全部读出返回 true
 *   - Peek(dst, len)         -> uint16_t  // 窥视但不推进 tail
 *   - Drop(len)              -> uint16_t  // 直接推进 tail
 *
 * 强类型读写（要求 T 是 trivially-copyable）：
 *   - TryPushObject<T>(const T& value) -> bool
 *   - TryPopObject<T>(T* out)          -> bool
 *   - TryPeekObject<T>(T* out) const   -> bool
 *
 * 容量查询：
 *   - Size()                 -> uint16_t   // 已用字节数
 *   - Space()                -> uint16_t   // 剩余可写字节数
 *   - Capacity()             -> uint16_t   // 最大容量（size-1）
 *   - Empty()                -> bool
 *
 * 原始句柄访问（用于和 C API 互操作，比如注册到 DMA 回调）：
 *   - raw()                  -> SpscRingBuf_t*
 *   - raw() const            -> const SpscRingBuf_t*
 *
 * @subsection threadsafe 线程安全
 * 同 spsc_ringbuf.h：单生产者写 Push/TryPush，单消费者写 Pop/TryPop/Drop/Peek。
 * TryPushObject/TryPopObject 内部是 memcpy 之后的两端长度校验，
 * 跨字段读到的对象在多生产者场景下可能撕裂，仅限 SPSC 使用。
 */

#include <cstdint>
#include <type_traits>

#include "component/container/spsc_ringbuf.h"

namespace mr::comp {

class SpscRingBufView final {
 public:
  SpscRingBufView() = default;

  SpscRingBufView(uint8_t* storage, uint16_t size) {
    (void)Init(storage, size);
  }

  int8_t Init(uint8_t* storage, uint16_t size) {
    return SpscRingBuf_Init(&rb_, storage, size);
  }

  uint16_t Push(const uint8_t* data, uint16_t len) {
    return SpscRingBuf_Put(&rb_, data, len);
  }

  bool TryPush(const uint8_t* data, uint16_t len) {
    if (data == nullptr || Space() < len) {
      return false;
    }
    return Push(data, len) == len;
  }

  uint16_t Pop(uint8_t* dst, uint16_t len) {
    return SpscRingBuf_Get(&rb_, dst, len);
  }

  bool TryPop(uint8_t* dst, uint16_t len) {
    if (dst == nullptr || Size() < len) {
      return false;
    }
    return Pop(dst, len) == len;
  }

  uint16_t Peek(uint8_t* dst, uint16_t len) const {
    return SpscRingBuf_Peek(&rb_, dst, len);
  }

  uint16_t Drop(uint16_t len) {
    return SpscRingBuf_Drop(&rb_, len);
  }

  uint16_t Size() const {
    return SpscRingBuf_Size(&rb_);
  }

  uint16_t Space() const {
    return SpscRingBuf_Space(&rb_);
  }

  uint16_t Capacity() const {
    return (rb_.size > 0u) ? static_cast<uint16_t>(rb_.size - 1u) : 0u;
  }

  bool Empty() const {
    return SpscRingBuf_IsEmpty(&rb_);
  }

  void Reset() {
    SpscRingBuf_Reset(&rb_);
  }

  template <typename T>
  bool TryPushObject(const T& value) {
    static_assert(std::is_trivially_copyable<T>::value,
                  "SpscRingBufView::TryPushObject requires a trivially copyable type");
    return TryPush(reinterpret_cast<const uint8_t*>(&value),
                   static_cast<uint16_t>(sizeof(T)));
  }

  template <typename T>
  bool TryPopObject(T* out) {
    static_assert(std::is_trivially_copyable<T>::value,
                  "SpscRingBufView::TryPopObject requires a trivially copyable type");
    return TryPop(reinterpret_cast<uint8_t*>(out),
                  static_cast<uint16_t>(sizeof(T)));
  }

  template <typename T>
  bool TryPeekObject(T* out) const {
    static_assert(std::is_trivially_copyable<T>::value,
                  "SpscRingBufView::TryPeekObject requires a trivially copyable type");
    if (out == nullptr || Size() < sizeof(T)) {
      return false;
    }
    return Peek(reinterpret_cast<uint8_t*>(out),
                static_cast<uint16_t>(sizeof(T))) == sizeof(T);
  }

  SpscRingBuf_t* raw() {
    return &rb_;
  }

  const SpscRingBuf_t* raw() const {
    return &rb_;
  }

 private:
  SpscRingBuf_t rb_{};
};

template <uint16_t StorageSize>
class StaticSpscRingBuf final {
 public:
  static_assert(StorageSize >= 2u,
                "StaticSpscRingBuf storage must be at least 2 bytes");

  StaticSpscRingBuf() {
    (void)view_.Init(storage_, StorageSize);
  }

  uint16_t Push(const uint8_t* data, uint16_t len) {
    return view_.Push(data, len);
  }

  bool TryPush(const uint8_t* data, uint16_t len) {
    return view_.TryPush(data, len);
  }

  uint16_t Pop(uint8_t* dst, uint16_t len) {
    return view_.Pop(dst, len);
  }

  bool TryPop(uint8_t* dst, uint16_t len) {
    return view_.TryPop(dst, len);
  }

  uint16_t Peek(uint8_t* dst, uint16_t len) const {
    return view_.Peek(dst, len);
  }

  uint16_t Drop(uint16_t len) {
    return view_.Drop(len);
  }

  uint16_t Size() const {
    return view_.Size();
  }

  uint16_t Space() const {
    return view_.Space();
  }

  uint16_t Capacity() const {
    return view_.Capacity();
  }

  bool Empty() const {
    return view_.Empty();
  }

  void Reset() {
    view_.Reset();
  }

  template <typename T>
  bool TryPushObject(const T& value) {
    return view_.TryPushObject(value);
  }

  template <typename T>
  bool TryPopObject(T* out) {
    return view_.TryPopObject(out);
  }

  template <typename T>
  bool TryPeekObject(T* out) const {
    return view_.TryPeekObject(out);
  }

  SpscRingBufView& view() {
    return view_;
  }

  const SpscRingBufView& view() const {
    return view_;
  }

  SpscRingBuf_t* raw() {
    return view_.raw();
  }

  const SpscRingBuf_t* raw() const {
    return view_.raw();
  }

 private:
  uint8_t storage_[StorageSize]{};
  SpscRingBufView view_;
};

}  // namespace mr::comp
