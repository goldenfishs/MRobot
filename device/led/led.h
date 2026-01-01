#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
/* USER DEFIN BEGIN */

/* USER DEFIN END */
#include <stdint.h>
#ifdef LED_GPIO
#include "bsp/gpio.h"
#endif
#ifdef LED_PWM
#include "bsp/pwm.h"
#endif
#include "bsp/bsp.h"
/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */


typedef struct {
#ifdef LED_GPIO
BSP_GPIO_t gpio;
#endif
#ifdef LED_PWM
BSP_PWM_Channel_t channel;	
#endif
} DEVICE_LED_t;


 extern DEVICE_LED_t LED_Map;
/* Exported functions prototypes -------------------------------------------- */
#ifdef LED_PWM
int8_t DEVICE_LED_PWM_Set(BSP_PWM_Channel_t channel, float duty_cycle)
{
    if (duty_cycle < 0.0f || duty_cycle > 1.0f) {
        return DEVICE_ERR_NULL; // 错误：占空比超出范围
    }
    uint16_t pulse = (uint16_t)(duty_cycle * (float)UINT16_MAX);
    BSP_PWM_Start(channel);
    BSP_PWM_SetComp(channel, pulse);
    return DEVICE_OK;
}
#endif

#ifdef LED_GPIO
int8_t DEVICE_LED_GPIO_Set(BSP_GPIO_t gpio, bool value)
{
	if (value) {
		BSP_GPIO_WritePin(gpio, true);
	} else {
		BSP_GPIO_WritePin(gpio, false);
	}
	return DEVICE_OK;
}
#endif

#ifdef __cplusplus
}
#endif
