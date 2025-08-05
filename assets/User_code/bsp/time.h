#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include <stdint.h>

#include "bsp/bsp.h"

/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */
/* Exported functions prototypes -------------------------------------------- */
uint32_t BSP_TIME_Get_ms();

uint64_t BSP_TIME_Get_us();

uint64_t BSP_TIME_Get();

int8_t BSP_TIME_Delay_ms(uint32_t ms);

/*微秒阻塞延时，一般别用*/
int8_t BSP_TIME_Delay_us(uint32_t us);

int8_t BSP_TIME_Delay(uint32_t ms);

#ifdef __cplusplus
}
#endif
