/* Includes ----------------------------------------------------------------- */
#include <spi.h>
#include "bsp/spi.h"

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

/* Private define ----------------------------------------------------------- */
/* USER DEFINE BEGIN */

/* USER DEFINE END */

/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* USER STRUCT BEGIN */

/* USER STRUCT END */

/* Private variables -------------------------------------------------------- */
static void (*SPI_Callback[BSP_SPI_NUM][BSP_SPI_CB_NUM])(void);

/* Private function  -------------------------------------------------------- */
static BSP_SPI_t SPI_Get(SPI_HandleTypeDef *hspi) {
/* AUTO GENERATED SPI_GET */
  else
    return BSP_SPI_ERR;
}

void HAL_SPI_TxCpltCallback(SPI_HandleTypeDef *hspi) {
  BSP_SPI_t bsp_spi = SPI_Get(hspi);
  if (bsp_spi != BSP_SPI_ERR) {
    if (SPI_Callback[bsp_spi][BSP_SPI_TX_CPLT_CB]) {
      SPI_Callback[bsp_spi][BSP_SPI_TX_CPLT_CB]();
    }
  }
}

void HAL_SPI_RxCpltCallback(SPI_HandleTypeDef *hspi) {
  BSP_SPI_t bsp_spi = SPI_Get(hspi);
  if (bsp_spi != BSP_SPI_ERR) {
    if (SPI_Callback[SPI_Get(hspi)][BSP_SPI_RX_CPLT_CB])
      SPI_Callback[SPI_Get(hspi)][BSP_SPI_RX_CPLT_CB]();
  }
}

void HAL_SPI_TxRxCpltCallback(SPI_HandleTypeDef *hspi) {
  BSP_SPI_t bsp_spi = SPI_Get(hspi);
  if (bsp_spi != BSP_SPI_ERR) {
    if (SPI_Callback[SPI_Get(hspi)][BSP_SPI_TX_RX_CPLT_CB])
      SPI_Callback[SPI_Get(hspi)][BSP_SPI_TX_RX_CPLT_CB]();
  }
}

void HAL_SPI_TxHalfCpltCallback(SPI_HandleTypeDef *hspi) {
  BSP_SPI_t bsp_spi = SPI_Get(hspi);
  if (bsp_spi != BSP_SPI_ERR) {
    if (SPI_Callback[SPI_Get(hspi)][BSP_SPI_TX_HALF_CPLT_CB])
      SPI_Callback[SPI_Get(hspi)][BSP_SPI_TX_HALF_CPLT_CB]();
  }
}

void HAL_SPI_RxHalfCpltCallback(SPI_HandleTypeDef *hspi) {
  BSP_SPI_t bsp_spi = SPI_Get(hspi);
  if (bsp_spi != BSP_SPI_ERR) {
    if (SPI_Callback[SPI_Get(hspi)][BSP_SPI_RX_HALF_CPLT_CB])
      SPI_Callback[SPI_Get(hspi)][BSP_SPI_RX_HALF_CPLT_CB]();
  }
}

void HAL_SPI_TxRxHalfCpltCallback(SPI_HandleTypeDef *hspi) {
  BSP_SPI_t bsp_spi = SPI_Get(hspi);
  if (bsp_spi != BSP_SPI_ERR) {
    if (SPI_Callback[SPI_Get(hspi)][BSP_SPI_TX_RX_HALF_CPLT_CB])
      SPI_Callback[SPI_Get(hspi)][BSP_SPI_TX_RX_HALF_CPLT_CB]();
  }
}

void HAL_SPI_ErrorCallback(SPI_HandleTypeDef *hspi) {
  BSP_SPI_t bsp_spi = SPI_Get(hspi);
  if (bsp_spi != BSP_SPI_ERR) {
    if (SPI_Callback[SPI_Get(hspi)][BSP_SPI_ERROR_CB])
      SPI_Callback[SPI_Get(hspi)][BSP_SPI_ERROR_CB]();
  }
}

void HAL_SPI_AbortCpltCallback(SPI_HandleTypeDef *hspi) {
  BSP_SPI_t bsp_spi = SPI_Get(hspi);
  if (bsp_spi != BSP_SPI_ERR) {
    if (SPI_Callback[SPI_Get(hspi)][BSP_SPI_ABORT_CPLT_CB])
      SPI_Callback[SPI_Get(hspi)][BSP_SPI_ABORT_CPLT_CB]();
  }
}

/* Exported functions ------------------------------------------------------- */
SPI_HandleTypeDef *BSP_SPI_GetHandle(BSP_SPI_t spi) {
  switch (spi) {
/* AUTO GENERATED BSP_SPI_GET_HANDLE */
    default:
      return NULL;
  }
}

int8_t BSP_SPI_RegisterCallback(BSP_SPI_t spi, BSP_SPI_Callback_t type,
                                void (*callback)(void)) {
  if (callback == NULL) return BSP_ERR_NULL;
  SPI_Callback[spi][type] = callback;
  return BSP_OK;
}

int8_t BSP_SPI_Transmit(BSP_SPI_t spi, uint8_t *data, uint16_t size, bool dma) {
  if (spi >= BSP_SPI_NUM) return BSP_ERR;
  SPI_HandleTypeDef *hspi = BSP_SPI_GetHandle(spi);
  if (hspi == NULL) return BSP_ERR;

  if (dma) {
    return HAL_SPI_Transmit_DMA(hspi, data, size)!= HAL_OK;;
  } else {
    return HAL_SPI_Transmit(hspi, data, size, 20)!= HAL_OK;;
  }
}

int8_t BSP_SPI_Receive(BSP_SPI_t spi, uint8_t *data, uint16_t size, bool dma) {
  if (spi >= BSP_SPI_NUM) return BSP_ERR;
  SPI_HandleTypeDef *hspi = BSP_SPI_GetHandle(spi);
  if (hspi == NULL) return BSP_ERR;

  if (dma) {
    return HAL_SPI_Receive_DMA(hspi, data, size)!= HAL_OK;;
  } else {
    return HAL_SPI_Receive(hspi, data, size, 20)!= HAL_OK;;
  }
}

int8_t BSP_SPI_TransmitReceive(BSP_SPI_t spi, uint8_t *txData, uint8_t *rxData,
                               uint16_t size, bool dma) {
  if (spi >= BSP_SPI_NUM) return BSP_ERR;
  SPI_HandleTypeDef *hspi = BSP_SPI_GetHandle(spi);
  if (hspi == NULL) return BSP_ERR;
  
  if (dma) {
    return HAL_SPI_TransmitReceive_DMA(hspi, txData, rxData, size)!= HAL_OK;;
  } else {
    return HAL_SPI_TransmitReceive(hspi, txData, rxData, size, 20)!= HAL_OK;;
  }
}

uint8_t BSP_SPI_MemReadByte(BSP_SPI_t spi, uint8_t reg) {
  if (spi >= BSP_SPI_NUM) return 0xFF;
  uint8_t tmp[2] = {reg | 0x80, 0x00};
  BSP_SPI_TransmitReceive(spi, tmp, tmp, 2u, true);
  return tmp[1];
}

int8_t BSP_SPI_MemWriteByte(BSP_SPI_t spi, uint8_t reg, uint8_t data) {
  if (spi >= BSP_SPI_NUM) return BSP_ERR;
  uint8_t tmp[2] = {reg & 0x7f, data};
  return BSP_SPI_Transmit(spi, tmp, 2u, true);
}

int8_t BSP_SPI_MemRead(BSP_SPI_t spi, uint8_t reg, uint8_t *data, uint16_t size) {
  if (spi >= BSP_SPI_NUM) return BSP_ERR;
  if (data == NULL || size == 0) return BSP_ERR_NULL;
  reg = reg | 0x80;
  BSP_SPI_Transmit(spi, &reg, 1u, true);
  return BSP_SPI_Receive(spi, data, size, true);
}

int8_t BSP_SPI_MemWrite(BSP_SPI_t spi, uint8_t reg, uint8_t *data, uint16_t size) {
  if (spi >= BSP_SPI_NUM) return BSP_ERR;
  if (data == NULL || size == 0) return BSP_ERR_NULL;
  reg = reg & 0x7f;
  BSP_SPI_Transmit(spi, &reg, 1u, true);
  return BSP_SPI_Transmit(spi, data, size, true);
}

/* USER FUNCTION BEGIN */

/* USER FUNCTION END */
