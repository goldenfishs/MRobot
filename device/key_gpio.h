#ifndef KEY_GPIO_H
#define KEY_GPIO_H
/* Includes ----------------------------------------------------------------- */
#include <stdint.h>
#include "main.h"

/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */

///* KEY����״̬�������� */
typedef enum
{
    DEVICE_KEY_RELEASED,  //�����ͷ�
    DEVICE_KEY_PRESSED,   //��������
} DEVICE_KEY_Status_t;

void KEY_Process(void);
uint8_t KEY_Get_State(void);

#endif
