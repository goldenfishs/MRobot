/* Includes ----------------------------------------------------------------- */
#include "bsp/time.h"
#include "bsp.h"

#include <cmsis_os2.h>
#include "FreeRTOS.h"
#include "main.h"
#include "task.h"

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */
/* Private define ----------------------------------------------------------- */
/* USER DEFINE BEGIN */

/* USER DEFINE END */

/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* USER STRUCT BEGIN */

/* USER STRUCT END */

/* Private variables -------------------------------------------------------- */
/* Private function  -------------------------------------------------------- */
/* Exported functions ------------------------------------------------------- */

uint32_t BSP_TIME_Get_ms() { return xTaskGetTickCount(); }

uint64_t BSP_TIME_Get_us() {
  uint32_t tick_freq = osKernelGetTickFreq();
  uint32_t ticks_old = xTaskGetTickCount()*(1000/tick_freq);
  uint32_t tick_value_old = SysTick->VAL;
  uint32_t ticks_new = xTaskGetTickCount()*(1000/tick_freq);
  uint32_t tick_value_new = SysTick->VAL;
  if (ticks_old == ticks_new) {
    return ticks_new * 1000 + 1000 - tick_value_old * 1000 / (SysTick->LOAD + 1);
  } else {
    return ticks_new * 1000 + 1000 - tick_value_new * 1000 / (SysTick->LOAD + 1);
  }
}

uint64_t BSP_TIME_Get() __attribute__((alias("BSP_TIME_Get_us")));

int8_t BSP_TIME_Delay_ms(uint32_t ms) {
  uint32_t tick_period = 1000u / osKernelGetTickFreq();
  uint32_t ticks = ms / tick_period;

  switch (osKernelGetState()) {
    case osKernelError:
    case osKernelReserved:
    case osKernelLocked:
    case osKernelSuspended:
      return BSP_ERR;

    case osKernelRunning:
      osDelay(ticks ? ticks : 1);
      break;

    case osKernelInactive:
    case osKernelReady:
      HAL_Delay(ms);
      break;
  }
  return BSP_OK;
}

/*阻塞us延迟*/
int8_t BSP_TIME_Delay_us(uint32_t us) {
    uint64_t start = BSP_TIME_Get_us();
    while (BSP_TIME_Get_us() - start < us) {
        // 等待us时间
    }
    return BSP_OK;
}

int8_t BSP_TIME_Delay(uint32_t ms) __attribute__((alias("BSP_TIME_Delay_ms")));

/* USER FUNCTION BEGIN */

/* USER FUNCTION END */