/* Includes ----------------------------------------------------------------- */
#include "key_gpio.h"
#include "bsp.h"
#include <gpio.h>

/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */

static uint32_t key_stats; // 使用位掩码记录每个通道的状态，最多支持32LED
/* 按键配置表（根据实际硬件修改） */
static const BSP_Key_Config_t KEY_CONFIGS[] = {
    {GPIOA, GPIO_PIN_7, GPIO_PIN_SET},   // KEY1按下时电平为高
    {GPIOA, GPIO_PIN_9, GPIO_PIN_SET}, // KEY2按下时电平为低
    // 添加更多按键...
};

#define KEY_COUNT (sizeof(KEY_CONFIGS)/sizeof(KEY_CONFIGS[0])
	

//读取按键状态（带消抖）
int8_t BSP_Key_Read(BSP_Key_Channel_t ch) {
    static uint32_t last_press_time[BSP_KEY_COUNT] = {0};      //上次按下时间
    const uint32_t debounce_ms = 20;      //按键消抖时间
    const uint32_t long_press_ms = 2000;      //按键长按时间
    
    if(ch >= BSP_KEY_COUNT) return BSP_KEY_RELEASED ;
    
    const BSP_Key_Config_t *cfg = &KEY_CONFIGS[ch];
    GPIO_PinState state = HAL_GPIO_ReadPin(cfg->port, cfg->pin);
    
    if(state == cfg->active_level) {
        uint32_t now = HAL_GetTick();      //用于记录按键按下时间（这里比较state是为了方便适应不同有效电平做出修改的，也可以改成直接检测电平高低）
        
        //消抖检测(只有按下超过20ms才被认为按下）
        if((now - last_press_time[ch]) > debounce_ms) {
            //长按检测（只有被按下超过2000ms才被认为是长按，根据实际情况可做出修改）
            if((now - last_press_time[ch]) > long_press_ms) {
                return BSP_KEY_LONG_PRESS;
            }
            return BSP_KEY_PRESSED;
        }
    } else {
        last_press_time[ch] = HAL_GetTick();
    }
    return BSP_KEY_RELEASED;
}	
