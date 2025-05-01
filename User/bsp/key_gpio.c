/* Includes ----------------------------------------------------------------- */
#include "key_gpio.h"
#include "bsp.h"
#include <gpio.h>

/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */

static uint32_t key_stats; // ʹ��λ�����¼ÿ��ͨ����״̬�����֧��32LED
/* �������ñ�����ʵ��Ӳ���޸ģ� */
static const BSP_Key_Config_t KEY_CONFIGS[] = {
    {GPIOA, GPIO_PIN_7, GPIO_PIN_SET},   // KEY1����ʱ��ƽΪ��
    {GPIOA, GPIO_PIN_9, GPIO_PIN_SET}, // KEY2����ʱ��ƽΪ��
    // ��Ӹ��ఴ��...
};

#define KEY_COUNT (sizeof(KEY_CONFIGS)/sizeof(KEY_CONFIGS[0])
	

//��ȡ����״̬����������
int8_t BSP_Key_Read(BSP_Key_Channel_t ch) {
    static uint32_t last_press_time[BSP_KEY_COUNT] = {0};      //�ϴΰ���ʱ��
    const uint32_t debounce_ms = 20;      //��������ʱ��
    const uint32_t long_press_ms = 2000;      //��������ʱ��
    
    if(ch >= BSP_KEY_COUNT) return BSP_KEY_RELEASED ;
    
    const BSP_Key_Config_t *cfg = &KEY_CONFIGS[ch];
    GPIO_PinState state = HAL_GPIO_ReadPin(cfg->port, cfg->pin);
    
    if(state == cfg->active_level) {
        uint32_t now = HAL_GetTick();      //���ڼ�¼��������ʱ�䣨����Ƚ�state��Ϊ�˷�����Ӧ��ͬ��Ч��ƽ�����޸ĵģ�Ҳ���Ըĳ�ֱ�Ӽ���ƽ�ߵͣ�
        
        //�������(ֻ�а��³���20ms�ű���Ϊ���£�
        if((now - last_press_time[ch]) > debounce_ms) {
            //������⣨ֻ�б����³���2000ms�ű���Ϊ�ǳ���������ʵ������������޸ģ�
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
