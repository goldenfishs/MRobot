/* Includes ----------------------------------------------------------------- */
#include "bsp\gpio.h"

#include <gpio.h>
#include <main.h>

/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */
static void (*GPIO_Callback[BSP_GPIO_NUM][BSP_GPIO_CB_NUM])(void);

/* Private function  -------------------------------------------------------- */
static BSP_GPIO_t GPIO_Get(uint16_t pin) {
  switch (pin) {
    case USER_KEY_Pin:
      return BSP_GPIO_USER_KEY;
    /* case XXX_Pin:
      return BSP_GPIO_XXX; */
    default:
      return BSP_GPIO_ERR;
  }
}

void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin) {
  BSP_GPIO_t gpio = GPIO_Get(GPIO_Pin);
  if (gpio != BSP_GPIO_ERR) {
    if (GPIO_Callback[gpio][BSP_GPIO_EXTI_CB]) {
      GPIO_Callback[gpio][BSP_GPIO_EXTI_CB]();
    }
  }
}

/* Exported functions ------------------------------------------------------- */
int8_t BSP_GPIO_RegisterCallback(BSP_GPIO_t gpio, BSP_GPIO_Callback_t type, void (*callback)(void)) {
  if (callback == NULL || gpio >= BSP_GPIO_NUM || type >= BSP_GPIO_CB_NUM) return BSP_ERR_NULL;

  GPIO_Callback[gpio][type] = callback;
  return BSP_OK;
}

int8_t BSP_GPIO_EnableIRQ(BSP_GPIO_t gpio) {
  switch (gpio) {
    case BSP_GPIO_USER_KEY:
      HAL_NVIC_EnableIRQ(USER_KEY_EXTI_IRQn);
      break;

    /* case BSP_GPIO_XXX:
      HAL_NVIC_EnableIRQ(XXX_IRQn);
      break; */

    default:
      return BSP_ERR;
  }
  return BSP_OK;
}

int8_t BSP_GPIO_DisableIRQ(BSP_GPIO_t gpio) {
  switch (gpio) {
    case BSP_GPIO_USER_KEY:
      HAL_NVIC_DisableIRQ(USER_KEY_EXTI_IRQn);
      break;

    /* case BSP_GPIO_XXX:
      HAL_NVIC_DisableIRQ(XXX_IRQn);
      break; */

    default:
      return BSP_ERR;
  }
  return BSP_OK;
}