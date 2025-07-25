/* Includes ----------------------------------------------------------------- */
#include "servo_pwm.h"

#include "main.h"


/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */
/* Private function  -------------------------------------------------------- */
/* Exported functions ------------------------------------------------------- */

int8_t BSP_PWM_Start(BSP_PWM_Channel_t ch) {
  
  TIM_HandleTypeDef* htim = pwm_channel_config[ch].htim;
  uint32_t channel = pwm_channel_config[ch].channel;

  if(HAL_TIM_PWM_Start(htim, channel)!=HAL_OK){
	return -1;
  }else return 0;
}

int8_t BSP_PWM_Set(BSP_PWM_Channel_t ch, float duty_cycle) {
  if (duty_cycle > 1.0f) return -1;

  uint16_t pulse = duty_cycle/CYCLE * PWM_RESOLUTION;

  if(__HAL_TIM_SET_COMPARE(pwm_channel_config[ch].htim, pwm_channel_config[ch].channel, pulse)!=HAL_OK){
	return -1;
  }else return 0;
}

int8_t BSP_PWM_Stop(BSP_PWM_Channel_t ch){

  TIM_HandleTypeDef* htim = pwm_channel_config[ch].htim;
  uint32_t channel = pwm_channel_config[ch].channel;

  if(HAL_TIM_PWM_Stop(htim, channel)!=HAL_OK){
	return -1;
  }else return 0;


};




