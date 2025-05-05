#pragma once

/* Includes ----------------------------------------------------------------- */
#include <stdint.h>
#include "main.h"
//#include "key_gpio.h"
/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */

///* KEY按键状态，设置用 */
typedef enum
{
    DEVICE_KEY_RELEASED,  //按键释放
    DEVICE_KEY_PRESSED,   //按键按下
    DEVICE_KEY_LONG_PRESS,  //按键长按
} DEVICE_KEY_Status_t;


/* 按键通道定义 */
typedef enum {
    DEVICE_KEY_1,
    DEVICE_KEY_2,
    /* 可根据需要扩展 */
    DEVICE_KEY_COUNT
} DEVICE_Key_Channel_t;

/* 按键硬件配置结构体 */
typedef struct {
    GPIO_TypeDef *port;    // GPIO端口
    uint16_t pin;          // 引脚编号
    uint8_t active_level;  // 有效电平（GPIO_PIN_SET/RESET）
	uint32_t trigger_edge;    // 中断触发边沿（RISING/FALLING）
} DEVICE_Key_Config_t;

void Key_Process(void);
uint16_t Get_Key_State(void);
void KeyTask(void);