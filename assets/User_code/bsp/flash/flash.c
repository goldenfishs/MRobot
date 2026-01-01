/* Includes ----------------------------------------------------------------- */
#include "bsp/flash.h"

#include <main.h>
#include <string.h>

/* Private define ----------------------------------------------------------- */
/* USER CODE BEGIN FLASH_MAX_SECTOR */
/* AUTO GENERATED FLASH_MAX_SECTOR */
/* USER CODE END FLASH_MAX_SECTOR */

/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */
/* Private function  -------------------------------------------------------- */
/* Exported functions ------------------------------------------------------- */

void BSP_Flash_EraseSector(uint32_t sector) {
  FLASH_EraseInitTypeDef flash_erase;
  uint32_t sector_error;

  /* USER CODE BEGIN FLASH_ERASE_CHECK */
  /* AUTO GENERATED FLASH_ERASE_CHECK */
  /* USER CODE END FLASH_ERASE_CHECK */
    flash_erase.Sector = sector;
    flash_erase.TypeErase = FLASH_TYPEERASE_SECTORS;
    flash_erase.VoltageRange = FLASH_VOLTAGE_RANGE_3;
    flash_erase.NbSectors = 1;

    HAL_FLASH_Unlock();
    while (FLASH_WaitForLastOperation(50) != HAL_OK)
      ;
    HAL_FLASHEx_Erase(&flash_erase, &sector_error);
    HAL_FLASH_Lock();
  }
  /* USER CODE BEGIN FLASH_ERASE_END */
  /* USER CODE END FLASH_ERASE_END */
}

void BSP_Flash_WriteBytes(uint32_t address, const uint8_t *buf, size_t len) {
  HAL_FLASH_Unlock();
  while (len > 0) {
    while (FLASH_WaitForLastOperation(50) != HAL_OK)
      ;
    HAL_FLASH_Program(FLASH_TYPEPROGRAM_BYTE, address, *buf);
    address++;
    buf++;
    len--;
  }
  HAL_FLASH_Lock();
}

void BSP_Flash_ReadBytes(uint32_t address, void *buf, size_t len) {
  memcpy(buf, (void *)address, len);
}
