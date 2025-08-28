#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include "device.h"          
#include "bsp/pwm.h"         
#include <stddef.h>

/* Exported constants ------------------------------------------------------- */

/* Exported types ----------------------------------------------------------- */
typedef struct {
    DEVICE_Header_t header;    
    BSP_PWM_Channel_t channel; 
} BUZZER_t;

/* Exported functions prototypes -------------------------------------------- */


int8_t BUZZER_Init(BUZZER_t *buzzer, BSP_PWM_Channel_t channel);


int8_t BUZZER_Start(BUZZER_t *buzzer);


int8_t BUZZER_Stop(BUZZER_t *buzzer);


int8_t BUZZER_Set(BUZZER_t *buzzer, float freq, float duty_cycle);

#ifdef __cplusplus
}
#endif
