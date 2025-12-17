/*
 * CMD 模块 V2 - 行为处理器
 * 实现PC端按键到行为的映射和处理
 */
#pragma once

#include "cmd_types.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================== */
/*                           行为处理器接口                                     */
/* ========================================================================== */

/* 行为处理函数类型 */
struct CMD_Context;  /* 前向声明 */
typedef int8_t (*CMD_BehaviorHandler)(struct CMD_Context *ctx);

/* 行为配置项 */
typedef struct {
    CMD_Behavior_t behavior;      /* 行为枚举 */
    uint32_t key;                  /* 绑定的按键 */
    CMD_TriggerType_t trigger;    /* 触发类型 */
    CMD_ModuleMask_t module_mask; /* 影响的模块 */
    CMD_BehaviorHandler handler;  /* 处理函数 */
} CMD_BehaviorConfig_t;

/* ========================================================================== */
/*                           行为表生成宏                                       */
/* ========================================================================== */

/* 从宏表生成配置数组 */
#define BUILD_BEHAVIOR_CONFIG(name, key, trigger, mask) \
    { CMD_BEHAVIOR_##name, key, trigger, mask, CMD_Behavior_Handle_##name },

/* 声明所有行为处理函数 */
#define DECLARE_BEHAVIOR_HANDLER(name, key, trigger, mask) \
    int8_t CMD_Behavior_Handle_##name(struct CMD_Context *ctx);

/* 展开声明 */
CMD_BEHAVIOR_TABLE(DECLARE_BEHAVIOR_HANDLER)
#undef DECLARE_BEHAVIOR_HANDLER

/* ========================================================================== */
/*                           行为处理器API                                      */
/* ========================================================================== */

/* 初始化行为处理器 */
int8_t CMD_Behavior_Init(void);

/* 检查行为是否被触发 */
bool CMD_Behavior_IsTriggered(const CMD_RawInput_t *current, 
                               const CMD_RawInput_t *last,
                               const CMD_BehaviorConfig_t *config);

/* 处理所有触发的行为 */
int8_t CMD_Behavior_ProcessAll(struct CMD_Context *ctx,
                                const CMD_RawInput_t *current,
                                const CMD_RawInput_t *last,
                                CMD_ModuleMask_t active_modules);

/* 获取行为配置 */
const CMD_BehaviorConfig_t* CMD_Behavior_GetConfig(CMD_Behavior_t behavior);

#ifdef __cplusplus
}
#endif
