#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include <can.h>
#include "bsp/bsp.h"
#include "bsp/mm.h"
#include <stdint.h>
#include <stdbool.h>
#include <cmsis_os.h>

/* Exported constants ------------------------------------------------------- */
#define BSP_CAN_MAX_DLC                 8
#define BSP_CAN_DEFAULT_QUEUE_SIZE      10
#define BSP_CAN_TIMEOUT_IMMEDIATE       0
#define BSP_CAN_TIMEOUT_FOREVER         osWaitForever

/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */
typedef enum {
/* AUTO GENERATED BSP_CAN_NAME */
  BSP_CAN_NUM,
  BSP_CAN_ERR,
} BSP_CAN_t;

typedef enum {
  HAL_CAN_TX_MAILBOX0_CPLT_CB,
  HAL_CAN_TX_MAILBOX1_CPLT_CB,
  HAL_CAN_TX_MAILBOX2_CPLT_CB,
  HAL_CAN_TX_MAILBOX0_ABORT_CB,
  HAL_CAN_TX_MAILBOX1_ABORT_CB,
  HAL_CAN_TX_MAILBOX2_ABORT_CB,
  HAL_CAN_RX_FIFO0_MSG_PENDING_CB,
  HAL_CAN_RX_FIFO0_FULL_CB,
  HAL_CAN_RX_FIFO1_MSG_PENDING_CB,
  HAL_CAN_RX_FIFO1_FULL_CB,
  HAL_CAN_SLEEP_CB,
  HAL_CAN_WAKEUP_FROM_RX_MSG_CB,
  HAL_CAN_ERROR_CB,
  BSP_CAN_CB_NUM,
} BSP_CAN_Callback_t;

/* CAN消息格式枚举 - 用于发送和接收消息时指定格式 */
typedef enum {
  BSP_CAN_FORMAT_STD_DATA,    /* 标准数据帧 */
  BSP_CAN_FORMAT_EXT_DATA,    /* 扩展数据帧 */
  BSP_CAN_FORMAT_STD_REMOTE,  /* 标准远程帧 */
  BSP_CAN_FORMAT_EXT_REMOTE,  /* 扩展远程帧 */
} BSP_CAN_Format_t;

/* CAN帧类型枚举 - 用于区分不同类型的CAN帧 */
typedef enum {
  BSP_CAN_FRAME_STD_DATA,     /* 标准数据帧 */
  BSP_CAN_FRAME_EXT_DATA,     /* 扩展数据帧 */
  BSP_CAN_FRAME_STD_REMOTE,   /* 标准远程帧 */
  BSP_CAN_FRAME_EXT_REMOTE,   /* 扩展远程帧 */
} BSP_CAN_FrameType_t;

/* CAN消息结构体 - 支持不同类型帧 */
typedef struct {
    BSP_CAN_FrameType_t frame_type;     /* 帧类型 */
    uint32_t original_id;               /* 原始ID（未解析） */
    uint32_t parsed_id;                 /* 解析后的实际ID */
    uint8_t dlc;                        /* 数据长度 */
    uint8_t data[BSP_CAN_MAX_DLC];      /* 数据 */
    uint32_t timestamp;                 /* 时间戳（可选） */
} BSP_CAN_Message_t;

/* 标准数据帧结构 */
typedef struct {
    uint32_t id;                        /* CAN ID */
    uint8_t dlc;                        /* 数据长度 */
    uint8_t data[BSP_CAN_MAX_DLC];      /* 数据 */
} BSP_CAN_StdDataFrame_t;

/* 扩展数据帧结构 */
typedef struct {
    uint32_t id;                        /* 扩展CAN ID */
    uint8_t dlc;                        /* 数据长度 */
    uint8_t data[BSP_CAN_MAX_DLC];      /* 数据 */
} BSP_CAN_ExtDataFrame_t;

/* 远程帧结构 */
typedef struct {
    uint32_t id;                        /* CAN ID */
    uint8_t dlc;                        /* 请求的数据长度 */
    bool is_extended;                   /* 是否为扩展帧 */
} BSP_CAN_RemoteFrame_t;

/* ID解析回调函数类型 */
typedef uint32_t (*BSP_CAN_IdParser_t)(uint32_t original_id, BSP_CAN_FrameType_t frame_type);

/* Exported functions prototypes -------------------------------------------- */

/**
 * @brief 初始化 CAN 模块
 * @return BSP_OK 成功，其他值失败
 */
int8_t BSP_CAN_Init(void);

/**
 * @brief 反初始化 CAN 模块
 * @return BSP_OK 成功，其他值失败
 */
int8_t BSP_CAN_DeInit(void);

/**
 * @brief 获取 CAN 句柄
 * @param can CAN 枚举
 * @return CAN_HandleTypeDef 指针，失败返回 NULL
 */
CAN_HandleTypeDef *BSP_CAN_GetHandle(BSP_CAN_t can);

/**
 * @brief 注册 CAN 回调函数
 * @param can CAN 枚举
 * @param type 回调类型
 * @param callback 回调函数指针
 * @return BSP_OK 成功，其他值失败
 */
int8_t BSP_CAN_RegisterCallback(BSP_CAN_t can, BSP_CAN_Callback_t type,
                                void (*callback)(void));

/**
 * @brief 发送 CAN 消息
 * @param can CAN 枚举
 * @param format 消息格式
 * @param id CAN ID
 * @param data 数据指针
 * @param dlc 数据长度
 * @return BSP_OK 成功，其他值失败
 */
int8_t BSP_CAN_Transmit(BSP_CAN_t can, BSP_CAN_Format_t format,
                        uint32_t id, uint8_t *data, uint8_t dlc);

/**
 * @brief 发送标准数据帧
 * @param can CAN 枚举
 * @param frame 标准数据帧指针
 * @return BSP_OK 成功，其他值失败
 */
int8_t BSP_CAN_TransmitStdDataFrame(BSP_CAN_t can, BSP_CAN_StdDataFrame_t *frame);

/**
 * @brief 发送扩展数据帧
 * @param can CAN 枚举
 * @param frame 扩展数据帧指针
 * @return BSP_OK 成功，其他值失败
 */
int8_t BSP_CAN_TransmitExtDataFrame(BSP_CAN_t can, BSP_CAN_ExtDataFrame_t *frame);

/**
 * @brief 发送远程帧
 * @param can CAN 枚举
 * @param frame 远程帧指针
 * @return BSP_OK 成功，其他值失败
 */
int8_t BSP_CAN_TransmitRemoteFrame(BSP_CAN_t can, BSP_CAN_RemoteFrame_t *frame);

/**
 * @brief 注册 CAN ID 接收队列
 * @param can CAN 枚举
 * @param can_id 解析后的CAN ID
 * @param queue_size 队列大小，0使用默认值
 * @return BSP_OK 成功，其他值失败
 */
int8_t BSP_CAN_RegisterId(BSP_CAN_t can, uint32_t can_id, uint8_t queue_size);

/**
 * @brief 注销 CAN ID 接收队列
 * @param can CAN 枚举
 * @param can_id 解析后的CAN ID
 * @return BSP_OK 成功，其他值失败
 */
int8_t BSP_CAN_UnregisterIdQueue(BSP_CAN_t can, uint32_t can_id);

/**
 * @brief 获取 CAN 消息
 * @param can CAN 枚举
 * @param can_id 解析后的CAN ID
 * @param msg 存储消息的结构体指针
 * @param timeout 超时时间（毫秒），0为立即返回，osWaitForever为永久等待
 * @return BSP_OK 成功，其他值失败
 */
int8_t BSP_CAN_GetMessage(BSP_CAN_t can, uint32_t can_id, BSP_CAN_Message_t *msg, uint32_t timeout);

/**
 * @brief 获取指定ID队列中的消息数量
 * @param can CAN 枚举
 * @param can_id 解析后的CAN ID
 * @return 消息数量，-1表示队列不存在
 */
int32_t BSP_CAN_GetQueueCount(BSP_CAN_t can, uint32_t can_id);

/**
 * @brief 清空指定ID队列中的所有消息
 * @param can CAN 枚举
 * @param can_id 解析后的CAN ID
 * @return BSP_OK 成功，其他值失败
 */
int8_t BSP_CAN_FlushQueue(BSP_CAN_t can, uint32_t can_id);

/**
 * @brief 注册ID解析器
 * @param parser ID解析回调函数
 * @return BSP_OK 成功，其他值失败
 */
int8_t BSP_CAN_RegisterIdParser(BSP_CAN_IdParser_t parser);

/**
 * @brief 注销ID解析器
 * @return BSP_OK 成功，其他值失败
 */
int8_t BSP_CAN_UnregisterIdParser(void);

/**
 * @brief 解析CAN ID
 * @param original_id 原始ID
 * @param frame_type 帧类型
 * @return 解析后的ID
 */
uint32_t BSP_CAN_ParseId(uint32_t original_id, BSP_CAN_FrameType_t frame_type);

/* USER CAN FUNCTIONS BEGIN */
/* USER CAN FUNCTIONS END */

#ifdef __cplusplus
}
#endif