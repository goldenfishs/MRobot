#include "device/buzzer.h"

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

/* USER DEFINE BEGIN */

/* USER DEFINE END */


int8_t BUZZER_Init(BUZZER_t *buzzer, BSP_PWM_Channel_t channel) {
    if (buzzer == NULL) return DEVICE_ERR;
    
    buzzer->channel = channel;
    buzzer->header.online = true;
    
    BUZZER_Stop(buzzer);
    
    return DEVICE_OK ;
}

int8_t BUZZER_Start(BUZZER_t *buzzer) {
    if (buzzer == NULL || !buzzer->header.online) 
        return DEVICE_ERR;
    
    return (BSP_PWM_Start(buzzer->channel) == BSP_OK) ? 
           DEVICE_OK  : DEVICE_ERR;
}

int8_t BUZZER_Stop(BUZZER_t *buzzer) {
    if (buzzer == NULL || !buzzer->header.online) 
        return DEVICE_ERR;
    
    return (BSP_PWM_Stop(buzzer->channel) == BSP_OK) ? 
           DEVICE_OK  : DEVICE_ERR;
}

int8_t BUZZER_Set(BUZZER_t *buzzer, float freq, float duty_cycle) {
    if (buzzer == NULL || !buzzer->header.online) 
        return DEVICE_ERR;
    
    int result = DEVICE_OK ;
    
    if (BSP_PWM_SetFreq(buzzer->channel, freq) != BSP_OK) 
        result = DEVICE_ERR;
    
    if (BSP_PWM_SetComp(buzzer->channel, duty_cycle) != BSP_OK) 
        result = DEVICE_ERR;
    
    return result;
}

/* USER FUNCTION BEGIN */

/* USER FUNCTION END */
