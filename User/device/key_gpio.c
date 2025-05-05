/* Includes ----------------------------------------------------------------- */
#include "key_gpio.h"
#include "device.h"
#include <gpio.h>

/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */

static uint32_t key_stats; // 使用位掩码记录每个通道的状态，最多支持32LED

/* 外部声明标志位（标志问） */
extern volatile uint8_t key_flag; // 1=按下，0=松开

/* 按键状态结构 */
typedef struct {
    uint16_t state;       // 当前状态
    uint32_t press_timestamp; // 按下时间戳
    uint8_t last_flag;       // 上一次的标志位（用于消抖）
} Key_Status_t;

static Key_Status_t key = { 
    .state = DEVICE_KEY_RELEASED,
    .press_timestamp = 0,
    .last_flag = 0
};

/* 按键中断处理 */
void Key_Process(void) {
    uint32_t now = HAL_GetTick();
    uint8_t current_flag = key_flag; // 获取当前标志位

    switch(key.state) {
        case DEVICE_KEY_RELEASED:
            if(current_flag == 1) {
                // 首次检测到按下，记录时间戳
                if(key.last_flag == 0) {
                    key.press_timestamp = now;
                }
                // 消抖确认（20ms后仍为按下）
                if((now - key.press_timestamp) > 20) {
                    key.state = DEVICE_KEY_PRESSED;
                }
            }
            break;

        case DEVICE_KEY_PRESSED:
            case DEVICE_KEY_LONG_PRESS:
                if(current_flag == 1) {
                    // 持续按住超过20ms进入HOLD状态
                    if((now - key.press_timestamp) > 20) {
                        key.state = DEVICE_KEY_LONG_PRESS;
                    }
                } else {
                    key.state = DEVICE_KEY_RELEASED; // 松开复位
                }
                break;
    }

    key.last_flag = current_flag; // 更新历史状态
}

//获取当前按键状态 
uint16_t Get_Key_State(void) {
    return key.state;
}
//也许是后续逻辑(跟在前面的代码后面放在循环里）
void KeyTask(void)
{
	
	//仅按下就执行逻辑
//	if( key.state == DEVICE_KEY_PRESSED)
//	{
//		//循环执行逻辑（按下）
//	}
	//按住才执行逻辑，松开就停下
	if (key.state == DEVICE_KEY_LONG_PRESS)
	{
		//执行逻辑
	}
	else if	(key.state == DEVICE_KEY_RELEASED)
	{
		//停止逻辑
	}
}