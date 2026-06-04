#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>
#include <stdint.h>

#include "bsp/fdcan.h"
#include "bsp/uart.h"

#define MRLINK_CHANNEL_OK       (0)
#define MRLINK_CHANNEL_ERR      (-1)
#define MRLINK_CHANNEL_ERR_NULL (-2)
#define MRLINK_CHANNEL_ERR_UNSUPPORTED (-3)

#define MRLINK_CHANNEL_BACKEND_STORAGE_SIZE (128u)
#define MRLINK_CHANNEL_FDCAN_MAX_FRAME_SIZE (64u)

typedef void (*MrLink_ChannelNotify_t)(void *ctx);

typedef enum {
  MRLINK_CHANNEL_HW_NONE = 0,
  MRLINK_CHANNEL_HW_UART = 1,
  MRLINK_CHANNEL_HW_USB = 2,
  MRLINK_CHANNEL_HW_FDCAN = 3,
} MrLink_ChannelHardware_t;

typedef union {
  uint32_t words[(MRLINK_CHANNEL_BACKEND_STORAGE_SIZE + 3u) / 4u];
  void *ptr_align;
  uint64_t u64_align;
} MrLink_ChannelBackendStorage_t;

typedef struct {
  MrLink_ChannelHardware_t hardware;
  const void *backend_ops;
  MrLink_ChannelBackendStorage_t backend_storage;
} MrLink_Channel_t;

typedef struct {
  BSP_UART_t uart;
  uint8_t *rx_slots;
  uint16_t rx_slot_size;
  uint8_t rx_slot_count;
  volatile uint16_t *rx_len_storage;
  MrLink_ChannelNotify_t rx_ready;
  void *rx_ready_ctx;
} MrLink_ChannelUartConfig_t;

typedef struct {
  BSP_FDCAN_t fdcan;
  BSP_FDCAN_Format_t tx_format;
  uint32_t tx_id;
  uint32_t rx_id;
  uint8_t rx_queue_size;
  uint8_t max_frame_size;
  MrLink_ChannelNotify_t rx_ready;
  void *rx_ready_ctx;
} MrLink_ChannelFdcanConfig_t;

typedef int8_t (*MrLink_ChannelUsbStartRx_t)(void *ctx);
typedef uint16_t (*MrLink_ChannelUsbPopRx_t)(void *ctx,
                                             uint8_t *dst,
                                             uint16_t dst_size);
typedef int8_t (*MrLink_ChannelUsbSend_t)(void *ctx,
                                          uint8_t *data,
                                          uint16_t len);
typedef int8_t (*MrLink_ChannelUsbRegisterTxCallbacks_t)(
    void *ctx,
    MrLink_ChannelNotify_t tx_done,
    MrLink_ChannelNotify_t tx_error,
    void *callback_ctx);
typedef bool (*MrLink_ChannelUsbIsRxActive_t)(void *ctx);

typedef struct {
  void *ctx;
  MrLink_ChannelUsbStartRx_t start_rx;
  MrLink_ChannelUsbPopRx_t pop_rx;
  MrLink_ChannelUsbSend_t send;
  MrLink_ChannelUsbRegisterTxCallbacks_t register_tx_callbacks;
  MrLink_ChannelUsbIsRxActive_t is_rx_active;
} MrLink_ChannelUsbConfig_t;

int8_t MrLink_Channel_InitUart(MrLink_Channel_t *channel,
                               const MrLink_ChannelUartConfig_t *config);
int8_t MrLink_Channel_InitFdcan(MrLink_Channel_t *channel,
                                const MrLink_ChannelFdcanConfig_t *config);
int8_t MrLink_Channel_InitUsb(MrLink_Channel_t *channel,
                              const MrLink_ChannelUsbConfig_t *config);

MrLink_ChannelHardware_t MrLink_Channel_GetHardware(
    const MrLink_Channel_t *channel);

int8_t MrLink_Channel_StartRx(const MrLink_Channel_t *channel);
uint16_t MrLink_Channel_PopRx(const MrLink_Channel_t *channel,
                              uint8_t *dst, uint16_t dst_size);
int8_t MrLink_Channel_Send(const MrLink_Channel_t *channel,
                           uint8_t *data, uint16_t len);
int8_t MrLink_Channel_RegisterTxCallbacks(
    const MrLink_Channel_t *channel,
    MrLink_ChannelNotify_t tx_done,
    MrLink_ChannelNotify_t tx_error,
    void *callback_ctx);
bool MrLink_Channel_IsRxActive(const MrLink_Channel_t *channel);

uint32_t MrLink_Channel_GetRxOverflowCount(const MrLink_Channel_t *channel);
uint32_t MrLink_Channel_GetRxIrqCount(const MrLink_Channel_t *channel);
uint32_t MrLink_Channel_GetRxIrqByteCount(const MrLink_Channel_t *channel);
uint32_t MrLink_Channel_GetRxStartFailCount(const MrLink_Channel_t *channel);

#ifdef __cplusplus
}
#endif