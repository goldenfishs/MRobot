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

#define MOTOR_ENC_RES            (8192)   /* 电机编码器分辨率 */
#define MOTOR_CUR_RES            (16384)  /* 电机转矩电流分辨率 */

/* USER DEFINE BEGIN */

/* USER DEFINE END */

/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* USER STRUCT BEGIN */

/* USER STRUCT END */

/* Private variables -------------------------------------------------------- */
static MOTOR_RM_CANManager_t *can_managers[BSP_CAN_NUM] = {NULL};

/* Private function  -------------------------------------------------------- */
/* USER FUNCTION BEGIN */

/* USER FUNCTION END */

static int8_t MOTOR_RM_GetLogicalIndex(uint16_t can_id, MOTOR_RM_Module_t module) {
    switch (module) {
        case MOTOR_M2006:
        case MOTOR_M3508:
            if (can_id >= M3508_M2006_FB_ID_BASE && can_id < M3508_M2006_FB_ID_BASE + 7) {
                return can_id - M3508_M2006_FB_ID_BASE;
            }
            break;
        case MOTOR_GM6020:
            if (can_id >= GM6020_FB_ID_BASE && can_id < GM6020_FB_ID_BASE + 6) {
                return can_id - GM6020_FB_ID_BASE + 4;
            }
            break;
        default:
            break;
    }
    return DEVICE_ERR;
}

static float MOTOR_RM_GetRatio(MOTOR_RM_Module_t module) {
    switch (module) {
        case MOTOR_M2006: return 36.0f;
        case MOTOR_M3508: return 19.0f;
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

    float rotor_angle = raw_angle / (float)MOTOR_ENC_RES * M_2PI;
    float rotor_speed = raw_speed;
    float torque_current = raw_current * lsb / (float)MOTOR_CUR_RES;

    if (motor->param.gear) {
        // 多圈累加
        int32_t delta = (int32_t)raw_angle - (int32_t)motor->last_raw_angle;
        if (delta > (MOTOR_ENC_RES / 2)) {
            motor->gearbox_round_count--;
        } else if (delta < -(MOTOR_ENC_RES / 2)) {
            motor->gearbox_round_count++;
        }
        motor->last_raw_angle = raw_angle;
        float single_turn = rotor_angle;
        motor->gearbox_total_angle = (motor->gearbox_round_count * M_2PI + single_turn) / ratio;
        // 输出轴多圈绝对值
        motor->feedback.rotor_abs_angle = motor->gearbox_total_angle;
        motor->feedback.rotor_speed = rotor_speed / ratio;
        motor->feedback.torque_current = torque_current * ratio;
    } else {
        // 非gear模式，直接用转子单圈
        motor->gearbox_round_count = 0;
        motor->last_raw_angle = raw_angle;
        motor->gearbox_total_angle = 0.0f;
        motor->feedback.rotor_abs_angle = rotor_angle;
        motor->feedback.rotor_speed = rotor_speed;
        motor->feedback.torque_current = torque_current;
    }
    if (motor->motor.reverse) {
        while (motor->feedback.rotor_abs_angle < 0) {
            motor->feedback.rotor_abs_angle += M_2PI;
        }
        while (motor->feedback.rotor_abs_angle >= M_2PI) {
            motor->feedback.rotor_abs_angle -= M_2PI;
        }
        motor->feedback.rotor_abs_angle = M_2PI - motor->feedback.rotor_abs_angle;
        motor->feedback.rotor_speed = -motor->feedback.rotor_speed;
        motor->feedback.torque_current = -motor->feedback.torque_current;
    }
    motor->feedback.temp = msg->data[6];
}

/* Exported functions ------------------------------------------------------- */

int8_t MOTOR_RM_Register(MOTOR_RM_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    if (MOTOR_RM_CreateCANManager(param->can) != DEVICE_OK) return DEVICE_ERR;
    MOTOR_RM_CANManager_t *manager = MOTOR_RM_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR;
    // 检查是否已注册
    for (int i = 0; i < manager->motor_count; i++) {
        if (manager->motors[i] && manager->motors[i]->param.id == param->id) {
            return DEVICE_ERR_INITED;
        }
    }
    // 检查数量
    if (manager->motor_count >= MOTOR_RM_MAX_MOTORS) return DEVICE_ERR;
    // 创建新电机实例
    MOTOR_RM_t *new_motor = (MOTOR_RM_t*)BSP_Malloc(sizeof(MOTOR_RM_t));
    if (new_motor == NULL) return DEVICE_ERR;
    memcpy(&new_motor->param, param, sizeof(MOTOR_RM_Param_t));
    memset(&new_motor->motor, 0, sizeof(MOTOR_t));
    new_motor->motor.reverse = param->reverse;
    // 注册CAN接收ID
    if (BSP_CAN_RegisterId(param->can, param->id, 3) != BSP_OK) {
        BSP_Free(new_motor);
        return DEVICE_ERR;
    }
    manager->motors[manager->motor_count] = new_motor;
    manager->motor_count++;
    return DEVICE_OK;
}

int8_t MOTOR_RM_Update(MOTOR_RM_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    MOTOR_RM_CANManager_t *manager = MOTOR_RM_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR_NO_DEV;
    for (int i = 0; i < manager->motor_count; i++) {
        MOTOR_RM_t *motor = manager->motors[i];
        if (motor && motor->param.id == param->id) {
            BSP_CAN_Message_t rx_msg;
            if (BSP_CAN_GetMessage(param->can, param->id, &rx_msg, BSP_CAN_TIMEOUT_IMMEDIATE) != BSP_OK) {
                uint64_t now_time = BSP_TIME_Get();
                if (now_time - motor->motor.header.last_online_time > 1000) {
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
    }
    return DEVICE_ERR_NO_DEV;
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
    }
    return ret;
}

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
    return DEVICE_OK;
}

int8_t MOTOR_RM_Ctrl(MOTOR_RM_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    MOTOR_RM_CANManager_t *manager = MOTOR_RM_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR_NO_DEV;
    MOTOR_RM_MsgOutput_t *output_msg = &manager->output_msg;
    BSP_CAN_StdDataFrame_t tx_frame;
    uint16_t id = param->id;
    switch (id) {
        case M3508_M2006_FB_ID_BASE:
        case M3508_M2006_FB_ID_BASE+1:
        case M3508_M2006_FB_ID_BASE+2:
        case M3508_M2006_FB_ID_BASE+3:
            tx_frame.id = M3508_M2006_CTRL_ID_BASE;
            tx_frame.dlc = MOTOR_TX_BUF_SIZE;
            for (int i = 0; i < 4; i++) {
                tx_frame.data[i*2] = (uint8_t)((output_msg->output[i] >> 8) & 0xFF);
                tx_frame.data[i*2+1] = (uint8_t)(output_msg->output[i] & 0xFF);
            }
            break;
        case M3508_M2006_FB_ID_BASE+4:
        case M3508_M2006_FB_ID_BASE+5:
        case M3508_M2006_FB_ID_BASE+6:
        case M3508_M2006_FB_ID_BASE+7:
            tx_frame.id = M3508_M2006_CTRL_ID_EXTAND;
            tx_frame.dlc = MOTOR_TX_BUF_SIZE;
            for (int i = 4; i < 8; i++) {
                tx_frame.data[(i-4)*2] = (uint8_t)((output_msg->output[i] >> 8) & 0xFF);
                tx_frame.data[(i-4)*2+1] = (uint8_t)(output_msg->output[i] & 0xFF);
            }
            break;
        case GM6020_FB_ID_BASE+4:
        case GM6020_FB_ID_BASE+5:
        case GM6020_FB_ID_BASE+6:
            tx_frame.id = GM6020_CTRL_ID_EXTAND;
            tx_frame.dlc = MOTOR_TX_BUF_SIZE;
            for (int i = 8; i < 11; i++) {
                tx_frame.data[(i-8)*2] = (uint8_t)((output_msg->output[i] >> 8) & 0xFF);
                tx_frame.data[(i-8)*2+1] = (uint8_t)(output_msg->output[i] & 0xFF);
            }
            tx_frame.data[6] = 0;
            tx_frame.data[7] = 0;
            break;
        default:
            return DEVICE_ERR;
    }
    return BSP_CAN_TransmitStdDataFrame(param->can, &tx_frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}

MOTOR_RM_t* MOTOR_RM_GetMotor(MOTOR_RM_Param_t *param) {
    if (param == NULL) return NULL;
    MOTOR_RM_CANManager_t *manager = MOTOR_RM_GetCANManager(param->can);
    if (manager == NULL) return NULL;
    for (int i = 0; i < manager->motor_count; i++) {
        MOTOR_RM_t *motor = manager->motors[i];
        if (motor && motor->param.id == param->id) {
            return motor;
        }
    }
    return NULL;
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