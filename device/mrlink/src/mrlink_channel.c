#include "mrlink/mrlink_channel.h"

#include <stddef.h>

#include "mrlink/internal/mrlink_channel_internal.h"

static const MrLink_ChannelOps_t *ChannelOps(const MrLink_Channel_t *channel) {
  return (channel != NULL) ? (const MrLink_ChannelOps_t *)channel->backend_ops
                           : NULL;
}

static void *ChannelCtx(const MrLink_Channel_t *channel) {
  return (channel != NULL) ? (void *)&channel->backend_storage : NULL;
}

void MrLink_Channel_SetBackend(MrLink_Channel_t *channel,
                               MrLink_ChannelHardware_t hardware,
                               const MrLink_ChannelOps_t *ops) {
  if (channel == NULL) {
    return;
  }
  channel->hardware = hardware;
  channel->backend_ops = ops;
}

int8_t MrLink_Channel_InitUart(MrLink_Channel_t *channel,
                               const MrLink_ChannelUartConfig_t *config) {
  return MrLink_ChannelBackend_InitUart(channel, config);
}

int8_t MrLink_Channel_InitFdcan(MrLink_Channel_t *channel,
                                const MrLink_ChannelFdcanConfig_t *config) {
  return MrLink_ChannelBackend_InitFdcan(channel, config);
}

int8_t MrLink_Channel_InitUsb(MrLink_Channel_t *channel,
                              const MrLink_ChannelUsbConfig_t *config) {
  return MrLink_ChannelBackend_InitUsb(channel, config);
}

MrLink_ChannelHardware_t MrLink_Channel_GetHardware(
    const MrLink_Channel_t *channel) {
  return (channel != NULL) ? channel->hardware : MRLINK_CHANNEL_HW_NONE;
}

int8_t MrLink_Channel_StartRx(const MrLink_Channel_t *channel) {
  const MrLink_ChannelOps_t *ops = ChannelOps(channel);
  if (ops == NULL || ops->start_rx == NULL) {
    return MRLINK_CHANNEL_ERR_NULL;
  }
  return ops->start_rx(ChannelCtx(channel));
}

uint16_t MrLink_Channel_PopRx(const MrLink_Channel_t *channel,
                              uint8_t *dst, uint16_t dst_size) {
  const MrLink_ChannelOps_t *ops = ChannelOps(channel);
  if (ops == NULL || ops->pop_rx == NULL) {
    return 0u;
  }
  return ops->pop_rx(ChannelCtx(channel), dst, dst_size);
}

int8_t MrLink_Channel_Send(const MrLink_Channel_t *channel,
                           uint8_t *data, uint16_t len) {
  const MrLink_ChannelOps_t *ops = ChannelOps(channel);
  if (ops == NULL || ops->send == NULL) {
    return MRLINK_CHANNEL_ERR_NULL;
  }
  return ops->send(ChannelCtx(channel), data, len);
}

int8_t MrLink_Channel_RegisterTxCallbacks(
    const MrLink_Channel_t *channel,
    MrLink_ChannelNotify_t tx_done,
    MrLink_ChannelNotify_t tx_error,
    void *callback_ctx) {
  const MrLink_ChannelOps_t *ops = ChannelOps(channel);
  if (ops == NULL || ops->register_tx_callbacks == NULL) {
    return MRLINK_CHANNEL_ERR_NULL;
  }
  return ops->register_tx_callbacks(ChannelCtx(channel), tx_done, tx_error,
                                    callback_ctx);
}

bool MrLink_Channel_IsRxActive(const MrLink_Channel_t *channel) {
  const MrLink_ChannelOps_t *ops = ChannelOps(channel);
  if (ops == NULL || ops->is_rx_active == NULL) {
    return false;
  }
  return ops->is_rx_active(ChannelCtx(channel));
}

uint32_t MrLink_Channel_GetRxOverflowCount(const MrLink_Channel_t *channel) {
  const MrLink_ChannelOps_t *ops = ChannelOps(channel);
  if (ops == NULL || ops->get_rx_overflow_count == NULL) {
    return 0u;
  }
  return ops->get_rx_overflow_count(ChannelCtx(channel));
}

uint32_t MrLink_Channel_GetRxIrqCount(const MrLink_Channel_t *channel) {
  const MrLink_ChannelOps_t *ops = ChannelOps(channel);
  if (ops == NULL || ops->get_rx_irq_count == NULL) {
    return 0u;
  }
  return ops->get_rx_irq_count(ChannelCtx(channel));
}

uint32_t MrLink_Channel_GetRxIrqByteCount(const MrLink_Channel_t *channel) {
  const MrLink_ChannelOps_t *ops = ChannelOps(channel);
  if (ops == NULL || ops->get_rx_irq_byte_count == NULL) {
    return 0u;
  }
  return ops->get_rx_irq_byte_count(ChannelCtx(channel));
}

uint32_t MrLink_Channel_GetRxStartFailCount(const MrLink_Channel_t *channel) {
  const MrLink_ChannelOps_t *ops = ChannelOps(channel);
  if (ops == NULL || ops->get_rx_start_fail_count == NULL) {
    return 0u;
  }
  return ops->get_rx_start_fail_count(ChannelCtx(channel));
}
