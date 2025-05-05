#pragma once

/* Includes ----------------------------------------------------------------- */
#include <stdint.h>
#include "main.h"
//#include "key_gpio.h"
/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */

///* KEY����״̬�������� */
typedef enum
{
    DEVICE_KEY_RELEASED,  //�����ͷ�
    DEVICE_KEY_PRESSED,   //��������
    DEVICE_KEY_LONG_PRESS,  //��������
} DEVICE_KEY_Status_t;


/* ����ͨ������ */
typedef enum {
    DEVICE_KEY_1,
    DEVICE_KEY_2,
    /* �ɸ�����Ҫ��չ */
    DEVICE_KEY_COUNT
} DEVICE_Key_Channel_t;

/* ����Ӳ�����ýṹ�� */
typedef struct {
    GPIO_TypeDef *port;    // GPIO�˿�
    uint16_t pin;          // ���ű��
    uint8_t active_level;  // ��Ч��ƽ��GPIO_PIN_SET/RESET��
	uint32_t trigger_edge;    // �жϴ������أ�RISING/FALLING��
} DEVICE_Key_Config_t;

void Key_Process(void);
uint16_t Get_Key_State(void);
void KeyTask(void);