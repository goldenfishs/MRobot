#include "mrlink/internal/mrlink_channel_internal.h"

#include <stddef.h>
#include <string.h>

typedef struct {
  void *ctx;
  MrLink_ChannelUsbStartRx_t start_rx;
  MrLink_ChannelUsbPopRx_t pop_rx;
  MrLink_ChannelUsbSend_t send;
  MrLink_ChannelUsbRegisterTxCallbacks_t register_tx_callbacks;
  MrLink_ChannelUsbIsRxActive_t is_rx_active;
} MrLink_UsbBackend_t;

static int8_t UsbStartRx(void *ctx);
static uint16_t UsbPopRx(void *ctx, uint8_t *dst, uint16_t dst_size);
static int8_t UsbSend(void *ctx, uint8_t *data, uint16_t len);
static int8_t UsbRegisterTxCallbacks(void *ctx,
                                     MrLink_ChannelNotify_t tx_done,
                                     MrLink_ChannelNotify_t tx_error,
                                     void *callback_ctx);
static bool UsbIsRxActive(void *ctx);

static const MrLink_ChannelOps_t kUsbOps = {
    .start_rx = UsbStartRx,
    .pop_rx = UsbPopRx,
    .send = UsbSend,
    .register_tx_callbacks = UsbRegisterTxCallbacks,
    .is_rx_active = UsbIsRxActive,
    .get_rx_overflow_count = NULL,
    .get_rx_irq_count = NULL,
    .get_rx_irq_byte_count = NULL,
    .get_rx_start_fail_count = NULL,
};

_Static_assert(sizeof(MrLink_UsbBackend_t) <=
                   sizeof(MrLink_ChannelBackendStorage_t),
               "MrLink channel backend storage is too small for USB");

static MrLink_UsbBackend_t *ChannelUsb(MrLink_Channel_t *channel) {
  return (MrLink_UsbBackend_t *)&channel->backend_storage;
}

int8_t MrLink_ChannelBackend_InitUsb(
    MrLink_Channel_t *channel,
    const MrLink_ChannelUsbConfig_t *config) {
  if (channel == NULL || config == NULL) {
    return MRLINK_CHANNEL_ERR_NULL;
  }
  if (config->send == NULL || config->pop_rx == NULL) {
    return MRLINK_CHANNEL_ERR_UNSUPPORTED;
  }

  memset(channel, 0, sizeof(*channel));
  MrLink_UsbBackend_t *backend = ChannelUsb(channel);
  backend->ctx = config->ctx;
  backend->start_rx = config->start_rx;
  backend->pop_rx = config->pop_rx;
  backend->send = config->send;
  backend->register_tx_callbacks = config->register_tx_callbacks;
  backend->is_rx_active = config->is_rx_active;

  MrLink_Channel_SetBackend(channel, MRLINK_CHANNEL_HW_USB, &kUsbOps);
  return MRLINK_CHANNEL_OK;
}

static int8_t UsbStartRx(void *ctx) {
  MrLink_UsbBackend_t *backend = (MrLink_UsbBackend_t *)ctx;
  if (backend == NULL) {
    return MRLINK_CHANNEL_ERR_NULL;
  }
  if (backend->start_rx == NULL) {
    return MRLINK_CHANNEL_OK;
  }
  return backend->start_rx(backend->ctx);
}

static uint16_t UsbPopRx(void *ctx, uint8_t *dst, uint16_t dst_size) {
  MrLink_UsbBackend_t *backend = (MrLink_UsbBackend_t *)ctx;
  if (backend == NULL || backend->pop_rx == NULL) {
    return 0u;
  }
  return backend->pop_rx(backend->ctx, dst, dst_size);
}

static int8_t UsbSend(void *ctx, uint8_t *data, uint16_t len) {
  MrLink_UsbBackend_t *backend = (MrLink_UsbBackend_t *)ctx;
  if (backend == NULL || backend->send == NULL) {
    return MRLINK_CHANNEL_ERR_UNSUPPORTED;
  }
  return backend->send(backend->ctx, data, len);
}

static int8_t UsbRegisterTxCallbacks(void *ctx,
                                     MrLink_ChannelNotify_t tx_done,
                                     MrLink_ChannelNotify_t tx_error,
                                     void *callback_ctx) {
  MrLink_UsbBackend_t *backend = (MrLink_UsbBackend_t *)ctx;
  if (backend == NULL) {
    return MRLINK_CHANNEL_ERR_NULL;
  }
  if (backend->register_tx_callbacks == NULL) {
    return MRLINK_CHANNEL_ERR_UNSUPPORTED;
  }
  return backend->register_tx_callbacks(backend->ctx, tx_done, tx_error,
                                        callback_ctx);
}

static bool UsbIsRxActive(void *ctx) {
  MrLink_UsbBackend_t *backend = (MrLink_UsbBackend_t *)ctx;
  if (backend == NULL) {
    return false;
  }
  if (backend->is_rx_active == NULL) {
    return true;
  }
  return backend->is_rx_active(backend->ctx);
}