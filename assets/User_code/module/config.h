/*
 * 配置相关
 */

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

typedef struct {
    
} Config_RobotParam_t;

/* Exported functions prototypes -------------------------------------------- */

/**
 * @brief 获取机器人配置参数
 * @return 机器人配置参数指针
 */
Config_RobotParam_t* Config_GetRobotParam(void);

#ifdef __cplusplus
}
#endif
