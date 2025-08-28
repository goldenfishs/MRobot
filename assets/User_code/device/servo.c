/*
	pwm控制舵机
*/

/*Includes   -----------------------------------------*/ 

#include "bsp/pwm.h"
#include "servo.h"

#define SERVO_MIN_DUTY  0.025f   
#define SERVO_MAX_DUTY  0.125f   

/**
 * @brief  
 * @param  
 * @retval BSP_OK / BSP_ERR
 */

int8_t SERVO_Init(SERVO_t *servo) {
    if (servo == NULL) return BSP_ERR;
    return BSP_PWM_Start(servo->pwm_ch);
}

int8_t SERVO_SetAngle(SERVO_t *servo, float angle) {
    if (servo == NULL) return BSP_ERR;
    
	  /*限制角度范围*/
    if (angle < 0.0f)   angle = 0.0f;
    if (angle > 180.0f) angle = 180.0f;
    /*角度映射到占空比*/
    float duty = servo->min_duty + (angle / 180.0f) * (servo->max_duty - servo->min_duty);

    return BSP_PWM_Set(servo->pwm_ch, duty);
}

int8_t SERVO_Stop(SERVO_t *servo) {
    if (servo == NULL) return BSP_ERR;
    return BSP_PWM_Stop(servo->pwm_ch);
}