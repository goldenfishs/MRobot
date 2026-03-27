/*
 * CMD 模块 V2 - 主控制模块实现
 */
#include "cmd.h"
#include "bsp/time.h"
#include "module/cmd/cmd_types.h"
#include "module/gimbal.h"
#include "module/shoot.h"
#include "module/gimbal.h"
#include <stdint.h>
#include <string.h>

/* ========================================================================== */
/*                           命令构建函数                                       */
/* ========================================================================== */

/* 从RC输入生成底盘命令 */
#if CMD_ENABLE_SRC_RC && CMD_ENABLE_MODULE_CHASSIS
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
  ctx->output.chassis.cmd.ctrl_vec.wz = ctx->input.rc.joy_left.x;
}
#endif /* CMD_ENABLE_SRC_RC && CMD_ENABLE_MODULE_CHASSIS */

/* 从 RC 输入生成云台命令 */
#if CMD_ENABLE_SRC_RC && CMD_ENABLE_MODULE_GIMBAL
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
  ctx->output.gimbal.cmd.delta_yaw = -ctx->input.rc.joy_right.x * 5.0f;
  ctx->output.gimbal.cmd.delta_pit = ctx->input.rc.joy_right.y * 5.0f;
}
#endif /* CMD_ENABLE_SRC_RC && CMD_ENABLE_MODULE_GIMBAL */

/* 从 RC 输入生成射击命令 */
#if CMD_ENABLE_SRC_RC && CMD_ENABLE_MODULE_SHOOT
static void CMD_RC_BuildShootCmd(CMD_t *ctx) {
  if (ctx->input.online[CMD_SRC_RC]) {
      ctx->output.shoot.cmd.mode = SHOOT_MODE_CONTINUE;
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
#endif /* CMD_ENABLE_SRC_RC && CMD_ENABLE_MODULE_SHOOT */

/* 从 RC 输入生成履带命令 */
#if CMD_ENABLE_SRC_RC && CMD_ENABLE_MODULE_TRACK
static void CMD_RC_BuildTrackCmd(CMD_t *ctx) {
  CMD_RCModeMap_t *map = &ctx->config->rc_mode_map;
  
  if (!ctx->input.online[CMD_SRC_RC]) {
      ctx->output.track.cmd.enable = false;
      ctx->output.track.cmd.vel = 0.0f;
      ctx->output.track.cmd.omega = 0.0f;
      return;
  }
    switch (ctx->input.rc.sw[0]) {
      case CMD_SW_UP:
          ctx->output.track.cmd.enable = map->track_sw_up;
          break;
      case CMD_SW_MID:
          ctx->output.track.cmd.enable = map->track_sw_mid;
          break;
      case CMD_SW_DOWN:
          ctx->output.track.cmd.enable = map->track_sw_down;
          break;
      default:
          ctx->output.track.cmd.enable = false;
          break;
  }
  ctx->output.track.cmd.enable = ctx->input.online[CMD_SRC_RC];
  ctx->output.track.cmd.vel = ctx->input.rc.joy_right.y * 2.0f;
  if(fabsf(ctx->input.rc.joy_right.y * 2.0f) > 1.0f)
          ctx->output.track.cmd.vel = ctx->output.track.cmd.vel > 0 ? 1.0f
          : -1.0f;
  
  CMD_Behavior_ProcessAll(ctx, &ctx->input, &ctx->last_input, CMD_MODULE_TRACK);
}
#endif /* CMD_ENABLE_SRC_RC && CMD_ENABLE_MODULE_TRACK */

/* 从PC输入生成底盘命令 */
#if CMD_ENABLE_SRC_PC && CMD_ENABLE_MODULE_CHASSIS
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
#endif /* CMD_ENABLE_SRC_PC && CMD_ENABLE_MODULE_CHASSIS */

/* 从PC输入生成云台命令 */
#if CMD_ENABLE_SRC_PC && CMD_ENABLE_MODULE_GIMBAL
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
#endif /* CMD_ENABLE_SRC_PC && CMD_ENABLE_MODULE_GIMBAL */

/* 从PC输入生成射击命令 */
#if CMD_ENABLE_SRC_PC && CMD_ENABLE_MODULE_SHOOT
static void CMD_PC_BuildShootCmd(CMD_t *ctx) {
  if (!ctx->input.online[CMD_SRC_PC]) {
      ctx->output.shoot.cmd.mode = SHOOT_MODE_SAFE;
      return;
  }
  
  ctx->output.shoot.cmd.ready = true;
  ctx->output.shoot.cmd.firecmd = ctx->input.pc.mouse.l_click;
}
#endif /* CMD_ENABLE_SRC_PC && CMD_ENABLE_MODULE_SHOOT */

/* 从PC输入生成履带命令 */
#if CMD_ENABLE_SRC_PC && CMD_ENABLE_MODULE_TRACK
static void CMD_PC_BuildTrackCmd(CMD_t *ctx) {
  if (!ctx->input.online[CMD_SRC_PC]) {
      ctx->output.track.cmd.enable = false;
      ctx->output.track.cmd.vel = 0.0f;
      ctx->output.track.cmd.omega = 0.0f;
      return;
  }
  
  ctx->output.track.cmd.enable = true;
  /* 可根据需要添加PC对履带的控制，例如键盘按键 */
  ctx->output.track.cmd.vel = 0.0f;
  ctx->output.track.cmd.omega = 0.0f;
  
  CMD_Behavior_ProcessAll(ctx, &ctx->input, &ctx->last_input, CMD_MODULE_TRACK);
}
#endif /* CMD_ENABLE_SRC_PC && CMD_ENABLE_MODULE_TRACK */

/* 从NUC/AI输入生成云台命令 */
#if CMD_ENABLE_SRC_NUC && CMD_ENABLE_MODULE_GIMBAL
static void CMD_NUC_BuildGimbalCmd(CMD_t *ctx) {
  if (!ctx->input.online[CMD_SRC_NUC]) {
      ctx->output.gimbal.cmd.mode = GIMBAL_MODE_RELAX;
      return;
  }
  
  /* 使用AI提供的云台控制数据 */
  if (ctx->input.nuc.mode != 0) {
    /* AI有目标：进入自瞄模式，下发setpoint和前馈 */
    ctx->output.gimbal.cmd.mode = GIMBAL_MODE_AI_CONTROL;
    ctx->output.gimbal.cmd.mode_ai = (uint8_t)ctx->input.nuc.mode;
    ctx->output.gimbal.cmd.setpoint_yaw = ctx->input.nuc.gimbal.setpoint.yaw;
    ctx->output.gimbal.cmd.setpoint_pit = ctx->input.nuc.gimbal.setpoint.pit;
    ctx->output.gimbal.cmd.ff_vel_yaw = ctx->input.nuc.gimbal.vel.yaw;
    ctx->output.gimbal.cmd.ff_vel_pit = ctx->input.nuc.gimbal.vel.pit;
    ctx->output.gimbal.cmd.ff_accl_yaw = ctx->input.nuc.gimbal.accl.yaw;
    ctx->output.gimbal.cmd.ff_accl_pit = ctx->input.nuc.gimbal.accl.pit;
  } else {
    /* AI丢失目标(mode==0)：保持普通模式，不使用全零的AI数据 */
    ctx->output.gimbal.cmd.mode = GIMBAL_MODE_ABSOLUTE;
    ctx->output.gimbal.cmd.mode_ai = 0;
    ctx->output.gimbal.cmd.delta_yaw = 0.0f;
    ctx->output.gimbal.cmd.delta_pit = 0.0f;
  }

}
#endif /* CMD_ENABLE_SRC_NUC && CMD_ENABLE_MODULE_GIMBAL */

/* 从 NUC/AI 输入生成射击命令 */
#if CMD_ENABLE_SRC_NUC && CMD_ENABLE_MODULE_SHOOT
static void CMD_NUC_BuildShootCmd(CMD_t *ctx) {
  if (!ctx->input.online[CMD_SRC_NUC]) {
      ctx->output.shoot.cmd.mode = SHOOT_MODE_SAFE;
      return;
  }
  
  /* 根据AI模式决定射击行为 */
  switch (ctx->input.nuc.mode) {
    case 0:
    case 1:
      /* mode=1 只控云台，不让射击机构进入 ready，避免摩擦轮继续预转。 */
      ctx->output.shoot.cmd.ready = false;
      ctx->output.shoot.cmd.firecmd = false; 
      break;
    case 2:
      if ((ctx->active_source == CMD_SRC_PC && ctx->input.pc.mouse.l_click) || 
          (ctx->active_source == CMD_SRC_RC && ctx->input.rc.sw[1] == CMD_SW_DOWN)) {
        ctx->output.shoot.cmd.ready = true;
        ctx->output.shoot.cmd.firecmd = true; 
      } else {
        ctx->output.shoot.cmd.ready = true;
        ctx->output.shoot.cmd.firecmd = false; 
      }
      break;
    default:
      ctx->output.shoot.cmd.ready = false;
      ctx->output.shoot.cmd.firecmd = false;
      break;
  }
}
#endif /* CMD_ENABLE_SRC_NUC && CMD_ENABLE_MODULE_SHOOT */

/* 从 RC 输入生成机械臂命令 */
#if CMD_ENABLE_SRC_RC && CMD_ENABLE_MODULE_ARM
static void CMD_RC_BuildArmCmd(CMD_t *ctx) {
  /*
   * 遥控器控制机械臂末端位姿 —— 笛卡尔增量方案
   *
   * 左拨杆 SW_L (sw[0]) —— 整体使能:
   *   UP   → 失能（电机松弛/重力补偿）
   *   MID  → 使能，笛卡尔增量控制
   *   DOWN → 使能（保留备用）
   *
   * 右拨杆 SW_R (sw[1]) —— 自由度分组:
   *
   *   UP  【位置模式】3轴平移 + 偏航（最常用操作放第一层）
   *         右摇杆X (RX) → X 平移（末端左右移动）
   *         右摇杆Y (RY) → Y 平移（末端前后移动）
   *         左摇杆Y (LY) → Z 平移（末端升降）
   *         左摇杆X (LX) → Yaw 偏航旋转
   *
   *   MID 【姿态模式】俯仰/横滚全姿态，同时保留 Z 和偏航可调
   *         右摇杆X (RX) → Yaw  偏航旋转（持续可调，避免强制切换模式）
   *         右摇杆Y (RY) → Pitch 俯仰旋转
   *         左摇杆X (LX) → Roll  横滚旋转
   *         左摇杆Y (LY) → Z 平移（升降保持可调，避免强制切换模式）
   *
   *   DOWN → set_target_as_current（目标位姿吸附当前实际位姿，消除累积漂移）
   *
   * 摇杆直觉映射总结:
   *   右摇杆 = "末端去哪里"（XY平移，最自然）
   *   左Y    = "臂的高低"  （Z升降，推上=升高）
   *   左X    = 位置模式→偏航 / 姿态模式→横滚
   */
  ctx->output.arm.cmd.set_target_as_current = false;
  if (ctx->input.rc.sw[1] == CMD_SW_DOWN) {
    ctx->output.arm.cmd.set_target_as_current = true;
  }

  switch (ctx->input.rc.sw[0]) {
    case CMD_SW_MID:
    case CMD_SW_DOWN:
      ctx->output.arm.cmd.enable = true;
      break;
    default:
      ctx->output.arm.cmd.enable = false;
      goto end;
  }

  /* 遥控器模式使用笛卡尔位姿累积控制 */
  ctx->output.arm.cmd.ctrl_type = ARM_CTRL_REMOTE_CARTESIAN;

  /* set_target_as_current 置位时不叠加摇杆增量，由上层负责同步位姿基准 */
  if (ctx->output.arm.cmd.set_target_as_current) return;

  /* 输出摇杆速度命令（m/s, rad/s）——不含 dt，由arm_main在正确坐标系下积分到世界系 target_pose */
  float pos_scale = 0.3f;   /* 末端线速度上限 (m/s) */
  float rot_scale = 1.0f;   /* 末端角速度上限 (rad/s) */

  memset(&ctx->output.arm.cmd.joy_vel, 0, sizeof(ctx->output.arm.cmd.joy_vel));

  switch (ctx->input.rc.sw[1]) {
    case CMD_SW_UP:
      /* 位置模式：3轴平移 + 偏航 */
      ctx->output.arm.cmd.joy_vel.x   = ctx->input.rc.joy_right.x * pos_scale;
      ctx->output.arm.cmd.joy_vel.y   = ctx->input.rc.joy_right.y * pos_scale;
      ctx->output.arm.cmd.joy_vel.z   = ctx->input.rc.joy_left.y  * pos_scale;
      ctx->output.arm.cmd.joy_vel.yaw = ctx->input.rc.joy_left.x  * rot_scale;
      break;
    case CMD_SW_MID:
      /* 姿态模式：俯仰 + 横滚 + 偏航 + 升降（全6自由度可达，Z/Yaw持续可调） */
      ctx->output.arm.cmd.joy_vel.yaw   = ctx->input.rc.joy_right.x * rot_scale;
      ctx->output.arm.cmd.joy_vel.pitch = ctx->input.rc.joy_right.y * rot_scale;
      ctx->output.arm.cmd.joy_vel.roll  = ctx->input.rc.joy_left.x  * rot_scale;
      ctx->output.arm.cmd.joy_vel.z     = ctx->input.rc.joy_left.y  * pos_scale;
      break;
    default:
      break;
  }
  end:
  return;
}
#endif /* CMD_ENABLE_SRC_RC && CMD_ENABLE_MODULE_ARM */

/* 从 PC 输入生成机械臂命令 */
#if CMD_ENABLE_SRC_PC && CMD_ENABLE_MODULE_ARM
static void CMD_PC_BuildArmCmd(CMD_t *ctx) {
  if (!ctx->input.online[CMD_SRC_PC]) {
      ctx->output.arm.cmd.enable = false;
      return;
  }
  ctx->output.arm.cmd.enable = true;
  ctx->output.arm.cmd.ctrl_type = ARM_CTRL_REMOTE_CARTESIAN;

  /* 鼠标控制末端位坐 XY，其他轴可根据需要扩展 */
  float sens = ctx->config->sensitivity.mouse_sens * 0.001f;
  ctx->output.arm.cmd.target_pose.x += (float)ctx->input.pc.mouse.x * sens * ctx->timer.dt;
  ctx->output.arm.cmd.target_pose.y += (float)ctx->input.pc.mouse.y * sens * ctx->timer.dt;
}
#endif /* CMD_ENABLE_SRC_PC && CMD_ENABLE_MODULE_ARM */

/* 从 RC 输入生成平衡底盘命令 */
#if CMD_ENABLE_SRC_RC && CMD_ENABLE_MODULE_BALANCE_CHASSIS
static void CMD_RC_BuildBalanceChassisCmd(CMD_t *ctx) {
  CMD_RCModeMap_t *map = &ctx->config->rc_mode_map;

  switch (ctx->input.rc.sw[0]) {
    case CMD_SW_UP:
      ctx->output.balance_chassis.cmd.mode = map->balance_sw_up;
      break;
    case CMD_SW_MID:
      ctx->output.balance_chassis.cmd.mode = map->balance_sw_mid;
      break;
    case CMD_SW_DOWN:
      ctx->output.balance_chassis.cmd.mode = map->balance_sw_down;
      break;
    default:
      ctx->output.balance_chassis.cmd.mode = CHASSIS_MODE_RELAX;
      break;
  }

  /* 左摩杆Y/X → 平移，右摩杆X → 转向 */
  ctx->output.balance_chassis.cmd.move_vec.vx = ctx->input.rc.joy_left.y;
  ctx->output.balance_chassis.cmd.move_vec.vy = ctx->input.rc.joy_left.x;
  ctx->output.balance_chassis.cmd.move_vec.wz = ctx->input.rc.joy_right.x;
  /* 拨轮传递目标高度 */
  ctx->output.balance_chassis.cmd.height       = ctx->input.rc.dial;
  ctx->output.balance_chassis.cmd.jump_trigger  = false;

}
#endif /* CMD_ENABLE_SRC_RC && CMD_ENABLE_MODULE_BALANCE_CHASSIS */

/* 从 PC 输入生成平衡底盘命令 */
#if CMD_ENABLE_SRC_PC && CMD_ENABLE_MODULE_BALANCE_CHASSIS
static void CMD_PC_BuildBalanceChassisCmd(CMD_t *ctx) {
  CMD_Sensitivity_t *sens = &ctx->config->sensitivity;

  if (!ctx->input.online[CMD_SRC_PC]) {
    ctx->output.balance_chassis.cmd.mode = CHASSIS_MODE_RELAX;
    return;
  }

  ctx->output.balance_chassis.cmd.move_vec.vx = 0.0f;
  ctx->output.balance_chassis.cmd.move_vec.vy = 0.0f;
  ctx->output.balance_chassis.cmd.move_vec.wz = 0.0f;

  ctx->output.balance_chassis.cmd.height += (float)ctx->input.pc.mouse.z * sens->mouse_sens * 0.001f * ctx->timer.dt;
  if (ctx->output.balance_chassis.cmd.height > 0.5f) {
    ctx->output.balance_chassis.cmd.height = 0.5f;
  } else if (ctx->output.balance_chassis.cmd.height < 0.2f) {
    ctx->output.balance_chassis.cmd.height = 0.2f;
  }
    ctx->output.balance_chassis.cmd.jump_trigger  = false;
  ctx->output.balance_chassis.cmd.mode = CHASSIS_MODE_WHELL_LEG_BALANCE;
  CMD_Behavior_ProcessAll(ctx, &ctx->input, &ctx->last_input, CMD_MODULE_BALANCE_CHASSIS);

}
#endif /* CMD_ENABLE_SRC_PC && CMD_ENABLE_MODULE_BALANCE_CHASSIS */
#if CMD_ENABLE_SRC_NUC && CMD_ENABLE_MODULE_REFUI
static void CMD_NUC_BuildRefUICmd(CMD_t *ctx) {
  if (!ctx->input.online[CMD_SRC_NUC]) {
    ctx->output.refui.cmd = UI_AUTO_AIM_STOP;
    return;
  }
  ctx->output.refui.cmd = (ctx->input.nuc.mode != 0) ? UI_AUTO_AIM_START : UI_AUTO_AIM_STOP;
}
#endif /* CMD_ENABLE_SRC_NUC && CMD_ENABLE_MODULE_REFUI */

/* 离线安全模式 */
static void CMD_SetOfflineMode(CMD_t *ctx) {
#if CMD_ENABLE_MODULE_CHASSIS
  ctx->output.chassis.cmd.mode = CHASSIS_MODE_RELAX;
#endif
#if CMD_ENABLE_MODULE_GIMBAL
  ctx->output.gimbal.cmd.mode = GIMBAL_MODE_RELAX;
#endif
#if CMD_ENABLE_MODULE_SHOOT
  ctx->output.shoot.cmd.mode = SHOOT_MODE_SAFE;
#endif
#if CMD_ENABLE_MODULE_TRACK
  ctx->output.track.cmd.enable = false;
#endif
#if CMD_ENABLE_MODULE_BALANCE_CHASSIS
  ctx->output.balance_chassis.cmd.mode = CHASSIS_MODE_RELAX;
#endif
#if CMD_ENABLE_MODULE_ARM
  ctx->output.arm.cmd.enable = false;
#endif
#if CMD_ENABLE_MODULE_REFUI
  ctx->output.refui.cmd = UI_NOTHING;
#endif
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
  CMD_BuildCommandFunc trackFunc;
  CMD_BuildCommandFunc armFunc;
  CMD_BuildCommandFunc refuiFunc;
    CMD_BuildCommandFunc balanceChassisFunc;
} CMD_SourceHandler_t;

/* Build-function conditional references */
#if CMD_ENABLE_MODULE_CHASSIS && CMD_ENABLE_SRC_RC
  #define _FN_RC_CHASSIS  CMD_RC_BuildChassisCmd
#else
  #define _FN_RC_CHASSIS  NULL
#endif
#if CMD_ENABLE_MODULE_GIMBAL && CMD_ENABLE_SRC_RC
  #define _FN_RC_GIMBAL   CMD_RC_BuildGimbalCmd
#else
  #define _FN_RC_GIMBAL   NULL
#endif
#if CMD_ENABLE_MODULE_SHOOT && CMD_ENABLE_SRC_RC
  #define _FN_RC_SHOOT    CMD_RC_BuildShootCmd
#else
  #define _FN_RC_SHOOT    NULL
#endif
#if CMD_ENABLE_MODULE_TRACK && CMD_ENABLE_SRC_RC
  #define _FN_RC_TRACK    CMD_RC_BuildTrackCmd
#else
  #define _FN_RC_TRACK    NULL
#endif
#if CMD_ENABLE_MODULE_CHASSIS && CMD_ENABLE_SRC_PC
  #define _FN_PC_CHASSIS  CMD_PC_BuildChassisCmd
#else
  #define _FN_PC_CHASSIS  NULL
#endif
#if CMD_ENABLE_MODULE_GIMBAL && CMD_ENABLE_SRC_PC
  #define _FN_PC_GIMBAL   CMD_PC_BuildGimbalCmd
#else
  #define _FN_PC_GIMBAL   NULL
#endif
#if CMD_ENABLE_MODULE_SHOOT && CMD_ENABLE_SRC_PC
  #define _FN_PC_SHOOT    CMD_PC_BuildShootCmd
#else
  #define _FN_PC_SHOOT    NULL
#endif
#if CMD_ENABLE_MODULE_TRACK && CMD_ENABLE_SRC_PC
  #define _FN_PC_TRACK    CMD_PC_BuildTrackCmd
#else
  #define _FN_PC_TRACK    NULL
#endif
#if CMD_ENABLE_MODULE_ARM && CMD_ENABLE_SRC_RC
  #define _FN_RC_ARM      CMD_RC_BuildArmCmd
#else
  #define _FN_RC_ARM      NULL
#endif
#if CMD_ENABLE_MODULE_ARM && CMD_ENABLE_SRC_PC
  #define _FN_PC_ARM      CMD_PC_BuildArmCmd
#else
  #define _FN_PC_ARM      NULL
#endif
#if CMD_ENABLE_MODULE_BALANCE_CHASSIS && CMD_ENABLE_SRC_RC
  #define _FN_RC_BALANCE_CHASSIS  CMD_RC_BuildBalanceChassisCmd
#else
  #define _FN_RC_BALANCE_CHASSIS  NULL
#endif
#if CMD_ENABLE_MODULE_BALANCE_CHASSIS && CMD_ENABLE_SRC_PC
  #define _FN_PC_BALANCE_CHASSIS  CMD_PC_BuildBalanceChassisCmd
#else
  #define _FN_PC_BALANCE_CHASSIS  NULL
#endif
#if CMD_ENABLE_MODULE_GIMBAL && CMD_ENABLE_SRC_NUC
  #define _FN_NUC_GIMBAL  CMD_NUC_BuildGimbalCmd
#else
  #define _FN_NUC_GIMBAL  NULL
#endif
#if CMD_ENABLE_MODULE_SHOOT && CMD_ENABLE_SRC_NUC
  #define _FN_NUC_SHOOT   CMD_NUC_BuildShootCmd
#else
  #define _FN_NUC_SHOOT   NULL
#endif

CMD_SourceHandler_t sourceHandlers[CMD_SRC_NUM] = {
#if CMD_ENABLE_SRC_RC
  [CMD_SRC_RC]  = {CMD_SRC_RC,  _FN_RC_CHASSIS, _FN_RC_GIMBAL, _FN_RC_SHOOT, _FN_RC_TRACK, _FN_RC_ARM,  NULL,  _FN_RC_BALANCE_CHASSIS},
#endif
#if CMD_ENABLE_SRC_PC
  [CMD_SRC_PC]  = {CMD_SRC_PC,  _FN_PC_CHASSIS, _FN_PC_GIMBAL, _FN_PC_SHOOT, _FN_PC_TRACK, _FN_PC_ARM,  NULL,  _FN_PC_BALANCE_CHASSIS},
#endif
#if CMD_ENABLE_SRC_NUC
  #if CMD_ENABLE_MODULE_REFUI
    #define _FN_NUC_REFUI  CMD_NUC_BuildRefUICmd
  #else
    #define _FN_NUC_REFUI  NULL
  #endif
  [CMD_SRC_NUC] = {CMD_SRC_NUC, NULL, _FN_NUC_GIMBAL, _FN_NUC_SHOOT, NULL, NULL, _FN_NUC_REFUI, NULL},
#endif
#if CMD_ENABLE_SRC_REF
  [CMD_SRC_REF] = {CMD_SRC_REF, NULL, NULL, NULL, NULL, NULL, NULL, NULL}
#endif
};

int8_t CMD_Arbitrate(CMD_t *ctx) {
  if (ctx == NULL) {
      return CMD_ERR_NULL;
  }
  
  /* RC > PC priority arbitration */
  CMD_InputSource_t candidates[] = {
#if CMD_ENABLE_SRC_RC
    CMD_SRC_RC,
#endif
#if CMD_ENABLE_SRC_PC
    CMD_SRC_PC,
#endif
  };
  const int num_candidates = sizeof(candidates) / sizeof(candidates[0]);
  
  /* keep current source if still online */
  if (ctx->active_source < CMD_SRC_NUM &&
#if CMD_ENABLE_SRC_REF
      ctx->active_source != CMD_SRC_REF &&
#endif
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

  /* 优先级抢占逻辑 */
  seize:

  /* reset output sources */
#if CMD_ENABLE_MODULE_CHASSIS
  ctx->output.chassis.source = ctx->active_source;
#endif
#if CMD_ENABLE_MODULE_GIMBAL
  ctx->output.gimbal.source = ctx->active_source;
#endif
#if CMD_ENABLE_MODULE_SHOOT
  ctx->output.shoot.source = ctx->active_source;
#endif
#if CMD_ENABLE_MODULE_TRACK
  ctx->output.track.source = ctx->active_source;
#endif
#if CMD_ENABLE_MODULE_ARM
  ctx->output.arm.source = ctx->active_source;
#endif
#if CMD_ENABLE_MODULE_REFUI
  ctx->output.refui.source = ctx->active_source;
#endif
#if CMD_ENABLE_MODULE_BALANCE_CHASSIS
  ctx->output.balance_chassis.source = ctx->active_source;
#endif

  CMD_Behavior_ProcessAll(ctx, &ctx->input, &ctx->last_input, CMD_MODULE_NONE);

#if CMD_ENABLE_SRC_NUC && CMD_ENABLE_SRC_RC && CMD_ENABLE_MODULE_GIMBAL && CMD_ENABLE_MODULE_SHOOT
  if (ctx->input.online[CMD_SRC_NUC]) {
    if (ctx->active_source==CMD_SRC_RC) {
      if (ctx->input.rc.sw[0] == CMD_SW_DOWN) {
        // 用遥控器调自瞄的时候打开下面两行
        // ctx->output.gimbal.source = CMD_SRC_NUC;
        // ctx->output.shoot.source = CMD_SRC_NUC;
#if CMD_ENABLE_MODULE_REFUI
        ctx->output.refui.source = CMD_SRC_NUC;
#endif
    }
  }
}
#endif
#ifdef CMD_ENABLE_SRC_RC && CMD_ENABLE_MODULE_BALANCE_CHASSIS
      if (ctx->input.rc.sw[0] == CMD_SW_DOWN) {
        ctx->output.balance_chassis.source = CMD_SRC_RC;
        ctx->output.gimbal.source = CMD_SRC_RC;
        ctx->output.balance_chassis.cmd.mode = CHASSIS_MODE_LEG_TEST;
        ctx->output.gimbal.cmd.mode = GIMBAL_MODE_RECOVER;
      }
#endif //CMD_ENABLE_SRC_RC && CMD_ENABLE_MODULE_BALANCE_CHASSIS
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

#if CMD_ENABLE_MODULE_GIMBAL
  if (sourceHandlers[ctx->output.gimbal.source].gimbalFunc != NULL) {
    sourceHandlers[ctx->output.gimbal.source].gimbalFunc(ctx);
  }
#endif
#if CMD_ENABLE_MODULE_CHASSIS
  if (sourceHandlers[ctx->output.chassis.source].chassisFunc != NULL) {
    sourceHandlers[ctx->output.chassis.source].chassisFunc(ctx);
  }
#endif
#if CMD_ENABLE_MODULE_SHOOT
  if (sourceHandlers[ctx->output.shoot.source].shootFunc != NULL) {
    sourceHandlers[ctx->output.shoot.source].shootFunc(ctx);
  }
#endif
#if CMD_ENABLE_MODULE_TRACK
  if (sourceHandlers[ctx->output.track.source].trackFunc != NULL) {
    sourceHandlers[ctx->output.track.source].trackFunc(ctx);
  }
#endif
#if CMD_ENABLE_MODULE_ARM
  if (sourceHandlers[ctx->output.arm.source].armFunc != NULL) {
    sourceHandlers[ctx->output.arm.source].armFunc(ctx);
  }
#endif
#if CMD_ENABLE_MODULE_REFUI
  if (sourceHandlers[ctx->output.refui.source].refuiFunc != NULL) {
    sourceHandlers[ctx->output.refui.source].refuiFunc(ctx);
  } else {
    ctx->output.refui.cmd = UI_NOTHING;
  }
#endif
#if CMD_ENABLE_MODULE_BALANCE_CHASSIS
  if (sourceHandlers[ctx->output.balance_chassis.source].balanceChassisFunc != NULL) {
    sourceHandlers[ctx->output.balance_chassis.source].balanceChassisFunc(ctx);
  }
#endif
  return CMD_OK;
}
  
#if CMD_ENABLE_SRC_REF
static void CMD_REF_BuildOutput(CMD_t *ctx) {
    ctx->output.ref = ctx->input.ref;
}
#endif

int8_t CMD_Update(CMD_t *ctx) {
    int8_t ret;
    
    ret = CMD_UpdateInput(ctx);
    if (ret != CMD_OK) return ret;
    
    CMD_Arbitrate(ctx);
    
    ret = CMD_GenerateCommands(ctx);

#if CMD_ENABLE_SRC_REF
    CMD_REF_BuildOutput(ctx);
#endif

    return ret;
}
