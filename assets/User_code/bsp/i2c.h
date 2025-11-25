#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include <i2c.h>
#include <stdint.h>
#include <stdbool.h>

#include "bsp/bsp.h"

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* USER DEFINE BEGIN */

/* USER DEFINE END */

/* Exported types ----------------------------------------------------------- */

/* 要添加使用I2C的新设备，需要先在此添加对应的枚举值 */

/* I2C实体枚举，与设备对应 */
typedef enum {
/* AUTO GENERATED BSP_I2C_NAME */
  /* USER BSP_I2C BEGIN*/
  /* USER_I2C_XXX */
  /* USER BSP_I2C END */
  BSP_I2C_NUM,
  BSP_I2C_ERR,
} BSP_I2C_t;

/* I2C支持的中断回调函数类型*/
typedef enum {
  HAL_I2C_MASTER_TX_CPLT_CB,
  HAL_I2C_MASTER_RX_CPLT_CB,
  HAL_I2C_SLAVE_TX_CPLT_CB,
  HAL_I2C_SLAVE_RX_CPLT_CB,
  HAL_I2C_LISTEN_CPLT_CB,
  HAL_I2C_MEM_TX_CPLT_CB,
  HAL_I2C_MEM_RX_CPLT_CB,
  HAL_I2C_ERROR_CB,
  HAL_I2C_ABORT_CPLT_CB,
  BSP_I2C_CB_NUM,
} BSP_I2C_Callback_t;

/* Exported functions prototypes -------------------------------------------- */
I2C_HandleTypeDef *BSP_I2C_GetHandle(BSP_I2C_t i2c);
int8_t BSP_I2C_RegisterCallback(BSP_I2C_t i2c, BSP_I2C_Callback_t type,
                                void (*callback)(void));

int8_t BSP_I2C_Transmit(BSP_I2C_t i2c, uint16_t devAddr, uint8_t *data,
                        uint16_t size, bool dma);
int8_t BSP_I2C_Receive(BSP_I2C_t i2c, uint16_t devAddr, uint8_t *data,
                       uint16_t size, bool dma);


uint8_t BSP_I2C_MemReadByte(BSP_I2C_t i2c, uint16_t devAddr, uint16_t memAddr);
int8_t BSP_I2C_MemWriteByte(BSP_I2C_t i2c, uint16_t devAddr, uint16_t memAddr,
                            uint8_t data);

int8_t BSP_I2C_MemRead(BSP_I2C_t i2c, uint16_t devAddr, uint16_t memAddr,
                       uint8_t *data, uint16_t size, bool dma);
int8_t BSP_I2C_MemWrite(BSP_I2C_t i2c, uint16_t devAddr, uint16_t memAddr,
                        uint8_t *data, uint16_t size, bool dma);

/* USER FUNCTION BEGIN */

/* USER FUNCTION END */

#ifdef __cplusplus
}
#endif
