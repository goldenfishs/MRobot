#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include <cmsis_os2.h>
#include <stdint.h>

#include "component/user_math.h"
#include "device/device.h"
/* Exported constants ------------------------------------------------------- */

#define OPS9_HEADER 0x0D0A
#define OPS9_TAIL   0x0A0D

/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */

// 数据包结构体
typedef struct __packed {
    uint16_t header; // 2字节
    float yaw;                // 4字节
    float pitch;              // 4字节
    float roll;               // 4字节
    float x;                  // 4字节
    float y;                  // 4字节
    float angular_velocity;   // 4字节
    uint16_t tail;     // 2字节
} OPS9_Data_t; // 共28字节

typedef struct {
    DEVICE_Header_t header; // 设备头
    OPS9_Data_t data;          // 存储接收到的数据
} OPS9_t;

/* Exported functions prototypes -------------------------------------------- */

int8_t OPS9_init(OPS9_t *ops9);
int8_t OPS9_Restart(void);
int8_t OPS9_StartDmaRecv(OPS9_t *ops9);
bool OPS9_WaitDmaCplt(uint32_t timeout);



#ifdef __cplusplus
}
#endif