#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

/* USER DEFINE BEGIN */

/* USER DEFINE END */

#define CRC8_INIT 0xFF

uint8_t CRC8_Calc(const uint8_t *buf, size_t len, uint8_t crc);
bool CRC8_Verify(const uint8_t *buf, size_t len);

/* USER FUNCTION BEGIN */

/* USER FUNCTION END */

#ifdef __cplusplus
}
#endif
