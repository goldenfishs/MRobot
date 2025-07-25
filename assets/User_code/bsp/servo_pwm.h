#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include <stdint.h>
#include "tim.h"
#include "bsp/bsp.h"

/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */
typedef struct {
  TIM_HandleTypeDef* htim; // 定时器句柄
  uint32_t channel;        // 定时器通道
} PWM_Channel_Config_t;

#define PWM_RESOLUTION 1000 // ARR                                      change begin
#define CYCLE 20 //ms

typedef enum {				
  BSP_PWM_SERVO = 0,      
  BSP_PWM_IMU_HEAT = 1,   
} BSP_PWM_Channel_t;

const PWM_Channel_Config_t pwm_channel_config[] = {		
  [BSP_PWM_SERVO] = { &htim1, TIM_CHANNEL_1 },  // xxx 对应 TIMx 通道x
  [BSP_PWM_IMU_HEAT] = { &htim1, TIM_CHANNEL_2 } 
};																	  //change end

/* Exported functions prototypes -------------------------------------------- */
int8_t BSP_PWM_Start(BSP_PWM_Channel_t ch);
int8_t BSP_PWM_Set(BSP_PWM_Channel_t ch, float duty_cycle);
int8_t BSP_PWM_Stop(BSP_PWM_Channel_t ch);

#ifdef __cplusplus
}
#endif





