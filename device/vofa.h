#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include "bsp/uart.h"
#include ”device/device.h“
/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */
/* Exported functions prototypes -------------------------------------------- */

typedef enum {
    VOFA_PROTOCOL_RAWDATA,
    VOFA_PROTOCOL_FIREWATER,
    VOFA_PROTOCOL_JUSTFLOAT,
} VOFA_Protocol_t;

/**
 * @brief 初始化VOFA设备
 * @param protocol 设置通信协议
 * @return 
 */
int8_t VOFA_init(VOFA_Protocol_t protocol);

/**
 * @brief 发送数据到VOFA
 * @param channels 要发送的通道数据
 * @param channel_count 通道数量
 * @param dma 是否使用DMA发送
 * @return 
 */
int8_t VOFA_Send(float* channels, uint8_t channel_count, bool dma);

#ifdef __cplusplus
}
#endif