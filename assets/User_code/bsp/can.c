/* Includes ----------------------------------------------------------------- */
#include "bsp/can.h"
#include "bsp/bsp.h"
#include <can.h>
#include <cmsis_os.h>
#include <stdlib.h>
#include <string.h>

/* Private define ----------------------------------------------------------- */

/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
typedef struct CAN_QueueNode {
    uint32_t can_id;
    osMessageQueueId_t queue;
    uint8_t queue_size;
    struct CAN_QueueNode *next;
} CAN_QueueNode_t;

/* Private variables -------------------------------------------------------- */
static CAN_QueueNode_t *can_queue_list = NULL;
static void (*CAN_Callback[BSP_CAN_NUM][BSP_CAN_CB_NUM])(void);

/* Private function prototypes ---------------------------------------------- */
static BSP_CAN_t CAN_Get(CAN_HandleTypeDef *hcan);
static osMessageQueueId_t find_queue(uint32_t can_id);
static void can_rx_fifo0_handler(void);
static void can_rx_fifo1_handler(void);

/* AUTO GENERATED CAN_RX_CALLBACKS */
/* Private function  -------------------------------------------------------- */

/* 查找指定CAN ID的队列 */
static osMessageQueueId_t find_queue(uint32_t can_id) {
    CAN_QueueNode_t *node = can_queue_list;
    while (node) {
        if (node->can_id == can_id) return node->queue;
        node = node->next;
    }
    return NULL;
}

/* FIFO0接收处理函数 */
static void can_rx_fifo0_handler(void) {
    CAN_RxHeaderTypeDef rx_header;
    uint8_t rx_data[8];
    
    // 遍历所有CAN接口处理FIFO0
    for (int can_idx = 0; can_idx < BSP_CAN_NUM; can_idx++) {
        CAN_HandleTypeDef *hcan = BSP_CAN_GetHandle((BSP_CAN_t)can_idx);
        if (hcan == NULL) continue;
        
        while (HAL_CAN_GetRxFifoFillLevel(hcan, CAN_RX_FIFO0) > 0) {
            if (HAL_CAN_GetRxMessage(hcan, CAN_RX_FIFO0, &rx_header, rx_data) == HAL_OK) {
                uint32_t can_id = (rx_header.IDE == CAN_ID_STD) ? rx_header.StdId : rx_header.ExtId;
                osMessageQueueId_t queue = find_queue(can_id);
                if (queue) {
                    CAN_Message_t msg;
                    msg.header = rx_header;
                    memcpy(msg.data, rx_data, 8);
                    // 非阻塞发送，如果队列满了就丢弃
                    osMessageQueuePut(queue, &msg, 0, 0);
                }
                // 如果没有找到对应的队列，消息被直接丢弃
            }
        }
    }
}

/* FIFO1接收处理函数 */
static void can_rx_fifo1_handler(void) {
    CAN_RxHeaderTypeDef rx_header;
    uint8_t rx_data[8];
    
    // 遍历所有CAN接口处理FIFO1
    for (int can_idx = 0; can_idx < BSP_CAN_NUM; can_idx++) {
        CAN_HandleTypeDef *hcan = BSP_CAN_GetHandle((BSP_CAN_t)can_idx);
        if (hcan == NULL) continue;
        
        while (HAL_CAN_GetRxFifoFillLevel(hcan, CAN_RX_FIFO1) > 0) {
            if (HAL_CAN_GetRxMessage(hcan, CAN_RX_FIFO1, &rx_header, rx_data) == HAL_OK) {
                uint32_t can_id = (rx_header.IDE == CAN_ID_STD) ? rx_header.StdId : rx_header.ExtId;
                osMessageQueueId_t queue = find_queue(can_id);
                if (queue) {
                    CAN_Message_t msg;
                    msg.header = rx_header;
                    memcpy(msg.data, rx_data, 8);
                    // 非阻塞发送，如果队列满了就丢弃
                    osMessageQueuePut(queue, &msg, 0, 0);
                }
                // 如果没有找到对应的队列，消息被直接丢弃
            }
        }
    }
}

static BSP_CAN_t CAN_Get(CAN_HandleTypeDef *hcan) {
/* AUTO GENERATED CAN_GET */
  else
    return BSP_CAN_ERR;
}

/* HAL Callback Functions --------------------------------------------------- */
void HAL_CAN_TxMailbox0CompleteCallback(CAN_HandleTypeDef *hcan) {
  BSP_CAN_t bsp_can = CAN_Get(hcan);
  if (bsp_can != BSP_CAN_ERR) {
    if (CAN_Callback[bsp_can][HAL_CAN_TX_MAILBOX0_CPLT_CB])
      CAN_Callback[bsp_can][HAL_CAN_TX_MAILBOX0_CPLT_CB]();
  }
}

void HAL_CAN_TxMailbox1CompleteCallback(CAN_HandleTypeDef *hcan) {
  BSP_CAN_t bsp_can = CAN_Get(hcan);
  if (bsp_can != BSP_CAN_ERR) {
    if (CAN_Callback[bsp_can][HAL_CAN_TX_MAILBOX1_CPLT_CB])
      CAN_Callback[bsp_can][HAL_CAN_TX_MAILBOX1_CPLT_CB]();
  }
}

void HAL_CAN_TxMailbox2CompleteCallback(CAN_HandleTypeDef *hcan) {
  BSP_CAN_t bsp_can = CAN_Get(hcan);
  if (bsp_can != BSP_CAN_ERR) {
    if (CAN_Callback[bsp_can][HAL_CAN_TX_MAILBOX2_CPLT_CB])
      CAN_Callback[bsp_can][HAL_CAN_TX_MAILBOX2_CPLT_CB]();
  }
}

void HAL_CAN_TxMailbox0AbortCallback(CAN_HandleTypeDef *hcan) {
  BSP_CAN_t bsp_can = CAN_Get(hcan);
  if (bsp_can != BSP_CAN_ERR) {
    if (CAN_Callback[bsp_can][HAL_CAN_TX_MAILBOX0_ABORT_CB])
      CAN_Callback[bsp_can][HAL_CAN_TX_MAILBOX0_ABORT_CB]();
  }
}

void HAL_CAN_TxMailbox1AbortCallback(CAN_HandleTypeDef *hcan) {
  BSP_CAN_t bsp_can = CAN_Get(hcan);
  if (bsp_can != BSP_CAN_ERR) {
    if (CAN_Callback[bsp_can][HAL_CAN_TX_MAILBOX1_ABORT_CB])
      CAN_Callback[bsp_can][HAL_CAN_TX_MAILBOX1_ABORT_CB]();
  }
}

void HAL_CAN_TxMailbox2AbortCallback(CAN_HandleTypeDef *hcan) {
  BSP_CAN_t bsp_can = CAN_Get(hcan);
  if (bsp_can != BSP_CAN_ERR) {
    if (CAN_Callback[bsp_can][HAL_CAN_TX_MAILBOX2_ABORT_CB])
      CAN_Callback[bsp_can][HAL_CAN_TX_MAILBOX2_ABORT_CB]();
  }
}

void HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *hcan) {
  BSP_CAN_t bsp_can = CAN_Get(hcan);
  if (bsp_can != BSP_CAN_ERR) {
    if (CAN_Callback[bsp_can][HAL_CAN_RX_FIFO0_MSG_PENDING_CB])
      CAN_Callback[bsp_can][HAL_CAN_RX_FIFO0_MSG_PENDING_CB]();
  }
}

void HAL_CAN_RxFifo0FullCallback(CAN_HandleTypeDef *hcan) {
  BSP_CAN_t bsp_can = CAN_Get(hcan);
  if (bsp_can != BSP_CAN_ERR) {
    if (CAN_Callback[bsp_can][HAL_CAN_RX_FIFO0_FULL_CB])
      CAN_Callback[bsp_can][HAL_CAN_RX_FIFO0_FULL_CB]();
  }
}

void HAL_CAN_RxFifo1MsgPendingCallback(CAN_HandleTypeDef *hcan) {
  BSP_CAN_t bsp_can = CAN_Get(hcan);
  if (bsp_can != BSP_CAN_ERR) {
    if (CAN_Callback[bsp_can][HAL_CAN_RX_FIFO1_MSG_PENDING_CB])
      CAN_Callback[bsp_can][HAL_CAN_RX_FIFO1_MSG_PENDING_CB]();
  }
}

void HAL_CAN_RxFifo1FullCallback(CAN_HandleTypeDef *hcan) {
  BSP_CAN_t bsp_can = CAN_Get(hcan);
  if (bsp_can != BSP_CAN_ERR) {
    if (CAN_Callback[bsp_can][HAL_CAN_RX_FIFO1_FULL_CB])
      CAN_Callback[bsp_can][HAL_CAN_RX_FIFO1_FULL_CB]();
  }
}

void HAL_CAN_SleepCallback(CAN_HandleTypeDef *hcan) {
  BSP_CAN_t bsp_can = CAN_Get(hcan);
  if (bsp_can != BSP_CAN_ERR) {
    if (CAN_Callback[bsp_can][HAL_CAN_SLEEP_CB])
      CAN_Callback[bsp_can][HAL_CAN_SLEEP_CB]();
  }
}

void HAL_CAN_WakeUpFromRxMsgCallback(CAN_HandleTypeDef *hcan) {
  BSP_CAN_t bsp_can = CAN_Get(hcan);
  if (bsp_can != BSP_CAN_ERR) {
    if (CAN_Callback[bsp_can][HAL_CAN_WAKEUP_FROM_RX_MSG_CB])
      CAN_Callback[bsp_can][HAL_CAN_WAKEUP_FROM_RX_MSG_CB]();
  }
}

void HAL_CAN_ErrorCallback(CAN_HandleTypeDef *hcan) {
  BSP_CAN_t bsp_can = CAN_Get(hcan);
  if (bsp_can != BSP_CAN_ERR) {
    if (CAN_Callback[bsp_can][HAL_CAN_ERROR_CB])
      CAN_Callback[bsp_can][HAL_CAN_ERROR_CB]();
  }
}

/* Exported functions ------------------------------------------------------- */
CAN_HandleTypeDef *BSP_CAN_GetHandle(BSP_CAN_t can) {
  switch (can) {
/* AUTO GENERATED BSP_CAN_GET_HANDLE */
    default:
      return NULL;
  }
}

int8_t BSP_CAN_RegisterCallback(BSP_CAN_t can, BSP_CAN_Callback_t type,
                                void (*callback)(void)) {
  if (callback == NULL) return BSP_ERR_NULL;
  if (can >= BSP_CAN_NUM) return BSP_ERR_INITED;
  if (type >= BSP_CAN_CB_NUM) return BSP_ERR;
  
  CAN_Callback[can][type] = callback;
  return BSP_OK;
}

int BSP_CAN_GetMessage(uint32_t can_id, CAN_Message_t *msg, uint32_t timeout) {
    if (msg == NULL) return BSP_ERR_NULL;
    osMessageQueueId_t queue = find_queue(can_id);
    if (!queue) return BSP_ERR_NO_DEV; // 没有该队列
    if (osMessageQueueGet(queue, msg, NULL, timeout) == osOK) {
        return BSP_OK; // 成功
    }
    return BSP_ERR; // 超时或队列为空
}

int8_t BSP_CAN_CreateIdQueue(uint32_t can_id, uint8_t queue_size) {
    // 检查是否已存在
    CAN_QueueNode_t *node = can_queue_list;
    while (node) {
        if (node->can_id == can_id) {
            return BSP_ERR; // 已存在
        }
        node = node->next;
    }
    // 创建新节点
    CAN_QueueNode_t *new_node = malloc(sizeof(CAN_QueueNode_t));
    if (new_node == NULL) return BSP_ERR_NULL;
    new_node->can_id = can_id;
    new_node->queue_size = queue_size;
    new_node->queue = osMessageQueueNew(queue_size, sizeof(CAN_Message_t), NULL);
    if (new_node->queue == NULL) {
        free(new_node);
        return BSP_ERR;
    }
    new_node->next = can_queue_list;
    can_queue_list = new_node;
    return BSP_OK;
}


int8_t BSP_CAN_DeleteIdQueue(uint32_t can_id) {
    CAN_QueueNode_t **current = &can_queue_list;
    while (*current) {
        if ((*current)->can_id == can_id) {
            CAN_QueueNode_t *to_delete = *current;
            *current = (*current)->next;
            osMessageQueueDelete(to_delete->queue);
            free(to_delete);
            return BSP_OK;
        }
        current = &(*current)->next;
    }
    return BSP_ERR; // 未找到
}


void BSP_CAN_RegisterId(uint32_t can_id, uint8_t queue_size) {
    BSP_CAN_CreateIdQueue(can_id, queue_size);
}


int8_t BSP_CAN_Transmit(BSP_CAN_t can, BSP_CAN_Format_t format,
                        uint32_t id, uint8_t *data, uint8_t dlc) {
  if (can >= BSP_CAN_NUM) return BSP_ERR;
  if (data == NULL) return BSP_ERR_NULL;
  if (dlc > 8) return BSP_ERR;
  
  CAN_HandleTypeDef *hcan = BSP_CAN_GetHandle(can);
  if (hcan == NULL) return BSP_ERR_NULL;
  
  CAN_TxHeaderTypeDef header;
  uint32_t mailbox;
  
  switch (format) {
    case CAN_FORMAT_STD_DATA:
      header.StdId = id;
      header.IDE = CAN_ID_STD;
      header.RTR = CAN_RTR_DATA;
      header.TransmitGlobalTime = DISABLE;
      header.DLC = dlc;
      break;
    case CAN_FORMAT_EXT_DATA:
      header.ExtId = id;
      header.IDE = CAN_ID_EXT;
      header.RTR = CAN_RTR_DATA;
      header.TransmitGlobalTime = DISABLE;
      header.DLC = dlc;
      break;
    case CAN_FORMAT_STD_REMOTE:
      header.StdId = id;
      header.IDE = CAN_ID_STD;
      header.RTR = CAN_RTR_REMOTE;
      header.TransmitGlobalTime = DISABLE;
      header.DLC = dlc;
      break;
    case CAN_FORMAT_EXT_REMOTE:
      header.ExtId = id;
      header.IDE = CAN_ID_EXT;
      header.RTR = CAN_RTR_REMOTE;
      header.TransmitGlobalTime = DISABLE;
      header.DLC = dlc;
      break;
    default:
      return BSP_ERR;
  }

  HAL_StatusTypeDef res = HAL_CAN_AddTxMessage(hcan, &header, data, &mailbox);

  if (res == HAL_OK) {
    return BSP_OK;
  } else {
    return BSP_ERR;
  }
}

int8_t BSP_CAN_Init(void) {
/* AUTO GENERATED CAN_INIT */
  
  // 注册接收中断处理函数
  for (int can_idx = 0; can_idx < BSP_CAN_NUM; can_idx++) {
    BSP_CAN_RegisterCallback((BSP_CAN_t)can_idx, HAL_CAN_RX_FIFO0_MSG_PENDING_CB, can_rx_fifo0_handler);
    BSP_CAN_RegisterCallback((BSP_CAN_t)can_idx, HAL_CAN_RX_FIFO1_MSG_PENDING_CB, can_rx_fifo1_handler);
  }

  return BSP_OK;
}

