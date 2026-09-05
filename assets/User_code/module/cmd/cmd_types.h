/*
 * CMD 模块 V2 - 类型定义
 * 统一的输入/输出抽象层
 */
#pragma once

#include <stdint.h>
#include <stdbool.h>

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
 * 使用方法：在config中定义需要启用的输入源
 * 格式: X(枚举名, 优先级, 适配器初始化函数, 获取数据函数)
 */
#define CMD_INPUT_SOURCE_TABLE(X) \
    X(RC,  CMD_RC_AdapterInit,  CMD_RC_GetInput)  \
    X(PC,  CMD_PC_AdapterInit,  CMD_PC_GetInput)  \
    X(NUC, CMD_NUC_AdapterInit, CMD_NUC_GetInput) \
    X(REF, CMD_REF_AdapterInit, CMD_REF_GetInput)

/* 输出模块配置宏表 */
#define CMD_OUTPUT_MODULE_TABLE(X) \
    X(CHASSIS, Chassis_CMD_t, chassis) \
    X(GIMBAL,  Gimbal_CMD_t,  gimbal)  \
    X(SHOOT,   Shoot_CMD_t,   shoot)


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

/* 裁判系统数据 */
typedef struct {
    uint8_t game_status;       /* 比赛状态 */
} CMD_Referee_t;

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

typedef struct {
  int a;
} CMD_RawInput_NUC_t;

typedef struct {
  CMD_Referee_t referee;
} CMD_RawInput_REF_t;

/* 统一的原始输入结构 - 所有设备适配后都转换成这个格式 */
typedef struct {
    bool online[CMD_SRC_NUM];

    /* 遥控器部分 */
    CMD_RawInput_RC_t rc;

    /* PC部分 */
    CMD_RawInput_PC_t pc;

    /* NUC部分 */
    /* 暂无定义，预留扩展 */
    CMD_RawInput_NUC_t nuc;

    /* REF部分 - 裁判系统数据 */
    CMD_RawInput_REF_t ref;
} CMD_RawInput_t;

/* ========================================================================== */
/*                              模块掩码                                        */
/* ========================================================================== */
typedef enum {
    CMD_MODULE_NONE    = (1 << 0),
    CMD_MODULE_CHASSIS = (1 << 1),
    CMD_MODULE_GIMBAL  = (1 << 2),
    CMD_MODULE_SHOOT   = (1 << 3),
    CMD_MODULE_ALL     = 0x0E
} CMD_ModuleMask_t;

/* ========================================================================== */
/*                              行为定义                                        */
/* ========================================================================== */
/* 行为-按键映射宏表 */
#define BEHAVIOR_CONFIG_COUNT (11)
#define CMD_BEHAVIOR_TABLE(X) \
  X(FORE,           CMD_KEY_W,     CMD_ACTIVE_PRESSED,      CMD_MODULE_CHASSIS) \
  X(BACK,           CMD_KEY_S,     CMD_ACTIVE_PRESSED,      CMD_MODULE_CHASSIS) \
  X(LEFT,           CMD_KEY_A,     CMD_ACTIVE_PRESSED,      CMD_MODULE_CHASSIS) \
  X(RIGHT,          CMD_KEY_D,     CMD_ACTIVE_PRESSED,      CMD_MODULE_CHASSIS) \
  X(ACCELERATE,     CMD_KEY_SHIFT, CMD_ACTIVE_PRESSED,      CMD_MODULE_CHASSIS) \
  X(DECELERATE,     CMD_KEY_CTRL,  CMD_ACTIVE_PRESSED,      CMD_MODULE_CHASSIS) \
  X(FIRE,           CMD_KEY_L_CLICK,  CMD_ACTIVE_PRESSED,      CMD_MODULE_SHOOT)   \
  X(FIRE_MODE,      CMD_KEY_B,     CMD_ACTIVE_RISING_EDGE,  CMD_MODULE_SHOOT)   \
  X(ROTOR,          CMD_KEY_E,     CMD_ACTIVE_PRESSED,  CMD_MODULE_CHASSIS) \
  X(AUTOAIM,        CMD_KEY_R,     CMD_ACTIVE_RISING_EDGE,  CMD_MODULE_GIMBAL | CMD_MODULE_SHOOT) \
  X(CHECKSOURCERCPC, CMD_KEY_CTRL|CMD_KEY_SHIFT|CMD_KEY_V, CMD_ACTIVE_RISING_EDGE, CMD_MODULE_NONE)
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
