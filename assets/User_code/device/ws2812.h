#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include <stdint.h>
/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */
/* Exported functions prototypes -------------------------------------------- */
uint8_t DEVICE_WS2812_Init(uint16_t led_num);
uint8_t DEVICE_WS2812_Set(uint16_t num, uint8_t R, uint8_t G, uint8_t B);
void DEVICE_WS2812_DeInit();

#ifdef __cplusplus
}
#endif