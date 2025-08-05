#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include <stdint.h>

#include "bsp.h"

/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */
/* PWM通道 */
typedef enum {
/* AUTO GENERATED BSP_PWM_ENUM */
  BSP_PWM_NUM,
  BSP_PWM_ERR,
} BSP_PWM_Channel_t;

/* Exported functions prototypes -------------------------------------------- */
int8_t BSP_PWM_Start(BSP_PWM_Channel_t ch);
int8_t BSP_PWM_SetComp(BSP_PWM_Channel_t ch, float duty_cycle);
int8_t BSP_PWM_SetFreq(BSP_PWM_Channel_t ch, float freq);
int8_t BSP_PWM_Stop(BSP_PWM_Channel_t ch);

#ifdef __cplusplus
}
#endif