#pragma once

/* Includes ----------------------------------------------------------------- */
#include <stdint.h>
#include "main.h"
//#include "key_gpio.h"
/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */

/* KEY����״̬�������� */
typedef enum
{
    BSP_KEY_RELEASED,  //�����ͷ�
    BSP_KEY_PRESSED,   //��������
    BSP_KEY_LONG_PRESS,  //��������
} BSP_KEY_Status_t;


/* ����ͨ������ */
typedef enum {
    BSP_KEY_1,
    BSP_KEY_2,
    /* �ɸ�����Ҫ��չ */
    BSP_KEY_COUNT
} BSP_Key_Channel_t;


/* ����Ӳ�����ýṹ�� */
typedef struct {
    GPIO_TypeDef *port;    // GPIO�˿�
    uint16_t pin;          // ���ű��
    uint8_t active_level;  // ��Ч��ƽ��GPIO_PIN_SET/RESET��
} BSP_Key_Config_t;

int8_t BSP_Key_Read(BSP_Key_Channel_t ch);