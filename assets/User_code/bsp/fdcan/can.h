/**
 * @file can.h
 * @brief CAN兼容层 - 将CAN接口映射到FDCAN
 * @note 本文件用于FDCAN兼容CAN接口，设备层代码可以继续使用BSP_CAN_xxx接口
 */

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include "bsp/fdcan.h"

/* 类型映射 */
typedef BSP_FDCAN_t BSP_CAN_t;
typedef BSP_FDCAN_Callback_t BSP_CAN_Callback_t;
typedef BSP_FDCAN_Format_t BSP_CAN_Format_t;
typedef BSP_FDCAN_FrameType_t BSP_CAN_FrameType_t;
typedef BSP_FDCAN_Message_t BSP_CAN_Message_t;
typedef BSP_FDCAN_StdDataFrame_t BSP_CAN_StdDataFrame_t;
typedef BSP_FDCAN_ExtDataFrame_t BSP_CAN_ExtDataFrame_t;
typedef BSP_FDCAN_RemoteFrame_t BSP_CAN_RemoteFrame_t;
typedef BSP_FDCAN_IdParser_t BSP_CAN_IdParser_t;

/* 常量映射 */
#define BSP_CAN_MAX_DLC                 BSP_FDCAN_MAX_DLC
#define BSP_CAN_DEFAULT_QUEUE_SIZE      BSP_FDCAN_DEFAULT_QUEUE_SIZE
#define BSP_CAN_TIMEOUT_IMMEDIATE       BSP_FDCAN_TIMEOUT_IMMEDIATE
#define BSP_CAN_TIMEOUT_FOREVER         BSP_FDCAN_TIMEOUT_FOREVER
#define BSP_CAN_TX_QUEUE_SIZE           BSP_FDCAN_TX_QUEUE_SIZE

/* 枚举值映射 */
#define BSP_CAN_1                       BSP_FDCAN_1
#define BSP_CAN_2                       BSP_FDCAN_2
#define BSP_CAN_3                       BSP_FDCAN_3
#define BSP_CAN_NUM                     BSP_FDCAN_NUM
#define BSP_CAN_ERR                     BSP_FDCAN_ERR

#define BSP_CAN_FORMAT_STD_DATA         BSP_FDCAN_FORMAT_STD_DATA
#define BSP_CAN_FORMAT_EXT_DATA         BSP_FDCAN_FORMAT_EXT_DATA
#define BSP_CAN_FORMAT_STD_REMOTE       BSP_FDCAN_FORMAT_STD_REMOTE
#define BSP_CAN_FORMAT_EXT_REMOTE       BSP_FDCAN_FORMAT_EXT_REMOTE

#define BSP_CAN_FRAME_STD_DATA          BSP_FDCAN_FRAME_STD_DATA
#define BSP_CAN_FRAME_EXT_DATA          BSP_FDCAN_FRAME_EXT_DATA
#define BSP_CAN_FRAME_STD_REMOTE        BSP_FDCAN_FRAME_STD_REMOTE
#define BSP_CAN_FRAME_EXT_REMOTE        BSP_FDCAN_FRAME_EXT_REMOTE

/* 函数映射 */
#define BSP_CAN_Init()                  BSP_FDCAN_Init()
#define BSP_CAN_GetHandle(can)          BSP_FDCAN_GetHandle(can)
#define BSP_CAN_RegisterCallback(can, type, callback) \
                                        BSP_FDCAN_RegisterCallback(can, type, callback)
#define BSP_CAN_Transmit(can, format, id, data, dlc) \
                                        BSP_FDCAN_Transmit(can, format, id, data, dlc)
#define BSP_CAN_TransmitStdDataFrame(can, frame) \
                                        BSP_FDCAN_TransmitStdDataFrame(can, frame)
#define BSP_CAN_TransmitExtDataFrame(can, frame) \
                                        BSP_FDCAN_TransmitExtDataFrame(can, frame)
#define BSP_CAN_TransmitRemoteFrame(can, frame) \
                                        BSP_FDCAN_TransmitRemoteFrame(can, frame)
#define BSP_CAN_RegisterId(can, can_id, queue_size) \
                                        BSP_FDCAN_RegisterId(can, can_id, queue_size)
#define BSP_CAN_GetMessage(can, can_id, msg, timeout) \
                                        BSP_FDCAN_GetMessage(can, can_id, msg, timeout)
#define BSP_CAN_GetQueueCount(can, can_id) \
                                        BSP_FDCAN_GetQueueCount(can, can_id)
#define BSP_CAN_FlushQueue(can, can_id) \
                                        BSP_FDCAN_FlushQueue(can, can_id)
#define BSP_CAN_RegisterIdParser(parser) \
                                        BSP_FDCAN_RegisterIdParser(parser)
#define BSP_CAN_ParseId(original_id, frame_type) \
                                        BSP_FDCAN_ParseId(original_id, frame_type)

#ifdef __cplusplus
}
#endif
