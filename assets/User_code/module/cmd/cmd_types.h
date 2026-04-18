/*
 * CMD 模块 V2 - 类型定义
 * 统一的输入/输出抽象层
 */
#pragma once

#include <stdint.h>
#include <stdbool.h>
#include "cmd_feature.h"          /* 功能特性开关 */

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================== */
/*                              错误码定义                                      */
/* ========================================================================== */
#define CMD_OK           (0)
#define CMD_ERR_NULL     (-1)
#define CMD_ERR_MODE     (-2)
#define CMD_ERR_SOURCE   (-3)
#define CMD_ERR_NO_INPUT (-4)

/* ========================================================================== */
/*                            输入源配置宏表                                    */
/* ========================================================================== */
/*
 * 使用方法：在 cmd_feature.h 中设置各 CMD_ENABLE_SRC_xxx 宏。
 * 格式: X(枚举名, 适配器初始化函数, 获取数据函数)
 */

/* 各输入源条件展开辅助宏 */
#if CMD_ENABLE_SRC_RC
  #define _X_SRC_RC(X)   X(RC,  CMD_RC_AdapterInit,  CMD_RC_GetInput)
#else
  #define _X_SRC_RC(X)
#endif

#if CMD_ENABLE_SRC_PC
  #define _X_SRC_PC(X)   X(PC,  CMD_PC_AdapterInit,  CMD_PC_GetInput)
#else
  #define _X_SRC_PC(X)
#endif

#if CMD_ENABLE_SRC_NUC
  #define _X_SRC_NUC(X)  X(NUC, CMD_NUC_AdapterInit, CMD_NUC_GetInput)
#else
  #define _X_SRC_NUC(X)
#endif

#if CMD_ENABLE_SRC_REF
  #define _X_SRC_REF(X)  X(REF, CMD_REF_AdapterInit, CMD_REF_GetInput)
#else
  #define _X_SRC_REF(X)
#endif

#define CMD_INPUT_SOURCE_TABLE(X) \
    _X_SRC_RC(X)  \
    _X_SRC_PC(X)  \
    _X_SRC_NUC(X) \
    _X_SRC_REF(X)

/* 各输出模块条件展开辅助宏 */
#if CMD_ENABLE_MODULE_CHASSIS
  #define _X_MOD_CHASSIS(X)  X(CHASSIS, Chassis_CMD_t, chassis)
#else
  #define _X_MOD_CHASSIS(X)
#endif

#if CMD_ENABLE_MODULE_GIMBAL
  #define _X_MOD_GIMBAL(X)   X(GIMBAL,  Gimbal_CMD_t,  gimbal)
#else
  #define _X_MOD_GIMBAL(X)
#endif

#if CMD_ENABLE_MODULE_SHOOT
  #define _X_MOD_SHOOT(X)    X(SHOOT,   Shoot_CMD_t,   shoot)
#else
  #define _X_MOD_SHOOT(X)
#endif

#if CMD_ENABLE_MODULE_TRACK
  #define _X_MOD_TRACK(X)    X(TRACK,   Track_CMD_t,   track)
#else
  #define _X_MOD_TRACK(X)
#endif

#if CMD_ENABLE_MODULE_ARM
  #define _X_MOD_ARM(X)      X(ARM,     Arm_CMD_t,     arm)
#else
  #define _X_MOD_ARM(X)
#endif

#if CMD_ENABLE_MODULE_REFUI
  #define _X_MOD_REFUI(X)    X(REFUI,   Referee_UI_CMD_t, refui)
#else
  #define _X_MOD_REFUI(X)
#endif

#if CMD_ENABLE_MODULE_BALANCE_CHASSIS
  #define _X_MOD_BALANCE_CHASSIS(X)  X(BALANCE_CHASSIS, Chassis_CMD_t, balance_chassis)
#else
  #define _X_MOD_BALANCE_CHASSIS(X)
#endif

/* 输出模块配置宏表 */
#define CMD_OUTPUT_MODULE_TABLE(X) \
    _X_MOD_CHASSIS(X) \
    _X_MOD_GIMBAL(X)  \
    _X_MOD_SHOOT(X)   \
    _X_MOD_TRACK(X)   \
    _X_MOD_ARM(X)     \
    _X_MOD_REFUI(X)   \
    _X_MOD_BALANCE_CHASSIS(X) \

/* ========================================================================== */
/*                              输入源枚举                                      */
/* ========================================================================== */
#define ENUM_INPUT_SOURCE(name, ...) CMD_SRC_##name,
typedef enum {
    CMD_INPUT_SOURCE_TABLE(ENUM_INPUT_SOURCE)
    CMD_SRC_NUM
} CMD_InputSource_t;
#undef ENUM_INPUT_SOURCE

/* ========================================================================== */
/*                            统一输入数据结构                                  */
/* ========================================================================== */

/* 摇杆数据 - 统一为-1.0 ~ 1.0 */
typedef struct {
    float x;
    float y;
} CMD_Joystick_t;

/* 开关位置 */
typedef enum {
    CMD_SW_ERR = 0,
    CMD_SW_UP,
    CMD_SW_MID,
    CMD_SW_DOWN,
} CMD_SwitchPos_t;

/* 鼠标数据 */
typedef struct {
    int16_t x;      /* 鼠标X轴移动速度 */
    int16_t y;      /* 鼠标Y轴移动速度 */
    int16_t z;      /* 鼠标滚轮 */
    bool l_click;   /* 左键 */
    bool r_click;   /* 右键 */
    bool m_click;   /* 中键 */
} CMD_Mouse_t;

/* 键盘数据 - 最多支持32个按键 */
typedef struct {
    uint32_t bitmap;  /* 按键位图 */
} CMD_Keyboard_t;

/* 键盘按键索引 */
typedef enum {
    CMD_KEY_W = (1 << 0), CMD_KEY_S = (1 << 1), CMD_KEY_A = (1 << 2), CMD_KEY_D = (1 << 3),
    CMD_KEY_SHIFT = (1 << 4), CMD_KEY_CTRL = (1 << 5), CMD_KEY_Q = (1 << 6), CMD_KEY_E = (1 << 7),
    CMD_KEY_R = (1 << 8), CMD_KEY_F = (1 << 9), CMD_KEY_G = (1 << 10), CMD_KEY_Z = (1 << 11),
    CMD_KEY_X = (1 << 12), CMD_KEY_C = (1 << 13), CMD_KEY_V = (1 << 14), CMD_KEY_B = (1 << 15),
    CMD_KEY_NUM
} CMD_KeyIndex_t;

typedef struct {
  CMD_Joystick_t joy_left;   /* 左摇杆 */
  CMD_Joystick_t joy_right;  /* 右摇杆 */
  CMD_SwitchPos_t sw[4];     /* 4个拨杆 */
  float dial;                /* 拨轮 */
} CMD_RawInput_RC_t;

typedef struct {
  CMD_Mouse_t mouse;
  CMD_Keyboard_t keyboard;
} CMD_RawInput_PC_t;

/* AI输入数据 */
typedef struct {
  uint8_t mode;
  struct {
    struct {
      float yaw;
      float pit;
    } setpoint;
    struct {
      float pit;
      float yaw;
    } accl;
    struct {
      float pit;
      float yaw;
    } vel;
  } gimbal;
} CMD_RawInput_NUC_t;

#if CMD_ENABLE_SRC_REF
#include "device/referee_proto_types.h" 
/* 裁判系统原始输入，包含需转发给各模块的完整子集 */
typedef struct {
    Referee_ForChassis_t chassis;
    Referee_ForShoot_t   shoot;
    Referee_ForCap_t     cap;
    Referee_ForAI_t      ai;
} CMD_RawInput_REF_t;
#endif

/* 统一的原始输入结构 - 所有设备适配后都转换成这个格式 */
typedef struct {
    bool online[CMD_SRC_NUM];

#if CMD_ENABLE_SRC_RC
    /* 遥控器部分 */
    CMD_RawInput_RC_t rc;
#endif

#if CMD_ENABLE_SRC_PC
    /* PC部分 */
    CMD_RawInput_PC_t pc;
#endif

#if CMD_ENABLE_SRC_NUC
    /* NUC部分 */
    CMD_RawInput_NUC_t nuc;
#endif

#if CMD_ENABLE_SRC_REF
    /* REF部分 - 裁判系统数据 */
    CMD_RawInput_REF_t ref;
#endif
} CMD_RawInput_t;

/* ========================================================================== */
/*                              模块掩码                                        */
/* ========================================================================== */
typedef enum {
    CMD_MODULE_NONE            = (1 << 0),
    CMD_MODULE_CHASSIS         = (1 << 1),
    CMD_MODULE_GIMBAL          = (1 << 2),
    CMD_MODULE_SHOOT           = (1 << 3),
    CMD_MODULE_TRACK           = (1 << 4),
    CMD_MODULE_ARM             = (1 << 5),
    CMD_MODULE_REFUI           = (1 << 6),
    CMD_MODULE_BALANCE_CHASSIS = (1 << 7),
    CMD_MODULE_ALL             = 0xFE

} CMD_ModuleMask_t;

/* ========================================================================== */
/*                              行为定义                                        */
/* ========================================================================== */
/* 行为-按键映射宏表 */
#define BEHAVIOR_CONFIG_COUNT (12)
#define CMD_BEHAVIOR_TABLE(X) \
  X(FORE,           CMD_KEY_W,     CMD_ACTIVE_PRESSED,      CMD_MODULE_BALANCE_CHASSIS) \
  X(BACK,           CMD_KEY_S,     CMD_ACTIVE_PRESSED,      CMD_MODULE_BALANCE_CHASSIS) \
  X(LEFT,           CMD_KEY_A,     CMD_ACTIVE_PRESSED,      CMD_MODULE_BALANCE_CHASSIS) \
  X(RIGHT,          CMD_KEY_D,     CMD_ACTIVE_PRESSED,      CMD_MODULE_BALANCE_CHASSIS) \
  X(ACCELERATE,     CMD_KEY_SHIFT, CMD_ACTIVE_PRESSED,      CMD_MODULE_BALANCE_CHASSIS) \
  X(ROTOR,          CMD_KEY_CTRL,  CMD_ACTIVE_PRESSED,      CMD_MODULE_BALANCE_CHASSIS) \
  X(FIRE,           CMD_KEY_L_CLICK,  CMD_ACTIVE_PRESSED,   CMD_MODULE_SHOOT)   \
  X(FIRE_MODE,      CMD_KEY_B,     CMD_ACTIVE_RISING_EDGE,  CMD_MODULE_SHOOT)   \
  X(CLIMB,          CMD_KEY_R,     CMD_ACTIVE_PRESSED,      CMD_MODULE_BALANCE_CHASSIS) \
  X(AUTOAIM,        CMD_KEY_R_CLICK,     CMD_ACTIVE_PRESSED,  CMD_MODULE_NONE) \
  X(CHECKSOURCERCPC,CMD_KEY_CTRL|CMD_KEY_SHIFT|CMD_KEY_V, CMD_ACTIVE_RISING_EDGE, CMD_MODULE_NONE) \
  X(RESET,          CMD_KEY_CTRL|CMD_KEY_SHIFT|CMD_KEY_G,     CMD_ACTIVE_RISING_EDGE,      CMD_MODULE_NONE)
/* 触发类型 */
typedef enum {
    CMD_ACTIVE_PRESSED,       /* 按住时触发 */
    CMD_ACTIVE_RISING_EDGE,   /* 按下瞬间触发 */
    CMD_ACTIVE_FALLING_EDGE,  /* 松开瞬间触发 */
} CMD_TriggerType_t;

/* 特殊按键值 */
#define CMD_KEY_NONE      0xFF
#define CMD_KEY_L_CLICK   (1 << 31)
#define CMD_KEY_R_CLICK   (1 << 30)
#define CMD_KEY_M_CLICK   (1 << 29)

/* 行为枚举 - 由宏表自动生成 */
#define ENUM_BEHAVIOR(name, key, trigger, mask) CMD_BEHAVIOR_##name,
typedef enum {
    CMD_BEHAVIOR_TABLE(ENUM_BEHAVIOR)
    CMD_BEHAVIOR_NUM
} CMD_Behavior_t;
#undef ENUM_BEHAVIOR

/* ========================================================================== */
/*                           键盘辅助宏                                         */
/* ========================================================================== */
#define CMD_KEY_PRESSED(kb, key)   (((kb)->bitmap >> (key)) & 1)
#define CMD_KEY_SET(kb, key)       ((kb)->bitmap |= (1 << (key)))
#define CMD_KEY_CLEAR(kb, key)     ((kb)->bitmap &= ~(1 << (key)))


#ifdef __cplusplus
}
#endif
