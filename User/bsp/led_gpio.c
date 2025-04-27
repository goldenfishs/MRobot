/* Includes ----------------------------------------------------------------- */
#include "bsp/led_gpio.h"
#include "bsp/bsp.h"
#include <gpio.h>

/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */
static uint32_t led_stats; // 使用位掩码记录每个通道的状态

// 定义 LED 引脚映射表
static const uint16_t LED_PINS[] = {GPIO_PIN_2, GPIO_PIN_3, GPIO_PIN_4};

/* Private function --------------------------------------------------------- */
/* Exported functions ------------------------------------------------------- */
int8_t BSP_LED_Set(BSP_LED_Channel_t ch, BSP_LED_Status_t s) {
    if (ch >= BSP_LED_1 && ch <= BSP_LED_3) {
        uint16_t pin = LED_PINS[ch - BSP_LED_1]; // 获取对应的 GPIO 引脚
        switch (s) {
            case BSP_LED_ON:
                led_stats |= (1 << ch); // 设置对应位为1
                HAL_GPIO_WritePin(GPIOA, pin, GPIO_PIN_SET); // 点亮LED
                break;
            case BSP_LED_OFF:
                led_stats &= ~(1 << ch); // 清除对应位为0
                HAL_GPIO_WritePin(GPIOA, pin, GPIO_PIN_RESET); // 熄灭LED
                break;
            case BSP_LED_TAGGLE:
                led_stats ^= (1 << ch); // 切换对应位
                HAL_GPIO_TogglePin(GPIOA, pin); // 切换LED状态
                break;
            default:
                return -1; // 无效的状态
        }
        return 0; // 成功
    }
    return -1; // 无效的通道
}