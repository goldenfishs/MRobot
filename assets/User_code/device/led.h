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


 extern DEVICE_LED_t LED_Map;
/* Exported functions prototypes -------------------------------------------- */


int8_t BSP_LED_Set(char sign,DEVICE_LED_t ch,bool value,float duty_cycle);

#ifdef __cplusplus
}
#endif
