#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include <stdint.h>
#include <stdbool.h>

#include "bsp/bsp.h"

/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */
typedef enum {
/* AUTO GENERATED BSP_GPIO_ENUM */
  BSP_GPIO_NUM,
  BSP_GPIO_ERR,
} BSP_GPIO_t;

/* Exported functions prototypes -------------------------------------------- */
int8_t BSP_GPIO_RegisterCallback(BSP_GPIO_t gpio, void (*callback)(void));

int8_t BSP_GPIO_EnableIRQ(BSP_GPIO_t gpio);
int8_t BSP_GPIO_DisableIRQ(BSP_GPIO_t gpio);

int8_t BSP_GPIO_WritePin(BSP_GPIO_t gpio, bool value);
int8_t BSP_GPIO_TogglePin(BSP_GPIO_t gpio);

bool BSP_GPIO_ReadPin(BSP_GPIO_t gpio);

#ifdef __cplusplus
}
#endif