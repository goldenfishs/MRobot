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
  BSP_GPIO_IMU_ACCL_CS,
  BSP_GPIO_IMU_GYRO_CS,
  BSP_GPIO_IMU_ACCL_INT,
  BSP_GPIO_IMU_GYRO_INT,
  BSP_GPIO_USER_KEY,
  BSP_GPIO_NUM,
  BSP_GPIO_ERR,
} BSP_GPIO_t;

/* Exported functions prototypes -------------------------------------------- */
int8_t BSP_GPIO_RegisterCallback(uint16_t pin, void (*callback)(void));

int8_t BSP_GPIO_EnableIRQ(uint16_t pin);
int8_t BSP_GPIO_DisableIRQ(uint16_t pin);

int8_t BSP_GPIO_WritePin(BSP_GPIO_t gpio, bool value);
int8_t BSP_GPIO_TogglePin(BSP_GPIO_t gpio);

bool BSP_GPIO_ReadPin(BSP_GPIO_t gpio);

#ifdef __cplusplus
}
#endif
