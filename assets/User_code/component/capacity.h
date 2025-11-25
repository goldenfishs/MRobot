/*
  剩余电量算法。

  通过电压值计算剩余电量。
*/

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include "user_math.h"

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

/* USER DEFINE BEGIN */

/* USER DEFINE END */

/**
 * @brief 通过电压计算电池剩余电量
 *
 * @param volt 电压值
 * @return float 剩余电量比例
 */
float Capacity_GetBatteryRemain(float volt);

/**
 * @brief
 *
 * @param vcap 电容电压
 * @param vbat 电池电压
 * @param v_cutoff 截止电压
 * @return float 电容剩余电量比例
 */
float Capacity_GetCapacitorRemain(float vcap, float vbat, float v_cutoff);

/* USER FUNCTION BEGIN */

/* USER FUNCTION END */

#ifdef __cplusplus
}
#endif
