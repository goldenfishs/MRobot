#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include <can.h>
#include "bsp/bsp.h"
#include <stdint.h>
#include <stdbool.h>
#include <cmsis_os.h>

/* Exported constants ------------------------------------------------------- */


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
  BSP_CAN_CB_NUM
} BSP_CAN_Callback_t;

typedef enum {
  CAN_FORMAT_STD_DATA, /* 标准数据帧 */
  CAN_FORMAT_EXT_DATA, /* 扩展数据帧 */
  CAN_FORMAT_STD_REMOTE,  /* 标准远程帧 */
  CAN_FORMAT_EXT_REMOTE,  /* 扩展远程帧 */
} BSP_CAN_Format_t;

typedef struct {
    CAN_RxHeaderTypeDef header;
    uint8_t data[8];
} CAN_Message_t;

/* Exported functions prototypes -------------------------------------------- */
/**
 * @brief 获取 CAN 句柄
 * @param can CAN 枚举类型
 * @return CAN_HandleTypeDef 指针，失败返回 NULL
 */
CAN_HandleTypeDef *BSP_CAN_GetHandle(BSP_CAN_t can);

/**
 * @brief 注册 CAN 回调
 * @param can CAN 枚举类型
 * @param type 回调类型
 * @param callback 回调函数指针
 * @return BSP_OK 成功，BSP_ERR_NULL/BSP_ERR_INVALID_PARAM 失败
 */
int8_t BSP_CAN_RegisterCallback(BSP_CAN_t can, BSP_CAN_Callback_t type,
                                void (*callback)(void));

/**
 * @brief 发送 CAN 消息
 * @param can CAN 枚举类型
 * @param format 消息格式
 * @param id CAN ID
 * @param data 数据指针
 * @param dlc 数据长度
 * @return BSP_OK 成功，BSP_ERR/BSP_ERR_NULL/BSP_ERR_INVALID_PARAM 失败
 */
int8_t BSP_CAN_Transmit(BSP_CAN_t can, BSP_CAN_Format_t format,
                        uint32_t id, uint8_t *data, uint8_t dlc);

/**
 * @brief 初始化 CAN
 * @return BSP_OK 成功，BSP_ERR/BSP_ERR_NULL/BSP_ERR_INITED 失败
 */
int8_t BSP_CAN_Init(void);

/**
 * @brief 获取 CAN 消息
 * @param can_id CAN ID
 * @param msg 存储消息的结构体指针
 * @param timeout 超时时间（毫秒）
 * @return BSP_OK 成功，BSP_ERR/BSP_ERR_NULL/BSP_ERR_NO_DEV 失败
 */
int BSP_CAN_GetMessage(uint32_t can_id, CAN_Message_t *msg, uint32_t timeout);

/**
 * @brief 注册 CAN ID
 * @param can_id CAN ID
 * @param queue_size 队列大小
 * @return 无
 */
void BSP_CAN_RegisterId(uint32_t can_id, uint8_t queue_size);

/**
 * @brief 创建指定 CAN ID 的队列
 * @param can_id CAN ID
 * @param queue_size 队列大小
 * @return BSP_OK 成功，BSP_ERR/BSP_ERR_NULL/BSP_ERR_INVALID_PARAM 失败
 */
int8_t BSP_CAN_CreateIdQueue(uint32_t can_id, uint8_t queue_size);

/**
 * @brief 删除指定 CAN ID 的队列
 * @param can_id CAN ID
 * @return BSP_OK 成功，BSP_ERR/BSP_ERR_INVALID_PARAM 失败
 */
int8_t BSP_CAN_DeleteIdQueue(uint32_t can_id);

/* USER CAN FUNCTIONS BEGIN */
/* USER CAN FUNCTIONS END */