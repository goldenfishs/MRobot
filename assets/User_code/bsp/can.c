/* Includes ----------------------------------------------------------------- */
#include "bsp/can.h"
#include "bsp/bsp.h"
#include <can.h>
#include <cmsis_os.h>
#include <string.h>

/* Private define ----------------------------------------------------------- */
#define CAN_QUEUE_MUTEX_TIMEOUT         100   /* 队列互斥锁超时时间(ms) */

/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
typedef struct BSP_CAN_QueueNode {
    BSP_CAN_t can;         /* CAN通道 */
    uint32_t can_id; /* 解析后的CAN ID */
    osMessageQueueId_t queue; /* 消息队列ID */
    uint8_t queue_size; /* 队列大小 */
    struct BSP_CAN_QueueNode *next; /* 指向下一个节点的指针 */
} BSP_CAN_QueueNode_t;

/* Private variables -------------------------------------------------------- */
static BSP_CAN_QueueNode_t *queue_list = NULL;
static osMutexId_t queue_mutex = NULL;
static void (*CAN_Callback[BSP_CAN_NUM][BSP_CAN_CB_NUM])(void);
static bool inited = false;
static BSP_CAN_IdParser_t id_parser = NULL; /* ID解析器 */

/* Private function prototypes ---------------------------------------------- */
static BSP_CAN_t CAN_Get(CAN_HandleTypeDef *hcan);
static osMessageQueueId_t BSP_CAN_FindQueue(BSP_CAN_t can, uint32_t can_id);
static int8_t BSP_CAN_CreateIdQueue(BSP_CAN_t can, uint32_t can_id, uint8_t queue_size);
static int8_t BSP_CAN_DeleteIdQueue(BSP_CAN_t can, uint32_t can_id);
static void BSP_CAN_RxFifo0Callback(void);
static void BSP_CAN_RxFifo1Callback(void);
static BSP_CAN_FrameType_t BSP_CAN_GetFrameType(CAN_RxHeaderTypeDef *header);
static uint32_t BSP_CAN_DefaultIdParser(uint32_t original_id, BSP_CAN_FrameType_t frame_type);

/* Private functions -------------------------------------------------------- */

/**
 * @brief 根据CAN句柄获取BSP_CAN实例
 */
static BSP_CAN_t CAN_Get(CAN_HandleTypeDef *hcan) {
    if (hcan == NULL) return BSP_CAN_ERR;
    
/* AUTO GENERATED CAN_GET */
    else
        return BSP_CAN_ERR;
}

/**
 * @brief 查找指定CAN ID的消息队列
 * @note 调用前需要获取互斥锁
 */
static osMessageQueueId_t BSP_CAN_FindQueue(BSP_CAN_t can, uint32_t can_id) {
    BSP_CAN_QueueNode_t *node = queue_list;
    while (node != NULL) {
        if (node->can == can && node->can_id == can_id) {
            return node->queue;
        }
        node = node->next;
    }
    return NULL;
}

/**
 * @brief 创建指定CAN ID的消息队列
 * @note 内部函数，已包含互斥锁保护
 */
static int8_t BSP_CAN_CreateIdQueue(BSP_CAN_t can, uint32_t can_id, uint8_t queue_size) {
    if (queue_size == 0) {
        queue_size = BSP_CAN_DEFAULT_QUEUE_SIZE;
    }
    if (osMutexAcquire(queue_mutex, CAN_QUEUE_MUTEX_TIMEOUT) != osOK) {
        return BSP_ERR_TIMEOUT;
    }
    BSP_CAN_QueueNode_t *node = queue_list;
    while (node != NULL) {
        if (node->can == can && node->can_id == can_id) {
            osMutexRelease(queue_mutex);
            return BSP_ERR;  // 已存在
        }
        node = node->next;
    }
    BSP_CAN_QueueNode_t *new_node = (BSP_CAN_QueueNode_t *)BSP_Malloc(sizeof(BSP_CAN_QueueNode_t));
    if (new_node == NULL) {
        osMutexRelease(queue_mutex);
        return BSP_ERR_NULL;
    }
    new_node->queue = osMessageQueueNew(queue_size, sizeof(BSP_CAN_Message_t), NULL);
    if (new_node->queue == NULL) {
        BSP_Free(new_node);
        osMutexRelease(queue_mutex);
        return BSP_ERR;
    }
    new_node->can = can;
    new_node->can_id = can_id;
    new_node->queue_size = queue_size;
    new_node->next = queue_list;
    queue_list = new_node;
    osMutexRelease(queue_mutex);
    return BSP_OK;
}

/**
 * @brief 删除指定CAN ID的消息队列
 * @note 内部函数，已包含互斥锁保护
 */
static int8_t BSP_CAN_DeleteIdQueue(BSP_CAN_t can, uint32_t can_id) {
    if (osMutexAcquire(queue_mutex, CAN_QUEUE_MUTEX_TIMEOUT) != osOK) {
        return BSP_ERR_TIMEOUT;
    }
    BSP_CAN_QueueNode_t **current = &queue_list;
    while (*current != NULL) {
        if ((*current)->can == can && (*current)->can_id == can_id) {
            BSP_CAN_QueueNode_t *to_delete = *current;
            *current = (*current)->next;
            osMessageQueueDelete(to_delete->queue);
            BSP_Free(to_delete);
            osMutexRelease(queue_mutex);
            return BSP_OK;
        }
        current = &(*current)->next;
    }
    osMutexRelease(queue_mutex);
    return BSP_ERR;  // 未找到
}
/**
 * @brief 获取帧类型
 */
static BSP_CAN_FrameType_t BSP_CAN_GetFrameType(CAN_RxHeaderTypeDef *header) {
    if (header->RTR == CAN_RTR_REMOTE) {
        return (header->IDE == CAN_ID_EXT) ? BSP_CAN_FRAME_EXT_REMOTE : BSP_CAN_FRAME_STD_REMOTE;
    } else {
        return (header->IDE == CAN_ID_EXT) ? BSP_CAN_FRAME_EXT_DATA : BSP_CAN_FRAME_STD_DATA;
    }
}

/**
 * @brief 默认ID解析器（直接返回原始ID）
 */
static uint32_t BSP_CAN_DefaultIdParser(uint32_t original_id, BSP_CAN_FrameType_t frame_type) {
    (void)frame_type;  // 避免未使用参数警告
    return original_id;
}

/**
 * @brief FIFO0接收处理函数
 */
static void BSP_CAN_RxFifo0Callback(void) {
    CAN_RxHeaderTypeDef rx_header;
    uint8_t rx_data[BSP_CAN_MAX_DLC];
    for (int can_idx = 0; can_idx < BSP_CAN_NUM; can_idx++) {
        CAN_HandleTypeDef *hcan = BSP_CAN_GetHandle((BSP_CAN_t)can_idx);
        if (hcan == NULL) continue;
        while (HAL_CAN_GetRxFifoFillLevel(hcan, CAN_RX_FIFO0) > 0) {
            if (HAL_CAN_GetRxMessage(hcan, CAN_RX_FIFO0, &rx_header, rx_data) == HAL_OK) {
                uint32_t original_id = (rx_header.IDE == CAN_ID_STD) ? rx_header.StdId : rx_header.ExtId;
                BSP_CAN_FrameType_t frame_type = BSP_CAN_GetFrameType(&rx_header);
                uint32_t parsed_id = BSP_CAN_ParseId(original_id, frame_type);
                osMessageQueueId_t queue = BSP_CAN_FindQueue((BSP_CAN_t)can_idx, parsed_id);
                if (queue != NULL) {
                    BSP_CAN_Message_t msg = {0};
                    msg.frame_type = frame_type;
                    msg.original_id = original_id;
                    msg.parsed_id = parsed_id;
                    msg.dlc = rx_header.DLC;
                    if (rx_header.RTR == CAN_RTR_DATA) {
                        memcpy(msg.data, rx_data, rx_header.DLC);
                    }
                    msg.timestamp = HAL_GetTick();
                    osMessageQueuePut(queue, &msg, 0, BSP_CAN_TIMEOUT_IMMEDIATE);
                }
            }
        }
    }
}

/**
 * @brief FIFO1接收处理函数
 */
static void BSP_CAN_RxFifo1Callback(void) {
    CAN_RxHeaderTypeDef rx_header;
    uint8_t rx_data[BSP_CAN_MAX_DLC];
    for (int can_idx = 0; can_idx < BSP_CAN_NUM; can_idx++) {
        CAN_HandleTypeDef *hcan = BSP_CAN_GetHandle((BSP_CAN_t)can_idx);
        if (hcan == NULL) continue;
        while (HAL_CAN_GetRxFifoFillLevel(hcan, CAN_RX_FIFO1) > 0) {
            if (HAL_CAN_GetRxMessage(hcan, CAN_RX_FIFO1, &rx_header, rx_data) == HAL_OK) {
                uint32_t original_id = (rx_header.IDE == CAN_ID_STD) ? rx_header.StdId : rx_header.ExtId;
                BSP_CAN_FrameType_t frame_type = BSP_CAN_GetFrameType(&rx_header);
                uint32_t parsed_id = BSP_CAN_ParseId(original_id, frame_type);
                osMessageQueueId_t queue = BSP_CAN_FindQueue((BSP_CAN_t)can_idx, parsed_id);
                if (queue != NULL) {
                    BSP_CAN_Message_t msg = {0};
                    msg.frame_type = frame_type;
                    msg.original_id = original_id;
                    msg.parsed_id = parsed_id;
                    msg.dlc = rx_header.DLC;
                    if (rx_header.RTR == CAN_RTR_DATA) {
                        memcpy(msg.data, rx_data, rx_header.DLC);
                    }
                    msg.timestamp = HAL_GetTick();
                    osMessageQueuePut(queue, &msg, 0, BSP_CAN_TIMEOUT_IMMEDIATE);
                }
            }
        }
    }
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

int8_t BSP_CAN_Init(void) {
    if (inited) {
        return BSP_ERR_INITED;
    }
    
    // 清零回调函数数组
    memset(CAN_Callback, 0, sizeof(CAN_Callback));
    
    // 初始化ID解析器为默认解析器
    id_parser = BSP_CAN_DefaultIdParser;
    
    // 创建互斥锁
    queue_mutex = osMutexNew(NULL);
    if (queue_mutex == NULL) {
        return BSP_ERR;
    }
    
/* AUTO GENERATED CAN_INIT */
    
    inited = true;
    return BSP_OK;
}

int8_t BSP_CAN_DeInit(void) {
    if (!inited) {
        return BSP_ERR;
    }
    
    // 删除所有队列
    if (osMutexAcquire(queue_mutex, CAN_QUEUE_MUTEX_TIMEOUT) == osOK) {
        BSP_CAN_QueueNode_t *current = queue_list;
        while (current != NULL) {
            BSP_CAN_QueueNode_t *next = current->next;
            osMessageQueueDelete(current->queue);
            BSP_Free(current);
            current = next;
        }
        queue_list = NULL;
        osMutexRelease(queue_mutex);
    }
    
    // 删除互斥锁
    if (queue_mutex != NULL) {
        osMutexDelete(queue_mutex);
        queue_mutex = NULL;
    }
    
    // 清零回调函数数组
    memset(CAN_Callback, 0, sizeof(CAN_Callback));
    
    // 重置ID解析器
    id_parser = NULL;
    
    inited = false;
    return BSP_OK;
}

CAN_HandleTypeDef *BSP_CAN_GetHandle(BSP_CAN_t can) {
    if (can >= BSP_CAN_NUM) {
        return NULL;
    }
    
    switch (can) {
/* AUTO GENERATED BSP_CAN_GET_HANDLE */
        default:
            return NULL;
    }
}

int8_t BSP_CAN_RegisterCallback(BSP_CAN_t can, BSP_CAN_Callback_t type,
                                void (*callback)(void)) {
    if (!inited) {
        return BSP_ERR_INITED;
    }
    if (callback == NULL) {
        return BSP_ERR_NULL;
    }
    if (can >= BSP_CAN_NUM) {
        return BSP_ERR;
    }
    if (type >= BSP_CAN_CB_NUM) {
        return BSP_ERR;
    }
    
    CAN_Callback[can][type] = callback;
    return BSP_OK;
}

int8_t BSP_CAN_Transmit(BSP_CAN_t can, BSP_CAN_Format_t format,
                        uint32_t id, uint8_t *data, uint8_t dlc) {
    if (!inited) {
        return BSP_ERR_INITED;
    }
    if (can >= BSP_CAN_NUM) {
        return BSP_ERR;
    }
    if (data == NULL && format != BSP_CAN_FORMAT_STD_REMOTE && format != BSP_CAN_FORMAT_EXT_REMOTE) {
        return BSP_ERR_NULL;
    }
    if (dlc > BSP_CAN_MAX_DLC) {
        return BSP_ERR;
    }
    
    CAN_HandleTypeDef *hcan = BSP_CAN_GetHandle(can);
    if (hcan == NULL) {
        return BSP_ERR_NULL;
    }
    
    CAN_TxHeaderTypeDef header = {0};
    uint32_t mailbox;
    
    switch (format) {
        case BSP_CAN_FORMAT_STD_DATA:
            header.StdId = id;
            header.IDE = CAN_ID_STD;
            header.RTR = CAN_RTR_DATA;
            break;
        case BSP_CAN_FORMAT_EXT_DATA:
            header.ExtId = id;
            header.IDE = CAN_ID_EXT;
            header.RTR = CAN_RTR_DATA;
            break;
        case BSP_CAN_FORMAT_STD_REMOTE:
            header.StdId = id;
            header.IDE = CAN_ID_STD;
            header.RTR = CAN_RTR_REMOTE;
            break;
        case BSP_CAN_FORMAT_EXT_REMOTE:
            header.ExtId = id;
            header.IDE = CAN_ID_EXT;
            header.RTR = CAN_RTR_REMOTE;
            break;
        default:
            return BSP_ERR;
    }
    
    header.DLC = dlc;
    header.TransmitGlobalTime = DISABLE;
    
    HAL_StatusTypeDef result = HAL_CAN_AddTxMessage(hcan, &header, data, &mailbox);
    return (result == HAL_OK) ? BSP_OK : BSP_ERR;
}

int8_t BSP_CAN_TransmitStdDataFrame(BSP_CAN_t can, BSP_CAN_StdDataFrame_t *frame) {
    if (frame == NULL) {
        return BSP_ERR_NULL;
    }
    return BSP_CAN_Transmit(can, BSP_CAN_FORMAT_STD_DATA, frame->id, frame->data, frame->dlc);
}

int8_t BSP_CAN_TransmitExtDataFrame(BSP_CAN_t can, BSP_CAN_ExtDataFrame_t *frame) {
    if (frame == NULL) {
        return BSP_ERR_NULL;
    }
    return BSP_CAN_Transmit(can, BSP_CAN_FORMAT_EXT_DATA, frame->id, frame->data, frame->dlc);
}

int8_t BSP_CAN_TransmitRemoteFrame(BSP_CAN_t can, BSP_CAN_RemoteFrame_t *frame) {
    if (frame == NULL) {
        return BSP_ERR_NULL;
    }
    BSP_CAN_Format_t format = frame->is_extended ? BSP_CAN_FORMAT_EXT_REMOTE : BSP_CAN_FORMAT_STD_REMOTE;
    return BSP_CAN_Transmit(can, format, frame->id, NULL, frame->dlc);
}

int8_t BSP_CAN_RegisterId(BSP_CAN_t can, uint32_t can_id, uint8_t queue_size) {
    if (!inited) {
        return BSP_ERR_INITED;
    }
    return BSP_CAN_CreateIdQueue(can, can_id, queue_size);
}

int8_t BSP_CAN_UnregisterIdQueue(BSP_CAN_t can, uint32_t can_id) {
    if (!inited) {
        return BSP_ERR_INITED;
    }
    return BSP_CAN_DeleteIdQueue(can, can_id);
}

int8_t BSP_CAN_GetMessage(BSP_CAN_t can, uint32_t can_id, BSP_CAN_Message_t *msg, uint32_t timeout) {
    if (!inited) {
        return BSP_ERR_INITED;
    }
    if (msg == NULL) {
        return BSP_ERR_NULL;
    }
    if (osMutexAcquire(queue_mutex, CAN_QUEUE_MUTEX_TIMEOUT) != osOK) {
        return BSP_ERR_TIMEOUT;
    }
    osMessageQueueId_t queue = BSP_CAN_FindQueue(can, can_id);
    osMutexRelease(queue_mutex);
    if (queue == NULL) {
        return BSP_ERR_NO_DEV;
    }
    osStatus_t result = osMessageQueueGet(queue, msg, NULL, timeout);
    return (result == osOK) ? BSP_OK : BSP_ERR;
}

int32_t BSP_CAN_GetQueueCount(BSP_CAN_t can, uint32_t can_id) {
    if (!inited) {
        return -1;
    }
    if (osMutexAcquire(queue_mutex, CAN_QUEUE_MUTEX_TIMEOUT) != osOK) {
        return -1;
    }
    osMessageQueueId_t queue = BSP_CAN_FindQueue(can, can_id);
    osMutexRelease(queue_mutex);
    if (queue == NULL) {
        return -1;
    }
    return (int32_t)osMessageQueueGetCount(queue);
}

int8_t BSP_CAN_FlushQueue(BSP_CAN_t can, uint32_t can_id) {
    if (!inited) {
        return BSP_ERR_INITED;
    }
    if (osMutexAcquire(queue_mutex, CAN_QUEUE_MUTEX_TIMEOUT) != osOK) {
        return BSP_ERR_TIMEOUT;
    }
    osMessageQueueId_t queue = BSP_CAN_FindQueue(can, can_id);
    osMutexRelease(queue_mutex);
    if (queue == NULL) {
        return BSP_ERR_NO_DEV;
    }
    BSP_CAN_Message_t temp_msg;
    while (osMessageQueueGet(queue, &temp_msg, NULL, BSP_CAN_TIMEOUT_IMMEDIATE) == osOK) {
        // 清空
    }
    return BSP_OK;
}

int8_t BSP_CAN_RegisterIdParser(BSP_CAN_IdParser_t parser) {
    if (!inited) {
        return BSP_ERR_INITED;
    }
    if (parser == NULL) {
        return BSP_ERR_NULL;
    }
    
    id_parser = parser;
    return BSP_OK;
}

int8_t BSP_CAN_UnregisterIdParser(void) {
    if (!inited) {
        return BSP_ERR_INITED;
    }
    
    id_parser = BSP_CAN_DefaultIdParser;
    return BSP_OK;
}

uint32_t BSP_CAN_ParseId(uint32_t original_id, BSP_CAN_FrameType_t frame_type) {
    if (id_parser != NULL) {
        return id_parser(original_id, frame_type);
    }
    return BSP_CAN_DefaultIdParser(original_id, frame_type);
}

/* USER CAN FUNCTIONS BEGIN */
/* USER CAN FUNCTIONS END */