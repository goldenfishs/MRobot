#include "mrlink/internal/mrlink_channel_internal.h"

#include <stddef.h>
#include <string.h>

typedef struct {
  BSP_FDCAN_t fdcan;
  BSP_FDCAN_Format_t tx_format;
  uint32_t tx_id;
  uint32_t rx_id;
  uint8_t rx_queue_size;
  uint8_t max_frame_size;
  bool rx_active;
  MrLink_ChannelNotify_t rx_ready;
  void *rx_ready_ctx;
  uint32_t rx_irq_count;
  uint32_t rx_irq_byte_count;
  uint32_t rx_overflow_count;
  uint32_t rx_start_fail_count;
} MrLink_FdcanBackend_t;

static int8_t FdcanStartRx(void *ctx);
static uint16_t FdcanPopRx(void *ctx, uint8_t *dst, uint16_t dst_size);
static int8_t FdcanSend(void *ctx, uint8_t *data, uint16_t len);
static int8_t FdcanRegisterTxCallbacks(void *ctx,
                                       MrLink_ChannelNotify_t tx_done,
                                       MrLink_ChannelNotify_t tx_error,
                                       void *callback_ctx);
static bool FdcanIsRxActive(void *ctx);
static uint32_t FdcanGetRxOverflowCount(const void *ctx);
static uint32_t FdcanGetRxIrqCount(const void *ctx);
static uint32_t FdcanGetRxIrqByteCount(const void *ctx);
static uint32_t FdcanGetRxStartFailCount(const void *ctx);

static const MrLink_ChannelOps_t kFdcanOps = {
    .start_rx = FdcanStartRx,
    .pop_rx = FdcanPopRx,
    .send = FdcanSend,
    .register_tx_callbacks = FdcanRegisterTxCallbacks,
    .is_rx_active = FdcanIsRxActive,
    .get_rx_overflow_count = FdcanGetRxOverflowCount,
    .get_rx_irq_count = FdcanGetRxIrqCount,
    .get_rx_irq_byte_count = FdcanGetRxIrqByteCount,
    .get_rx_start_fail_count = FdcanGetRxStartFailCount,
};

_Static_assert(sizeof(MrLink_FdcanBackend_t) <=
                   sizeof(MrLink_ChannelBackendStorage_t),
               "MrLink channel backend storage is too small for FDCAN");

static MrLink_FdcanBackend_t *ChannelFdcan(MrLink_Channel_t *channel) {
  return (MrLink_FdcanBackend_t *)&channel->backend_storage;
}

static bool FdcanFormatIsData(BSP_FDCAN_Format_t format) {
  return format == BSP_FDCAN_FORMAT_STD_DATA ||
         format == BSP_FDCAN_FORMAT_EXT_DATA;
}

int8_t MrLink_ChannelBackend_InitFdcan(
    MrLink_Channel_t *channel,
    const MrLink_ChannelFdcanConfig_t *config) {
  if (channel == NULL || config == NULL) {
    return MRLINK_CHANNEL_ERR_NULL;
  }
  if (config->fdcan >= BSP_FDCAN_NUM || !FdcanFormatIsData(config->tx_format)) {
    return MRLINK_CHANNEL_ERR;
  }

  const uint8_t max_frame_size =
      (config->max_frame_size > 0u) ? config->max_frame_size
                                    : MRLINK_CHANNEL_FDCAN_MAX_FRAME_SIZE;
  if (max_frame_size > MRLINK_CHANNEL_FDCAN_MAX_FRAME_SIZE) {
    return MRLINK_CHANNEL_ERR;
  }

  memset(channel, 0, sizeof(*channel));
  MrLink_FdcanBackend_t *backend = ChannelFdcan(channel);
  backend->fdcan = config->fdcan;
  backend->tx_format = config->tx_format;
  backend->tx_id = config->tx_id;
  backend->rx_id = config->rx_id;
  backend->rx_queue_size = config->rx_queue_size;
  backend->max_frame_size = max_frame_size;
  backend->rx_ready = config->rx_ready;
  backend->rx_ready_ctx = config->rx_ready_ctx;

  MrLink_Channel_SetBackend(channel, MRLINK_CHANNEL_HW_FDCAN, &kFdcanOps);
  return FdcanStartRx(backend);
}

static int8_t FdcanStartRx(void *ctx) {
  MrLink_FdcanBackend_t *backend = (MrLink_FdcanBackend_t *)ctx;
  if (backend == NULL) {
    return MRLINK_CHANNEL_ERR_NULL;
  }
  if (backend->rx_active) {
    return MRLINK_CHANNEL_OK;
  }
  const uint8_t queue_size = backend->rx_queue_size > 0u
                                 ? backend->rx_queue_size
                                 : BSP_FDCAN_DEFAULT_QUEUE_SIZE;
  const int8_t ret = BSP_FDCAN_RegisterId(backend->fdcan,
                                          backend->rx_id,
                                          queue_size);
  backend->rx_active = (ret == BSP_OK);
  if (ret != BSP_OK) {
    backend->rx_start_fail_count++;
  }
  return ret;
}

static uint16_t FdcanPopRx(void *ctx, uint8_t *dst, uint16_t dst_size) {
  MrLink_FdcanBackend_t *backend = (MrLink_FdcanBackend_t *)ctx;
  if (backend == NULL || dst == NULL || dst_size == 0u) {
    return 0u;
  }

  BSP_FDCAN_Message_t msg = {0};
  if (BSP_FDCAN_GetMessage(backend->fdcan, backend->rx_id, &msg,
                           BSP_FDCAN_TIMEOUT_IMMEDIATE) != BSP_OK) {
    return 0u;
  }

  backend->rx_irq_count++;
  backend->rx_irq_byte_count += msg.dlc;
  if (msg.dlc > backend->max_frame_size || msg.dlc > dst_size) {
    backend->rx_overflow_count++;
    return 0u;
  }

  memcpy(dst, msg.data, msg.dlc);
  if (backend->rx_ready != NULL) {
    backend->rx_ready(backend->rx_ready_ctx);
  }
  return msg.dlc;
}

static int8_t FdcanSend(void *ctx, uint8_t *data, uint16_t len) {
  MrLink_FdcanBackend_t *backend = (MrLink_FdcanBackend_t *)ctx;
  if (backend == NULL) {
    return MRLINK_CHANNEL_ERR_NULL;
  }
  if (data == NULL && len > 0u) {
    return MRLINK_CHANNEL_ERR_NULL;
  }
  if (len > backend->max_frame_size || len > MRLINK_CHANNEL_FDCAN_MAX_FRAME_SIZE) {
    return MRLINK_CHANNEL_ERR;
  }
  return BSP_FDCAN_Transmit(backend->fdcan, backend->tx_format,
                            backend->tx_id, data, (uint8_t)len);
}

static int8_t FdcanRegisterTxCallbacks(void *ctx,
                                       MrLink_ChannelNotify_t tx_done,
                                       MrLink_ChannelNotify_t tx_error,
                                       void *callback_ctx) {
  (void)ctx;
  (void)tx_done;
  (void)tx_error;
  (void)callback_ctx;
  return MRLINK_CHANNEL_ERR_UNSUPPORTED;
}

static bool FdcanIsRxActive(void *ctx) {
  const MrLink_FdcanBackend_t *backend = (const MrLink_FdcanBackend_t *)ctx;
  return (backend != NULL) ? backend->rx_active : false;
}

static uint32_t FdcanGetRxOverflowCount(const void *ctx) {
  const MrLink_FdcanBackend_t *backend = (const MrLink_FdcanBackend_t *)ctx;
  return (backend != NULL) ? backend->rx_overflow_count : 0u;
}

static uint32_t FdcanGetRxIrqCount(const void *ctx) {
  const MrLink_FdcanBackend_t *backend = (const MrLink_FdcanBackend_t *)ctx;
  return (backend != NULL) ? backend->rx_irq_count : 0u;
}

static uint32_t FdcanGetRxIrqByteCount(const void *ctx) {
  const MrLink_FdcanBackend_t *backend = (const MrLink_FdcanBackend_t *)ctx;
  return (backend != NULL) ? backend->rx_irq_byte_count : 0u;
}

static uint32_t FdcanGetRxStartFailCount(const void *ctx) {
  const MrLink_FdcanBackend_t *backend = (const MrLink_FdcanBackend_t *)ctx;
  return (backend != NULL) ? backend->rx_start_fail_count : 0u;
}
