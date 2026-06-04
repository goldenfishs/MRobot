#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include "mrlink/mrlink_channel.h"

typedef struct {
  int8_t (*start_rx)(void *ctx);
  uint16_t (*pop_rx)(void *ctx, uint8_t *dst, uint16_t dst_size);
  int8_t (*send)(void *ctx, uint8_t *data, uint16_t len);
  int8_t (*register_tx_callbacks)(void *ctx,
                                  MrLink_ChannelNotify_t tx_done,
                                  MrLink_ChannelNotify_t tx_error,
                                  void *callback_ctx);
  bool (*is_rx_active)(void *ctx);
  uint32_t (*get_rx_overflow_count)(const void *ctx);
  uint32_t (*get_rx_irq_count)(const void *ctx);
  uint32_t (*get_rx_irq_byte_count)(const void *ctx);
  uint32_t (*get_rx_start_fail_count)(const void *ctx);
} MrLink_ChannelOps_t;

void MrLink_Channel_SetBackend(MrLink_Channel_t *channel,
                               MrLink_ChannelHardware_t hardware,
                               const MrLink_ChannelOps_t *ops);

int8_t MrLink_ChannelBackend_InitUart(
    MrLink_Channel_t *channel,
    const MrLink_ChannelUartConfig_t *config);
int8_t MrLink_ChannelBackend_InitFdcan(
    MrLink_Channel_t *channel,
    const MrLink_ChannelFdcanConfig_t *config);
int8_t MrLink_ChannelBackend_InitUsb(
    MrLink_Channel_t *channel,
    const MrLink_ChannelUsbConfig_t *config);

#ifdef __cplusplus
}
#endif
