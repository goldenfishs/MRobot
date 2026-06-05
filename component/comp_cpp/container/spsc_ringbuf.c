/**
 ******************************************************************************
 * @file    spsc_ringbuf.c
 * @brief   通用单生产者-单消费者字节环形缓冲实现 / Generic SPSC byte ring buffer impl.
 ******************************************************************************
 */

#include "component/container/spsc_ringbuf.h"

#include <string.h>

#include "cmsis_compiler.h"

static uint32_t SpscRingBuf_EnterCritical(void) {
  const uint32_t primask = __get_PRIMASK();
  __disable_irq();
  return primask;
}

static void SpscRingBuf_ExitCritical(uint32_t primask) {
  if (primask == 0u) {
    __enable_irq();
  }
}

static uint16_t SpscRingBuf_Used(uint16_t size, uint16_t head, uint16_t tail) {
  return (head >= tail) ? (uint16_t)(head - tail)
                        : (uint16_t)(size - tail + head);
}

static bool SpscRingBuf_IsValid(const SpscRingBuf_t *rb) {
  return rb != NULL && rb->buf != NULL && rb->size >= 2u;
}

int8_t SpscRingBuf_Init(SpscRingBuf_t *rb, uint8_t *storage, uint16_t size) {
  if (rb == NULL || storage == NULL) {
    return SPSC_RINGBUF_ERR_NULL;
  }
  if (size < 2u) {
    return SPSC_RINGBUF_ERR_ARGS;
  }

  rb->buf = storage;
  rb->size = size;
  rb->head = 0u;
  rb->tail = 0u;
  return SPSC_RINGBUF_OK;
}

uint16_t SpscRingBuf_Put(SpscRingBuf_t *rb, const uint8_t *data, uint16_t len) {
  if (!SpscRingBuf_IsValid(rb) || data == NULL || len == 0u) {
    return 0u;
  }

  const uint32_t primask = SpscRingBuf_EnterCritical();
  const uint16_t size = rb->size;
  const uint16_t head = rb->head;
  const uint16_t tail = rb->tail;
  const uint16_t used = SpscRingBuf_Used(size, head, tail);
  uint16_t space = (uint16_t)(size - 1u - used);

  if (len > space) {
    len = space;
  }
  if (len == 0u) {
    SpscRingBuf_ExitCritical(primask);
    return 0u;
  }

  const uint16_t first_chunk = (head + len > size) ? (uint16_t)(size - head)
                                                   : len;
  memcpy(&rb->buf[head], data, first_chunk);

  const uint16_t second_chunk = (uint16_t)(len - first_chunk);
  if (second_chunk > 0u) {
    memcpy(&rb->buf[0], &data[first_chunk], second_chunk);
  }

  uint16_t new_head = (uint16_t)(head + len);
  if (new_head >= size) {
    new_head = (uint16_t)(new_head - size);
  }
  rb->head = new_head;

  SpscRingBuf_ExitCritical(primask);
  return len;
}

uint16_t SpscRingBuf_Get(SpscRingBuf_t *rb, uint8_t *dst, uint16_t len) {
  if (!SpscRingBuf_IsValid(rb) || dst == NULL || len == 0u) {
    return 0u;
  }

  const uint32_t primask = SpscRingBuf_EnterCritical();
  const uint16_t size = rb->size;
  const uint16_t head = rb->head;
  const uint16_t tail = rb->tail;
  const uint16_t used = SpscRingBuf_Used(size, head, tail);

  if (len > used) {
    len = used;
  }
  if (len == 0u) {
    SpscRingBuf_ExitCritical(primask);
    return 0u;
  }

  const uint16_t first_chunk = (tail + len > size) ? (uint16_t)(size - tail)
                                                   : len;
  memcpy(dst, &rb->buf[tail], first_chunk);

  const uint16_t second_chunk = (uint16_t)(len - first_chunk);
  if (second_chunk > 0u) {
    memcpy(&dst[first_chunk], &rb->buf[0], second_chunk);
  }

  uint16_t new_tail = (uint16_t)(tail + len);
  if (new_tail >= size) {
    new_tail = (uint16_t)(new_tail - size);
  }
  rb->tail = new_tail;

  SpscRingBuf_ExitCritical(primask);
  return len;
}

uint16_t SpscRingBuf_Drop(SpscRingBuf_t *rb, uint16_t len) {
  if (!SpscRingBuf_IsValid(rb) || len == 0u) {
    return 0u;
  }

  const uint32_t primask = SpscRingBuf_EnterCritical();
  const uint16_t size = rb->size;
  const uint16_t head = rb->head;
  const uint16_t tail = rb->tail;
  const uint16_t used = SpscRingBuf_Used(size, head, tail);

  if (len > used) {
    len = used;
  }
  if (len == 0u) {
    SpscRingBuf_ExitCritical(primask);
    return 0u;
  }

  uint16_t new_tail = (uint16_t)(tail + len);
  if (new_tail >= size) {
    new_tail = (uint16_t)(new_tail - size);
  }
  rb->tail = new_tail;

  SpscRingBuf_ExitCritical(primask);
  return len;
}

uint16_t SpscRingBuf_Peek(const SpscRingBuf_t *rb, uint8_t *dst, uint16_t len) {
  if (!SpscRingBuf_IsValid(rb) || dst == NULL || len == 0u) {
    return 0u;
  }

  const uint32_t primask = SpscRingBuf_EnterCritical();
  const uint16_t size = rb->size;
  const uint16_t head = rb->head;
  const uint16_t tail = rb->tail;
  const uint16_t used = SpscRingBuf_Used(size, head, tail);

  if (len > used) {
    len = used;
  }
  if (len == 0u) {
    SpscRingBuf_ExitCritical(primask);
    return 0u;
  }

  const uint16_t first_chunk = (tail + len > size) ? (uint16_t)(size - tail)
                                                   : len;
  memcpy(dst, &rb->buf[tail], first_chunk);

  const uint16_t second_chunk = (uint16_t)(len - first_chunk);
  if (second_chunk > 0u) {
    memcpy(&dst[first_chunk], &rb->buf[0], second_chunk);
  }

  SpscRingBuf_ExitCritical(primask);
  return len;
}

uint16_t SpscRingBuf_Size(const SpscRingBuf_t *rb) {
  if (!SpscRingBuf_IsValid(rb)) {
    return 0u;
  }
  const uint16_t head = rb->head;
  const uint16_t tail = rb->tail;
  return SpscRingBuf_Used(rb->size, head, tail);
}

uint16_t SpscRingBuf_Space(const SpscRingBuf_t *rb) {
  if (!SpscRingBuf_IsValid(rb)) {
    return 0u;
  }
  return (uint16_t)(rb->size - 1u - SpscRingBuf_Size(rb));
}

bool SpscRingBuf_IsEmpty(const SpscRingBuf_t *rb) {
  if (!SpscRingBuf_IsValid(rb)) {
    return true;
  }
  return rb->head == rb->tail;
}

void SpscRingBuf_Reset(SpscRingBuf_t *rb) {
  if (!SpscRingBuf_IsValid(rb)) {
    return;
  }
  const uint32_t primask = SpscRingBuf_EnterCritical();
  rb->head = 0u;
  rb->tail = 0u;
  SpscRingBuf_ExitCritical(primask);
}
