/*
 * CMD 模块 V2 - 主控制模块实现
 */
#include "cmd.h"
#include "bsp/time.h"
#include <stdint.h>
#include <string.h>

/* ========================================================================== */
/*                           命令构建函数                                       */
/* ========================================================================== */

/* 从RC输入生成底盘命令 */
static void CMD_RC_BuildChassisCmd(CMD_t *ctx) {
  CMD_RCModeMap_t *map = &ctx->config->rc_mode_map;
  
  /* 根据左拨杆位置选择模式 */
  switch (ctx->input.rc.sw[0]) {
      case CMD_SW_UP:
          ctx->output.chassis.cmd.mode = map->sw_left_up;
          break;
      case CMD_SW_MID:
          ctx->output.chassis.cmd.mode = map->sw_left_mid;
          break;
      case CMD_SW_DOWN:
          ctx->output.chassis.cmd.mode = map->sw_left_down;
          break;
      default:
          ctx->output.chassis.cmd.mode = CHASSIS_MODE_RELAX;
          break;
  }
  
  /* 摇杆控制移动 */
  ctx->output.chassis.cmd.ctrl_vec.vx = ctx->input.rc.joy_right.x;
  ctx->output.chassis.cmd.ctrl_vec.vy = ctx->input.rc.joy_right.y;
}

/* 从RC输入生成云台命令 */
static void CMD_RC_BuildGimbalCmd(CMD_t *ctx) {
  CMD_RCModeMap_t *map = &ctx->config->rc_mode_map;
  
  /* 根据拨杆选择云台模式 */
  switch (ctx->input.rc.sw[0]) {
      case CMD_SW_UP:
          ctx->output.gimbal.cmd.mode = map->gimbal_sw_up;
          break;
      case CMD_SW_MID:
          ctx->output.gimbal.cmd.mode = map->gimbal_sw_mid;
          break;
      case CMD_SW_DOWN:
          ctx->output.gimbal.cmd.mode = map->gimbal_sw_down;
          break;
      default:
          ctx->output.gimbal.cmd.mode = GIMBAL_MODE_RELAX;
          break;
  }
  
  /* 左摇杆控制云台 */
  ctx->output.gimbal.cmd.delta_yaw = -ctx->input.rc.joy_left.x * 2.0f;
  ctx->output.gimbal.cmd.delta_pit = -ctx->input.rc.joy_left.y * 1.5f;
}

/* 从RC输入生成射击命令 */
static void CMD_RC_BuildShootCmd(CMD_t *ctx) {
  if (ctx->input.online[CMD_SRC_RC]) {
      ctx->output.shoot.cmd.mode = SHOOT_MODE_SINGLE;
  } else {
      ctx->output.shoot.cmd.mode = SHOOT_MODE_SAFE;
  }
  
  /* 根据右拨杆控制射击 */
  switch (ctx->input.rc.sw[1]) {
      case CMD_SW_DOWN:
          ctx->output.shoot.cmd.ready = true;
          ctx->output.shoot.cmd.firecmd = true;
          break;
      case CMD_SW_MID:
          ctx->output.shoot.cmd.ready = true;
          ctx->output.shoot.cmd.firecmd = false;
          break;
      case CMD_SW_UP:
      default:
          ctx->output.shoot.cmd.ready = false;
          ctx->output.shoot.cmd.firecmd = false;
          break;
  }
}

/* 从PC输入生成底盘命令 */
static void CMD_PC_BuildChassisCmd(CMD_t *ctx) {
  
  if (!ctx->input.online[CMD_SRC_PC]) {
      ctx->output.chassis.cmd.mode = CHASSIS_MODE_RELAX;
      return;
  }
  
  ctx->output.chassis.cmd.mode = CHASSIS_MODE_FOLLOW_GIMBAL;
  
  /* WASD控制移动 */
  ctx->output.chassis.cmd.ctrl_vec.vx = 0.0f;
  ctx->output.chassis.cmd.ctrl_vec.vy = 0.0f;
  CMD_Behavior_ProcessAll(ctx, &ctx->input, &ctx->last_input, CMD_MODULE_CHASSIS);
}

/* 从PC输入生成云台命令 */
static void CMD_PC_BuildGimbalCmd(CMD_t *ctx) {
  CMD_Sensitivity_t *sens = &ctx->config->sensitivity;
  
  if (!ctx->input.online[CMD_SRC_PC]) {
      ctx->output.gimbal.cmd.mode = GIMBAL_MODE_RELAX;
      return;
  }
  
  ctx->output.gimbal.cmd.mode = GIMBAL_MODE_ABSOLUTE;
  
  /* 鼠标控制云台 */
  ctx->output.gimbal.cmd.delta_yaw = (float)-ctx->input.pc.mouse.x * ctx->timer.dt * sens->mouse_sens;
  ctx->output.gimbal.cmd.delta_pit = (float)ctx->input.pc.mouse.y * ctx->timer.dt * sens->mouse_sens * 1.5f;
  CMD_Behavior_ProcessAll(ctx, &ctx->input, &ctx->last_input, CMD_MODULE_GIMBAL);
}

/* 从PC输入生成射击命令 */
static void CMD_PC_BuildShootCmd(CMD_t *ctx) {
  if (!ctx->input.online[CMD_SRC_PC]) {
      ctx->output.shoot.cmd.mode = SHOOT_MODE_SAFE;
      return;
  }
  
  ctx->output.shoot.cmd.ready = true;
  ctx->output.shoot.cmd.firecmd = ctx->input.pc.mouse.l_click;

  CMD_Behavior_ProcessAll(ctx, &ctx->input, &ctx->last_input, CMD_MODULE_SHOOT);

}

/* 离线安全模式 */
static void CMD_SetOfflineMode(CMD_t *ctx) {
  ctx->output.chassis.cmd.mode = CHASSIS_MODE_RELAX;
  ctx->output.gimbal.cmd.mode = GIMBAL_MODE_RELAX;
  ctx->output.shoot.cmd.mode = SHOOT_MODE_SAFE;
}

/* ========================================================================== */
/*                           公开API实现                                        */
/* ========================================================================== */

int8_t CMD_Init(CMD_t *ctx, CMD_Config_t *config) {
  if (ctx == NULL || config == NULL) {
      return CMD_ERR_NULL;
  }
  
  memset(ctx, 0, sizeof(CMD_t));
  ctx->config = config;
  
  /* 初始化适配器 */
  CMD_Adapter_InitAll();
  
  /* 初始化行为处理器 */
  CMD_Behavior_Init();
  
  return CMD_OK;
}

int8_t CMD_UpdateInput(CMD_t *ctx) {
  if (ctx == NULL) {
      return CMD_ERR_NULL;
  }
  
  /* 保存上一帧输入 */
  memcpy(&ctx->last_input, &ctx->input, sizeof(ctx->input));
  
  /* 更新所有输入源 */
  for (int i = 0; i < CMD_SRC_NUM; i++) {
      CMD_Adapter_GetInput((CMD_InputSource_t)i, &ctx->input);
  }
  
  return CMD_OK;
}
typedef void (*CMD_BuildCommandFunc)(CMD_t *cmd);
typedef struct {
  CMD_InputSource_t source;
  CMD_BuildCommandFunc chassisFunc;
  CMD_BuildCommandFunc gimbalFunc;
  CMD_BuildCommandFunc shootFunc;
} CMD_SourceHandler_t;

CMD_SourceHandler_t sourceHandlers[CMD_SRC_NUM] = {
  {CMD_SRC_RC, CMD_RC_BuildChassisCmd, CMD_RC_BuildGimbalCmd, CMD_RC_BuildShootCmd},
  {CMD_SRC_PC, CMD_PC_BuildChassisCmd, CMD_PC_BuildGimbalCmd, CMD_PC_BuildShootCmd},
  {CMD_SRC_NUC, NULL, NULL, NULL},
  {CMD_SRC_REF, NULL, NULL, NULL},
};

int8_t CMD_Arbitrate(CMD_t *ctx) {
  if (ctx == NULL) {
      return CMD_ERR_NULL;
  }
  
  /* 自动仲裁：优先级 PC > RC > NUC */
  CMD_InputSource_t candidates[] = {CMD_SRC_PC, CMD_SRC_RC, CMD_SRC_NUC};
  const int num_candidates = sizeof(candidates) / sizeof(candidates[0]);
  
  /* 如果当前输入源仍然在线且有效，保持使用 */
  if (ctx->active_source < CMD_SRC_NUM && 
      ctx->active_source != CMD_SRC_REF && 
      ctx->input.online[ctx->active_source]) {
      goto seize;
  }
  
  /* 否则选择第一个可用的控制输入源 */
  for (int i = 0; i < num_candidates; i++) {
      CMD_InputSource_t src = candidates[i];
      if (ctx->input.online[src]) {
          ctx->active_source = src;
          break;
      }else {
          ctx->active_source = CMD_SRC_NUM;
          continue;
      }
  }
  ctx->output.chassis.source = ctx->active_source;
  ctx->output.gimbal.source = ctx->active_source;
  ctx->output.shoot.source = ctx->active_source;

  /* 优先级抢占逻辑 */
  seize:
  CMD_Behavior_ProcessAll(ctx, &ctx->input, &ctx->last_input, CMD_MODULE_NONE);

  return CMD_OK;
}

int8_t CMD_GenerateCommands(CMD_t *ctx) {
  if (ctx == NULL) {
      return CMD_ERR_NULL;
  }
  
  /* 更新时间 */
  uint64_t now_us = BSP_TIME_Get_us();
  ctx->timer.now = now_us / 1000000.0f;
  ctx->timer.dt = (now_us - ctx->timer.last_us) / 1000000.0f;
  ctx->timer.last_us = now_us;
  
  /* 没有有效输入源 */
  if (ctx->active_source >= CMD_SRC_NUM) {
      CMD_SetOfflineMode(ctx);
      return CMD_ERR_NO_INPUT;
  }

  sourceHandlers[ctx->output.gimbal.source].gimbalFunc(ctx);
  sourceHandlers[ctx->output.chassis.source].chassisFunc(ctx);
  sourceHandlers[ctx->output.shoot.source].shootFunc(ctx);
  return CMD_OK;
}

int8_t CMD_Update(CMD_t *ctx) {
    int8_t ret;
    
    ret = CMD_UpdateInput(ctx);
    if (ret != CMD_OK) return ret;
    
    CMD_Arbitrate(ctx);
    
    ret = CMD_GenerateCommands(ctx);
    return ret;
}
