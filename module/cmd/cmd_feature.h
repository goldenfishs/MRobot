/*
 * CMD 模块 V2 - 功能特性开关配置
 *
 * 修改此文件来快速使能/失能各个模块和输入源。
 * 失能后，对应的代码和头文件依赖将被完全排除在编译之外。
 */
#pragma once

/* ========================================================================== */
/*                          输入源使能开关                                      */
/* ========================================================================== */

/** 遥控器输入 (DR16 / AT9S 等) */
#define CMD_ENABLE_SRC_RC    1

/** PC 端键鼠输入 (通过 DR16 转发) */
#define CMD_ENABLE_SRC_PC    1

/** NUC / AI 输入  */
#define CMD_ENABLE_SRC_NUC   1

/**
 * 裁判系统数据中转开关
 *  1 (比赛模式): cmd 将 referee 数据转发到各模块的 .ref 队列
 *  0 (调试模式): cmd 不转发，裁判系统可断开，不影响其他功能
 */
#define CMD_ENABLE_SRC_REF   1

/* ========================================================================== */
/*                          输出模块使能开关                                    */
/* ========================================================================== */

/** 底盘模块 (需要 module/chassis.h) */
#define CMD_ENABLE_MODULE_CHASSIS  0

/** 云台模块 (需要 module/gimbal.h) */
#define CMD_ENABLE_MODULE_GIMBAL   1

/** 射击模块 (需要 module/shoot.h) */
#define CMD_ENABLE_MODULE_SHOOT    1

/** 履带模块 (需要 module/track.h) */
#define CMD_ENABLE_MODULE_TRACK    0

/** 机械臂模块 (需要 component/arm_kinematics/arm6dof.h) */
#define CMD_ENABLE_MODULE_ARM      0

/** 裁判系统UI命令模块 (需要 device/referee.h) */
#define CMD_ENABLE_MODULE_REFUI    1

/** 平衡底盘模块 (需要 module/balance_chassis.h) */
#define CMD_ENABLE_MODULE_BALANCE_CHASSIS  1

/* ========================================================================== */
/*                          合法性检查                                          */
/* ========================================================================== */

/* PC输入源依赖RC适配器共同存在（DR16同时提供RC和PC数据） */
#if CMD_ENABLE_SRC_PC && !CMD_ENABLE_SRC_RC
  #error "CMD_ENABLE_SRC_PC requires CMD_ENABLE_SRC_RC (both share the DR16 adapter)"
#endif

/* NUC依赖vision_bridge模块，确保已包含相关模块 */
/* #if CMD_ENABLE_SRC_NUC && !defined(VISION_BRIDGE_ENABLED)
  #error "CMD_ENABLE_SRC_NUC requires vision_bridge module"
#endif */
