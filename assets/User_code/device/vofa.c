/* Includes ----------------------------------------------------------------- */
#include <stdio.h>
#include <string.h>
#include "vofa.h"
#include "bsp/uart.h"
/* Private define ----------------------------------------------------------- */

//#define PROTOCOL_RAWDATA
#define PROTOCOL_FIREWATER
//#define PROTOCOL_JUSTFLOAT

#define MAX_CHANNEL  64u   		// 根据实际最大通道数调整

#define JUSTFLOAT_TAIL 0x7F800000
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */
static uint8_t vofa_tx_buf[sizeof(float) * MAX_CHANNEL + sizeof(uint32_t)];

/* Private function  -------------------------------------------------------- */

/************************  RawData  *************************/
void VOFA_RawData_Send(const char* data, bool dma) {
    BSP_UART_Transmit(BSP_UART_VOFA, (uint8_t*)data, strlen(data), dma);
}

/************************ FireWater *************************/
void VOFA_FireWater_Send(float *channels, uint8_t channel_count, bool dma)
{
    if (channel_count == 0 || channel_count > MAX_CHANNEL)
        return;

    char *buf = (char *)vofa_tx_buf;
    size_t len = 0;

    for (uint8_t i = 0; i < channel_count; ++i) {
        len += snprintf(buf + len,
                        sizeof(vofa_tx_buf) - len,
                        "%s%.2f",
                        (i ? "," : ""),
                        channels[i]);
    }
    snprintf(buf + len, sizeof(vofa_tx_buf) - len, "\n");

    BSP_UART_Transmit(BSP_UART_VOFA, vofa_tx_buf, strlen(buf), dma);
}

/************************ JustFloat *************************/
void VOFA_JustFloat_Send(float *channels, uint8_t channel_count, bool dma)
{
    if (channel_count == 0 || channel_count > MAX_CHANNEL)
        return;
    memcpy(vofa_tx_buf, channels, channel_count * sizeof(float));

    uint32_t tail = JUSTFLOAT_TAIL;                     // 0x7F800000
    memcpy(vofa_tx_buf + channel_count * sizeof(float), &tail, sizeof(tail));

    BSP_UART_Transmit(BSP_UART_VOFA, vofa_tx_buf, channel_count * sizeof(float) + sizeof(tail), dma);
}

/* Exported functions ------------------------------------------------------- */
init8_t VOFA_Send(float* channels, uint8_t channel_count, bool dma) {
#ifdef PROTOCOL_RAWDATA
    sprintf(vofa_tx_buf, "Channel1:%.2f,Channel2:%.2f\n", channels[0],channels[1]);
    VOFA_RawData_Send(vofa_tx_buf, dma);
#elif defined(PROTOCOL_FIREWATER)
    VOFA_FireWater_Send(channels, channel_count, dma);
#elif defined(PROTOCOL_JUSTFLOAT)
    VOFA_JustFloat_Send(channels, channel_count, dma);
#else
    // 默认使用RawData协议
    char data[256];
    sprintf(data, "Channel1: %.2f, Channel2: %.2f\n", channels[0], channels[1]);
    VOFA_RawData_Send(data, dma);
#endif
    return DEVICE_OK;
}
