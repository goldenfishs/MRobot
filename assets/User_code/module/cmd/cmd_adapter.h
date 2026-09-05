/*
 * CMD 模块 V2 - 输入适配器接口
 * 定义设备到统一输入结构的转换接口
 */
#pragma once

#include "cmd_types.h"

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================== */
/*                           适配器接口定义                                     */
/* ========================================================================== */

/* 适配器操作函数指针类型 */
typedef int8_t (*CMD_AdapterInitFunc)(void *device_data);
typedef int8_t (*CMD_AdapterGetInputFunc)(void *device_data, CMD_RawInput_t *output);
typedef bool   (*CMD_AdapterIsOnlineFunc)(void *device_data);

/* 适配器描述结构 */
typedef struct {
    const char *name;                   /* 适配器名称 */
    CMD_InputSource_t source;           /* 对应的输入源 */
    void *device_data;                  /* 设备数据指针 */
    CMD_AdapterInitFunc init;           /* 初始化函数 */
    CMD_AdapterGetInputFunc get_input;  /* 获取输入函数 */
    CMD_AdapterIsOnlineFunc is_online;  /* 在线检测函数 */
} CMD_InputAdapter_t;

/* ========================================================================== */
/*                           适配器注册宏                                       */
/* ========================================================================== */

/* 
 * 声明适配器
 * 使用示例:
 * CMD_DECLARE_ADAPTER(DR16, dr16, DR16_t)
 * 
 * 会生成:
 * - extern DR16_t dr16;  // 设备实例声明
 * - int8_t CMD_DR16_Init(void *data);
 * - int8_t CMD_DR16_GetInput(void *data, CMD_RawInput_t *output);
 * - bool CMD_DR16_IsOnline(void *data);
 */
#define CMD_DECLARE_ADAPTER(NAME, var, TYPE) \
    extern TYPE var; \
    int8_t CMD_##NAME##_Init(void *data); \
    int8_t CMD_##NAME##_GetInput(void *data, CMD_RawInput_t *output); \
    bool CMD_##NAME##_IsOnline(void *data);

/* 
 * 定义适配器实例
 * 使用示例:
 * CMD_DEFINE_ADAPTER(DR16_RC, dr16, CMD_SRC_RC, CMD_DR16_Init, CMD_DR16_RC_GetInput, CMD_DR16_RC_IsOnline)
 */
#define CMD_DEFINE_ADAPTER(NAME, var, source_enum, init_func, get_func, online_func) \
    static CMD_InputAdapter_t g_adapter_##NAME = { \
        .name = #NAME, \
        .source = source_enum, \
        .device_data = (void*)&var, \
        .init = init_func, \
        .get_input = get_func, \
        .is_online = online_func, \
    };

/* ========================================================================== */
/*                        RC设备适配器配置                                      */
/* ========================================================================== */

/* 选择使用的RC设备 - 只需修改这里 */
#define CMD_RC_DEVICE_TYPE  0   /* 0:DR16, 1:AT9S, 2:VT13 */

#if CMD_RC_DEVICE_TYPE == 0
    #include "device/dr16.h"
    CMD_DECLARE_ADAPTER(DR16_RC, dr16, DR16_t)
    CMD_DECLARE_ADAPTER(DR16_PC, dr16, DR16_t)
    #define CMD_RC_ADAPTER_NAME DR16
    #define CMD_RC_ADAPTER_VAR  dr16
#elif CMD_RC_DEVICE_TYPE == 1
    #include "device/at9s_pro.h"
    CMD_DECLARE_ADAPTER(AT9S, at9s, AT9S_t)
    #define CMD_RC_ADAPTER_NAME AT9S
    #define CMD_RC_ADAPTER_VAR  at9s
#elif CMD_RC_DEVICE_TYPE == 2
    #include "device/vt13.h"
    CMD_DECLARE_ADAPTER(VT13, vt13, VT13_t)
    #define CMD_RC_ADAPTER_NAME VT13
    #define CMD_RC_ADAPTER_VAR  vt13
#endif

/* ========================================================================== */
/*                           适配器管理接口                                     */
/* ========================================================================== */

/* 初始化所有适配器 */
int8_t CMD_Adapter_InitAll(void);

/* 获取指定输入源的原始输入 */
int8_t CMD_Adapter_GetInput(CMD_InputSource_t source, CMD_RawInput_t *output);

/* 检查输入源是否在线 */
bool CMD_Adapter_IsOnline(CMD_InputSource_t source);

/* 注册适配器 (运行时注册，可选) */
int8_t CMD_Adapter_Register(CMD_InputAdapter_t *adapter);

#ifdef __cplusplus
}
#endif
