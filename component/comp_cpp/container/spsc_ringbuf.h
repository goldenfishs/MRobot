/**
 ******************************************************************************
 * @file    spsc_ringbuf.h
 * @brief   通用单生产者-单消费者字节环形缓冲 / Generic SPSC byte ring buffer.
 *
 * @section usage 用法示例
 *
 * 模块无任何 static/global 状态，可同时创建任意多个互相独立的实例；
 * 每个实例需要调用方提供一段存储区（栈/全局/静态均可，模块不分配）。
 * 容量上限 65535 字节（size 字段为 uint16_t），要更大请用 .hpp 模板版本。
 *
 * @code
 *   // 1. 为每个通道准备独立的存储区与句柄
 *   static uint8_t  sensor_a_storage[256];
 *   static uint8_t  sensor_b_storage[512];
 *   static uint8_t  log_storage[1024];
 *
 *   static SpscRingBuf_t sensor_a_rb;
 *   static SpscRingBuf_t sensor_b_rb;
 *   static SpscRingBuf_t log_rb;
 *
 *   // 2. 初始化（head/tail 自动清零，storage 内容无关紧要）
 *   SpscRingBuf_Init(&sensor_a_rb, sensor_a_storage, sizeof(sensor_a_storage));
 *   SpscRingBuf_Init(&sensor_b_rb, sensor_b_storage, sizeof(sensor_b_storage));
 *   SpscRingBuf_Init(&log_rb,       log_storage,       sizeof(log_storage));
 *
 *   // 3. 生产者（ISR / 高频任务）—— 单写者写 head
 *   void SensorA_ProducerISR(const uint8_t *data, uint16_t len) {
 *     (void)SpscRingBuf_Put(&sensor_a_rb, data, len);
 *   }
 *
 *   // 4. 消费者（低频任务）—— 单读者写 tail
 *   void SensorA_ConsumerTask(void) {
 *     uint8_t buf[64];
 *     uint16_t got = SpscRingBuf_Get(&sensor_a_rb, buf, sizeof(buf));
 *     // 处理 buf[0..got) ...
 *   }
 *
 *   // 5. 容量查询
 *   if (SpscRingBuf_Space(&log_rb) >= sizeof(LogEntry_t)) {
 *     // 有空位，可以压入
 *   }
 * @endcode
 *
 * @section api 可用 API（C 接口）
 *
 * 生命周期：
 *   - SpscRingBuf_Init(rb, storage, size)  // 绑定外部存储并清零 head/tail
 *   - SpscRingBuf_Reset(rb)                // 丢弃所有数据，head/tail=0
 *
 * 字节级读写（返回实际处理字节数；空间/数据不足时返回 0 或部分长度）：
 *   - SpscRingBuf_Put(rb, data, len)       // 生产者写入（可能部分写）
 *   - SpscRingBuf_Get(rb, dst, len)        // 消费者读取并推进 tail
 *   - SpscRingBuf_Peek(rb, dst, len)       // 消费者读取但不推进 tail
 *   - SpscRingBuf_Drop(rb, len)            // 直接推进 tail，丢弃数据
 *
 * 容量查询（用于在写之前预检，避免部分写）：
 *   - SpscRingBuf_Size(rb)                 // 当前已用字节数
 *   - SpscRingBuf_Space(rb)                // 当前剩余可写字节数
 *   - SpscRingBuf_IsEmpty(rb)              // 是否空（Size==0）
 *
 * 返回值约定：
 *   - 长度类（Put/Get/Peek/Drop/Size/Space）返回 uint16_t；
 *     Put/Get 可处理流式数据，空间不足时返回实际写入/读出的字节数。
 *   - 初始化类（Init）返回 int8_t，取值见 SPSC_RINGBUF_OK/ERR/ERR_NULL/ERR_ARGS。
 *
 * @section safety 线程安全
 * - 同一时刻只允许一个生产者写 Put、一个消费者写 Get/Pop/Drop。
 * - Size/Space/IsEmpty/Peek 允许多读，但读到的值可能在下一条指令失效。
 * - 若生产/消费侧都在任务上下文（非 ISR），注意 head/tail 是 16 位
 *   自然回绕，不需要额外取模。
 ******************************************************************************
 */

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>
#include <stdint.h>

#define SPSC_RINGBUF_OK       (0)
#define SPSC_RINGBUF_ERR      (-1)
#define SPSC_RINGBUF_ERR_NULL (-2)
#define SPSC_RINGBUF_ERR_ARGS (-3)

typedef struct {
  uint8_t *buf;
  uint16_t size;
  volatile uint16_t head;
  volatile uint16_t tail;
} SpscRingBuf_t;

int8_t SpscRingBuf_Init(SpscRingBuf_t *rb, uint8_t *storage, uint16_t size);
uint16_t SpscRingBuf_Put(SpscRingBuf_t *rb, const uint8_t *data, uint16_t len);
uint16_t SpscRingBuf_Get(SpscRingBuf_t *rb, uint8_t *dst, uint16_t len);
uint16_t SpscRingBuf_Drop(SpscRingBuf_t *rb, uint16_t len);
uint16_t SpscRingBuf_Peek(const SpscRingBuf_t *rb, uint8_t *dst, uint16_t len);
uint16_t SpscRingBuf_Size(const SpscRingBuf_t *rb);
uint16_t SpscRingBuf_Space(const SpscRingBuf_t *rb);
bool SpscRingBuf_IsEmpty(const SpscRingBuf_t *rb);
void SpscRingBuf_Reset(SpscRingBuf_t *rb);

#ifdef __cplusplus
}
#endif