#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include <spi.h>
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

/* 要添加使用SPI的新设备，需要先在此添加对应的枚举值 */

/* SPI实体枚举，与设备对应 */
typedef enum {
/* AUTO GENERATED BSP_SPI_NAME */
  BSP_SPI_NUM,
  BSP_SPI_ERR,
} BSP_SPI_t;

/* SPI支持的中断回调函数类型，具体参考HAL中定义 */
typedef enum {
  BSP_SPI_TX_CPLT_CB,
  BSP_SPI_RX_CPLT_CB,
  BSP_SPI_TX_RX_CPLT_CB,
  BSP_SPI_TX_HALF_CPLT_CB,
  BSP_SPI_RX_HALF_CPLT_CB,
  BSP_SPI_TX_RX_HALF_CPLT_CB,
  BSP_SPI_ERROR_CB,
  BSP_SPI_ABORT_CPLT_CB,
  BSP_SPI_CB_NUM,
} BSP_SPI_Callback_t;

/* Exported functions prototypes -------------------------------------------- */
SPI_HandleTypeDef *BSP_SPI_GetHandle(BSP_SPI_t spi);
int8_t BSP_SPI_RegisterCallback(BSP_SPI_t spi, BSP_SPI_Callback_t type,
                                void (*callback)(void));


int8_t BSP_SPI_Transmit(BSP_SPI_t spi, uint8_t *data, uint16_t size, bool dma);
int8_t BSP_SPI_Receive(BSP_SPI_t spi, uint8_t *data, uint16_t size, bool dma);
int8_t BSP_SPI_TransmitReceive(BSP_SPI_t spi, uint8_t *txData, uint8_t *rxData,
                               uint16_t size, bool dma);

uint8_t BSP_SPI_MemReadByte(BSP_SPI_t spi, uint8_t reg);
int8_t BSP_SPI_MemWriteByte(BSP_SPI_t spi, uint8_t reg, uint8_t data);
int8_t BSP_SPI_MemRead(BSP_SPI_t spi, uint8_t reg, uint8_t *data, uint16_t size);
int8_t BSP_SPI_MemWrite(BSP_SPI_t spi, uint8_t reg, uint8_t *data, uint16_t size);

/* USER FUNCTION BEGIN */

/* USER FUNCTION END */

#ifdef __cplusplus
}
#endif
