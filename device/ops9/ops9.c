/*
    ACTION全场定位码盘ops9
*/

/* Includes ----------------------------------------------------------------- */
#include "device/ops9.h"

#include <string.h>

#include "bsp/uart.h"
#include "bsp/time.h"
/* Private define ----------------------------------------------------------- */


/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */
static osThreadId_t thread_alert;
static bool inited = false;

/* Private function  -------------------------------------------------------- */
static void OPS9_RxCpltCallback(void) {
  osThreadFlagsSet(thread_alert, SIGNAL_OPS9_RAW_REDY);

}

/* Exported functions ------------------------------------------------------- */
int8_t OPS9_init(OPS9_t *ops9) {
  if (ops9 == NULL) return DEVICE_ERR_NULL;
  if (inited) return DEVICE_ERR_INITED;
  if ((thread_alert = osThreadGetId()) == NULL) return DEVICE_ERR_NULL;

  BSP_UART_RegisterCallback(BSP_UART_OPS9, BSP_UART_RX_CPLT_CB,
                            OPS9_RxCpltCallback);

  inited = true;
  return DEVICE_OK;
}

int8_t OPS9_Restart(void) {
  __HAL_UART_DISABLE(BSP_UART_GetHandle(BSP_UART_OPS9));
  __HAL_UART_ENABLE(BSP_UART_GetHandle(BSP_UART_OPS9));
  return DEVICE_OK;
}

int8_t OPS9_StartDmaRecv(OPS9_t *ops9) {
  if (HAL_UART_Receive_DMA(BSP_UART_GetHandle(BSP_UART_OPS9),
                           (uint8_t *)&(ops9->data),
                           sizeof(ops9->data)) == HAL_OK)
    return DEVICE_OK;
  return DEVICE_ERR;
}

bool OPS9_WaitDmaCplt(uint32_t timeout) {
  return (osThreadFlagsWait(SIGNAL_OPS9_RAW_REDY, osFlagsWaitAll, timeout) ==
          SIGNAL_OPS9_RAW_REDY);
}

