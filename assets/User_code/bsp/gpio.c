/* Includes ----------------------------------------------------------------- */
#include "bsp/gpio.h"

#include <gpio.h>
#include <main.h>

/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */
static void (*GPIO_Callback[16])(void);

/* Private function  -------------------------------------------------------- */
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
int8_t BSP_GPIO_RegisterCallback(uint16_t pin, void (*callback)(void)) {
  if (callback == NULL) return BSP_ERR_NULL;

  for (uint8_t i = 0; i < 16; i++) {
    if (pin & (1 << i)) {
      GPIO_Callback[i] = callback;
      break;
    }
  }
  return BSP_OK;
}

int8_t BSP_GPIO_EnableIRQ(uint16_t pin) {
  switch (pin) {
    /* AUTO GENERATED BSP_GPIO_ENABLE_IRQ */
    default:
      return BSP_ERR;
  }
  return BSP_OK;
}

int8_t BSP_GPIO_DisableIRQ(uint16_t pin) {
  switch (pin) {
    /* AUTO GENERATED BSP_GPIO_DISABLE_IRQ */
    default:
      return BSP_ERR;
  }
  return BSP_OK;
}