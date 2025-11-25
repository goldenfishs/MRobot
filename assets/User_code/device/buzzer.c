#include "device/buzzer.h"
#include "bsp/time.h"
#include <math.h>

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

/* USER DEFINE BEGIN */

/* USER DEFINE END */

#define MUSIC_DEFAULT_VOLUME 0.5f
#define MUSIC_A4_FREQ 440.0f  // A4音符频率

/* USER MUSIC MENU BEGIN */
// RM音乐
const Tone_t RM[] = {
    {NOTE_B, 5, 200},
    {NOTE_G, 4, 200},
    {NOTE_B, 5, 400},
    {NOTE_G, 4, 200},
    {NOTE_B, 5, 400},
    {NOTE_G, 4, 200},
    {NOTE_D, 5, 400},
    {NOTE_G, 4, 200},
    {NOTE_C, 5, 200},
    {NOTE_C, 5, 200},
    {NOTE_G, 4, 200},
    {NOTE_B, 5, 200},
    {NOTE_C, 5, 200}
};

// Nokia 经典铃声音符
const Tone_t NOKIA[] = {
    {NOTE_E, 5, 125}, {NOTE_D, 5, 125}, {NOTE_FS, 4, 250}, {NOTE_GS, 4, 250},
    {NOTE_CS, 5, 125}, {NOTE_B, 4, 125}, {NOTE_D, 4, 250}, {NOTE_E, 4, 250},
    {NOTE_B, 4, 125}, {NOTE_A, 4, 125}, {NOTE_CS, 4, 250}, {NOTE_E, 4, 250},
    {NOTE_A, 4, 500}
};
/* USER MUSIC MENU END */

static void BUZZER_Update(BUZZER_t *buzzer){
    buzzer->header.online = true;
    buzzer->header.last_online_time = BSP_TIME_Get_ms();
}

// 根据音符和八度计算频率的辅助函数
static float BUZZER_CalcFreq(NOTE_t note, uint8_t octave) {
    if (note == NOTE_REST) {
        return 0.0f; // 休止符返回0频率
    }
    
    // 将音符和八度转换为MIDI音符编号
    int midi_num = (int)note + (int)((octave + 1) * 12);
    
    // 使用A4 (440Hz) 作为参考，计算频率
    // 公式: freq = 440 * 2^((midi_num - 69)/12)
    float freq = 440.0f * powf(2.0f, ((float)midi_num - 69.0f) / 12.0f);
    
    return freq;
}

// 播放单个音符
static int8_t BUZZER_PlayTone(BUZZER_t *buzzer, NOTE_t note, uint8_t octave, uint16_t duration_ms) {
    if (buzzer == NULL || !buzzer->header.online) 
        return DEVICE_ERR;
    
    float freq = BUZZER_CalcFreq(note, octave);
    
    if (freq > 0.0f) {
        // 播放音符
        if (BUZZER_Set(buzzer, freq, MUSIC_DEFAULT_VOLUME) != DEVICE_OK) 
            return DEVICE_ERR;
        
        if (BUZZER_Start(buzzer) != DEVICE_OK) 
            return DEVICE_ERR;
    } else {
        // 休止符，停止播放
        BUZZER_Stop(buzzer);
    }
    
    // 等待指定时间
    BSP_TIME_Delay_ms(duration_ms);
    
    // 停止当前音符，为下一个音符做准备
    BUZZER_Stop(buzzer);
    BSP_TIME_Delay_ms(20); // 短暂间隔
    
    return DEVICE_OK;
}

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
    BUZZER_Update(buzzer);
    return (BSP_PWM_Start(buzzer->channel) == BSP_OK) ? 
           DEVICE_OK  : DEVICE_ERR;
}

int8_t BUZZER_Stop(BUZZER_t *buzzer) {
    if (buzzer == NULL || !buzzer->header.online) 
        return DEVICE_ERR;
    BUZZER_Update(buzzer);
    return (BSP_PWM_Stop(buzzer->channel) == BSP_OK) ? 
           DEVICE_OK  : DEVICE_ERR;
}

int8_t BUZZER_Set(BUZZER_t *buzzer, float freq, float duty_cycle) {
    if (buzzer == NULL || !buzzer->header.online) 
        return DEVICE_ERR;
    
    int result = DEVICE_OK ;
    BUZZER_Update(buzzer);
    if (BSP_PWM_SetFreq(buzzer->channel, freq) != BSP_OK) 
        result = DEVICE_ERR;
    
    if (BSP_PWM_SetComp(buzzer->channel, duty_cycle) != BSP_OK) 
        result = DEVICE_ERR;
    
    return result;
}

int8_t BUZZER_PlayMusic(BUZZER_t *buzzer, MUSIC_t music) {
    if (buzzer == NULL || !buzzer->header.online) 
        return DEVICE_ERR;
    
    const Tone_t *melody = NULL;
    size_t melody_length = 0;
    
    // 根据音乐类型选择对应的音符数组
    switch (music) {
        case MUSIC_RM:
            melody = RM;
            melody_length = sizeof(RM) / sizeof(Tone_t);
            break;
        case MUSIC_NOKIA:
            melody = NOKIA;
            melody_length = sizeof(NOKIA) / sizeof(Tone_t);
            break;
        default:
            return DEVICE_ERR;
    }
    
    // 播放整首音乐
    for (size_t i = 0; i < melody_length; i++) {
        if (BUZZER_PlayTone(buzzer, melody[i].note, melody[i].octave, melody[i].duration_ms) != DEVICE_OK) {
            BUZZER_Stop(buzzer); // 出错时停止播放
            return DEVICE_ERR;
        }
    }
    
    // 音乐播放完成后停止
    BUZZER_Stop(buzzer);
    return DEVICE_OK;
}

/* USER FUNCTION BEGIN */

/* USER FUNCTION END */
