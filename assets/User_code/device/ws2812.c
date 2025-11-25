/* Includes ----------------------------------------------------------------- */
#include "ws2812.h"
#include "device.h"

#include "bsp/pwm.h"
#include <stdlib.h>

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

/* Private define ----------------------------------------------------------- */
#define DEVICE_WS2812_T1H            (uint16_t)(BSP_PWM_GetAutoReloadPreload(BSP_PWM_WS2812) * 0.56)   // High-level width of logic-1 pulse
#define DEVICE_WS2812_T0H            (BSP_PWM_GetAutoReloadPreload(BSP_PWM_WS2812) * 0.29)             // High-level width of logic-0 pulse
#define DEVICE_WS2812_WS_REST        40   // Number of reset pulses (low level) after data stream
#define DEVICE_WS2812_DATA_LEN       24   // WS2812 data length: 24 bits (GRB) per LED
#define DEVICE_WS2812_RST_NUM        50   // Extra reset pulses reserved at the end of the buffer

/* USER DEFINE BEGIN */

/* USER DEFINE END */

/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* USER STRUCT BEGIN */

/* USER STRUCT END */

/* Private variables -------------------------------------------------------- */
static uint16_t DEVICE_WS2812_LED_NUM; 	       // Total number of LEDs
static uint16_t *DEVICE_WS2812_RGB_Buff = NULL;// PWM duty buffer for DMA
/* Private function  -------------------------------------------------------- */
/* USER FUNCTION BEGIN */

/* USER FUNCTION END */

/* Exported functions ------------------------------------------------------- */
/**
 * Set color of a single WS2812 LED
 * @param num LED index (1-based)
 * @param R   Red value   (0-255)
 * @param G   Green value (0-255)
 * @param B   Blue value  (0-255)
 * @return    DEVICE_OK on success, DEVICE_ERR if num is invalid
 */
uint8_t DEVICE_WS2812_Set(uint16_t num, uint8_t R, uint8_t G, uint8_t B)
{
  if(num<1 || num>DEVICE_WS2812_LED_NUM) return DEVICE_ERR;
  uint32_t indexx = (num-1) * DEVICE_WS2812_DATA_LEN;
  
  /* WS2812 uses GRB order, MSB first */
  for (uint8_t i = 0; i < 8; i++) {
    // G
    DEVICE_WS2812_RGB_Buff[indexx + i]      = (G & (0x80 >> i)) ? DEVICE_WS2812_T1H : DEVICE_WS2812_T0H;
    // R
    DEVICE_WS2812_RGB_Buff[indexx + i + 8]  = (R & (0x80 >> i)) ? DEVICE_WS2812_T1H : DEVICE_WS2812_T0H;
    // B
    DEVICE_WS2812_RGB_Buff[indexx + i + 16] = (B & (0x80 >> i)) ? DEVICE_WS2812_T1H : DEVICE_WS2812_T0H;
  }
  return DEVICE_OK;
}

/**
 * Initialize WS2812 driver
 * @param ledNum Number of LEDs in the strip
 * @return DEVICE_OK on success, DEVICE_ERR if memory allocation or PWM setup fails
 */
uint8_t DEVICE_WS2812_Init(uint16_t ledNum)
{
	DEVICE_WS2812_LED_NUM = ledNum;

    if (DEVICE_WS2812_RGB_Buff != NULL)
    {
        free(DEVICE_WS2812_RGB_Buff);
        DEVICE_WS2812_RGB_Buff = NULL;
    }

    /* Allocate new buffer: 24 PWM samples per LED + reset pulses */
    size_t bufLen = ledNum * DEVICE_WS2812_DATA_LEN + DEVICE_WS2812_RST_NUM;
    DEVICE_WS2812_RGB_Buff = (uint16_t *)malloc(bufLen * sizeof(uint16_t));
    if (DEVICE_WS2812_RGB_Buff == NULL)
        return DEVICE_ERR;              

    /* Initialize all LEDs to dim green */
    for (int i = 1; i <= ledNum; i++)
        DEVICE_WS2812_Set(i, 0, 20, 0);
	
	/* Configure PWM frequency to 800 kHz and start DMA */
    if (BSP_PWM_SetFreq(BSP_PWM_WS2812, 800000) == DEVICE_OK)
        BSP_PWM_Start_DMA(
            BSP_PWM_WS2812,
            (uint32_t *)DEVICE_WS2812_RGB_Buff,
            bufLen);
    else
        return DEVICE_ERR;

    return DEVICE_OK;
}

/**
 * De-initialize WS2812 driver
 * Frees the DMA buffer and stops PWM
 */
void DEVICE_WS2812_DeInit()
{
	for (int i = 1; i <= DEVICE_WS2812_LED_NUM; i++)
        DEVICE_WS2812_Set(i, 0, 0, 0);
	if (DEVICE_WS2812_RGB_Buff != NULL)
    {
        free(DEVICE_WS2812_RGB_Buff);
        DEVICE_WS2812_RGB_Buff = NULL;
    }
	BSP_PWM_Stop_DMA(BSP_PWM_WS2812);
}