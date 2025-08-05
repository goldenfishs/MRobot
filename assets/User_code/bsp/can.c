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
    uint32_t can_id;
    osMessageQueueId_t queue;
    uint8_t queue_size;
    struct BSP_CAN_QueueNode *next;
} BSP_CAN_QueueNode_t;

/* Private variables -------------------------------------------------------- */
static BSP_CAN_QueueNode_t *g_can_queue_list = NULL;
static osMutexId_t g_can_queue_mutex = NULL;
static void (*g_can_callbacks[BSP_CAN_NUM][BSP_CAN_CB_NUM])(void);
static bool g_can_initialized = false;

/* Private function prototypes ---------------------------------------------- */
static BSP_CAN_t BSP_CAN_GetInstance(CAN_HandleTypeDef *hcan);
static osMessageQueueId_t BSP_CAN_FindQueue(uint32_t can_id);
static int8_t BSP_CAN_CreateIdQueue(uint32_t can_id, uint8_t queue_size);
static int8_t BSP_CAN_DeleteIdQueue(uint32_t can_id);
static void BSP_CAN_RxFifo0Handler(void);
static void BSP_CAN_RxFifo1Handler(void);

/* Private functions -------------------------------------------------------- */

/**
 * @brief 根据CAN句柄获取BSP_CAN实例
 */
static BSP_CAN_t BSP_CAN_GetInstance(CAN_HandleTypeDef *hcan) {
    if (hcan == NULL) return BSP_CAN_ERR;
    
/* AUTO GENERATED CAN_GET */
    else
        return BSP_CAN_ERR;
}

/**
 * @brief 查找指定CAN ID的消息队列
 * @note 调用前需要获取互斥锁
 */
static osMessageQueueId_t BSP_CAN_FindQueue(uint32_t can_id) {
    BSP_CAN_QueueNode_t *node = g_can_queue_list;
    while (node != NULL) {
        if (node->can_id == can_id) {
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
static int8_t BSP_CAN_CreateIdQueue(uint32_t can_id, uint8_t queue_size) {
    if (queue_size == 0) {
        queue_size = BSP_CAN_DEFAULT_QUEUE_SIZE;
    }
    
    // 获取互斥锁
    if (osMutexAcquire(g_can_queue_mutex, CAN_QUEUE_MUTEX_TIMEOUT) != osOK) {
        return BSP_ERR_TIMEOUT;
    }
    
    // 检查是否已存在
    BSP_CAN_QueueNode_t *node = g_can_queue_list;
    while (node != NULL) {
        if (node->can_id == can_id) {
            osMutexRelease(g_can_queue_mutex);
            return BSP_ERR;  // 已存在
        }
        node = node->next;
    }
    
    // 创建新节点
    BSP_CAN_QueueNode_t *new_node = (BSP_CAN_QueueNode_t *)BSP_Malloc(sizeof(BSP_CAN_QueueNode_t));
    if (new_node == NULL) {
        osMutexRelease(g_can_queue_mutex);
        return BSP_ERR_NULL;
    }
    
    // 创建消息队列
    new_node->queue = osMessageQueueNew(queue_size, sizeof(BSP_CAN_Message_t), NULL);
    if (new_node->queue == NULL) {
        BSP_Free(new_node);
        osMutexRelease(g_can_queue_mutex);
        return BSP_ERR;
    }
    
    // 初始化节点
    new_node->can_id = can_id;
    new_node->queue_size = queue_size;
    new_node->next = g_can_queue_list;
    g_can_queue_list = new_node;
    
    osMutexRelease(g_can_queue_mutex);
    return BSP_OK;
}

/**
 * @brief 删除指定CAN ID的消息队列
 * @note 内部函数，已包含互斥锁保护
 */
static int8_t BSP_CAN_DeleteIdQueue(uint32_t can_id) {
    // 获取互斥锁
    if (osMutexAcquire(g_can_queue_mutex, CAN_QUEUE_MUTEX_TIMEOUT) != osOK) {
        return BSP_ERR_TIMEOUT;
    }
    
    BSP_CAN_QueueNode_t **current = &g_can_queue_list;
    while (*current != NULL) {
        if ((*current)->can_id == can_id) {
            BSP_CAN_QueueNode_t *to_delete = *current;
            *current = (*current)->next;
            
            // 删除队列和节点
            osMessageQueueDelete(to_delete->queue);
            BSP_Free(to_delete);
            
            osMutexRelease(g_can_queue_mutex);
            return BSP_OK;
        }
        current = &(*current)->next;
    }
    
    osMutexRelease(g_can_queue_mutex);
    return BSP_ERR;  // 未找到
}

/**
 * @brief FIFO0接收处理函数
 */
static void BSP_CAN_RxFifo0Handler(void) {
    CAN_RxHeaderTypeDef rx_header;
    uint8_t rx_data[BSP_CAN_MAX_DLC];
    
    // 遍历所有CAN接口处理FIFO0
    for (int can_idx = 0; can_idx < BSP_CAN_NUM; can_idx++) {
        CAN_HandleTypeDef *hcan = BSP_CAN_GetHandle((BSP_CAN_t)can_idx);
        if (hcan == NULL) continue;
        
        while (HAL_CAN_GetRxFifoFillLevel(hcan, CAN_RX_FIFO0) > 0) {
            if (HAL_CAN_GetRxMessage(hcan, CAN_RX_FIFO0, &rx_header, rx_data) == HAL_OK) {
                uint32_t can_id = (rx_header.IDE == CAN_ID_STD) ? rx_header.StdId : rx_header.ExtId;
                
                // 线程安全地查找队列
                if (osMutexAcquire(g_can_queue_mutex, CAN_QUEUE_MUTEX_TIMEOUT) == osOK) {
                    osMessageQueueId_t queue = BSP_CAN_FindQueue(can_id);
                    osMutexRelease(g_can_queue_mutex);
                    
                    if (queue != NULL) {
                        BSP_CAN_Message_t msg;
                        msg.header = rx_header;
                        memcpy(msg.data, rx_data, BSP_CAN_MAX_DLC);
                        
                        // 非阻塞发送，如果队列满了就丢弃
                        osMessageQueuePut(queue, &msg, 0, BSP_CAN_TIMEOUT_IMMEDIATE);
                    }
                }
                // 如果没有找到对应的队列或获取互斥锁超时，消息被直接丢弃
            }
        }
    }
}

/**
 * @brief FIFO1接收处理函数
 */
static void BSP_CAN_RxFifo1Handler(void) {
    CAN_RxHeaderTypeDef rx_header;
    uint8_t rx_data[BSP_CAN_MAX_DLC];
    
    // 遍历所有CAN接口处理FIFO1
    for (int can_idx = 0; can_idx < BSP_CAN_NUM; can_idx++) {
        CAN_HandleTypeDef *hcan = BSP_CAN_GetHandle((BSP_CAN_t)can_idx);
        if (hcan == NULL) continue;
        
        while (HAL_CAN_GetRxFifoFillLevel(hcan, CAN_RX_FIFO1) > 0) {
            if (HAL_CAN_GetRxMessage(hcan, CAN_RX_FIFO1, &rx_header, rx_data) == HAL_OK) {
                uint32_t can_id = (rx_header.IDE == CAN_ID_STD) ? rx_header.StdId : rx_header.ExtId;
                
                // 线程安全地查找队列
                if (osMutexAcquire(g_can_queue_mutex, CAN_QUEUE_MUTEX_TIMEOUT) == osOK) {
                    osMessageQueueId_t queue = BSP_CAN_FindQueue(can_id);
                    osMutexRelease(g_can_queue_mutex);
                    
                    if (queue != NULL) {
                        BSP_CAN_Message_t msg;
                        msg.header = rx_header;
                        memcpy(msg.data, rx_data, BSP_CAN_MAX_DLC);
                        
                        // 非阻塞发送，如果队列满了就丢弃
                        osMessageQueuePut(queue, &msg, 0, BSP_CAN_TIMEOUT_IMMEDIATE);
                    }
                }
                // 如果没有找到对应的队列或获取互斥锁超时，消息被直接丢弃
            }
        }
    }
}

/* HAL Callback Functions --------------------------------------------------- */
void HAL_CAN_TxMailbox0CompleteCallback(CAN_HandleTypeDef *hcan) {
    BSP_CAN_t bsp_can = BSP_CAN_GetInstance(hcan);
    if (bsp_can != BSP_CAN_ERR) {
        if (g_can_callbacks[bsp_can][BSP_CAN_TX_MAILBOX0_CPLT_CB] != NULL) {
            g_can_callbacks[bsp_can][BSP_CAN_TX_MAILBOX0_CPLT_CB]();
        }
    }
}

void HAL_CAN_TxMailbox1CompleteCallback(CAN_HandleTypeDef *hcan) {
    BSP_CAN_t bsp_can = BSP_CAN_GetInstance(hcan);
    if (bsp_can != BSP_CAN_ERR) {
        if (g_can_callbacks[bsp_can][BSP_CAN_TX_MAILBOX1_CPLT_CB] != NULL) {
            g_can_callbacks[bsp_can][BSP_CAN_TX_MAILBOX1_CPLT_CB]();
        }
    }
}

void HAL_CAN_TxMailbox2CompleteCallback(CAN_HandleTypeDef *hcan) {
    BSP_CAN_t bsp_can = BSP_CAN_GetInstance(hcan);
    if (bsp_can != BSP_CAN_ERR) {
        if (g_can_callbacks[bsp_can][BSP_CAN_TX_MAILBOX2_CPLT_CB] != NULL) {
            g_can_callbacks[bsp_can][BSP_CAN_TX_MAILBOX2_CPLT_CB]();
        }
    }
}

void HAL_CAN_TxMailbox0AbortCallback(CAN_HandleTypeDef *hcan) {
    BSP_CAN_t bsp_can = BSP_CAN_GetInstance(hcan);
    if (bsp_can != BSP_CAN_ERR) {
        if (g_can_callbacks[bsp_can][BSP_CAN_TX_MAILBOX0_ABORT_CB] != NULL) {
            g_can_callbacks[bsp_can][BSP_CAN_TX_MAILBOX0_ABORT_CB]();
        }
    }
}

void HAL_CAN_TxMailbox1AbortCallback(CAN_HandleTypeDef *hcan) {
    BSP_CAN_t bsp_can = BSP_CAN_GetInstance(hcan);
    if (bsp_can != BSP_CAN_ERR) {
        if (g_can_callbacks[bsp_can][BSP_CAN_TX_MAILBOX1_ABORT_CB] != NULL) {
            g_can_callbacks[bsp_can][BSP_CAN_TX_MAILBOX1_ABORT_CB]();
        }
    }
}

void HAL_CAN_TxMailbox2AbortCallback(CAN_HandleTypeDef *hcan) {
    BSP_CAN_t bsp_can = BSP_CAN_GetInstance(hcan);
    if (bsp_can != BSP_CAN_ERR) {
        if (g_can_callbacks[bsp_can][BSP_CAN_TX_MAILBOX2_ABORT_CB] != NULL) {
            g_can_callbacks[bsp_can][BSP_CAN_TX_MAILBOX2_ABORT_CB]();
        }
    }
}

void HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *hcan) {
    BSP_CAN_t bsp_can = BSP_CAN_GetInstance(hcan);
    if (bsp_can != BSP_CAN_ERR) {
        if (g_can_callbacks[bsp_can][BSP_CAN_RX_FIFO0_MSG_PENDING_CB] != NULL) {
            g_can_callbacks[bsp_can][BSP_CAN_RX_FIFO0_MSG_PENDING_CB]();
        }
    }
}

void HAL_CAN_RxFifo0FullCallback(CAN_HandleTypeDef *hcan) {
    BSP_CAN_t bsp_can = BSP_CAN_GetInstance(hcan);
    if (bsp_can != BSP_CAN_ERR) {
        if (g_can_callbacks[bsp_can][BSP_CAN_RX_FIFO0_FULL_CB] != NULL) {
            g_can_callbacks[bsp_can][BSP_CAN_RX_FIFO0_FULL_CB]();
        }
    }
}

void HAL_CAN_RxFifo1MsgPendingCallback(CAN_HandleTypeDef *hcan) {
    BSP_CAN_t bsp_can = BSP_CAN_GetInstance(hcan);
    if (bsp_can != BSP_CAN_ERR) {
        if (g_can_callbacks[bsp_can][BSP_CAN_RX_FIFO1_MSG_PENDING_CB] != NULL) {
            g_can_callbacks[bsp_can][BSP_CAN_RX_FIFO1_MSG_PENDING_CB]();
        }
    }
}

void HAL_CAN_RxFifo1FullCallback(CAN_HandleTypeDef *hcan) {
    BSP_CAN_t bsp_can = BSP_CAN_GetInstance(hcan);
    if (bsp_can != BSP_CAN_ERR) {
        if (g_can_callbacks[bsp_can][BSP_CAN_RX_FIFO1_FULL_CB] != NULL) {
            g_can_callbacks[bsp_can][BSP_CAN_RX_FIFO1_FULL_CB]();
        }
    }
}

void HAL_CAN_SleepCallback(CAN_HandleTypeDef *hcan) {
    BSP_CAN_t bsp_can = BSP_CAN_GetInstance(hcan);
    if (bsp_can != BSP_CAN_ERR) {
        if (g_can_callbacks[bsp_can][BSP_CAN_SLEEP_CB] != NULL) {
            g_can_callbacks[bsp_can][BSP_CAN_SLEEP_CB]();
        }
    }
}

void HAL_CAN_WakeUpFromRxMsgCallback(CAN_HandleTypeDef *hcan) {
    BSP_CAN_t bsp_can = BSP_CAN_GetInstance(hcan);
    if (bsp_can != BSP_CAN_ERR) {
        if (g_can_callbacks[bsp_can][BSP_CAN_WAKEUP_FROM_RX_MSG_CB] != NULL) {
            g_can_callbacks[bsp_can][BSP_CAN_WAKEUP_FROM_RX_MSG_CB]();
        }
    }
}

void HAL_CAN_ErrorCallback(CAN_HandleTypeDef *hcan) {
    BSP_CAN_t bsp_can = BSP_CAN_GetInstance(hcan);
    if (bsp_can != BSP_CAN_ERR) {
        if (g_can_callbacks[bsp_can][BSP_CAN_ERROR_CB] != NULL) {
            g_can_callbacks[bsp_can][BSP_CAN_ERROR_CB]();
        }
    }
}

/* Exported functions ------------------------------------------------------- */

int8_t BSP_CAN_Init(void) {
    if (g_can_initialized) {
        return BSP_ERR_INITED;
    }
    
    // 清零回调函数数组
    memset(g_can_callbacks, 0, sizeof(g_can_callbacks));
    
    // 创建互斥锁
    g_can_queue_mutex = osMutexNew(NULL);
    if (g_can_queue_mutex == NULL) {
        return BSP_ERR;
    }
    
/* AUTO GENERATED CAN_INIT */
    
    // 注册默认的接收中断处理函数
    for (int can_idx = 0; can_idx < BSP_CAN_NUM; can_idx++) {
        BSP_CAN_RegisterCallback((BSP_CAN_t)can_idx, BSP_CAN_RX_FIFO0_MSG_PENDING_CB, BSP_CAN_RxFifo0Handler);
        BSP_CAN_RegisterCallback((BSP_CAN_t)can_idx, BSP_CAN_RX_FIFO1_MSG_PENDING_CB, BSP_CAN_RxFifo1Handler);
    }
    
    g_can_initialized = true;
    return BSP_OK;
}

int8_t BSP_CAN_DeInit(void) {
    if (!g_can_initialized) {
        return BSP_ERR;
    }
    
    // 删除所有队列
    if (osMutexAcquire(g_can_queue_mutex, CAN_QUEUE_MUTEX_TIMEOUT) == osOK) {
        BSP_CAN_QueueNode_t *current = g_can_queue_list;
        while (current != NULL) {
            BSP_CAN_QueueNode_t *next = current->next;
            osMessageQueueDelete(current->queue);
            BSP_Free(current);
            current = next;
        }
        g_can_queue_list = NULL;
        osMutexRelease(g_can_queue_mutex);
    }
    
    // 删除互斥锁
    if (g_can_queue_mutex != NULL) {
        osMutexDelete(g_can_queue_mutex);
        g_can_queue_mutex = NULL;
    }
    
    // 清零回调函数数组
    memset(g_can_callbacks, 0, sizeof(g_can_callbacks));
    
    g_can_initialized = false;
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
    if (!g_can_initialized) {
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
    
    g_can_callbacks[can][type] = callback;
    return BSP_OK;
}

int8_t BSP_CAN_Transmit(BSP_CAN_t can, BSP_CAN_Format_t format,
                        uint32_t id, uint8_t *data, uint8_t dlc) {
    if (!g_can_initialized) {
        return BSP_ERR_INITED;
    }
    if (can >= BSP_CAN_NUM) {
        return BSP_ERR;
    }
    if (data == NULL) {
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

int8_t BSP_CAN_RegisterId(uint32_t can_id, uint8_t queue_size) {
    if (!g_can_initialized) {
        return BSP_ERR_INITED;
    }
    
    return BSP_CAN_CreateIdQueue(can_id, queue_size);
}

int8_t BSP_CAN_UnregisterIdQueue(uint32_t can_id) {
    if (!g_can_initialized) {
        return BSP_ERR_INITED;
    }
    
    return BSP_CAN_DeleteIdQueue(can_id);
}

int8_t BSP_CAN_GetMessage(uint32_t can_id, BSP_CAN_Message_t *msg, uint32_t timeout) {
    if (!g_can_initialized) {
        return BSP_ERR_INITED;
    }
    if (msg == NULL) {
        return BSP_ERR_NULL;
    }
    
    // 线程安全地查找队列
    if (osMutexAcquire(g_can_queue_mutex, CAN_QUEUE_MUTEX_TIMEOUT) != osOK) {
        return BSP_ERR_TIMEOUT;
    }
    
    osMessageQueueId_t queue = BSP_CAN_FindQueue(can_id);
    osMutexRelease(g_can_queue_mutex);
    
    if (queue == NULL) {
        return BSP_ERR_NO_DEV;  // 队列不存在
    }
    
    osStatus_t result = osMessageQueueGet(queue, msg, NULL, timeout);
    return (result == osOK) ? BSP_OK : BSP_ERR;
}

int32_t BSP_CAN_GetQueueCount(uint32_t can_id) {
    if (!g_can_initialized) {
        return -1;
    }
    
    // 线程安全地查找队列
    if (osMutexAcquire(g_can_queue_mutex, CAN_QUEUE_MUTEX_TIMEOUT) != osOK) {
        return -1;
    }
    
    osMessageQueueId_t queue = BSP_CAN_FindQueue(can_id);
    osMutexRelease(g_can_queue_mutex);
    
    if (queue == NULL) {
        return -1;  // 队列不存在
    }
    
    return (int32_t)osMessageQueueGetCount(queue);
}

int8_t BSP_CAN_FlushQueue(uint32_t can_id) {
    if (!g_can_initialized) {
        return BSP_ERR_INITED;
    }
    
    // 线程安全地查找队列
    if (osMutexAcquire(g_can_queue_mutex, CAN_QUEUE_MUTEX_TIMEOUT) != osOK) {
        return BSP_ERR_TIMEOUT;
    }
    
    osMessageQueueId_t queue = BSP_CAN_FindQueue(can_id);
    osMutexRelease(g_can_queue_mutex);
    
    if (queue == NULL) {
        return BSP_ERR_NO_DEV;  // 队列不存在
    }
    
    // 清空队列中的所有消息
    BSP_CAN_Message_t temp_msg;
    while (osMessageQueueGet(queue, &temp_msg, NULL, BSP_CAN_TIMEOUT_IMMEDIATE) == osOK) {
        // 继续取出消息直到队列为空
    }
    
    return BSP_OK;
}

/* USER CAN FUNCTIONS BEGIN */
/* USER CAN FUNCTIONS END */