/*
 * CMD 模块 V2 - 使用示例和配置模板
 * 
 * 本文件展示如何配置和使用新的CMD模块
 */
#include "cmd.h"

/* ========================================================================== */
/*                           配置示例                                          */
/* ========================================================================== */

/* 默认配置 */
// static CMD_Config_t g_cmd_config = { 
//     /* 灵敏度设置 */
//     .sensitivity = {
//         .mouse_sens = 0.8f,
//         .move_sens = 1.0f,
//         .move_fast_mult = 1.5f,
//         .move_slow_mult = 0.5f,
//     },
    
//     /* RC拨杆模式映射 */
//     .rc_mode_map = {
//         /* 左拨杆控制底盘模式 */
//         .sw_left_up   = CHASSIS_MODE_BREAK,
//         .sw_left_mid  = CHASSIS_MODE_FOLLOW_GIMBAL,
//         .sw_left_down = CHASSIS_MODE_ROTOR,
        
//         /* 用于云台模式 */
//         .gimbal_sw_up   = GIMBAL_MODE_ABSOLUTE,
//         .gimbal_sw_mid  = GIMBAL_MODE_ABSOLUTE,
//         .gimbal_sw_down = GIMBAL_MODE_RELATIVE,
//     },
    
// };

// /* CMD上下文 */
// static CMD_t g_cmd_ctx;

/* ========================================================================== */
/*                           任务示例                                          */
/* ========================================================================== */

/*
 * 初始化示例
 */
// void Example_CMD_Init(void) {
//     CMD_Init(&g_cmd_ctx, &g_cmd_config);
// }

// /*
//  * 任务循环示例
//  */
// void Example_CMD_Task(void) {
//     /* 一键更新 */
//     CMD_Update(&g_cmd_ctx);
    
//     /* 获取命令发送到各模块 */
//     Chassis_CMD_t *chassis_cmd = CMD_GetChassisCmd(&g_cmd_ctx);
//     Gimbal_CMD_t *gimbal_cmd = CMD_GetGimbalCmd(&g_cmd_ctx);
//     Shoot_CMD_t *shoot_cmd = CMD_GetShootCmd(&g_cmd_ctx);
    
//     /* 使用命令... */
//     (void)chassis_cmd;
//     (void)gimbal_cmd;
//     (void)shoot_cmd;
// }

/* ========================================================================== */
/*                   架构说明                                                   */
/* ========================================================================== */

/*
 * ## 新架构优势
 * 
 * ### 1. 统一的输入抽象层 (CMD_RawInput_t)
 * - 所有设备（DR16/AT9S/VT13等）都转换成相同格式
 * - 上层代码无需关心具体设备类型
 * - 添加新设备只需实现适配器，不改动主逻辑
 * 
 * ### 2. 适配器模式
 * - 每个设备一个适配器文件
 * - 实现 Init, GetInput, IsOnline 三个函数
 * - 通过宏选择编译哪个适配器
 * 
 * ### 3. X-Macro配置表
 * - CMD_INPUT_SOURCE_TABLE: 配置输入源
 * - CMD_OUTPUT_MODULE_TABLE: 配置输出模块  
 * - CMD_BEHAVIOR_TABLE: 配置按键行为映射
 * - 编译时生成枚举、配置数组、处理函数
 * 
 * ### 4. 行为驱动设计
 * - 行为与按键解耦
 * - 运行时可修改映射
 * - 支持边沿触发和持续触发
 * 
 * ### 5. 清晰的分层
 * 
 *     ┌──────────────────────────────────────┐
 *     │          应用层 (cmd.c)              │
 *     │  - CMD_Update()                      │
 *     │  - 仲裁、命令生成                     │
 *     └──────────────┬───────────────────────┘
 *                    │
 *     ┌──────────────▼───────────────────────┐
 *     │        行为处理层 (cmd_behavior.c)    │
 *     │  - 按键触发检测                       │
 *     │  - 行为函数调用                       │
 *     └──────────────┬───────────────────────┘
 *                    │
 *     ┌──────────────▼──────────────────────────┐
 *     │        抽象输入层 (cmd_types.h)          │
 *     │  - 多输入源操作同一CMD_RawInput_t不同分区 │
 *     │  - 统一的摇杆、开关、键鼠结构             │
 *     └──────────────┬──────────────────────────┘
 *                    │
 *     ┌──────────────▼───────────────────────┐
 *     │        适配器层 (cmd_adapter.c)       │
 *     │  - DR16_Adapter                      │
 *     │  - AT9S_Adapter                      │
 *     │  - 设备数据 → CMD_RawInput_t          │
 *     └──────────────────────────────────────┘
 * 
 * ## 扩展指南
 * 
 * ### 添加新遥控器设备
 * 1. 在 cmd_adapter.h 中添加宏定义选项
 * 2. 在 cmd_adapter.c 中实现三个适配器函数
 * 3. 修改 CMD_RC_DEVICE_TYPE 宏选择新设备
 * 
 * ### 添加新输入源（如自定义协议）
 * 1. 在 CMD_INPUT_SOURCE_TABLE 添加条目
 * 2. 实现对应的适配器
 * 3. 在 CMD_GenerateCommands 添加处理分支
 * 
 * ### 添加新行为
 * 1. 在 CMD_BEHAVIOR_TABLE 添加条目,并修正BEHAVIOR_CONFIG_COUNT
 * 2. 实现 CMD_Behavior_Handle_XXX 函数
 * 
 * ### 添加新输出模块
 * 1. 在 CMD_OUTPUT_MODULE_TABLE 添加条目
 * 2. 在 CMD_t 中添加输出成员
 * 3. 实现对应的 BuildXXXCmd 函数
 */
