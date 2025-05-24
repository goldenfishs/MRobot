/* Includes ----------------------------------------------------------------- */
#include "bsp/led_gpio.h"
#include "bsp/bsp.h"
#include <gpio.h>

/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */

/* Private variables -------------------------------------------------------- */
static uint32_t led_stats; // 使用位掩码记录每个通道的状态，最多支持32LED

// 定义 LED 引脚和端口映射表：需要根据自己的修改，添加，或删减。
static const BSP_LED_Config_t LED_CONFIGS[] = {
    {GPIOA, GPIO_PIN_2}, // BSP_LED_1
    {GPIOA, GPIO_PIN_3}, // BSP_LED_2
    {GPIOA, GPIO_PIN_4}, // BSP_LED_3
};

#define LED_CHANNEL_COUNT (sizeof(LED_CONFIGS) / sizeof(LED_CONFIGS[0])) // 通道数量

/* Private function --------------------------------------------------------- */
/* Exported functions ------------------------------------------------------- */
int8_t BSP_LED_Set(BSP_LED_Channel_t ch, BSP_LED_Status_t s)
{
    if (ch < LED_CHANNEL_COUNT)
    {
        GPIO_TypeDef *port = LED_CONFIGS[ch].port;
        uint16_t pin = LED_CONFIGS[ch].pin;
        switch (s)
        {
        case BSP_LED_ON:
            led_stats |= (1 << ch);
            HAL_GPIO_WritePin(port, pin, GPIO_PIN_SET); // 点亮LED
            break;
        case BSP_LED_OFF:
            led_stats &= ~(1 << ch);
            HAL_GPIO_WritePin(port, pin, GPIO_PIN_RESET); // 熄灭LED
            break;
        case BSP_LED_TAGGLE:
            led_stats ^= (1 << ch);
            HAL_GPIO_TogglePin(port, pin); // 切换LED状态
            break;
        default:
            return BSP_ERR;
        }
        return BSP_OK;
    }
    return BSP_ERR;
}