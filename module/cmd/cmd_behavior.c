/*
 * CMD 模块 V2 - 行为处理器实现
 */
#include "cmd_behavior.h"
#include "cmd.h"
#include "module/gimbal.h"
#include <string.h>

/* ========================================================================== */
/*                           行为回调函数                                        */
/* ========================================================================== */

/* 行为处理函数实现 */
int8_t CMD_Behavior_Handle_FORE(CMD_t *ctx) {
    ctx->output.chassis.cmd.ctrl_vec.vy += ctx->config->sensitivity.move_sens;
    return CMD_OK;
}

int8_t CMD_Behavior_Handle_BACK(CMD_t *ctx) {
    ctx->output.chassis.cmd.ctrl_vec.vy -= ctx->config->sensitivity.move_sens;
    return CMD_OK;
}

int8_t CMD_Behavior_Handle_LEFT(CMD_t *ctx) {
    ctx->output.chassis.cmd.ctrl_vec.vx -= ctx->config->sensitivity.move_sens;
    return CMD_OK;
}

int8_t CMD_Behavior_Handle_RIGHT(CMD_t *ctx) {
    ctx->output.chassis.cmd.ctrl_vec.vx += ctx->config->sensitivity.move_sens;
    return CMD_OK;
}

int8_t CMD_Behavior_Handle_ACCELERATE(CMD_t *ctx) {
    ctx->output.chassis.cmd.ctrl_vec.vx *= ctx->config->sensitivity.move_fast_mult;
    ctx->output.chassis.cmd.ctrl_vec.vy *= ctx->config->sensitivity.move_fast_mult;
    return CMD_OK;
}

int8_t CMD_Behavior_Handle_DECELERATE(CMD_t *ctx) {
    ctx->output.chassis.cmd.ctrl_vec.vx *= ctx->config->sensitivity.move_slow_mult;
    ctx->output.chassis.cmd.ctrl_vec.vy *= ctx->config->sensitivity.move_slow_mult;
    return CMD_OK;
}

int8_t CMD_Behavior_Handle_FIRE(CMD_t *ctx) {
    ctx->output.shoot.cmd.firecmd = true;
    return CMD_OK;
}

int8_t CMD_Behavior_Handle_FIRE_MODE(CMD_t *ctx) {
    ctx->output.shoot.cmd.mode = (ctx->output.shoot.cmd.mode + 1) % SHOOT_MODE_NUM;
    return CMD_OK;
}

int8_t CMD_Behavior_Handle_ROTOR(CMD_t *ctx) {
  ctx->output.chassis.cmd.mode = CHASSIS_MODE_ROTOR;
  ctx->output.chassis.cmd.mode_rotor = ROTOR_MODE_RAND;
  ctx->output.gimbal.cmd.mode = GIMBAL_MODE_RELATIVE;
  return CMD_OK;
}

int8_t CMD_Behavior_Handle_AUTOAIM(CMD_t *ctx) {
    /* TODO: 自瞄模式切换 */
    return CMD_OK;
}

int8_t CMD_Behavior_Handle_CHECKSOURCERCPC(CMD_t *ctx) {
    /* TODO: 切换RC和PC输入源 */
    if (ctx->active_source == CMD_SRC_PC) {
      ctx->active_source = CMD_SRC_RC;
      ctx->output.chassis.source = CMD_SRC_RC;
      ctx->output.gimbal.source = CMD_SRC_RC;
      ctx->output.shoot.source = CMD_SRC_RC;
    } else if(ctx->active_source == CMD_SRC_RC) {
      ctx->active_source = CMD_SRC_PC;
      ctx->output.chassis.source = CMD_SRC_PC;
      ctx->output.gimbal.source = CMD_SRC_PC;
      ctx->output.shoot.source = CMD_SRC_PC;
    }
    return CMD_OK;
}

/* 行为配置表 - 由宏生成 */
static const CMD_BehaviorConfig_t g_behavior_configs[] = {
    CMD_BEHAVIOR_TABLE(BUILD_BEHAVIOR_CONFIG)
};

/* ========================================================================== */
/*                           API实现                                            */
/* ========================================================================== */

int8_t CMD_Behavior_Init(void) {
    /* 当前静态配置，无需初始化 */
    return CMD_OK;
}

bool CMD_Behavior_IsTriggered(const CMD_RawInput_t *current,
                               const CMD_RawInput_t *last,
                               const CMD_BehaviorConfig_t *config) {
    if (config == NULL || current == NULL) {
        return false;
    }
    
        bool now_pressed = false;
        bool last_pressed = false;

        // 鼠标特殊按键处理
        if (config->key == (CMD_KEY_L_CLICK)) {
            now_pressed = current->pc.mouse.l_click;
            last_pressed = last ? last->pc.mouse.l_click : false;
        } else if (config->key == (CMD_KEY_R_CLICK)) {
            now_pressed = current->pc.mouse.r_click;
            last_pressed = last ? last->pc.mouse.r_click : false;
        } else if (config->key == (CMD_KEY_M_CLICK)) {
            now_pressed = current->pc.mouse.m_click;
            last_pressed = last ? last->pc.mouse.m_click : false;
        } else if (config->key == 0) {
            return false;
        } else {
            // 多按键组合检测
            now_pressed = ((current->pc.keyboard.bitmap & config->key) == config->key);
            last_pressed = last ? ((last->pc.keyboard.bitmap & config->key) == config->key) : false;
        }

        switch (config->trigger) {
            case CMD_ACTIVE_PRESSED:
                return now_pressed;
            case CMD_ACTIVE_RISING_EDGE:
                return now_pressed && !last_pressed;
            case CMD_ACTIVE_FALLING_EDGE:
                return !now_pressed && last_pressed;
            default:
                return false;
        }
}

int8_t CMD_Behavior_ProcessAll(CMD_t *ctx,
                                const CMD_RawInput_t *current,
                                const CMD_RawInput_t *last,
                                CMD_ModuleMask_t active_modules) {
    if (ctx == NULL || current == NULL) {
        return CMD_ERR_NULL;
    }
    
    for (size_t i = 0; i < BEHAVIOR_CONFIG_COUNT; i++) {
        const CMD_BehaviorConfig_t *config = &g_behavior_configs[i];
        
        /* 过滤模块掩码 */
        if ((config->module_mask & active_modules) == 0) {
            continue;
        }
        
        /* 检查是否触发 */
        if (CMD_Behavior_IsTriggered(current, last, config)) {
            if (config->handler != NULL) {
                config->handler(ctx);
            }
        }
    }
    
    return CMD_OK;
}

const CMD_BehaviorConfig_t* CMD_Behavior_GetConfig(CMD_Behavior_t behavior) {
    for (size_t i = 0; i < BEHAVIOR_CONFIG_COUNT; i++) {
        if (g_behavior_configs[i].behavior == behavior) {
            return &g_behavior_configs[i];
        }
    }
    return NULL;
}
