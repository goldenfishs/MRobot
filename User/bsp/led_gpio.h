#pragma once

/* Includes ----------------------------------------------------------------- */
#include <stdint.h>

/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */

/* LED灯状态，设置用 */
typedef enum
{
    BSP_LED_ON,
    BSP_LED_OFF,
    BSP_LED_TAGGLE,
} BSP_LED_Status_t;

/* LED通道 */
typedef enum
{
    BSP_LED_1,
    BSP_LED_2,
    BSP_LED_3,
    /*BSP_LED_XXX*/
} BSP_LED_Channel_t;

/* LED GPIO 配置 */
typedef struct
{
    GPIO_TypeDef *port; // GPIO 端口 (如 GPIOA, GPIOB)
    uint16_t pin;       // GPIO 引脚
} BSP_LED_Config_t;

/* Exported functions prototypes -------------------------------------------- */

int8_t BSP_LED_Set(BSP_LED_Channel_t ch, BSP_LED_Status_t s);