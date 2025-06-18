/* Includes ----------------------------------------------------------------- */
#include "main.h"
#include "servo.h"

#include "bsp/servo_pwm.h"


/* Private define ----------------------------------------------------------- */
#define MIN_CYCLE 0.5f		//change begin
#define MAX_CYCLE 2.5f
#define ANGLE_LIMIT 180		//change end
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */
/* Private function  -------------------------------------------------------- */
/* Exported functions ------------------------------------------------------- */
int serve_Init(BSP_PWM_Channel_t ch)
{
	if(BSP_PWM_Start(ch)!=0){
		return -1;
	}else return 0;	
}


int set_servo_angle(BSP_PWM_Channel_t ch,float angle)
{
	if (angle < 0.0f || angle > ANGLE_LIMIT) {
        return -1; // 无效的角度
    }
	
	float duty_cycle=MIN_CYCLE+(MAX_CYCLE-MIN_CYCLE)*(angle/ANGLE_LIMIT);
	if(BSP_PWM_Set(ch,duty_cycle)!=0){
		return -1;
	}else return 0;
}

