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
  BSP_CAN_ERR = 0xFF,
} BSP_CAN_t;

typedef enum {
  BSP_CAN_TX_MAILBOX0_CPLT_CB,
  BSP_CAN_TX_MAILBOX1_CPLT_CB,
  BSP_CAN_TX_MAILBOX2_CPLT_CB,
  BSP_CAN_TX_MAILBOX0_ABORT_CB,
  BSP_CAN_TX_MAILBOX1_ABORT_CB,
  BSP_CAN_TX_MAILBOX2_ABORT_CB,
  BSP_CAN_RX_FIFO0_MSG_PENDING_CB,
  BSP_CAN_RX_FIFO0_FULL_CB,
  BSP_CAN_RX_FIFO1_MSG_PENDING_CB,
  BSP_CAN_RX_FIFO1_FULL_CB,
  BSP_CAN_SLEEP_CB,
  BSP_CAN_WAKEUP_FROM_RX_MSG_CB,
  BSP_CAN_ERROR_CB,
  BSP_CAN_CB_NUM
} BSP_CAN_Callback_t;

typedef enum {
  BSP_CAN_FORMAT_STD_DATA,    /* 标准数据帧 */
  BSP_CAN_FORMAT_EXT_DATA,    /* 扩展数据帧 */
  BSP_CAN_FORMAT_STD_REMOTE,  /* 标准远程帧 */
  BSP_CAN_FORMAT_EXT_REMOTE,  /* 扩展远程帧 */
} BSP_CAN_Format_t;

typedef struct {
    CAN_RxHeaderTypeDef header;
    uint8_t data[BSP_CAN_MAX_DLC];
} BSP_CAN_Message_t;

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
 * @brief 注册 CAN ID 接收队列
 * @param can_id CAN ID
 * @param queue_size 队列大小，0使用默认值
 * @return BSP_OK 成功，其他值失败
 */
int8_t BSP_CAN_RegisterId(uint32_t can_id, uint8_t queue_size);

/**
 * @brief 注销 CAN ID 接收队列
 * @param can_id CAN ID
 * @return BSP_OK 成功，其他值失败
 */
int8_t BSP_CAN_UnregisterIdQueue(uint32_t can_id);

/**
 * @brief 获取 CAN 消息（阻塞方式）
 * @param can_id CAN ID
 * @param msg 存储消息的结构体指针
 * @param timeout 超时时间（毫秒），0为立即返回，osWaitForever为永久等待
 * @return BSP_OK 成功，其他值失败
 */
int8_t BSP_CAN_GetMessage(uint32_t can_id, BSP_CAN_Message_t *msg, uint32_t timeout);

/**
 * @brief 获取指定ID队列中的消息数量
 * @param can_id CAN ID
 * @return 消息数量，-1表示队列不存在
 */
int32_t BSP_CAN_GetQueueCount(uint32_t can_id);

/**
 * @brief 清空指定ID队列中的所有消息
 * @param can_id CAN ID
 * @return BSP_OK 成功，其他值失败
 */
int8_t BSP_CAN_FlushQueue(uint32_t can_id);

/* USER CAN FUNCTIONS BEGIN */
/* USER CAN FUNCTIONS END */

#ifdef __cplusplus
}
#endif