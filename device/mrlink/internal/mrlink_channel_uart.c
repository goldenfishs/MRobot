#include "mrlink/internal/mrlink_channel_internal.h"

#include <stddef.h>
#include <string.h>

#include "cmsis_compiler.h"

typedef struct {
  BSP_UART_t uart;
  uint8_t *rx_slots;
  uint16_t rx_slot_size;
  uint8_t rx_slot_count;
  volatile bool rx_active;
  volatile uint8_t rx_write_idx;
  volatile uint8_t rx_read_idx;
  volatile uint16_t *rx_len;
  MrLink_ChannelNotify_t rx_ready;
  void *rx_ready_ctx;
  MrLink_ChannelNotify_t tx_done;
  MrLink_ChannelNotify_t tx_error;
  void *tx_callback_ctx;
  uint32_t rx_overflow_count;
  uint32_t rx_irq_count;
  uint32_t rx_irq_byte_count;
  uint32_t rx_start_fail_count;
} MrLink_UartBackend_t;

static MrLink_UartBackend_t *s_uart_backends[BSP_UART_NUM];

static int8_t UartStartRx(void *ctx);
static uint16_t UartPopRx(void *ctx, uint8_t *dst, uint16_t dst_size);
static int8_t UartSend(void *ctx, uint8_t *data, uint16_t len);
static int8_t UartRegisterTxCallbacks(void *ctx,
                                      MrLink_ChannelNotify_t tx_done,
                                      MrLink_ChannelNotify_t tx_error,
                                      void *callback_ctx);
static bool UartIsRxActive(void *ctx);
static uint32_t UartGetRxOverflowCount(const void *ctx);
static uint32_t UartGetRxIrqCount(const void *ctx);
static uint32_t UartGetRxIrqByteCount(const void *ctx);
static uint32_t UartGetRxStartFailCount(const void *ctx);

static const MrLink_ChannelOps_t kUartOps = {
    .start_rx = UartStartRx,
    .pop_rx = UartPopRx,
    .send = UartSend,
    .register_tx_callbacks = UartRegisterTxCallbacks,
    .is_rx_active = UartIsRxActive,
    .get_rx_overflow_count = UartGetRxOverflowCount,
    .get_rx_irq_count = UartGetRxIrqCount,
    .get_rx_irq_byte_count = UartGetRxIrqByteCount,
    .get_rx_start_fail_count = UartGetRxStartFailCount,
};

_Static_assert(sizeof(MrLink_UartBackend_t) <=
                   sizeof(MrLink_ChannelBackendStorage_t),
               "MrLink channel backend storage is too small for UART");

static MrLink_UartBackend_t *ChannelUart(MrLink_Channel_t *channel) {
  return (MrLink_UartBackend_t *)&channel->backend_storage;
}

static bool UartBackendHasConflict(BSP_UART_t uart,
                                   const MrLink_UartBackend_t *backend) {
  if (s_uart_backends[uart] != NULL && s_uart_backends[uart] != backend) {
    return true;
  }

  for (uint8_t i = 0u; i < BSP_UART_NUM; i++) {
    if ((BSP_UART_t)i != uart && s_uart_backends[i] == backend) {
      return true;
    }
  }
  return false;
}

static uint8_t *UartSlotPtr(MrLink_UartBackend_t *backend, uint8_t idx) {
  return &backend->rx_slots[(uint32_t)idx * backend->rx_slot_size];
}

static void UartDropPendingSlot(MrLink_UartBackend_t *backend, uint8_t idx) {
  backend->rx_overflow_count++;
  backend->rx_len[idx] = 0u;
  if (backend->rx_read_idx == idx) {
    backend->rx_read_idx = (uint8_t)((idx + 1u) % backend->rx_slot_count);
  }
}

static void UartRxEvent(MrLink_UartBackend_t *backend, uint16_t size) {
  if (backend == NULL) {
    return;
  }

  backend->rx_active = false;
  const uint8_t ready_idx = backend->rx_write_idx;

  if (size > backend->rx_slot_size) {
    backend->rx_start_fail_count++;
    (void)UartStartRx(backend);
    return;
  }

  if (size > 0u) {
    backend->rx_len[ready_idx] = size;
    backend->rx_irq_count++;
    backend->rx_irq_byte_count += size;

    const uint8_t next_idx =
        (uint8_t)((ready_idx + 1u) % backend->rx_slot_count);
    if (backend->rx_len[next_idx] != 0u) {
      UartDropPendingSlot(backend, next_idx);
    }
    backend->rx_write_idx = next_idx;
  }

  if (UartStartRx(backend) != BSP_OK) {
    backend->rx_start_fail_count++;
  }

  if (size > 0u && backend->rx_ready != NULL) {
    backend->rx_ready(backend->rx_ready_ctx);
  }
}

static void UartRxEventRc(uint16_t size) {
  UartRxEvent(s_uart_backends[BSP_UART_RC], size);
}

static void UartRxEventPc(uint16_t size) {
  UartRxEvent(s_uart_backends[BSP_UART_PC], size);
}

static void UartRxEventIr(uint16_t size) {
  UartRxEvent(s_uart_backends[BSP_UART_IR], size);
}

static BSP_UART_RxEventCallback_t UartRxTrampoline(BSP_UART_t uart) {
  switch (uart) {
    case BSP_UART_RC:
      return UartRxEventRc;
    case BSP_UART_PC:
      return UartRxEventPc;
    case BSP_UART_IR:
      return UartRxEventIr;
    default:
      return NULL;
  }
}

static void UartTxDone(MrLink_UartBackend_t *backend) {
  if (backend != NULL && backend->tx_done != NULL) {
    backend->tx_done(backend->tx_callback_ctx);
  }
}

static void UartTxError(MrLink_UartBackend_t *backend) {
  if (backend != NULL && backend->tx_error != NULL) {
    backend->tx_error(backend->tx_callback_ctx);
  }
}

static void UartTxDoneRc(void) { UartTxDone(s_uart_backends[BSP_UART_RC]); }
static void UartTxDonePc(void) { UartTxDone(s_uart_backends[BSP_UART_PC]); }
static void UartTxDoneIr(void) { UartTxDone(s_uart_backends[BSP_UART_IR]); }
static void UartTxErrorRc(void) { UartTxError(s_uart_backends[BSP_UART_RC]); }
static void UartTxErrorPc(void) { UartTxError(s_uart_backends[BSP_UART_PC]); }
static void UartTxErrorIr(void) { UartTxError(s_uart_backends[BSP_UART_IR]); }

static void (*UartTxDoneTrampoline(BSP_UART_t uart))(void) {
  switch (uart) {
    case BSP_UART_RC:
      return UartTxDoneRc;
    case BSP_UART_PC:
      return UartTxDonePc;
    case BSP_UART_IR:
      return UartTxDoneIr;
    default:
      return NULL;
  }
}

static void (*UartTxErrorTrampoline(BSP_UART_t uart))(void) {
  switch (uart) {
    case BSP_UART_RC:
      return UartTxErrorRc;
    case BSP_UART_PC:
      return UartTxErrorPc;
    case BSP_UART_IR:
      return UartTxErrorIr;
    default:
      return NULL;
  }
}

int8_t MrLink_ChannelBackend_InitUart(
    MrLink_Channel_t *channel,
    const MrLink_ChannelUartConfig_t *config) {
  if (channel == NULL || config == NULL) {
    return MRLINK_CHANNEL_ERR_NULL;
  }
  if (config->rx_slots == NULL || config->rx_len_storage == NULL) {
    return MRLINK_CHANNEL_ERR_NULL;
  }
  if ((uint32_t)config->uart >= (uint32_t)BSP_UART_NUM ||
      config->rx_slot_count < 2u || config->rx_slot_size == 0u) {
    return MRLINK_CHANNEL_ERR;
  }

  MrLink_UartBackend_t *backend = ChannelUart(channel);
  if (UartBackendHasConflict(config->uart, backend)) {
    return MRLINK_CHANNEL_ERR;
  }

  const int8_t ret = BSP_UART_RegisterRxEventCallback(
      config->uart, UartRxTrampoline(config->uart));
  if (ret != BSP_OK) {
    return ret;
  }

  memset(channel, 0, sizeof(*channel));

  backend = ChannelUart(channel);
  backend->uart = config->uart;
  backend->rx_slots = config->rx_slots;
  backend->rx_slot_size = config->rx_slot_size;
  backend->rx_slot_count = config->rx_slot_count;
  backend->rx_len = config->rx_len_storage;
  backend->rx_ready = config->rx_ready;
  backend->rx_ready_ctx = config->rx_ready_ctx;

  for (uint8_t i = 0u; i < config->rx_slot_count; i++) {
    config->rx_len_storage[i] = 0u;
  }

  s_uart_backends[config->uart] = backend;

  MrLink_Channel_SetBackend(channel, MRLINK_CHANNEL_HW_UART, &kUartOps);
  return MRLINK_CHANNEL_OK;
}

static int8_t UartStartRx(void *ctx) {
  MrLink_UartBackend_t *backend = (MrLink_UartBackend_t *)ctx;
  if (backend == NULL) {
    return MRLINK_CHANNEL_ERR_NULL;
  }

  const uint8_t idx = backend->rx_write_idx;
  if (backend->rx_len[idx] != 0u) {
    UartDropPendingSlot(backend, idx);
  }

  int8_t ret = BSP_UART_ReceiveToIdle(backend->uart, UartSlotPtr(backend, idx),
                                      backend->rx_slot_size, true);
  if (ret == BSP_OK) {
    backend->rx_active = true;
    return BSP_OK;
  }

  UART_HandleTypeDef *huart = BSP_UART_GetHandle(backend->uart);
  if (huart != NULL) {
    (void)HAL_UART_AbortReceive(huart);
    ret = BSP_UART_ReceiveToIdle(backend->uart, UartSlotPtr(backend, idx),
                                 backend->rx_slot_size, true);
  }
  backend->rx_active = (ret == BSP_OK);
  return ret;
}

static uint16_t UartPopRx(void *ctx, uint8_t *dst, uint16_t dst_size) {
  MrLink_UartBackend_t *backend = (MrLink_UartBackend_t *)ctx;
  if (backend == NULL || dst == NULL || dst_size == 0u) {
    return 0u;
  }

  uint16_t len = 0u;
  const uint32_t primask = __get_PRIMASK();
  __disable_irq();
  const uint8_t idx = backend->rx_read_idx;
  len = backend->rx_len[idx];
  if (len > 0u) {
    if (len > dst_size) {
      len = dst_size;
    }
    memcpy(dst, UartSlotPtr(backend, idx), len);
    backend->rx_len[idx] = 0u;
    backend->rx_read_idx = (uint8_t)((idx + 1u) % backend->rx_slot_count);
  }
  if (primask == 0u) {
    __enable_irq();
  }
  return len;
}

static int8_t UartSend(void *ctx, uint8_t *data, uint16_t len) {
  MrLink_UartBackend_t *backend = (MrLink_UartBackend_t *)ctx;
  if (backend == NULL) {
    return MRLINK_CHANNEL_ERR_NULL;
  }
  return BSP_UART_Transmit(backend->uart, data, len, true);
}

static int8_t UartRegisterTxCallbacks(void *ctx,
                                      MrLink_ChannelNotify_t tx_done,
                                      MrLink_ChannelNotify_t tx_error,
                                      void *callback_ctx) {
  MrLink_UartBackend_t *backend = (MrLink_UartBackend_t *)ctx;
  if (backend == NULL) {
    return MRLINK_CHANNEL_ERR_NULL;
  }

  void (*done_trampoline)(void) = UartTxDoneTrampoline(backend->uart);
  void (*error_trampoline)(void) = UartTxErrorTrampoline(backend->uart);
  if (done_trampoline == NULL || error_trampoline == NULL) {
    return MRLINK_CHANNEL_ERR;
  }

  backend->tx_done = tx_done;
  backend->tx_error = tx_error;
  backend->tx_callback_ctx = callback_ctx;

  int8_t ret = BSP_UART_RegisterCallback(backend->uart, BSP_UART_TX_CPLT_CB,
                                         done_trampoline);
  if (ret != BSP_OK) {
    return ret;
  }
  ret = BSP_UART_RegisterCallback(backend->uart, BSP_UART_ERROR_CB,
                                  error_trampoline);
  if (ret != BSP_OK) {
    return ret;
  }
  return BSP_UART_RegisterCallback(backend->uart, BSP_UART_ABORT_TX_CPLT_CB,
                                   error_trampoline);
}

static bool UartIsRxActive(void *ctx) {
  const MrLink_UartBackend_t *backend = (const MrLink_UartBackend_t *)ctx;
  return (backend != NULL) ? backend->rx_active : false;
}

static uint32_t UartGetRxOverflowCount(const void *ctx) {
  const MrLink_UartBackend_t *backend = (const MrLink_UartBackend_t *)ctx;
  return (backend != NULL) ? backend->rx_overflow_count : 0u;
}

static uint32_t UartGetRxIrqCount(const void *ctx) {
  const MrLink_UartBackend_t *backend = (const MrLink_UartBackend_t *)ctx;
  return (backend != NULL) ? backend->rx_irq_count : 0u;
}

static uint32_t UartGetRxIrqByteCount(const void *ctx) {
  const MrLink_UartBackend_t *backend = (const MrLink_UartBackend_t *)ctx;
  return (backend != NULL) ? backend->rx_irq_byte_count : 0u;
}

static uint32_t UartGetRxStartFailCount(const void *ctx) {
  const MrLink_UartBackend_t *backend = (const MrLink_UartBackend_t *)ctx;
  return (backend != NULL) ? backend->rx_start_fail_count : 0u;
}
