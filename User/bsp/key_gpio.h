#pragma once

/* Includes ----------------------------------------------------------------- */
#include <stdint.h>
#include "main.h"
//#include "key_gpio.h"
/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */

/* KEY按键状态，设置用 */
typedef enum
{
    BSP_KEY_RELEASED,  //按键释放
    BSP_KEY_PRESSED,   //按键按下
    BSP_KEY_LONG_PRESS,  //按键长按
} BSP_KEY_Status_t;


/* 按键通道定义 */
typedef enum {
    BSP_KEY_1,
    BSP_KEY_2,
    /* 可根据需要扩展 */
    BSP_KEY_COUNT
} BSP_Key_Channel_t;


/* 按键硬件配置结构体 */
typedef struct {
    GPIO_TypeDef *port;    // GPIO端口
    uint16_t pin;          // 引脚编号
    uint8_t active_level;  // 有效电平（GPIO_PIN_SET/RESET）
} BSP_Key_Config_t;

int8_t BSP_Key_Read(BSP_Key_Channel_t ch);