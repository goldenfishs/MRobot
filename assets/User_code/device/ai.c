/*
AI
*/

/* Includes ----------------------------------------------------------------- */
#include "ai.h"

#include <stdbool.h>
#include <string.h>

#include "bsp/time.h"
#include "bsp/uart.h"
#include "component/ahrs.h"
#include "component/crc16.h"
#include "component/crc8.h"
#include "component/user_math.h"
#include "component/filter.h"


/* Private define ----------------------------------------------------------- */
#define AI_LEN_RX_BUFF (sizeof(AI_DownPackage_t))

/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */

static uint8_t rxbuf[AI_LEN_RX_BUFF];

static bool inited = false;

static osThreadId_t thread_alert;

static uint32_t drop_message = 0;

// uint16_t crc16;

/* Private function  -------------------------------------------------------- */

static void Ai_RxCpltCallback(void) {
  osThreadFlagsSet(thread_alert, SIGNAL_AI_RAW_REDY);
}

static void Ai_IdleLineCallback(void) {
  osThreadFlagsSet(thread_alert, SIGNAL_AI_RAW_REDY);
}

/* Exported functions ------------------------------------------------------- */
int8_t AI_Init(AI_t *ai) {
  UNUSED(ai);
  if (inited) return DEVICE_ERR_INITED;
  thread_alert = osThreadGetId();

  BSP_UART_RegisterCallback(BSP_UART_AI, BSP_UART_RX_CPLT_CB,
                            Ai_RxCpltCallback);
  BSP_UART_RegisterCallback(BSP_UART_AI, BSP_UART_IDLE_LINE_CB,
                            Ai_IdleLineCallback);
  
  inited = true;
  return 0;
}

int8_t AI_Restart(AI_t *ai) {
  UNUSED(ai);
  __HAL_UART_DISABLE(BSP_UART_GetHandle(BSP_UART_AI));
  __HAL_UART_ENABLE(BSP_UART_GetHandle(BSP_UART_AI));
  return DEVICE_OK;
}

int8_t AI_StartReceiving(AI_t *ai) {
  UNUSED(ai);
  // if (HAL_UART_Receive_DMA(BSP_UART_GetHandle(BSP_UART_AI), rxbuf,
  //                          AI_LEN_RX_BUFF) == HAL_OK)
  if (BSP_UART_Receive(BSP_UART_AI, rxbuf,
                           AI_LEN_RX_BUFF, true) == HAL_OK)
    return DEVICE_OK;
  return DEVICE_ERR;
}

bool AI_WaitDmaCplt(void) {
  return (osThreadFlagsWait(SIGNAL_AI_RAW_REDY, osFlagsWaitAll,0) ==
          SIGNAL_AI_RAW_REDY);
}

int8_t AI_ParseHost(AI_t *ai) {
  // crc16 = CRC16_Calc((const uint8_t *)&(rxbuf), sizeof(ai->from_host) - 2, CRC16_INIT);
  if (!CRC16_Verify((const uint8_t *)&(rxbuf), sizeof(ai->from_host)))
    goto error;
  ai->header.online = true;
  ai->header.last_online_time = BSP_TIME_Get();
  memcpy(&(ai->from_host), rxbuf, sizeof(ai->from_host));
  memset(rxbuf, 0, AI_LEN_RX_BUFF);
  return DEVICE_OK;

error:
  drop_message++;
  return DEVICE_ERR;
}

int8_t AI_PackMCU(AI_t *ai, const AHRS_Quaternion_t *data){
  if (ai == NULL || data == NULL) return DEVICE_ERR_NULL;
  ai->to_host.mcu.id = AI_ID_MCU;
  ai->to_host.mcu.package.quat=*data;
  ai->to_host.mcu.package.notice = ai->status;
  ai->to_host.mcu.crc16 = CRC16_Calc((const uint8_t *)&(ai->to_host.mcu), sizeof(AI_UpPackageMCU_t) - 2, CRC16_INIT);
  return DEVICE_OK;
}

int8_t AI_PackRef(AI_t *ai, const AI_UpPackageReferee_t *data) {
  if (ai == NULL || data == NULL) return DEVICE_ERR_NULL;
  ai->to_host.ref = *data;
  return DEVICE_OK;
}

int8_t AI_HandleOffline(AI_t *ai) {
  if (ai == NULL) return DEVICE_ERR_NULL;
  if (BSP_TIME_Get() - ai->header.last_online_time >
      100000) {
    ai->header.online = false;
  }
  return DEVICE_OK;
}

int8_t AI_StartSend(AI_t *ai, bool ref_online){
  if (ai == NULL) return DEVICE_ERR_NULL;
  
  if (ref_online) {
    // 发送裁判系统数据和MCU数据
    if (BSP_UART_Transmit(BSP_UART_AI, (uint8_t *)&(ai->to_host),
                          sizeof(ai->to_host.ref) + sizeof(ai->to_host.mcu), true) == HAL_OK)
      return DEVICE_OK;
    else
      return DEVICE_ERR;
  } else {
    // 只发送MCU数据
    if (BSP_UART_Transmit(BSP_UART_AI, (uint8_t *)&(ai->to_host.mcu),
                          sizeof(ai->to_host.mcu), true) == HAL_OK)
      return DEVICE_OK;
    else
      return DEVICE_ERR;
  }
}

