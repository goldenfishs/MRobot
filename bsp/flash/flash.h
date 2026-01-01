#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------ */
#include <main.h>

#include "bsp/bsp.h"

/* Exported constants -------------------------------------------------------- */
/* Base address of the Flash sectors */
/* USER CODE BEGIN FLASH_SECTOR_DEFINES */
/* AUTO GENERATED FLASH_SECTORS */
/* USER CODE END FLASH_SECTOR_DEFINES */

/* USER CODE BEGIN FLASH_END_ADDRESS */
/* AUTO GENERATED FLASH_END_ADDRESS */
/* USER CODE END FLASH_END_ADDRESS */

/* Exported macro ------------------------------------------------------------ */
/* Exported types ------------------------------------------------------------ */
/* Exported functions prototypes --------------------------------------------- */
void BSP_Flash_EraseSector(uint32_t sector);
void BSP_Flash_WriteBytes(uint32_t address, const uint8_t *buf, size_t len);
void BSP_Flash_ReadBytes(uint32_t address, void *buf, size_t len);

#ifdef __cplusplus
}
#endif
