/* Includes ----------------------------------------------------------------- */
#include "key_gpio.h"
#include "device.h"
#include <gpio.h>

/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */

static uint32_t key_stats; // ʹ��λ�����¼ÿ��ͨ����״̬�����֧��32LED

/* �ⲿ������־λ����־�ʣ� */
extern volatile uint8_t key_flag; // 1=���£�0=�ɿ�

/* ����״̬�ṹ */
typedef struct {
    uint16_t state;       // ��ǰ״̬
    uint32_t press_timestamp; // ����ʱ���
    uint8_t last_flag;       // ��һ�εı�־λ������������
} Key_Status_t;

static Key_Status_t key = { 
    .state = DEVICE_KEY_RELEASED,
    .press_timestamp = 0,
    .last_flag = 0
};

/* �����жϴ��� */
void Key_Process(void) {
    uint32_t now = HAL_GetTick();
    uint8_t current_flag = key_flag; // ��ȡ��ǰ��־λ

    switch(key.state) {
        case DEVICE_KEY_RELEASED:
            if(current_flag == 1) {
                // �״μ�⵽���£���¼ʱ���
                if(key.last_flag == 0) {
                    key.press_timestamp = now;
                }
                // ����ȷ�ϣ�20ms����Ϊ���£�
                if((now - key.press_timestamp) > 20) {
                    key.state = DEVICE_KEY_PRESSED;
                }
            }
            break;

        case DEVICE_KEY_PRESSED:
            case DEVICE_KEY_LONG_PRESS:
                if(current_flag == 1) {
                    // ������ס����20ms����HOLD״̬
                    if((now - key.press_timestamp) > 20) {
                        key.state = DEVICE_KEY_LONG_PRESS;
                    }
                } else {
                    key.state = DEVICE_KEY_RELEASED; // �ɿ���λ
                }
                break;
    }

    key.last_flag = current_flag; // ������ʷ״̬
}

//��ȡ��ǰ����״̬ 
uint16_t Get_Key_State(void) {
    return key.state;
}
//Ҳ���Ǻ����߼�(����ǰ��Ĵ���������ѭ���
void KeyTask(void)
{
	
	//�����¾�ִ���߼�
//	if( key.state == DEVICE_KEY_PRESSED)
//	{
//		//ѭ��ִ���߼������£�
//	}
	//��ס��ִ���߼����ɿ���ͣ��
	if (key.state == DEVICE_KEY_LONG_PRESS)
	{
		//ִ���߼�
	}
	else if	(key.state == DEVICE_KEY_RELEASED)
	{
		//ֹͣ�߼�
	}
}