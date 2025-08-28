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
/* Forward declarations */
typedef struct __TIM_HandleTypeDef TIM_HandleTypeDef;

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
uint32_t BSP_PWM_GetAutoReloadPreload(BSP_PWM_Channel_t ch);
uint16_t BSP_PWM_GetChannel(BSP_PWM_Channel_t ch);
TIM_HandleTypeDef* BSP_PWM_GetHandle(BSP_PWM_Channel_t ch);
int8_t BSP_PWM_Start_DMA(BSP_PWM_Channel_t ch, uint32_t *pData, uint16_t Length);
int8_t BSP_PWM_Stop_DMA(BSP_PWM_Channel_t ch);

#ifdef __cplusplus
}
#endif