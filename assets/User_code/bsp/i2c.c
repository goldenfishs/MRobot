/* Includes ----------------------------------------------------------------- */
#include "bsp\i2c.h"

/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */
static void (*I2C_Callback[BSP_I2C_NUM][BSP_I2C_CB_NUM])(void);

/* Private function  -------------------------------------------------------- */
static BSP_I2C_t I2C_Get(I2C_HandleTypeDef *hi2c) {
/* AUTO GENERATED I2C_GET */
  else
    return BSP_I2C_ERR;
}

void HAL_I2C_MasterTxCpltCallback(I2C_HandleTypeDef *hi2c) {
  BSP_I2C_t bsp_i2c = I2C_Get(hi2c);
  if (bsp_i2c != BSP_I2C_ERR) {
    if (I2C_Callback[bsp_i2c][HAL_I2C_MASTER_TX_CPLT_CB])
      I2C_Callback[bsp_i2c][HAL_I2C_MASTER_TX_CPLT_CB]();
  }
}

void HAL_I2C_MasterRxCpltCallback(I2C_HandleTypeDef *hi2c) {
  BSP_I2C_t bsp_i2c = I2C_Get(hi2c);
  if (bsp_i2c != BSP_I2C_ERR) {
    if (I2C_Callback[bsp_i2c][HAL_I2C_MASTER_RX_CPLT_CB])
      I2C_Callback[bsp_i2c][HAL_I2C_MASTER_RX_CPLT_CB]();
  }
}

void HAL_I2C_SlaveTxCpltCallback(I2C_HandleTypeDef *hi2c) {
  BSP_I2C_t bsp_i2c = I2C_Get(hi2c);
  if (bsp_i2c != BSP_I2C_ERR) {
    if (I2C_Callback[bsp_i2c][HAL_I2C_SLAVE_TX_CPLT_CB])
      I2C_Callback[bsp_i2c][HAL_I2C_SLAVE_TX_CPLT_CB]();
  }
}

void HAL_I2C_SlaveRxCpltCallback(I2C_HandleTypeDef *hi2c) {
  BSP_I2C_t bsp_i2c = I2C_Get(hi2c);
  if (bsp_i2c != BSP_I2C_ERR) {
    if (I2C_Callback[bsp_i2c][HAL_I2C_SLAVE_RX_CPLT_CB])
      I2C_Callback[bsp_i2c][HAL_I2C_SLAVE_RX_CPLT_CB]();
  }
}

void HAL_I2C_ListenCpltCallback(I2C_HandleTypeDef *hi2c) {
  BSP_I2C_t bsp_i2c = I2C_Get(hi2c);
  if (bsp_i2c != BSP_I2C_ERR) {
    if (I2C_Callback[bsp_i2c][HAL_I2C_LISTEN_CPLT_CB])
      I2C_Callback[bsp_i2c][HAL_I2C_LISTEN_CPLT_CB]();
  }
}

void HAL_I2C_MemTxCpltCallback(I2C_HandleTypeDef *hi2c) {
  BSP_I2C_t bsp_i2c = I2C_Get(hi2c);
  if (bsp_i2c != BSP_I2C_ERR) {
    if (I2C_Callback[bsp_i2c][HAL_I2C_MEM_TX_CPLT_CB])
      I2C_Callback[bsp_i2c][HAL_I2C_MEM_TX_CPLT_CB]();
  }
}

void HAL_I2C_MemRxCpltCallback(I2C_HandleTypeDef *hi2c) {
  BSP_I2C_t bsp_i2c = I2C_Get(hi2c);
  if (bsp_i2c != BSP_I2C_ERR) {
    if (I2C_Callback[bsp_i2c][HAL_I2C_MEM_RX_CPLT_CB])
      I2C_Callback[bsp_i2c][HAL_I2C_MEM_RX_CPLT_CB]();
  }
}

void HAL_I2C_ErrorCallback(I2C_HandleTypeDef *hi2c) {
  BSP_I2C_t bsp_i2c = I2C_Get(hi2c);
  if (bsp_i2c != BSP_I2C_ERR) {
    if (I2C_Callback[bsp_i2c][HAL_I2C_ERROR_CB])
      I2C_Callback[bsp_i2c][HAL_I2C_ERROR_CB]();
  }
}

void HAL_I2C_AbortCpltCallback(I2C_HandleTypeDef *hi2c) {
  BSP_I2C_t bsp_i2c = I2C_Get(hi2c);
  if (bsp_i2c != BSP_I2C_ERR) {
    if (I2C_Callback[bsp_i2c][HAL_I2C_ABORT_CPLT_CB])
      I2C_Callback[bsp_i2c][HAL_I2C_ABORT_CPLT_CB]();
  }
}

/* Exported functions ------------------------------------------------------- */
I2C_HandleTypeDef *BSP_I2C_GetHandle(BSP_I2C_t i2c) {
  switch (i2c) {
/* AUTO GENERATED BSP_I2C_GET_HANDLE */
    default:
      return NULL;
  }
}

int8_t BSP_I2C_RegisterCallback(BSP_I2C_t i2c, BSP_I2C_Callback_t type,
                                void (*callback)(void)) {
  if (callback == NULL) return BSP_ERR_NULL;
  I2C_Callback[i2c][type] = callback;
  return BSP_OK;
}

int8_t BSP_I2C_Transmit(BSP_I2C_t i2c, uint16_t devAddr, uint8_t *data,
                        uint16_t size, bool dma) {
  if (i2c >= BSP_I2C_NUM) return BSP_ERR;
  I2C_HandleTypeDef *hi2c = BSP_I2C_GetHandle(i2c);
  if (hi2c == NULL) return BSP_ERR;

  if (dma) {
    return HAL_I2C_Master_Transmit_DMA(hi2c, devAddr, data, size);
  } else {
    return HAL_I2C_Master_Transmit(hi2c, devAddr, data, size, 10);
  }
}

int8_t BSP_I2C_Receive(BSP_I2C_t i2c, uint16_t devAddr, uint8_t *data,
                       uint16_t size, bool dma) {
  if (i2c >= BSP_I2C_NUM) return BSP_ERR;
  I2C_HandleTypeDef *hi2c = BSP_I2C_GetHandle(i2c);
  if (hi2c == NULL) return BSP_ERR;

  if (dma) {
    return HAL_I2C_Master_Receive_DMA(hi2c, devAddr, data, size);
  } else {
    return HAL_I2C_Master_Receive(hi2c, devAddr, data, size, 10);
  }
}

uint8_t BSP_I2C_MemReadByte(BSP_I2C_t i2c, uint16_t devAddr, uint16_t memAddr) {
  if (i2c >= BSP_I2C_NUM) return 0xFF;
  I2C_HandleTypeDef *hi2c = BSP_I2C_GetHandle(i2c);
  if (hi2c == NULL) return 0xFF;

  uint8_t data;
  HAL_I2C_Mem_Read(hi2c, devAddr, memAddr, I2C_MEMADD_SIZE_16BIT, &data, 1, HAL_MAX_DELAY);
  return data;
}

int8_t BSP_I2C_MemWriteByte(BSP_I2C_t i2c, uint16_t devAddr, uint16_t memAddr,
                            uint8_t data) {
  if (i2c >= BSP_I2C_NUM) return BSP_ERR;
  I2C_HandleTypeDef *hi2c = BSP_I2C_GetHandle(i2c);
  if (hi2c == NULL) return BSP_ERR;

  return HAL_I2C_Mem_Write(hi2c, devAddr, memAddr, I2C_MEMADD_SIZE_16BIT, &data, 1, HAL_MAX_DELAY);
}

int8_t BSP_I2C_MemRead(BSP_I2C_t i2c, uint16_t devAddr, uint16_t memAddr,
                       uint8_t *data, uint16_t size, bool dma) {
  if (i2c >= BSP_I2C_NUM || data == NULL || size == 0) return BSP_ERR;
  I2C_HandleTypeDef *hi2c = BSP_I2C_GetHandle(i2c);
  if (hi2c == NULL) return BSP_ERR;

  if (dma) {
    return HAL_I2C_Mem_Read_DMA(hi2c, devAddr, memAddr, I2C_MEMADD_SIZE_16BIT, data, size);
  }
  else {
    return HAL_I2C_Mem_Read(hi2c, devAddr, memAddr, I2C_MEMADD_SIZE_16BIT, data, size, HAL_MAX_DELAY);
  }
}


int8_t BSP_I2C_MemWrite(BSP_I2C_t i2c, uint16_t devAddr, uint16_t memAddr,
                        uint8_t *data, uint16_t size, bool dma) {
  if (i2c >= BSP_I2C_NUM || data == NULL || size == 0) return BSP_ERR;
  I2C_HandleTypeDef *hi2c = BSP_I2C_GetHandle(i2c);
  if (hi2c == NULL) return BSP_ERR;

  if (dma) {
    return HAL_I2C_Mem_Write_DMA(hi2c, devAddr, memAddr, I2C_MEMADD_SIZE_16BIT, data, size);
  } else {
    return HAL_I2C_Mem_Write(hi2c, devAddr, memAddr, I2C_MEMADD_SIZE_16BIT, data, size, HAL_MAX_DELAY);
  }
}