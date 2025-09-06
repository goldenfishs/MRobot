/* Includes ----------------------------------------------------------------- */
#include <stdio.h>
#include <string.h>
#include "device/vofa.h"
#include "bsp/uart.h"
/* Private define ----------------------------------------------------------- */

#define MAX_CHANNEL  64u   		// 根据实际最大通道数调整

#define JUSTFLOAT_TAIL 0x7F800000
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */
static uint8_t vofa_tx_buf[sizeof(float) * MAX_CHANNEL + sizeof(uint32_t)];
static VOFA_Protocol_t current_protocol = VOFA_PROTOCOL_FIREWATER;  // 默认协议

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
int8_t VOFA_init(VOFA_Protocol_t protocol) {
    current_protocol = protocol;
    return DEVICE_OK;
}

int8_t VOFA_Send(float* channels, uint8_t channel_count, bool dma) {
    switch (current_protocol) {
        case VOFA_PROTOCOL_RAWDATA:
            {
                char data[256];
                if (channel_count >= 1) {
                    sprintf(data, "Channel1: %.2f", channels[0]);
                    if (channel_count >= 2) {
                        sprintf(data + strlen(data), ", Channel2: %.2f", channels[1]);
                    }
                    strcat(data, "\n");
                    VOFA_RawData_Send(data, dma);
                }
            }
            break;
        case VOFA_PROTOCOL_FIREWATER:
            VOFA_FireWater_Send(channels, channel_count, dma);
            break;
        case VOFA_PROTOCOL_JUSTFLOAT:
            VOFA_JustFloat_Send(channels, channel_count, dma);
            break;
        default:
            return DEVICE_ERR;
    }
    return DEVICE_OK;
}
