#ifndef KEY_GPIO_H
#define KEY_GPIO_H
/* Includes ----------------------------------------------------------------- */
#include <stdint.h>
#include "main.h"

/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */

///* KEY按键状态，设置用 */
typedef enum
{
    DEVICE_KEY_RELEASED,  //按键释放
    DEVICE_KEY_PRESSED,   //按键按下
} DEVICE_KEY_Status_t;

void KEY_Process(void);
uint8_t KEY_Get_State(void);

#endif
