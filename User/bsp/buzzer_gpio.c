/* Includes ----------------------------------------------------------------- */
#include "bsp/buzzer_gpio.h"
#include "bsp/bsp.h"
#include <gpio.h>

/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */

/* Private function --------------------------------------------------------- */
/* Exported functions ------------------------------------------------------- */

int8_t BSP_Buzzer_Set(BSP_Buzzer_Status_t s) {
    switch (s) {
        case BSP_BUZZER_ON:
            HAL_GPIO_WritePin(GPIOA, GPIO_PIN_1, GPIO_PIN_SET); // 打开蜂鸣器
            break;
        case BSP_BUZZER_OFF:
            HAL_GPIO_WritePin(GPIOA, GPIO_PIN_1, GPIO_PIN_RESET); // 关闭蜂鸣器
            break;
        case BSP_BUZZER_TAGGLE:
            HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_1); // 切换蜂鸣器状态
            break;
        default:
            return -1; // 无效的状态
    }
    return 0; // 成功
}