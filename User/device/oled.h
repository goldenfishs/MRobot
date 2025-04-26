#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include <stdint.h>

/* Exported constants ------------------------------------------------------- */
#define OLED_COLOR_BLACK 0
#define OLED_COLOR_WHITE 1

/* Exported functions prototypes -------------------------------------------- */
void OLED_Init(void);
void OLED_Clear(void);
void OLED_UpdateScreen(void);
void OLED_DrawPixel(uint8_t x, uint8_t y, uint8_t color);
void OLED_DrawString(uint8_t x, uint8_t y, const char *str, uint8_t color);
void OLED_DrawChar(uint8_t x, uint8_t y, char ch, uint8_t color);
void OLED_ShowChinese(uint8_t x, uint8_t y, uint8_t index);


#ifdef __cplusplus
}
#endif