/*
  CAN总线上的设备
  将所有CAN总线上挂载的设备抽象成一个设备进行配置和控制
*/

/* Includes ----------------------------------------------------------------- */
#include "motor_rm.h"

#include <stdbool.h>
#include <string.h>

#include "bsp/can.h"
#include "bsp/mm.h"
#include "bsp/time.h"
#include "component/user_math.h"

/* Private define ----------------------------------------------------------- */
/* Motor id */
/* id		feedback id		control id */
/* 1-4		0x205 to 0x208  0x1ff */
/* 5-7		0x209 to 0x20B  0x2ff */
#define GM6020_FB_ID_BASE (0x205)
#define GM6020_CTRL_ID_BASE (0x1ff)
#define GM6020_CTRL_ID_EXTAND (0x2ff)

/* id		feedback id		control id */
/* 1-4		0x201 to 0x204  0x200 */
/* 5-8		0x205 to 0x208  0x1ff */
#define M3508_M2006_FB_ID_BASE (0x201)
#define M3508_M2006_CTRL_ID_BASE (0x200)
#define M3508_M2006_CTRL_ID_EXTAND (0x1ff)
#define M3508_M2006_ID_SETTING_ID (0x700)

#define GM6020_MAX_ABS_LSB (30000)
#define M3508_MAX_ABS_LSB (16384)
#define M2006_MAX_ABS_LSB (10000)

#define MOTOR_TX_BUF_SIZE (8)
#define MOTOR_RX_BUF_SIZE (8)

#define MOTOR_ENC_RES (8192)  /* 电机编码器分辨率 */
#define MOTOR_CUR_RES (16384) /* 电机转矩电流分辨率 */

/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */
static MOTOR_RM_CANManager_t *can_managers[BSP_CAN_NUM] = {NULL};

/* Private function  -------------------------------------------------------- */
static int8_t MOTOR_RM_GetLogicalIndex(uint16_t can_id, MOTOR_RM_Module_t module) {
    switch (module) {
        case MOTOR_M2006:
        case MOTOR_M3508:
            if (can_id >= M3508_M2006_FB_ID_BASE && can_id < M3508_M2006_FB_ID_BASE + 7) {
                return can_id - M3508_M2006_FB_ID_BASE; // 返回1-8
            }
            break;
        case MOTOR_GM6020:
            if (can_id >= GM6020_FB_ID_BASE && can_id < GM6020_FB_ID_BASE + 6) {
                return can_id - GM6020_FB_ID_BASE + 4; // 返回5-11
            }
            break;
        default:
            break;
    }
    return DEVICE_ERR;
}

static int16_t MOTOR_RM_GetLSB(MOTOR_RM_Module_t module) {
  switch (module) {
    case MOTOR_M2006:
      return M2006_MAX_ABS_LSB;
    case MOTOR_M3508:
      return M3508_MAX_ABS_LSB;
    case MOTOR_GM6020:
      return GM6020_MAX_ABS_LSB;
    default:
      return DEVICE_ERR;
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
    
    return 0;
}

static void Motor_RM_Decode(MOTOR_RM_t *motor, BSP_CAN_Message_t *msg) {
    uint16_t raw_angle = (uint16_t)((msg->data[0] << 8) | msg->data[1]);
    int16_t raw_current = (int16_t)((msg->data[4] << 8) | msg->data[5]);

    motor->motor.feedback.rotor_abs_angle = raw_angle / (float)MOTOR_ENC_RES * M_2PI;
    motor->motor.feedback.rotor_speed = (int16_t)((msg->data[2] << 8) | msg->data[3]);
    
    // 根据电机类型选择正确的LSB
    int16_t lsb = MOTOR_RM_GetLSB(motor->param.module);
    motor->motor.feedback.torque_current = raw_current * lsb / (float)MOTOR_CUR_RES;
    motor->motor.feedback.temp = msg->data[6];
}

/* Exported functions ------------------------------------------------------- */

int8_t MOTOR_RM_Register(MOTOR_RM_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;

    // 1. 检查并创建CAN管理器
    if (MOTOR_RM_CreateCANManager(param->can) != DEVICE_OK) {
        return DEVICE_ERR;
    }

    // 获取对应的CAN管理器
    MOTOR_RM_CANManager_t *manager = MOTOR_RM_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR;

    // 2. 检查电机是否已注册
    for (int i = 0; i < manager->motor_count; i++) {
        if (manager->motors[i] != NULL &&
            manager->motors[i]->param.id == param->id) {
            return DEVICE_ERR_INITED; // 电机已存在
        }
    }

    // 3. 检查是否还能添加更多电机
    if (manager->motor_count >= MOTOR_RM_MAX_MOTORS) {
        return DEVICE_ERR; // 电机数量已满
    }

    // 4. 创建新的电机实例
    MOTOR_RM_t *new_motor = (MOTOR_RM_t*)BSP_Malloc(sizeof(MOTOR_RM_t));
    if (new_motor == NULL) return DEVICE_ERR;

    // 5. 初始化电机参数
    memcpy(&new_motor->param, param, sizeof(MOTOR_RM_Param_t));
    memset(&new_motor->motor, 0, sizeof(MOTOR_t));
    new_motor->motor.reverse = param->reverse;

    // 6. 注册CAN接收ID（直接使用实际CAN ID）
    if (BSP_CAN_RegisterId(param->can, param->id, 3) != BSP_OK) {
        BSP_Free(new_motor);
        return DEVICE_ERR;
    }
    // 7. 将电机添加到管理器中
    manager->motors[manager->motor_count] = new_motor;
    manager->motor_count++;

    return DEVICE_OK;
}

int8_t MOTOR_RM_Update(BSP_CAN_t can, uint16_t id) {
    MOTOR_RM_CANManager_t *manager = MOTOR_RM_GetCANManager(can);
    if (manager == NULL) return DEVICE_ERR_NO_DEV;

    for (int i = 0; i < manager->motor_count; i++) {
        MOTOR_RM_t *motor = manager->motors[i];
        if (motor != NULL && motor->param.id == id) {
            BSP_CAN_Message_t rx_msg;
            if (BSP_CAN_GetMessage(can, id, &rx_msg, BSP_CAN_TIMEOUT_IMMEDIATE) != BSP_OK) {
                uint64_t now_time = BSP_TIME_Get();
                if (now_time - motor->motor.header.last_online_time > 1000) {
                    motor->motor.header.online = false;
                    return DEVICE_ERR_NO_DEV; // 电机不在线
                }
                return DEVICE_ERR; // 没有新数据但电机在线
            }
            // 解码接收到的消息
            motor->motor.header.online = true;
            motor->motor.header.last_online_time = BSP_TIME_Get();
            Motor_RM_Decode(motor, &rx_msg);
            return DEVICE_OK; // 成功更新
        }
    }
    return DEVICE_ERR_NO_DEV; // 未找到对应电机
}

int8_t MOTOR_RM_UpdateAll(void) {
    int8_t ret = DEVICE_OK;
    for (int can = 0; can < BSP_CAN_NUM; can++) {
        MOTOR_RM_CANManager_t *manager = MOTOR_RM_GetCANManager((BSP_CAN_t)can);
        if (manager == NULL) continue;

        for (int i = 0; i < manager->motor_count; i++) {
            MOTOR_RM_t *motor = manager->motors[i];
            if (motor != NULL) {
                if (MOTOR_RM_Update((BSP_CAN_t)can, motor->param.id) != DEVICE_OK) {
                    ret = DEVICE_ERR;
                }
            }
        }
    }
    return ret;
}

int8_t MOTOR_RM_SetOutput(BSP_CAN_t can, uint16_t id, float value) {
    MOTOR_RM_CANManager_t *manager = MOTOR_RM_GetCANManager(can);
    if (manager == NULL) return DEVICE_ERR_NO_DEV;

    if (value > 1.0f) value = 1.0f;
    if (value < -1.0f) value = -1.0f;

    MOTOR_RM_t *motor = MOTOR_RM_GetMotor(can, id);
    if (motor == NULL) return DEVICE_ERR_NO_DEV;

    int8_t logical_index = MOTOR_RM_GetLogicalIndex(id, motor->param.module);
    if (logical_index < 0) return DEVICE_ERR;

    MOTOR_RM_MsgOutput_t *output_msg = &manager->output_msg;
    int16_t output_value = (int16_t)(value * (float)MOTOR_RM_GetLSB(motor->param.module));
    output_msg->output[logical_index] = output_value;

    return DEVICE_OK;
}

int8_t MOTOR_RM_Ctrl(BSP_CAN_t can, uint16_t id) {
    MOTOR_RM_CANManager_t *manager = MOTOR_RM_GetCANManager(can);
    if (manager == NULL) return DEVICE_ERR_NO_DEV;

    MOTOR_RM_MsgOutput_t *output_msg = &manager->output_msg;
    BSP_CAN_StdDataFrame_t tx_frame;

    switch (id) {
        case M3508_M2006_FB_ID_BASE:
        case M3508_M2006_FB_ID_BASE+1:
        case M3508_M2006_FB_ID_BASE+2:
        case M3508_M2006_FB_ID_BASE+3:
            tx_frame.id = M3508_M2006_CTRL_ID_BASE;
            tx_frame.dlc = MOTOR_TX_BUF_SIZE;
            tx_frame.data[0] = (uint8_t)((output_msg->output[0] >> 8) & 0xFF);
            tx_frame.data[1] = (uint8_t)(output_msg->output[0] & 0xFF);
            tx_frame.data[2] = (uint8_t)((output_msg->output[1] >> 8) & 0xFF);
            tx_frame.data[3] = (uint8_t)(output_msg->output[1] & 0xFF);
            tx_frame.data[4] = (uint8_t)((output_msg->output[2] >> 8) & 0xFF);
            tx_frame.data[5] = (uint8_t)(output_msg->output[2] & 0xFF);
            tx_frame.data[6] = (uint8_t)((output_msg->output[3] >> 8) & 0xFF);
            tx_frame.data[7] = (uint8_t)(output_msg->output[3] & 0xFF);
            break;
        case M3508_M2006_FB_ID_BASE+4:
        case M3508_M2006_FB_ID_BASE+5:
        case M3508_M2006_FB_ID_BASE+6:
        case M3508_M2006_FB_ID_BASE+7:
            tx_frame.id = M3508_M2006_CTRL_ID_EXTAND;
            tx_frame.dlc = MOTOR_TX_BUF_SIZE;
            tx_frame.data[0] = (uint8_t)((output_msg->output[4] >> 8) & 0xFF);
            tx_frame.data[1] = (uint8_t)(output_msg->output[4] & 0xFF);
            tx_frame.data[2] = (uint8_t)((output_msg->output[5] >> 8) & 0xFF);
            tx_frame.data[3] = (uint8_t)(output_msg->output[5] & 0xFF);
            tx_frame.data[4] = (uint8_t)((output_msg->output[6] >> 8) & 0xFF);
            tx_frame.data[5] = (uint8_t)(output_msg->output[6] & 0xFF);
            tx_frame.data[6] = (uint8_t)((output_msg->output[7] >> 8) & 0xFF);
            tx_frame.data[7] = (uint8_t)(output_msg->output[7] & 0xFF);
            break;

        case GM6020_FB_ID_BASE+4:
        case GM6020_FB_ID_BASE+5:
        case GM6020_FB_ID_BASE+6:
            tx_frame.id = GM6020_CTRL_ID_EXTAND;
            tx_frame.dlc = MOTOR_TX_BUF_SIZE;
            tx_frame.data[0] = (uint8_t)((output_msg->output[8] >> 8) & 0xFF);
            tx_frame.data[1] = (uint8_t)(output_msg->output[8] & 0xFF);
            tx_frame.data[2] = (uint8_t)((output_msg->output[9] >> 8) & 0xFF);
            tx_frame.data[3] = (uint8_t)(output_msg->output[9] & 0xFF);
            tx_frame.data[4] = (uint8_t)((output_msg->output[10] >> 8) & 0xFF);
            tx_frame.data[5] = (uint8_t)(output_msg->output[10] & 0xFF);
            tx_frame.data[6] = 0;
            tx_frame.data[7] = 0;
            break;
        default:
            return DEVICE_ERR; // 不支持的控制ID
    }

    return BSP_CAN_TransmitStdDataFrame(can, &tx_frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}

MOTOR_RM_t* MOTOR_RM_GetMotor(BSP_CAN_t can, uint16_t id) {
    MOTOR_RM_CANManager_t *manager = MOTOR_RM_GetCANManager(can);
    if (manager == NULL) return NULL;

    for (int i = 0; i < manager->motor_count; i++) {
        MOTOR_RM_t *motor = manager->motors[i];
        if (motor != NULL && motor->param.id == id) {
            return motor;
        }
    }
    return NULL;
}

int8_t MOTOR_RM_Relax(BSP_CAN_t can, uint16_t id) {
    int8_t ret = MOTOR_RM_SetOutput(can, id, 0.0f);
    if (ret != DEVICE_OK) return ret;
    return DEVICE_OK;
}

int8_t MOTOR_RM_Offine(BSP_CAN_t can, uint16_t id) {
    MOTOR_RM_t *motor = MOTOR_RM_GetMotor(can, id);
    if (motor != NULL) {
        motor->motor.header.online = false;
        return DEVICE_OK;
    }
    return DEVICE_ERR_NO_DEV;
}