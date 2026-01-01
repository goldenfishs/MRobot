/*
	pwm���ƶ��
*/

/*Includes   -----------------------------------------*/ 

#include "bsp/pwm.h"
#include "servo.h"

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

#define SERVO_MIN_DUTY  0.025f   
#define SERVO_MAX_DUTY  0.125f   

/* USER DEFINE BEGIN */

/* USER DEFINE END */   

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
    
	  /*���ƽǶȷ�Χ*/
    if (angle < 0.0f)   angle = 0.0f;
    if (angle > 180.0f) angle = 180.0f;
    /*�Ƕ�ӳ�䵽ռ�ձ�*/
    float duty = servo->min_duty + (angle / 180.0f) * (servo->max_duty - servo->min_duty);

    return BSP_PWM_Set(servo->pwm_ch, duty);
}

int8_t SERVO_Stop(SERVO_t *servo) {
    if (servo == NULL) return BSP_ERR;
    return BSP_PWM_Stop(servo->pwm_ch);
}