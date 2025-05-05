#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include <stdint.h>
#include "tim.h"
#include "bsp/bsp.h"
#include "bsp/servo_pwm.h"
/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */
	
	
	
extern int serve_Init(BSP_PWM_Channel_t ch);
extern int set_servo_angle(BSP_PWM_Channel_t ch,float angle);
	
	
	
	
	
	
	
	
	
	
	
	
	
	
#ifdef __cplusplus
}
#endif





