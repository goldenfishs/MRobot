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


int8_t LED_PWMSet(BSP_PWM_Channel_t channel,float duty_cycle)
{

			    if (duty_cycle < 0.0f || duty_cycle > 1.0f) {
                return DEVICE_ERR_NULL; // 错误：占空比超出范围
				}
		uint16_t pulse = (uint16_t)(duty_cycle * (float)UINT16_MAX);
		BSP_PWM_Start(channel);
		BSP_PWM_SetComp(channel, pulse);
		return DEVICE_OK;
}

int8_t LED_GPIOSet(BSP_GPIO_t gpio,bool value)		
{					
		BSP_GPIO_WritePin(gpio,value);
	return DEVICE_OK;
}






