#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>

#define CRC16_INIT 0XFFFF

uint16_t CRC16_Calc(const uint8_t *buf, size_t len, uint16_t crc);
bool CRC16_Verify(const uint8_t *buf, size_t len);

#ifdef __cplusplus
}
#endif
