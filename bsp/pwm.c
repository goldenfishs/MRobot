/* Includes ----------------------------------------------------------------- */
#include "tim.h"
#include "bsp/pwm.h"
#include "bsp.h"

/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
typedef struct {
  TIM_HandleTypeDef *tim;
  uint16_t channel;
} BSP_PWM_Config_t;

/* Private variables -------------------------------------------------------- */
static const BSP_PWM_Config_t PWM_Map[BSP_PWM_NUM] = {
/* AUTO GENERATED BSP_PWM_MAP */
};

/* Private function  -------------------------------------------------------- */
/* Exported functions ------------------------------------------------------- */

int8_t BSP_PWM_Start(BSP_PWM_Channel_t ch) {
  if (ch >= BSP_PWM_NUM) return BSP_ERR;
  
  HAL_TIM_PWM_Start(PWM_Map[ch].tim, PWM_Map[ch].channel);
  return BSP_OK;
}

int8_t BSP_PWM_SetComp(BSP_PWM_Channel_t ch, float duty_cycle) {
  if (ch >= BSP_PWM_NUM) return BSP_ERR;
  
  if (duty_cycle > 1.0f) {
    duty_cycle = 1.0f;
  }
  if (duty_cycle < 0.0f) {
    duty_cycle = 0.0f;
  }
  // 获取ARR值（周期值）
  uint32_t arr = __HAL_TIM_GET_AUTORELOAD(PWM_Map[ch].tim);
  
  // 计算比较值：CCR = duty_cycle * (ARR + 1)
  uint32_t ccr = (uint32_t)(duty_cycle * (arr + 1));
  
  __HAL_TIM_SET_COMPARE(PWM_Map[ch].tim, PWM_Map[ch].channel, ccr);

  return BSP_OK;
}

int8_t BSP_PWM_SetFreq(BSP_PWM_Channel_t ch, float freq) {
  if (ch >= BSP_PWM_NUM) return BSP_ERR;

  uint32_t timer_clock = HAL_RCC_GetPCLK1Freq(); // Get the timer clock frequency
  uint32_t prescaler = PWM_Map[ch].tim->Init.Prescaler;
  uint32_t period = (timer_clock / (prescaler + 1)) / freq - 1;
  
  if (period > UINT16_MAX) {
    return BSP_ERR; // Frequency too low
  }
  __HAL_TIM_SET_AUTORELOAD(PWM_Map[ch].tim, period);
  
  return BSP_OK;
}

int8_t BSP_PWM_Stop(BSP_PWM_Channel_t ch) {
  if (ch >= BSP_PWM_NUM) return BSP_ERR;
  
  HAL_TIM_PWM_Stop(PWM_Map[ch].tim, PWM_Map[ch].channel);
  return BSP_OK;
}

uint32_t BSP_PWM_GetAutoReloadPreload(BSP_PWM_Channel_t ch) {
    if (ch >= BSP_PWM_NUM) return BSP_ERR;
    return PWM_Map[ch].tim->Init.AutoReloadPreload;  
}

TIM_HandleTypeDef* BSP_PWM_GetHandle(BSP_PWM_Channel_t ch) {
  return PWM_Map[ch].tim;
}


uint16_t BSP_PWM_GetChannel(BSP_PWM_Channel_t ch) {
  if (ch >= BSP_PWM_NUM) return BSP_ERR;
  return PWM_Map[ch].channel;
}

int8_t BSP_PWM_Start_DMA(BSP_PWM_Channel_t ch, uint32_t *pData, uint16_t Length) {
  if (ch >= BSP_PWM_NUM) return BSP_ERR;
  
  HAL_TIM_PWM_Start_DMA(PWM_Map[ch].tim, PWM_Map[ch].channel, pData, Length);
  return BSP_OK;
}

int8_t BSP_PWM_Stop_DMA(BSP_PWM_Channel_t ch) {
  if (ch >= BSP_PWM_NUM) return BSP_ERR;
  
  HAL_TIM_PWM_Stop_DMA(PWM_Map[ch].tim, PWM_Map[ch].channel);
  return BSP_OK;
}