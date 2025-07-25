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
int8_t BSP_Delay(uint32_t ms);

int8_t BSP_Delay_Init(void);
int8_t BSP_Delay_us(uint32_t us);
int8_t BSP_Delay_ms(uint32_t ms);

#ifdef __cplusplus
}
#endif
