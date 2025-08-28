#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include <cmsis_os2.h>
	
#include "bsp\pwm.h"
	
/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */

/**
 * @brief ???????
 */
typedef struct {
   BSP_PWM_Channel_t pwm_ch;  
   float min_duty;         
   float max_duty;      
} SERVO_t;

/**
 * @brief  
 * @param  servo 
 * @retval BSP_OK / BSP_ERR
 */

int8_t SERVO_Init(SERVO_t *servo);

/**
 * @brief 
 * @param  servo
 * @param  angle 
 * @retval BSP_OK / BSP_ERR
 */
int8_t SERVO_SetAngle(SERVO_t *servo, float angle);

/**
 * @brief 
 * @param  servo 
 * @retval BSP_OK / BSP_ERR
 */
 
int8_t SERVO_Stop(SERVO_t *servo);

	
#ifdef __cplusplus
}
#endif