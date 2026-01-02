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
#if defined(STM32H7)
    flash_erase.Banks = FLASH_BANK_1;  // H7 requires Bank parameter
#endif

    HAL_FLASH_Unlock();
#if defined(STM32H7)
    while (FLASH_WaitForLastOperation(50, FLASH_BANK_1) != HAL_OK)
      ;
#else
    while (FLASH_WaitForLastOperation(50) != HAL_OK)
      ;
#endif
    HAL_FLASHEx_Erase(&flash_erase, &sector_error);
    HAL_FLASH_Lock();
  }
  /* USER CODE BEGIN FLASH_ERASE_END */
  /* USER CODE END FLASH_ERASE_END */
}

void BSP_Flash_WriteBytes(uint32_t address, const uint8_t *buf, size_t len) {
  HAL_FLASH_Unlock();
#if defined(STM32H7)
  // H7 uses FLASHWORD (32 bytes) programming
  uint8_t flash_word[32] __attribute__((aligned(32)));
  while (len > 0) {
    size_t chunk = (len < 32) ? len : 32;
    memset(flash_word, 0xFF, 32);
    memcpy(flash_word, buf, chunk);
    
    while (FLASH_WaitForLastOperation(50, FLASH_BANK_1) != HAL_OK)
      ;
    HAL_FLASH_Program(FLASH_TYPEPROGRAM_FLASHWORD, address, (uint32_t)flash_word);
    
    address += 32;
    buf += chunk;
    len -= chunk;
  }
#else
  // F4/F7 use byte programming
  while (len > 0) {
    while (FLASH_WaitForLastOperation(50) != HAL_OK)
      ;
    HAL_FLASH_Program(FLASH_TYPEPROGRAM_BYTE, address, *buf);
    address++;
    buf++;
    len--;
  }
#endif
  HAL_FLASH_Lock();
}

void BSP_Flash_ReadBytes(uint32_t address, void *buf, size_t len) {
  memcpy(buf, (void *)address, len);
}
