#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include <stdint.h>

#include "bsp/bsp.h"

/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */

/* GPIO设备枚举，与设备对应 */
typedef enum {
  BSP_GPIO_USER_KEY,
  /* BSP_GPIO_XXX, */
  BSP_GPIO_NUM,
  BSP_GPIO_ERR,
} BSP_GPIO_t;

/* GPIO支持的中断回调函数类型 */
typedef enum {
  BSP_GPIO_EXTI_CB,
  BSP_GPIO_CB_NUM,
} BSP_GPIO_Callback_t;

/* Exported functions prototypes -------------------------------------------- */
int8_t BSP_GPIO_RegisterCallback(BSP_GPIO_t gpio, BSP_GPIO_Callback_t type, void (*callback)(void));
int8_t BSP_GPIO_EnableIRQ(BSP_GPIO_t gpio);
int8_t BSP_GPIO_DisableIRQ(BSP_GPIO_t gpio);

#ifdef __cplusplus
}
#endif