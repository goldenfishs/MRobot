/*
  RM电机驱动
*/
/* Includes ----------------------------------------------------------------- */
#include "motor_rm.h"
#include <stdbool.h>
#include <string.h>
#include "bsp/can.h"
#include "bsp/mm.h"
#include "bsp/time.h"
#include "component/user_math.h"

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

/* Private define ----------------------------------------------------------- */
#define GM6020_FB_ID_BASE        (0x205)
#define GM6020_CTRL_ID_BASE      (0x1ff)
#define GM6020_CTRL_ID_EXTAND    (0x2ff)

#define M3508_M2006_FB_ID_BASE   (0x201)
#define M3508_M2006_CTRL_ID_BASE (0x200)
#define M3508_M2006_CTRL_ID_EXTAND (0x1ff)
#define M3508_M2006_ID_SETTING_ID (0x700)

#define GM6020_MAX_ABS_LSB       (30000)
#define M3508_MAX_ABS_LSB        (16384)
#define M2006_MAX_ABS_LSB        (10000)

#define MOTOR_TX_BUF_SIZE        (8)
#define MOTOR_RX_BUF_SIZE        (8)
#define MOTOR_RM_FEEDBACK_TIMEOUT_US (100000u)

#define MOTOR_RM_TX_GROUP_M3508_M2006_LOW  (0u)
#define MOTOR_RM_TX_GROUP_M3508_M2006_HIGH (1u)
#define MOTOR_RM_TX_GROUP_GM6020_HIGH      (2u)
#define MOTOR_RM_TX_GROUP_MASK(group)      ((uint8_t)(1u << (group)))

#define MOTOR_ENC_RES            (8192)   /* 电机编码器分辨率 */
#define MOTOR_CUR_RES            (16384)  /* 电机转矩电流分辨率 */
#define MOTOR_RM_SUSPICIOUS_DELTA_COUNT ((MOTOR_ENC_RES * 9) / 20)

/* USER DEFINE BEGIN */

/* USER DEFINE END */

/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* USER STRUCT BEGIN */

/* USER STRUCT END */

/* Private variables -------------------------------------------------------- */
static MOTOR_RM_CANManager_t *can_managers[BSP_CAN_NUM] = {NULL};
/* C++ motor 适配层调试快照：记录最近一次 RM 组帧发送。 */
/* MOTOR_CPP_ADAPTER_DEBUG_BEGIN: snapshots read by C++ tests/tools. */
static MOTOR_RM_TxDebug_t motor_rm_tx_debug = {0};
MOTOR_RM_SlotTxDebug_t g_motor_rm_slot_tx_debug[MOTOR_RM_MAX_MOTORS] = {0};
/* MOTOR_CPP_ADAPTER_DEBUG_END */

/* Private function  -------------------------------------------------------- */
/* USER FUNCTION BEGIN */

/* USER FUNCTION END */

static int8_t MOTOR_RM_GetLogicalIndex(uint16_t can_id, MOTOR_RM_Module_t module) {
    switch (module) {
        case MOTOR_M2006:
        case MOTOR_M3508:
            if (can_id >= M3508_M2006_FB_ID_BASE && can_id <= M3508_M2006_FB_ID_BASE + 7) {
                return can_id - M3508_M2006_FB_ID_BASE;
            }
            break;
        case MOTOR_GM6020:
            if (can_id >= GM6020_FB_ID_BASE && can_id <= GM6020_FB_ID_BASE + 6) {
                return can_id - GM6020_FB_ID_BASE + 4;
            }
            break;
        default:
            break;
    }
    return DEVICE_ERR;
}

static int8_t MOTOR_RM_GetTxGroupById(uint16_t can_id) {
    switch (can_id) {
        case M3508_M2006_FB_ID_BASE:
        case M3508_M2006_FB_ID_BASE+1:
        case M3508_M2006_FB_ID_BASE+2:
        case M3508_M2006_FB_ID_BASE+3:
            return MOTOR_RM_TX_GROUP_M3508_M2006_LOW;
        case M3508_M2006_FB_ID_BASE+4:
        case M3508_M2006_FB_ID_BASE+5:
        case M3508_M2006_FB_ID_BASE+6:
        case M3508_M2006_FB_ID_BASE+7:
            return MOTOR_RM_TX_GROUP_M3508_M2006_HIGH;
        case GM6020_FB_ID_BASE+4:
        case GM6020_FB_ID_BASE+5:
        case GM6020_FB_ID_BASE+6:
            return MOTOR_RM_TX_GROUP_GM6020_HIGH;
        default:
            return DEVICE_ERR;
    }
}

static int8_t MOTOR_RM_GetTxGroup(MOTOR_RM_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    return MOTOR_RM_GetTxGroupById(param->id);
}

static void MOTOR_RM_MarkPendingGroup(MOTOR_RM_CANManager_t *manager, int8_t group) {
    if (manager == NULL || group < 0) return;
    manager->pending_tx_groups |= MOTOR_RM_TX_GROUP_MASK((uint8_t)group);
}

static int8_t MOTOR_RM_FillTxFrame(const MOTOR_RM_CANManager_t *manager,
                                   uint8_t group,
                                   BSP_CAN_StdDataFrame_t *tx_frame) {
    if (manager == NULL || tx_frame == NULL) return DEVICE_ERR_NULL;
    const MOTOR_RM_MsgOutput_t *output_msg = &manager->output_msg;
    tx_frame->dlc = MOTOR_TX_BUF_SIZE;
    switch (group) {
        case MOTOR_RM_TX_GROUP_M3508_M2006_LOW:
            tx_frame->id = M3508_M2006_CTRL_ID_BASE;
            for (int i = 0; i < 4; i++) {
                tx_frame->data[i*2] = (uint8_t)((output_msg->output[i] >> 8) & 0xFF);
                tx_frame->data[i*2+1] = (uint8_t)(output_msg->output[i] & 0xFF);
            }
            return DEVICE_OK;
        case MOTOR_RM_TX_GROUP_M3508_M2006_HIGH:
            tx_frame->id = M3508_M2006_CTRL_ID_EXTAND;
            for (int i = 4; i < 8; i++) {
                tx_frame->data[(i-4)*2] = (uint8_t)((output_msg->output[i] >> 8) & 0xFF);
                tx_frame->data[(i-4)*2+1] = (uint8_t)(output_msg->output[i] & 0xFF);
            }
            return DEVICE_OK;
        case MOTOR_RM_TX_GROUP_GM6020_HIGH:
            tx_frame->id = GM6020_CTRL_ID_EXTAND;
            for (int i = 8; i < 11; i++) {
                tx_frame->data[(i-8)*2] = (uint8_t)((output_msg->output[i] >> 8) & 0xFF);
                tx_frame->data[(i-8)*2+1] = (uint8_t)(output_msg->output[i] & 0xFF);
            }
            tx_frame->data[6] = 0;
            tx_frame->data[7] = 0;
            return DEVICE_OK;
        default:
            return DEVICE_ERR;
    }
}

static void MOTOR_RM_UpdateTxDebug(const MOTOR_RM_CANManager_t *manager,
                                   const BSP_CAN_StdDataFrame_t *tx_frame,
                                   uint16_t source_motor_id,
                                   int8_t logical_index) {
    if (manager == NULL || tx_frame == NULL) return;
    motor_rm_tx_debug.valid = 1;
    motor_rm_tx_debug.can = manager->can;
    motor_rm_tx_debug.source_motor_id = source_motor_id;
    motor_rm_tx_debug.tx_frame_id = tx_frame->id;
    motor_rm_tx_debug.logical_index = logical_index;
    if (logical_index >= 0 && logical_index < MOTOR_RM_MAX_MOTORS) {
        motor_rm_tx_debug.requested_current = manager->output_msg.output[logical_index];
    } else {
        motor_rm_tx_debug.requested_current = 0;
    }
    memcpy(motor_rm_tx_debug.grouped_output,
           manager->output_msg.output,
           sizeof(motor_rm_tx_debug.grouped_output));
    memcpy(motor_rm_tx_debug.tx_data, tx_frame->data, sizeof(motor_rm_tx_debug.tx_data));
    motor_rm_tx_debug.pending_tx_groups = manager->pending_tx_groups;

    for (int i = 0; i < MOTOR_RM_MAX_MOTORS; i++) {
        g_motor_rm_slot_tx_debug[i].valid = 1;
        g_motor_rm_slot_tx_debug[i].can = manager->can;
        g_motor_rm_slot_tx_debug[i].tx_frame_id = tx_frame->id;
        g_motor_rm_slot_tx_debug[i].logical_index = (int8_t)i;
        g_motor_rm_slot_tx_debug[i].output_value = manager->output_msg.output[i];
        memcpy(g_motor_rm_slot_tx_debug[i].tx_data,
               tx_frame->data,
               sizeof(g_motor_rm_slot_tx_debug[i].tx_data));
    }
}

static int8_t MOTOR_RM_SendGroup(MOTOR_RM_CANManager_t *manager,
                                 uint8_t group,
                                 uint16_t source_motor_id,
                                 int8_t logical_index) {
    if (manager == NULL) return DEVICE_ERR_NULL;
    BSP_CAN_StdDataFrame_t tx_frame;
    const int8_t frame_ret = MOTOR_RM_FillTxFrame(manager, group, &tx_frame);
    if (frame_ret != DEVICE_OK) return frame_ret;

    MOTOR_RM_UpdateTxDebug(manager, &tx_frame, source_motor_id, logical_index);
    const int8_t ret = BSP_CAN_TransmitStdDataFrame(manager->can, &tx_frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
    if (ret == DEVICE_OK) {
        manager->pending_tx_groups &= (uint8_t)~MOTOR_RM_TX_GROUP_MASK(group);
        motor_rm_tx_debug.pending_tx_groups = manager->pending_tx_groups;
        motor_rm_tx_debug.flush_count++;
    }
    return ret;
}

static float MOTOR_RM_GetRatio(MOTOR_RM_Module_t module) {
    switch (module) {
        case MOTOR_M2006: return 36.0f;
        case MOTOR_M3508: return 3591.0f / 187.0f;
        case MOTOR_GM6020: return 1.0f;
        default: return 1.0f;
    }
}

static int16_t MOTOR_RM_GetLSB(MOTOR_RM_Module_t module) {
    switch (module) {
        case MOTOR_M2006: return M2006_MAX_ABS_LSB;
        case MOTOR_M3508: return M3508_MAX_ABS_LSB;
        case MOTOR_GM6020: return GM6020_MAX_ABS_LSB;
        default: return DEVICE_ERR;
    }
}

static float MOTOR_RM_GetCurrentRangeAmp(MOTOR_RM_Module_t module) {
    switch (module) {
        case MOTOR_M2006: return 10.0f;
        case MOTOR_M3508: return 20.0f;
        case MOTOR_GM6020: return 3.0f;
        default: return 0.0f;
    }
}

static float MOTOR_RM_WrapAnglePositive(float angle) {
    while (angle < 0.0f) {
        angle += M_2PI;
    }
    while (angle >= M_2PI) {
        angle -= M_2PI;
    }
    return angle;
}

static int32_t MOTOR_RM_UnwrapRawDelta(uint16_t current_raw_angle, uint16_t last_raw_angle) {
    int32_t delta = (int32_t)current_raw_angle - (int32_t)last_raw_angle;
    if (delta > (MOTOR_ENC_RES / 2)) {
        delta -= MOTOR_ENC_RES;
    } else if (delta < -(MOTOR_ENC_RES / 2)) {
        delta += MOTOR_ENC_RES;
    }
    return delta;
}

static void MOTOR_RM_ResetAngleTracker(MOTOR_RM_t *motor, uint16_t raw_angle) {
    if (motor == NULL) return;
    motor->last_raw_angle = raw_angle;
    motor->angle_inited = true;
    motor->gearbox_round_count = 0;
    motor->gearbox_total_raw_count = 0;
    motor->gearbox_total_angle = 0.0f;
}

static MOTOR_RM_CANManager_t* MOTOR_RM_GetCANManager(BSP_CAN_t can) {
    if (can >= BSP_CAN_NUM) return NULL;
    return can_managers[can];
}

static int8_t MOTOR_RM_CreateCANManager(BSP_CAN_t can) {
    if (can >= BSP_CAN_NUM) return DEVICE_ERR;
    if (can_managers[can] != NULL) return DEVICE_OK;
    can_managers[can] = (MOTOR_RM_CANManager_t*)BSP_Malloc(sizeof(MOTOR_RM_CANManager_t));
    if (can_managers[can] == NULL) return DEVICE_ERR;
    memset(can_managers[can], 0, sizeof(MOTOR_RM_CANManager_t));
    can_managers[can]->can = can;
    return DEVICE_OK;
}

static void Motor_RM_Decode(MOTOR_RM_t *motor, BSP_CAN_Message_t *msg) {
    uint16_t raw_angle = (uint16_t)((msg->data[0] << 8) | msg->data[1]);
    int16_t raw_speed = (int16_t)((msg->data[2] << 8) | msg->data[3]);
    int16_t raw_current = (int16_t)((msg->data[4] << 8) | msg->data[5]);
    int16_t lsb = MOTOR_RM_GetLSB(motor->param.module);
    float ratio = MOTOR_RM_GetRatio(motor->param.module);

    uint64_t now_time = BSP_TIME_Get();
    float rotor_angle = raw_angle / (float)MOTOR_ENC_RES * M_2PI;
    float rotor_speed = raw_speed;
    float torque_current = raw_current * lsb / (float)MOTOR_CUR_RES;

    /* MOTOR_CPP_ADAPTER_DATA: preserve raw feedback for rm_protocol.cpp. */
    motor->motor.raw_feedback.raw_angle = raw_angle;
    motor->motor.raw_feedback.raw_speed = raw_speed;
    motor->motor.raw_feedback.raw_current = raw_current;
    motor->motor.raw_feedback.raw_temp = msg->data[6];
    motor->motor.raw_feedback.raw_error_code = msg->data[7];

    if (motor->param.gear) {
        if (!motor->angle_inited) {
            MOTOR_RM_ResetAngleTracker(motor, raw_angle);
        }
        int32_t delta = MOTOR_RM_UnwrapRawDelta(raw_angle, motor->last_raw_angle);
        if (delta >= MOTOR_RM_SUSPICIOUS_DELTA_COUNT || delta <= -MOTOR_RM_SUSPICIOUS_DELTA_COUNT) {
            motor->angle_lost_count++;
        }
        motor->gearbox_total_raw_count += delta;
        motor->gearbox_round_count = motor->gearbox_total_raw_count / MOTOR_ENC_RES;
        motor->last_raw_angle = raw_angle;
        motor->gearbox_total_angle = ((float)motor->gearbox_total_raw_count / (float)MOTOR_ENC_RES) * M_2PI / ratio;
        // 输出轴多圈绝对值
        motor->feedback.rotor_total_angle = motor->gearbox_total_angle;
        motor->feedback.rotor_single_angle = MOTOR_RM_WrapAnglePositive(motor->gearbox_total_angle);
        motor->feedback.rotor_abs_angle = motor->feedback.rotor_single_angle;
        motor->feedback.rotor_speed = rotor_speed / ratio;
        motor->feedback.torque_current = torque_current * ratio;
    } else {
        // 非gear模式，直接用转子单圈
        MOTOR_RM_ResetAngleTracker(motor, raw_angle);
        motor->feedback.rotor_abs_angle = rotor_angle;
        motor->feedback.rotor_total_angle = rotor_angle;
        motor->feedback.rotor_single_angle = rotor_angle;
        motor->feedback.rotor_speed = rotor_speed;
        motor->feedback.torque_current = torque_current;
    }
    motor->feedback.angle_valid = (motor->angle_lost_count == 0U);
    if (motor->motor.reverse) {
        motor->feedback.rotor_total_angle = -motor->feedback.rotor_total_angle;
        motor->feedback.rotor_single_angle = MOTOR_RM_WrapAnglePositive(-motor->feedback.rotor_single_angle);
        motor->feedback.rotor_abs_angle = motor->feedback.rotor_single_angle;
        motor->feedback.rotor_speed = -motor->feedback.rotor_speed;
        motor->feedback.torque_current = -motor->feedback.torque_current;
    }
    motor->feedback.temp = msg->data[6];
    motor->feedback.angle_lost_count = motor->angle_lost_count;
    motor->feedback.last_update_time = (uint32_t)now_time;
    motor->last_feedback_time = (uint32_t)now_time;
}

static int8_t MOTOR_RM_BindMotor(MOTOR_RM_CANManager_t *manager, MOTOR_RM_Param_t *param, MOTOR_RM_t *motor) {
    if (manager == NULL || param == NULL || motor == NULL) return DEVICE_ERR_NULL;
    for (int i = 0; i < manager->motor_count; i++) {
        if (manager->motors[i] && manager->motors[i]->param.id == param->id) {
            return DEVICE_ERR_INITED;
        }
    }
    if (manager->motor_count >= MOTOR_RM_MAX_MOTORS) return DEVICE_ERR;
    memset(motor, 0, sizeof(MOTOR_RM_t));
    memcpy(&motor->param, param, sizeof(MOTOR_RM_Param_t));
    motor->motor.reverse = param->reverse;
    if (BSP_CAN_RegisterLatestId(param->can, param->id) != BSP_OK) {
        return DEVICE_ERR;
    }
    manager->motors[manager->motor_count] = motor;
    manager->motor_count++;
    return DEVICE_OK;
}

static MOTOR_RM_t* MOTOR_RM_FindMotorById(const MOTOR_RM_CANManager_t *manager, uint16_t id) {
    if (manager == NULL) return NULL;
    for (int i = 0; i < manager->motor_count; i++) {
        MOTOR_RM_t *motor = manager->motors[i];
        if (motor && motor->param.id == id) {
            return motor;
        }
    }
    for (int i = 0; i < manager->external_motor_count; i++) {
        MOTOR_RM_t *motor = manager->external_motors[i];
        if (motor && motor->param.id == id) {
            return motor;
        }
    }
    return NULL;
}

static int8_t MOTOR_RM_BindExternalMotor(MOTOR_RM_CANManager_t *manager, MOTOR_RM_Param_t *param, MOTOR_RM_t *motor) {
    if (manager == NULL || param == NULL || motor == NULL) return DEVICE_ERR_NULL;
    if (MOTOR_RM_FindMotorById(manager, param->id) != NULL) return DEVICE_ERR_INITED;
    if (manager->external_motor_count >= MOTOR_RM_MAX_MOTORS) return DEVICE_ERR;
    memset(motor, 0, sizeof(MOTOR_RM_t));
    memcpy(&motor->param, param, sizeof(MOTOR_RM_Param_t));
    motor->motor.reverse = param->reverse;
    if (BSP_CAN_RegisterLatestId(param->can, param->id) != BSP_OK) {
        return DEVICE_ERR;
    }
    manager->external_motors[manager->external_motor_count] = motor;
    manager->external_motor_count++;
    return DEVICE_OK;
}

static MOTOR_RM_Param_t* MOTOR_RM_FindParamByTxGroup(MOTOR_RM_CANManager_t *manager, uint8_t group) {
    if (manager == NULL) return NULL;
    for (int i = 0; i < manager->motor_count; i++) {
        MOTOR_RM_t *motor = manager->motors[i];
        if (motor != NULL && MOTOR_RM_GetTxGroup(&motor->param) == (int8_t)group) {
            return &motor->param;
        }
    }
    for (int i = 0; i < manager->external_motor_count; i++) {
        MOTOR_RM_t *motor = manager->external_motors[i];
        if (motor != NULL && MOTOR_RM_GetTxGroup(&motor->param) == (int8_t)group) {
            return &motor->param;
        }
    }
    return NULL;
}

/* Exported functions ------------------------------------------------------- */

int8_t MOTOR_RM_Register(MOTOR_RM_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    if (MOTOR_RM_CreateCANManager(param->can) != DEVICE_OK) return DEVICE_ERR;
    MOTOR_RM_CANManager_t *manager = MOTOR_RM_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR;
    MOTOR_RM_t *new_motor = (MOTOR_RM_t*)BSP_Malloc(sizeof(MOTOR_RM_t));
    if (new_motor == NULL) return DEVICE_ERR;
    const int8_t ret = MOTOR_RM_BindMotor(manager, param, new_motor);
    if (ret != DEVICE_OK) {
        BSP_Free(new_motor);
        return ret;
    }
    return DEVICE_OK;
}

int8_t MOTOR_RM_Update(MOTOR_RM_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    MOTOR_RM_CANManager_t *manager = MOTOR_RM_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR_NO_DEV;
    MOTOR_RM_t *motor = MOTOR_RM_FindMotorById(manager, param->id);
    if (motor == NULL) return DEVICE_ERR_NO_DEV;
    BSP_CAN_Message_t rx_msg;
    if (BSP_CAN_GetLatestMessage(param->can, param->id, &rx_msg) != BSP_OK) {
        uint64_t now_time = BSP_TIME_Get();
        if (now_time - motor->motor.header.last_online_time > MOTOR_RM_FEEDBACK_TIMEOUT_US) {
            motor->motor.header.online = false;
            return DEVICE_ERR_NO_DEV;
        }
        return DEVICE_ERR;
    }
    motor->motor.header.online = true;
    motor->motor.header.last_online_time = BSP_TIME_Get();
    Motor_RM_Decode(motor, &rx_msg);
    motor->motor.feedback = motor->feedback;
    return DEVICE_OK;
}

int8_t MOTOR_RM_UpdateAll(void) {
    int8_t ret = DEVICE_OK;
    for (int can = 0; can < BSP_CAN_NUM; can++) {
        MOTOR_RM_CANManager_t *manager = MOTOR_RM_GetCANManager((BSP_CAN_t)can);
        if (manager == NULL) continue;
        for (int i = 0; i < manager->motor_count; i++) {
            MOTOR_RM_t *motor = manager->motors[i];
            if (motor != NULL) {
                if (MOTOR_RM_Update(&motor->param) != DEVICE_OK) {
                    ret = DEVICE_ERR;
                }
            }
        }
        for (int i = 0; i < manager->external_motor_count; i++) {
            MOTOR_RM_t *motor = manager->external_motors[i];
            if (motor != NULL) {
                if (MOTOR_RM_Update(&motor->param) != DEVICE_OK) {
                    ret = DEVICE_ERR;
                }
            }
        }
    }
    return ret;
}

/* -------------------------------------------------------------------------- */
/* 原生 C 驱动接口：兼容旧模块的归一化输出、立即组帧发送与状态控制。 */
/* -------------------------------------------------------------------------- */

/*
 * 底层兼容接口：输入为归一化输出值 [-1, 1]。
 * 主要保留给旧代码或直接比例输出场景使用。
 */
int8_t MOTOR_RM_SetOutput(MOTOR_RM_Param_t *param, float value) {
    if (param == NULL) return DEVICE_ERR_NULL;
    MOTOR_RM_CANManager_t *manager = MOTOR_RM_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR_NO_DEV;
    if (value > 1.0f) value = 1.0f;
    if (value < -1.0f) value = -1.0f;
    if (param->reverse){
        value = -value;
    }
    MOTOR_RM_t *motor = MOTOR_RM_GetMotor(param);
    if (motor == NULL) return DEVICE_ERR_NO_DEV;
    int8_t logical_index = MOTOR_RM_GetLogicalIndex(param->id, param->module);
    if (logical_index < 0) return DEVICE_ERR;
    MOTOR_RM_MsgOutput_t *output_msg = &manager->output_msg;
    int16_t output_value = (int16_t)(value * (float)MOTOR_RM_GetLSB(param->module));
    output_msg->output[logical_index] = output_value;
    MOTOR_RM_MarkPendingGroup(manager, MOTOR_RM_GetTxGroup(param));
    return DEVICE_OK;
}

int8_t MOTOR_RM_Ctrl(MOTOR_RM_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    MOTOR_RM_CANManager_t *manager = MOTOR_RM_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR_NO_DEV;
    int8_t logical_index = MOTOR_RM_GetLogicalIndex(param->id, param->module);
    const int8_t group = MOTOR_RM_GetTxGroup(param);
    if (group < 0) return DEVICE_ERR;
    return MOTOR_RM_SendGroup(manager, (uint8_t)group, param->id, logical_index);
}

int8_t MOTOR_RM_FlushGroup(MOTOR_RM_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    MOTOR_RM_CANManager_t *manager = MOTOR_RM_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR_NO_DEV;
    const int8_t group = MOTOR_RM_GetTxGroup(param);
    if (group < 0) return DEVICE_ERR;
    if ((manager->pending_tx_groups & MOTOR_RM_TX_GROUP_MASK((uint8_t)group)) == 0u) {
        return DEVICE_OK;
    }
    return MOTOR_RM_Ctrl(param);
}

int8_t MOTOR_RM_FlushCAN(BSP_CAN_t can) {
    MOTOR_RM_CANManager_t *manager = MOTOR_RM_GetCANManager(can);
    if (manager == NULL) return DEVICE_ERR_NO_DEV;
    int8_t ret = DEVICE_OK;
    const uint8_t pending = manager->pending_tx_groups;
    for (uint8_t group = MOTOR_RM_TX_GROUP_M3508_M2006_LOW;
         group <= MOTOR_RM_TX_GROUP_GM6020_HIGH;
         group++) {
        if ((pending & MOTOR_RM_TX_GROUP_MASK(group)) == 0u) continue;
        MOTOR_RM_Param_t *param = MOTOR_RM_FindParamByTxGroup(manager, group);
        if (param == NULL || MOTOR_RM_Ctrl(param) != DEVICE_OK) {
            ret = DEVICE_ERR;
        }
    }
    return ret;
}

int8_t MOTOR_RM_FlushAll(void) {
    int8_t ret = DEVICE_OK;
    for (int can = 0; can < BSP_CAN_NUM; can++) {
        MOTOR_RM_CANManager_t *manager = MOTOR_RM_GetCANManager((BSP_CAN_t)can);
        if (manager == NULL || manager->pending_tx_groups == 0u) continue;
        if (MOTOR_RM_FlushCAN((BSP_CAN_t)can) != DEVICE_OK) {
            ret = DEVICE_ERR;
        }
    }
    return ret;
}

MOTOR_RM_t* MOTOR_RM_GetMotor(MOTOR_RM_Param_t *param) {
    if (param == NULL) return NULL;
    MOTOR_RM_CANManager_t *manager = MOTOR_RM_GetCANManager(param->can);
    if (manager == NULL) return NULL;
    return MOTOR_RM_FindMotorById(manager, param->id);
}

int8_t MOTOR_RM_Relax(MOTOR_RM_Param_t *param) {
    return MOTOR_RM_SetOutput(param, 0.0f);
}

int8_t MOTOR_RM_Offine(MOTOR_RM_Param_t *param) {
    MOTOR_RM_t *motor = MOTOR_RM_GetMotor(param);
    if (motor) {
        motor->motor.header.online = false;
        return DEVICE_OK;
    }
    return DEVICE_ERR_NO_DEV;
}

/* -------------------------------------------------------------------------- */
/* C++ motor 适配接口：protocol/motor_t 使用的外部实例、物理量命令、Flush 与调试。 */
/* -------------------------------------------------------------------------- */

/* C++ 驱动层将外部持有的 vendor instance 绑定到 C 管理器。 */
/* MOTOR_CPP_ADAPTER_IMPL_BEGIN: used by User/device/motor/protocol/rm_protocol.cpp. */
int8_t MOTOR_RM_AttachExternal(MOTOR_RM_Param_t *param, MOTOR_RM_t *external_motor) {
    if (param == NULL || external_motor == NULL) return DEVICE_ERR_NULL;
    if (MOTOR_RM_CreateCANManager(param->can) != DEVICE_OK) return DEVICE_ERR;
    MOTOR_RM_CANManager_t *manager = MOTOR_RM_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR;
    return MOTOR_RM_BindExternalMotor(manager, param, external_motor);
}

/* C++ RM 驱动的主下发接口：输入为转子侧目标电流，单位 A。 */
int8_t MOTOR_RM_SetTorqueCurrent(MOTOR_RM_Param_t *param, float current_a) {
    if (param == NULL) return DEVICE_ERR_NULL;
    const float lsb = (float)MOTOR_RM_GetLSB(param->module);
    const float current_range_a = MOTOR_RM_GetCurrentRangeAmp(param->module);
    if (lsb <= 0.0f || current_range_a <= 0.0f) return DEVICE_ERR;
    const float raw_current = current_a * lsb / current_range_a;
    const float normalized = raw_current / lsb;
    return MOTOR_RM_SetOutput(param, normalized);
}

/* C++ 驱动层读取底层原始反馈缓存。 */
const MOTOR_RM_RawFeedback_t* MOTOR_RM_GetRawFeedback(MOTOR_RM_Param_t *param) {
    MOTOR_RM_t *motor = MOTOR_RM_GetMotor(param);
    if (motor == NULL) {
        return NULL;
    }
    return &motor->motor.raw_feedback;
}

const MOTOR_RM_TxDebug_t* MOTOR_RM_GetTxDebug(void) {
    return &motor_rm_tx_debug;
}

const MOTOR_RM_SlotTxDebug_t* MOTOR_RM_GetSlotTxDebug(uint8_t logical_index) {
    if (logical_index >= MOTOR_RM_MAX_MOTORS) {
        return NULL;
    }
    return &g_motor_rm_slot_tx_debug[logical_index];
}
/* MOTOR_CPP_ADAPTER_IMPL_END */
