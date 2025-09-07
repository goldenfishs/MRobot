#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include <stdint.h>
#include "bsp/gpio.h"
#include "bsp/pwm.h"
#include "bsp/bsp.h"

/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */

typedef struct {
BSP_GPIO_t gpio;
BSP_PWM_Channel_t channel;	
} DEVICE_LED_t;

/* Exported functions prototypes -------------------------------------------- */
int8_t LED_PWMSet(BSP_PWM_Channel_t channel,float duty_cycle);
int8_t LED_GPIOSet(BSP_GPIO_t gpio,bool value);

#ifdef __cplusplus
}
#endif
