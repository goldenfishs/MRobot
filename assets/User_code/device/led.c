/*
   led控制
*/
/*Includes   -----------------------------------------*/
#include "device/led.h"
#include "bsp/gpio.h"
#include "bsp/pwm.h"
#include "device.h"


/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */

DEVICE_LED_t LED_Map={
 BSP_GPIO_BLUE,
BSP_PWM_TIM5_CH1,
};

int8_t BSP_LED_Set(char sign,DEVICE_LED_t ch,bool value,float duty_cycle)
{
	switch(sign){
		case 'p':
		case 'P':
			    if (duty_cycle < 0.0f || duty_cycle > 1.0f) {
                return DEVICE_ERR_NULL; // 错误：占空比超出范围
            }
				uint16_t pulse = (uint16_t)(duty_cycle * (float)UINT16_MAX);
		BSP_PWM_Start(LED_Map.channel);
		BSP_PWM_SetComp(LED_Map.channel, pulse);
			break;
	
		case 'g':
		case 'G':
		BSP_GPIO_WritePin(LED_Map.gpio,value);
		break;
	default:
            return DEVICE_ERR_INITED; // 错误：无效的控制方式
	}
	return DEVICE_OK;
}






