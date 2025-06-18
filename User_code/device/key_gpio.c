/* Includes ----------------------------------------------------------------- */
#include "key_gpio.h"
#include "device.h"
#include "bsp/gpio_exti.h"
#include "gpio.h"
/* Private define ----------------------------------------------------------- */
#define DEBOUNCE_TIME_MS  20
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */
/* Private function  -------------------------------------------------------- */
/* 外部声明标志位（标志位） */
volatile uint8_t key_flag = 0; // 1=按下，0=松开
volatile uint8_t key_exti = 0; 
volatile uint8_t key_pressed = 0;  // 全局标志位
static uint32_t last_debounce_time = 0;    // 消抖

/* Private function  -------------------------------------------------------- */
static void KEY_Interrupt_Callback(void) {
    // 切换标志位状态

    key_flag = !key_flag;
	key_exti = 1;

} 

/* Exported functions ------------------------------------------------------- */
void KEY_Process(void)
{
     BSP_GPIO_RegisterCallback(BSP_GPIO_USER_KEY, BSP_GPIO_EXTI_CB, KEY_Interrupt_Callback);

	if(key_exti == 1)
	{
		uint32_t now = HAL_GetTick();  
        // 检查是否超过消抖时间
        if ((now - last_debounce_time) > DEBOUNCE_TIME_MS) {
            // 更新有效状态（假设按下为低电平）
		    if(key_flag == 0)
	        {
		        key_pressed = DEVICE_KEY_RELEASED;
	        }
	        if(key_flag == 1)
	        {
		        key_pressed = DEVICE_KEY_PRESSED;
	         }
		 }
		else
		{
			 HAL_GPIO_ReadPin(GPIOA, GPIO_PIN_6);
			
		}
	   last_debounce_time = now; // 重置消抖计时器
	   key_exti = 0;
    }
	else
	{
		
	}
 }

uint8_t KEY_Get_State(void) {
    return key_pressed;
}


