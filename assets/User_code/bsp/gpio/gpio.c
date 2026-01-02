/* Includes ----------------------------------------------------------------- */
#include "bsp/gpio.h"

#include <gpio.h>
#include <main.h>

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

/* Private define ----------------------------------------------------------- */
/* USER DEFINE BEGIN */

/* USER DEFINE END */

/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
typedef struct {
  uint16_t pin;
  GPIO_TypeDef *gpio;
} BSP_GPIO_MAP_t;

/* USER STRUCT BEGIN */

/* USER STRUCT END */

/* Private variables -------------------------------------------------------- */
static const BSP_GPIO_MAP_t GPIO_Map[BSP_GPIO_NUM] = {
/* AUTO GENERATED BSP_GPIO_MAP */
};

static void (*GPIO_Callback[16])(void);

/* Private function  -------------------------------------------------------- */
/* USER FUNCTION BEGIN */

/* USER FUNCTION END */

void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin) {
  for (uint8_t i = 0; i < 16; i++) {
    if (GPIO_Pin & (1 << i)) {
      if (GPIO_Callback[i]) {
        GPIO_Callback[i]();
      }
    }
  }
}

/* Exported functions ------------------------------------------------------- */
int8_t BSP_GPIO_RegisterCallback(BSP_GPIO_t gpio, void (*callback)(void)) {
  if (callback == NULL) return BSP_ERR_NULL;
  if (gpio >= BSP_GPIO_NUM) return BSP_ERR;

  // 从GPIO映射中获取对应的pin值
  uint16_t pin = GPIO_Map[gpio].pin;
  
  for (uint8_t i = 0; i < 16; i++) {
    if (pin & (1 << i)) {
      GPIO_Callback[i] = callback;
      break;
    }
  }
  return BSP_OK;
}

int8_t BSP_GPIO_EnableIRQ(BSP_GPIO_t gpio) {
  switch (gpio) {
/* AUTO GENERATED BSP_GPIO_ENABLE_IRQ */
    default:
      return BSP_ERR;
  }
}

int8_t BSP_GPIO_DisableIRQ(BSP_GPIO_t gpio) {
  switch (gpio) {
/* AUTO GENERATED BSP_GPIO_DISABLE_IRQ */
    default:
      return BSP_ERR;
  }
}
int8_t BSP_GPIO_WritePin(BSP_GPIO_t gpio, bool value){
  if (gpio >= BSP_GPIO_NUM) return BSP_ERR;
  HAL_GPIO_WritePin(GPIO_Map[gpio].gpio, GPIO_Map[gpio].pin, value);
  return BSP_OK;
}

int8_t BSP_GPIO_TogglePin(BSP_GPIO_t gpio){
  if (gpio >= BSP_GPIO_NUM) return BSP_ERR;
  HAL_GPIO_TogglePin(GPIO_Map[gpio].gpio, GPIO_Map[gpio].pin);
  return BSP_OK;
}

bool BSP_GPIO_ReadPin(BSP_GPIO_t gpio){
  if (gpio >= BSP_GPIO_NUM) return false;
  return HAL_GPIO_ReadPin(GPIO_Map[gpio].gpio, GPIO_Map[gpio].pin) == GPIO_PIN_SET;
}