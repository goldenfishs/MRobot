#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include "device.h"          
#include "bsp/pwm.h"         
#include <stddef.h>

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

/* Exported constants ------------------------------------------------------- */

/* USER DEFINE BEGIN */

/* USER DEFINE END */

/* Exported types ----------------------------------------------------------- */
typedef struct {
    DEVICE_Header_t header;    
    BSP_PWM_Channel_t channel; 
} BUZZER_t;

/* USER STRUCT BEGIN */

/* USER STRUCT END */

/* Exported functions prototypes -------------------------------------------- */

int8_t BUZZER_Init(BUZZER_t *buzzer, BSP_PWM_Channel_t channel);


int8_t BUZZER_Start(BUZZER_t *buzzer);


int8_t BUZZER_Stop(BUZZER_t *buzzer);


int8_t BUZZER_Set(BUZZER_t *buzzer, float freq, float duty_cycle);

/* USER FUNCTION BEGIN */

/* USER FUNCTION END */

#ifdef __cplusplus
}
#endif
