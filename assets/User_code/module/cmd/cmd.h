/*
 * CMD 模块 V2 - 主控制模块
 * 统一的命令控制接口
 */
#pragma once

#include "cmd_types.h"
#include "cmd_adapter.h"
#include "cmd_behavior.h"

/* 引入输出模块的命令类型 */
#include "module/chassis.h"
#include "module/gimbal.h"
#include "module/shoot.h"
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================== */
/*                           输出命令结构                                       */
/* ========================================================================== */

/* 每个模块的输出包含源信息和命令 */
typedef struct {
    CMD_InputSource_t source;
    Chassis_CMD_t cmd;
} CMD_ChassisOutput_t;

typedef struct {
    CMD_InputSource_t source;
    Gimbal_CMD_t cmd;
} CMD_GimbalOutput_t;

typedef struct {
    CMD_InputSource_t source;
    Shoot_CMD_t cmd;
} CMD_ShootOutput_t;

/* ========================================================================== */
/*                           配置结构                                           */
/* ========================================================================== */

/* 灵敏度配置 */
typedef struct {
    float mouse_sens;       /* 鼠标灵敏度 */
    float move_sens;        /* 移动灵敏度 */
    float move_fast_mult;   /* 快速移动倍率 */
    float move_slow_mult;   /* 慢速移动倍率 */
} CMD_Sensitivity_t;

/* RC模式映射配置 - 定义开关位置到模式的映射 */
typedef struct {
    /* 左拨杆映射 - 底盘模式 */
    Chassis_Mode_t sw_left_up;
    Chassis_Mode_t sw_left_mid;
    Chassis_Mode_t sw_left_down;
    
    /* 右拨杆映射 - 云台/射击模式 */
    Gimbal_Mode_t gimbal_sw_up;
    Gimbal_Mode_t gimbal_sw_mid;
    Gimbal_Mode_t gimbal_sw_down;
} CMD_RCModeMap_t;

/* 整体配置 */
typedef struct {
    /* 输入源优先级，索引越小优先级越高 */
    CMD_InputSource_t source_priority[CMD_SRC_NUM];
    
    /* 灵敏度设置 */
    CMD_Sensitivity_t sensitivity;
    
    /* RC模式映射 */
    CMD_RCModeMap_t rc_mode_map;
    
} CMD_Config_t;

/* ========================================================================== */
/*                           主控制上下文                                       */
/* ========================================================================== */

typedef struct {
    float now;
    float dt;
    uint32_t last_us;
} CMD_Timer_t;

typedef struct CMD_Context {
    /* 配置 */
    CMD_Config_t *config;
    
    /* 时间 */
    CMD_Timer_t timer;
    
    /* 当前帧和上一帧的原始输入 */
    CMD_RawInput_t input;
    CMD_RawInput_t last_input;
    
    /* 仲裁后的活跃输入源 */
    CMD_InputSource_t active_source;
    
    /* 输出 */
    struct {
    CMD_ChassisOutput_t chassis;
    CMD_GimbalOutput_t gimbal;
    CMD_ShootOutput_t shoot;
    } output;
} CMD_t;

/* ========================================================================== */
/*                           主API接口                                          */
/* ========================================================================== */

/**
 * @brief 初始化CMD模块
 * @param ctx CMD上下文
 * @param config 配置指针
 * @return CMD_OK成功，其他失败
 */
int8_t CMD_Init(CMD_t *ctx, CMD_Config_t *config);

/**
 * @brief 更新所有输入源的数据
 * @param ctx CMD上下文
 * @return CMD_OK成功
 */
int8_t CMD_UpdateInput(CMD_t *ctx);

/**
 * @brief 执行仲裁，决定使用哪个输入源
 * @param ctx CMD上下文
 * @return 选中的输入源
 */
int8_t CMD_Arbitrate(CMD_t *ctx);

/**
 * @brief 生成所有模块的控制命令
 * @param ctx CMD上下文
 * @return CMD_OK成功
 */
int8_t CMD_GenerateCommands(CMD_t *ctx);

/**
 * @brief 一键更新（包含UpdateInput + Arbitrate + GenerateCommands）
 * @param ctx CMD上下文
 * @return CMD_OK成功
 */
int8_t CMD_Update(CMD_t *ctx);

/* ========================================================================== */
/*                           输出获取接口                                       */
/* ========================================================================== */

/* 获取底盘命令 */
static inline Chassis_CMD_t* CMD_GetChassisCmd(CMD_t *ctx) {
    return &ctx->output.chassis.cmd;
  }

/* 获取云台命令 */
static inline Gimbal_CMD_t* CMD_GetGimbalCmd(CMD_t *ctx) {
    return &ctx->output.gimbal.cmd;
}

/* 获取射击命令 */
static inline Shoot_CMD_t* CMD_GetShootCmd(CMD_t *ctx) {
    return &ctx->output.shoot.cmd;
}

#ifdef __cplusplus
}
#endif
