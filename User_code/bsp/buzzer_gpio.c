

/* Includes ----------------------------------------------------------------- */
#include <gpio.h>
#include "bsp/bsp.h"
#include "bsp/buzzer_gpio.h"
/* Private define ----------------------------------------------------------- */
#define BSP_BUZZER_GPIO GPIOA
#define BSP_BUZZER_PIN GPIO_PIN_1
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */
/* Private function --------------------------------------------------------- */
/* Exported functions ------------------------------------------------------- */
int8_t BSP_Buzzer_Set(BSP_Buzzer_Status_t s)
{
    switch (s)
    {
    case BSP_BUZZER_ON:
        HAL_GPIO_WritePin(BSP_BUZZER_GPIO, BSP_BUZZER_PIN, GPIO_PIN_SET); // 打开蜂鸣器
        break;
    case BSP_BUZZER_OFF:
        HAL_GPIO_WritePin(BSP_BUZZER_GPIO, BSP_BUZZER_PIN, GPIO_PIN_RESET); // 关闭蜂鸣器
        break;
    case BSP_BUZZER_TAGGLE:
        HAL_GPIO_TogglePin(BSP_BUZZER_GPIO, BSP_BUZZER_PIN); // 切换蜂鸣器状态
        break;
    default:
        return BSP_ERR;
    }
    return BSP_OK;
}