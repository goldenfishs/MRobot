#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include <stdint.h>
#include <stdbool.h>
#include "bsp/bsp.h"
#include "bsp/mm.h"
#include <cmsis_os.h>

/* USER INCLUDE BEGIN */
#include <fdcan.h>
/* USER INCLUDE END */

/* Exported constants ------------------------------------------------------- */
#define BSP_FDCAN_MAX_DLC                 64
#define BSP_FDCAN_DEFAULT_QUEUE_SIZE      10
#define BSP_FDCAN_TIMEOUT_IMMEDIATE       0
#define BSP_FDCAN_TIMEOUT_FOREVER         osWaitForever
#define BSP_FDCAN_TX_QUEUE_SIZE           32
/* Exported macro ----------------------------------------------------------- */
/* AUTO GENERATED FDCAN_ENABLE */

/* Exported types ----------------------------------------------------------- */
typedef enum {
  BSP_FDCAN_1,
  BSP_FDCAN_2,
  BSP_FDCAN_3,
  BSP_FDCAN_NUM,
  BSP_FDCAN_ERR,
} BSP_FDCAN_t;

typedef enum {
  HAL_FDCAN_TX_EVENT_FIFO_CB,
  HAL_FDCAN_TX_BUFFER_COMPLETE_CB,
  HAL_FDCAN_TX_BUFFER_ABORT_CB,
  HAL_FDCAN_RX_FIFO0_MSG_PENDING_CB,
  HAL_FDCAN_RX_FIFO0_FULL_CB,
  HAL_FDCAN_RX_FIFO1_MSG_PENDING_CB,
  HAL_FDCAN_RX_FIFO1_FULL_CB,
  HAL_FDCAN_ERROR_CB,
  HAL_FDCAN_CB_NUM,
} BSP_FDCAN_Callback_t;

typedef enum {
  BSP_FDCAN_FORMAT_STD_DATA,
  BSP_FDCAN_FORMAT_EXT_DATA,
  BSP_FDCAN_FORMAT_STD_REMOTE,
  BSP_FDCAN_FORMAT_EXT_REMOTE,
} BSP_FDCAN_Format_t;

typedef enum {
  BSP_FDCAN_FRAME_STD_DATA,
  BSP_FDCAN_FRAME_EXT_DATA,
  BSP_FDCAN_FRAME_STD_REMOTE,
  BSP_FDCAN_FRAME_EXT_REMOTE,
} BSP_FDCAN_FrameType_t;

typedef struct {
    BSP_FDCAN_FrameType_t frame_type;
    uint32_t original_id;
    uint32_t parsed_id;
    uint8_t dlc;
    uint8_t data[BSP_FDCAN_MAX_DLC];
    uint32_t timestamp;
} BSP_FDCAN_Message_t;

typedef struct {
    uint32_t id;
    uint8_t dlc;
    uint8_t data[BSP_FDCAN_MAX_DLC];
} BSP_FDCAN_StdDataFrame_t;

typedef struct {
    uint32_t id;
    uint8_t dlc;
    uint8_t data[BSP_FDCAN_MAX_DLC];
} BSP_FDCAN_ExtDataFrame_t;

typedef struct {
    uint32_t id;
    uint8_t dlc;
    bool is_extended;
} BSP_FDCAN_RemoteFrame_t;

typedef uint32_t (*BSP_FDCAN_IdParser_t)(uint32_t original_id, BSP_FDCAN_FrameType_t frame_type);

typedef struct {
  FDCAN_TxHeaderTypeDef header; /* HAL FDCAN header type */
  uint8_t data[BSP_FDCAN_MAX_DLC];
} BSP_FDCAN_TxMessage_t;

typedef struct {
  BSP_FDCAN_TxMessage_t buffer[BSP_FDCAN_TX_QUEUE_SIZE];
  volatile uint32_t head;
  volatile uint32_t tail;
} BSP_FDCAN_TxQueue_t;

/* Exported functions prototypes -------------------------------------------- */
int8_t BSP_FDCAN_Init(void);
FDCAN_HandleTypeDef *BSP_FDCAN_GetHandle(BSP_FDCAN_t can);
int8_t BSP_FDCAN_RegisterCallback(BSP_FDCAN_t can, BSP_FDCAN_Callback_t type, void (*callback)(void));
int8_t BSP_FDCAN_Transmit(BSP_FDCAN_t can, BSP_FDCAN_Format_t format, uint32_t id, uint8_t *data, uint8_t dlc);
int8_t BSP_FDCAN_TransmitStdDataFrame(BSP_FDCAN_t can, BSP_FDCAN_StdDataFrame_t *frame);
int8_t BSP_FDCAN_TransmitExtDataFrame(BSP_FDCAN_t can, BSP_FDCAN_ExtDataFrame_t *frame);
int8_t BSP_FDCAN_TransmitRemoteFrame(BSP_FDCAN_t can, BSP_FDCAN_RemoteFrame_t *frame);
int8_t BSP_FDCAN_RegisterId(BSP_FDCAN_t can, uint32_t can_id, uint8_t queue_size);
int8_t BSP_FDCAN_GetMessage(BSP_FDCAN_t can, uint32_t can_id, BSP_FDCAN_Message_t *msg, uint32_t timeout);
int32_t BSP_FDCAN_GetQueueCount(BSP_FDCAN_t can, uint32_t can_id);
int8_t BSP_FDCAN_FlushQueue(BSP_FDCAN_t can, uint32_t can_id);
int8_t BSP_FDCAN_RegisterIdParser(BSP_FDCAN_IdParser_t parser);
uint32_t BSP_FDCAN_ParseId(uint32_t original_id, BSP_FDCAN_FrameType_t frame_type);
#ifdef __cplusplus
}
#endif
