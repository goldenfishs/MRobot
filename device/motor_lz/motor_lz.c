/*
  灵足电机驱动
  
  灵足电机通信协议：
  - CAN 2.0通信接口，波特率1Mbps
  - 采用扩展帧格式(29位ID)
  - ID格式：Bit28~24(通信类型) + Bit23~8(数据区2) + Bit7~0(目标地址)
*/
/* Includes ----------------------------------------------------------------- */
#include "motor_lz.h"
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include "bsp/can.h"
#include "bsp/mm.h"
#include "bsp/time.h"
#include "component/user_math.h"

/* Private define ----------------------------------------------------------- */
// 灵足电机协议参数
#define LZ_ANGLE_RANGE_RAD          (12.57f)        /* 角度范围 ±12.57 rad */
#define LZ_VELOCITY_RANGE_RAD_S     (20.0f)         /* 角速度范围 ±20 rad/s */
#define LZ_KP_MAX                   (5000.0f)       /* Kp最大值 */
#define LZ_KD_MAX                   (100.0f)        /* Kd最大值 */

#define LZ_RAW_VALUE_MAX            (65535)         /* 16位原始值最大值 */
#define LZ_TEMP_SCALE               (10.0f)         /* 温度缩放因子 */

#define LZ_MAX_RECOVER_DIFF_RAD    (0.28f)
#define MOTOR_TX_BUF_SIZE           (8)
#define MOTOR_RX_BUF_SIZE           (8)
#define LZ_POSITION_CTRL_KP         (40.0f)
#define LZ_POSITION_CTRL_KD         (1.5f)
#define LZ_VELOCITY_CTRL_KD         (3.0f)
#define LZ_FEEDBACK_TIMEOUT_US      (100000u)

/* Private macro ------------------------------------------------------------ */

MOTOR_LZ_MotionParam_t lz_relax_param = {
    .target_angle = 0.0f,
    .target_velocity = 0.0f,
    .kp = 0.0f,
    .kd = 0.0f,
    .torque = 0.0f,
};
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */
static MOTOR_LZ_CANManager_t *can_managers[BSP_CAN_NUM] = {NULL};

/* Private function prototypes ---------------------------------------------- */
static MOTOR_LZ_CANManager_t* MOTOR_LZ_GetCANManager(BSP_CAN_t can);
static int8_t MOTOR_LZ_CreateCANManager(BSP_CAN_t can);
static void MOTOR_LZ_Decode(MOTOR_LZ_t *motor, BSP_CAN_Message_t *msg);
static uint32_t MOTOR_LZ_BuildExtID(MOTOR_LZ_CmdType_t cmd_type, uint16_t data2, uint8_t target_id);
static uint16_t MOTOR_LZ_FloatToRaw(float value, float max_value);
static float MOTOR_LZ_RawToFloat(uint16_t raw_value, float max_value);
static float MOTOR_LZ_GetTorqueRangeNm(MOTOR_LZ_Module_t module);
static int8_t MOTOR_LZ_SendExtFrame(BSP_CAN_t can, uint32_t ext_id, uint8_t *data, uint8_t dlc);
static uint32_t MOTOR_LZ_IdParser(uint32_t original_id, BSP_CAN_FrameType_t frame_type);

/* -------------------------------------------------------------------------- */
/* 协议层/管理层：LZ 扩展帧编解码、ID 解析器、CAN 管理器与电机查找绑定。 */
/* -------------------------------------------------------------------------- */

/**
 * @brief 获取CAN管理器
 */
static MOTOR_LZ_CANManager_t* MOTOR_LZ_GetCANManager(BSP_CAN_t can) {
    if (can >= BSP_CAN_NUM) return NULL;
    return can_managers[can];
}

/**
 * @brief 创建CAN管理器
 */
static int8_t MOTOR_LZ_CreateCANManager(BSP_CAN_t can) {
    if (can >= BSP_CAN_NUM) return DEVICE_ERR;
    if (can_managers[can] != NULL) return DEVICE_OK;
    
    can_managers[can] = (MOTOR_LZ_CANManager_t*)BSP_Malloc(sizeof(MOTOR_LZ_CANManager_t));
    if (can_managers[can] == NULL) return DEVICE_ERR;
    
    memset(can_managers[can], 0, sizeof(MOTOR_LZ_CANManager_t));
    can_managers[can]->can = can;
    return DEVICE_OK;
}

static int8_t MOTOR_LZ_BindMotor(MOTOR_LZ_CANManager_t *manager, MOTOR_LZ_Param_t *param, MOTOR_LZ_t *motor) {
    if (manager == NULL || param == NULL || motor == NULL) return DEVICE_ERR_NULL;
    for (int i = 0; i < manager->motor_count; i++) {
        if (manager->motors[i] && manager->motors[i]->param.motor_id == param->motor_id) {
            return DEVICE_ERR;
        }
    }
    if (manager->motor_count >= MOTOR_LZ_MAX_MOTORS) return DEVICE_ERR;
    memset(motor, 0, sizeof(MOTOR_LZ_t));
    memcpy(&motor->param, param, sizeof(MOTOR_LZ_Param_t));
    motor->motor.reverse = param->reverse;
    uint32_t original_feedback_id = MOTOR_LZ_BuildExtID(MOTOR_LZ_CMD_FEEDBACK, param->motor_id, param->host_id);
    uint32_t parsed_feedback_id = MOTOR_LZ_IdParser(original_feedback_id, BSP_CAN_FRAME_EXT_DATA);
    if (BSP_CAN_RegisterId(param->can, parsed_feedback_id, 3) != BSP_OK) {
        return DEVICE_ERR;
    }
    manager->motors[manager->motor_count] = motor;
    manager->motor_count++;
    return DEVICE_OK;
}

static MOTOR_LZ_t* MOTOR_LZ_FindMotorById(const MOTOR_LZ_CANManager_t *manager, uint8_t motor_id) {
    if (manager == NULL) return NULL;
    for (int i = 0; i < manager->motor_count; i++) {
        MOTOR_LZ_t *motor = manager->motors[i];
        if (motor && motor->param.motor_id == motor_id) {
            return motor;
        }
    }
    for (int i = 0; i < manager->external_motor_count; i++) {
        MOTOR_LZ_t *motor = manager->external_motors[i];
        if (motor && motor->param.motor_id == motor_id) {
            return motor;
        }
    }
    return NULL;
}

static int8_t MOTOR_LZ_BindExternalMotor(MOTOR_LZ_CANManager_t *manager, MOTOR_LZ_Param_t *param, MOTOR_LZ_t *motor) {
    if (manager == NULL || param == NULL || motor == NULL) return DEVICE_ERR_NULL;
    if (MOTOR_LZ_FindMotorById(manager, param->motor_id) != NULL) return DEVICE_ERR;
    if (manager->external_motor_count >= MOTOR_LZ_MAX_MOTORS) return DEVICE_ERR;
    memset(motor, 0, sizeof(MOTOR_LZ_t));
    memcpy(&motor->param, param, sizeof(MOTOR_LZ_Param_t));
    motor->motor.reverse = param->reverse;
    uint32_t original_feedback_id = MOTOR_LZ_BuildExtID(MOTOR_LZ_CMD_FEEDBACK, param->motor_id, param->host_id);
    uint32_t parsed_feedback_id = MOTOR_LZ_IdParser(original_feedback_id, BSP_CAN_FRAME_EXT_DATA);
    if (BSP_CAN_RegisterId(param->can, parsed_feedback_id, 3) != BSP_OK) {
        return DEVICE_ERR;
    }
    manager->external_motors[manager->external_motor_count] = motor;
    manager->external_motor_count++;
    return DEVICE_OK;
}

/**
 * @brief 构建扩展ID
 */
static uint32_t MOTOR_LZ_BuildExtID(MOTOR_LZ_CmdType_t cmd_type, uint16_t data2, uint8_t target_id) {
    uint32_t ext_id = 0;
    ext_id |= ((uint32_t)cmd_type & 0x1F) << 24;      // Bit28~24: 通信类型
    ext_id |= ((uint32_t)data2 & 0xFFFF) << 8;        // Bit23~8: 数据区2
    ext_id |= ((uint32_t)target_id & 0xFF);           // Bit7~0: 目标地址
    return ext_id;
}

/**
 * @brief 浮点值转换为原始值（对称范围：-max_value ~ +max_value）
 */
static uint16_t MOTOR_LZ_FloatToRaw(float value, float max_value) {
    // 限制范围
    if (value > max_value) value = max_value;
    if (value < -max_value) value = -max_value;
    
    // 转换为0~65535范围，对应-max_value~max_value
    return (uint16_t)((value + max_value) / (2.0f * max_value) * (float)LZ_RAW_VALUE_MAX);
}

/**
 * @brief 浮点值转换为原始值（单向范围：0 ~ +max_value）
 */
static uint16_t MOTOR_LZ_FloatToRawPositive(float value, float max_value) {
    // 限制范围
    if (value > max_value) value = max_value;
    if (value < 0.0f) value = 0.0f;
    
    // 转换为0~65535范围，对应0~max_value
    return (uint16_t)(value / max_value * (float)LZ_RAW_VALUE_MAX);
}

static float MOTOR_LZ_RawToFloat(uint16_t raw_value, float max_value) {
    return ((float)raw_value / (float)LZ_RAW_VALUE_MAX) * (2.0f * max_value) - max_value;
}

static float MOTOR_LZ_GetTorqueRangeNm(MOTOR_LZ_Module_t module) {
    switch (module) {
        case MOTOR_LZ_RSO0:
            return 14.0f;
        case MOTOR_LZ_RSO1:
        case MOTOR_LZ_RSO2:
            return 17.0f;
        case MOTOR_LZ_RSO3:
            return 60.0f;
        case MOTOR_LZ_RSO4:
            return 120.0f;
        case MOTOR_LZ_RSO5:
            return 5.5f;
        case MOTOR_LZ_RSO6:
            return 36.0f;
        default:
            return 60.0f;
    }
}

/**
 * @brief 发送扩展帧
 */
static int8_t MOTOR_LZ_SendExtFrame(BSP_CAN_t can, uint32_t ext_id, uint8_t *data, uint8_t dlc) {
    BSP_CAN_ExtDataFrame_t tx_frame;
    tx_frame.id = ext_id;
    tx_frame.dlc = dlc;
    if (data != NULL) {
        memcpy(tx_frame.data, data, dlc);
    } else {
        memset(tx_frame.data, 0, dlc);
    }
    return BSP_CAN_TransmitExtDataFrame(can, &tx_frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}

/**
 * @brief 灵足电机ID解析器
 * @param original_id 原始CAN ID（29位扩展帧）
 * @param frame_type 帧类型
 * @return 解析后的ID（用于队列匹配）
 * 
 * 灵足电机扩展ID格式：
 * Bit28~24: 通信类型 (0x1=运控控制, 0x2=反馈数据, 0x3=使能, 0x4=停止, 0x6=设零位)
 * Bit23~8:  数据区2 (根据通信类型而定)
 * Bit7~0:   目标地址 (目标电机CAN ID)
 */
static uint32_t MOTOR_LZ_IdParser(uint32_t original_id, BSP_CAN_FrameType_t frame_type) {
    // 只处理扩展数据帧
    if (frame_type != BSP_CAN_FRAME_EXT_DATA) {
        return original_id; // 非扩展帧直接返回原始ID
    }
    
    // 解析扩展ID各个字段
    uint8_t cmd_type = (original_id >> 24) & 0x1F;    // Bit28~24: 通信类型
    uint16_t data2 = (original_id >> 8) & 0xFFFF;     // Bit23~8: 数据区2
    uint8_t host_id = (uint8_t)(original_id & 0xFF);  // Bit7~0: 主机CAN ID
    
    // 对于反馈数据帧，我们使用特殊的解析规则
    if (cmd_type == MOTOR_LZ_CMD_FEEDBACK) {
        // 反馈数据的data2字段包含：
        // Bit8~15: 当前电机CAN ID
        // Bit16~21: 故障信息
        // Bit22~23: 模式状态
        uint8_t motor_can_id = data2 & 0xFF;          // bit8~15: 当前电机CAN ID
        
        // 返回格式化的ID，便于匹配
        // 格式：0x02HHMMTT (02=反馈命令, HH=主机ID, MM=电机ID, TT=主机ID)
        return (0x02000000) | (host_id << 16) | (motor_can_id << 8) | host_id;
    }
    
    // 对于其他命令类型，直接返回原始ID
    return original_id;
}

/**
 * @brief 解码灵足电机反馈数据
 */
static void MOTOR_LZ_Decode(MOTOR_LZ_t *motor, BSP_CAN_Message_t *msg) {
    if (motor == NULL || msg == NULL) return;
    uint8_t cmd_type = (msg->original_id >> 24) & 0x1F;
    if (cmd_type != MOTOR_LZ_CMD_FEEDBACK) return;
    uint16_t id_data2 = (msg->original_id >> 8) & 0xFFFF;
    uint8_t motor_can_id = id_data2 & 0xFF;
    uint8_t fault_info = (id_data2 >> 8) & 0x3F;
    uint8_t mode_state = (id_data2 >> 14) & 0x03;
    motor->lz_feedback.motor_can_id = motor_can_id;
    motor->lz_feedback.fault_bits = fault_info;
    motor->lz_feedback.state_bits = mode_state;
    motor->lz_feedback.fault.under_voltage = (fault_info & 0x01) != 0;
    motor->lz_feedback.fault.driver_fault = (fault_info & 0x02) != 0;
    motor->lz_feedback.fault.over_temp = (fault_info & 0x04) != 0;
    motor->lz_feedback.fault.encoder_fault = (fault_info & 0x08) != 0;
    motor->lz_feedback.fault.stall_overload = (fault_info & 0x10) != 0;
    motor->lz_feedback.fault.uncalibrated = (fault_info & 0x20) != 0;
    motor->lz_feedback.state = (MOTOR_LZ_State_t)mode_state;

    uint16_t raw_angle = (uint16_t)((msg->data[0] << 8) | msg->data[1]);
    uint16_t raw_velocity = (uint16_t)((msg->data[2] << 8) | msg->data[3]);
    uint16_t raw_torque = (uint16_t)((msg->data[4] << 8) | msg->data[5]);
    uint16_t raw_temp = (uint16_t)((msg->data[6] << 8) | msg->data[7]);

    float angle = MOTOR_LZ_RawToFloat(raw_angle, LZ_ANGLE_RANGE_RAD);
    float velocity = MOTOR_LZ_RawToFloat(raw_velocity, LZ_VELOCITY_RANGE_RAD_S);
    float torque = MOTOR_LZ_RawToFloat(raw_torque,
                                       MOTOR_LZ_GetTorqueRangeNm(motor->param.module));
    while (angle < 0.0f) {
        angle += M_2PI;
    }
    while (angle >= M_2PI) {
        angle -= M_2PI;
    }
    if (motor->param.reverse) {
        angle = M_2PI - angle;
        if (angle >= M_2PI) {
            angle -= M_2PI;
        }
        velocity = -velocity;
        torque = -torque;
    }
    const float temperature = (float)raw_temp / LZ_TEMP_SCALE;

    /* MOTOR_CPP_ADAPTER_DATA: preserve raw feedback for lz_protocol.cpp. */
    motor->motor.raw_feedback.raw_angle = raw_angle;
    motor->motor.raw_feedback.raw_speed = (int16_t)raw_velocity;
    motor->motor.raw_feedback.raw_current = (int16_t)raw_torque;
    motor->motor.raw_feedback.raw_temp = (uint8_t)(raw_temp / LZ_TEMP_SCALE);
    motor->motor.raw_feedback.raw_error_code = fault_info;

    motor->lz_feedback.current_angle = angle;
    motor->lz_feedback.current_velocity = velocity;
    motor->lz_feedback.current_torque = torque;
    motor->lz_feedback.temperature = temperature;

    motor->motor.feedback.rotor_abs_angle = angle;
    motor->motor.feedback.rotor_single_angle = angle;
    motor->motor.feedback.rotor_total_angle = angle;
    motor->motor.feedback.rotor_speed = velocity;
    motor->motor.feedback.torque_current = torque;
    motor->motor.feedback.temp = temperature;
    motor->motor.feedback.angle_valid = true;
    const uint64_t now_time = BSP_TIME_Get();
    motor->motor.feedback.last_update_time = (uint32_t)now_time;
    motor->motor.header.online = true;
    motor->motor.header.last_online_time = now_time;
}

/* -------------------------------------------------------------------------- */
/* 原生 C 驱动接口：初始化、注册、反馈更新、协议控制帧与状态控制。 */
/* -------------------------------------------------------------------------- */

/**
 * @brief 初始化灵足电机驱动系统
 * @return 设备状态码
 */
int8_t MOTOR_LZ_Init(void) {
    // 注册灵足电机专用的ID解析器
    return BSP_CAN_RegisterIdParser(MOTOR_LZ_IdParser) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}


int8_t MOTOR_LZ_Register(MOTOR_LZ_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    
    if (MOTOR_LZ_CreateCANManager(param->can) != DEVICE_OK) return DEVICE_ERR;
    MOTOR_LZ_CANManager_t *manager = MOTOR_LZ_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR;
    
    MOTOR_LZ_t *new_motor = (MOTOR_LZ_t*)BSP_Malloc(sizeof(MOTOR_LZ_t));
    if (new_motor == NULL) return DEVICE_ERR;
    const int8_t ret = MOTOR_LZ_BindMotor(manager, param, new_motor);
    if (ret != DEVICE_OK) {
        BSP_Free(new_motor);
        return ret;
    }
    return DEVICE_OK;
}

int8_t MOTOR_LZ_Update(MOTOR_LZ_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    
    MOTOR_LZ_CANManager_t *manager = MOTOR_LZ_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR_NO_DEV;
    
    MOTOR_LZ_t *motor = MOTOR_LZ_FindMotorById(manager, param->motor_id);
    if (motor == NULL) return DEVICE_ERR_NO_DEV;
    uint32_t original_feedback_id = MOTOR_LZ_BuildExtID(MOTOR_LZ_CMD_FEEDBACK, param->motor_id, param->host_id);
    uint32_t parsed_feedback_id = MOTOR_LZ_IdParser(original_feedback_id, BSP_CAN_FRAME_EXT_DATA);
    BSP_CAN_Message_t msg;
    bool got_feedback = false;
    while (BSP_CAN_GetMessage(param->can, parsed_feedback_id, &msg, 0) == BSP_OK) {
        MOTOR_LZ_Decode(motor, &msg);
        got_feedback = true;
    }
    if (got_feedback) {
        return DEVICE_OK;
    }
    const uint64_t now_time = BSP_TIME_Get();
    if (now_time - motor->motor.header.last_online_time > LZ_FEEDBACK_TIMEOUT_US) {
        motor->motor.header.online = false;
        return DEVICE_ERR_NO_DEV;
    }
    return DEVICE_ERR;
}

int8_t MOTOR_LZ_UpdateAll(void) {
    int8_t ret = DEVICE_OK;
    for (int can = 0; can < BSP_CAN_NUM; can++) {
        MOTOR_LZ_CANManager_t *manager = MOTOR_LZ_GetCANManager((BSP_CAN_t)can);
        if (manager == NULL) continue;
        
        for (int i = 0; i < manager->motor_count; i++) {
            MOTOR_LZ_t *motor = manager->motors[i];
            if (motor) {
                if (MOTOR_LZ_Update(&motor->param) != DEVICE_OK) {
                    ret = DEVICE_ERR;
                }
            }
        }
        for (int i = 0; i < manager->external_motor_count; i++) {
            MOTOR_LZ_t *motor = manager->external_motors[i];
            if (motor) {
                if (MOTOR_LZ_Update(&motor->param) != DEVICE_OK) {
                    ret = DEVICE_ERR;
                }
            }
        }
    }
    return ret;
}

int8_t MOTOR_LZ_MotionControl(MOTOR_LZ_Param_t *param, MOTOR_LZ_MotionParam_t *motion_param) {
    if (param == NULL || motion_param == NULL) return DEVICE_ERR_NULL;
    MOTOR_LZ_t *motor = MOTOR_LZ_GetMotor(param);
    if (motor == NULL) return DEVICE_ERR_NO_DEV;

    // 自动反向控制
    MOTOR_LZ_MotionParam_t send_param = *motion_param;
    if (param->reverse) {
        send_param.target_angle = -send_param.target_angle;
        send_param.target_velocity = -send_param.target_velocity;
        send_param.torque = -send_param.torque;
    }

    memcpy(&motor->motion_param, motion_param, sizeof(MOTOR_LZ_MotionParam_t));

    uint16_t raw_torque = MOTOR_LZ_FloatToRaw(send_param.torque,
                                             MOTOR_LZ_GetTorqueRangeNm(param->module));
    uint32_t ext_id = MOTOR_LZ_BuildExtID(MOTOR_LZ_CMD_MOTION, raw_torque, param->motor_id);
    uint8_t data[8];
    uint16_t raw_angle = MOTOR_LZ_FloatToRaw(send_param.target_angle, LZ_ANGLE_RANGE_RAD);
    data[0] = (raw_angle >> 8) & 0xFF;
    data[1] = raw_angle & 0xFF;
    uint16_t raw_velocity = MOTOR_LZ_FloatToRaw(send_param.target_velocity, LZ_VELOCITY_RANGE_RAD_S);
    data[2] = (raw_velocity >> 8) & 0xFF;
    data[3] = raw_velocity & 0xFF;
    uint16_t raw_kp = MOTOR_LZ_FloatToRawPositive(send_param.kp, LZ_KP_MAX);
    data[4] = (raw_kp >> 8) & 0xFF;
    data[5] = raw_kp & 0xFF;
    uint16_t raw_kd = MOTOR_LZ_FloatToRawPositive(send_param.kd, LZ_KD_MAX);
    data[6] = (raw_kd >> 8) & 0xFF;
    data[7] = raw_kd & 0xFF;
    return MOTOR_LZ_SendExtFrame(param->can, ext_id, data, 8);
}

int8_t MOTOR_LZ_TorqueControl(MOTOR_LZ_Param_t *param, float torque) {
    MOTOR_LZ_MotionParam_t motion_param = {
        .target_angle = 0.0f,
        .target_velocity = 0.0f,
        .kp = 0.0f,
        .kd = 0.0f,
        .torque = torque,
    };
    return MOTOR_LZ_MotionControl(param, &motion_param);
}

int8_t MOTOR_LZ_PositionControl(MOTOR_LZ_Param_t *param, float target_angle, float max_velocity) {
    MOTOR_LZ_MotionParam_t motion_param = {
        .target_angle = target_angle,
        .target_velocity = max_velocity,
        .kp = LZ_POSITION_CTRL_KP,
        .kd = LZ_POSITION_CTRL_KD,
        .torque = 0.0f,
    };
    return MOTOR_LZ_MotionControl(param, &motion_param);
}

int8_t MOTOR_LZ_VelocityControl(MOTOR_LZ_Param_t *param, float target_velocity) {
    MOTOR_LZ_MotionParam_t motion_param = {
        .target_angle = 0.0f,
        .target_velocity = target_velocity,
        .kp = 0.0f,
        .kd = LZ_VELOCITY_CTRL_KD,
        .torque = 0.0f,
    };
    return MOTOR_LZ_MotionControl(param, &motion_param);
}


int8_t MOTOR_LZ_Enable(MOTOR_LZ_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    
    // 构建扩展ID - 使能命令
    uint32_t ext_id = MOTOR_LZ_BuildExtID(MOTOR_LZ_CMD_ENABLE, param->host_id, param->motor_id);
    
    // 数据区清零
    uint8_t data[8] = {0};
    
    return MOTOR_LZ_SendExtFrame(param->can, ext_id, data, 8);
}

int8_t MOTOR_LZ_Disable(MOTOR_LZ_Param_t *param, bool clear_fault) {
    if (param == NULL) return DEVICE_ERR_NULL;
    
    // 构建扩展ID - 停止命令
    uint32_t ext_id = MOTOR_LZ_BuildExtID(MOTOR_LZ_CMD_DISABLE, param->host_id, param->motor_id);
    
    // 数据区
    uint8_t data[8] = {0};
    if (clear_fault) {
        data[0] = 1; // Byte[0]=1时清故障
    }
    
    return MOTOR_LZ_SendExtFrame(param->can, ext_id, data, 8);
}

int8_t MOTOR_LZ_SetZero(MOTOR_LZ_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    
    // 构建扩展ID - 设置零位命令
    uint32_t ext_id = MOTOR_LZ_BuildExtID(MOTOR_LZ_CMD_SET_ZERO, param->host_id, param->motor_id);
    
    // 数据区 - Byte[0]=1
    uint8_t data[8] = {1, 0, 0, 0, 0, 0, 0, 0};
    
    return MOTOR_LZ_SendExtFrame(param->can, ext_id, data, 8);
}

MOTOR_LZ_t* MOTOR_LZ_GetMotor(MOTOR_LZ_Param_t *param) {
    if (param == NULL) return NULL;
    
    MOTOR_LZ_CANManager_t *manager = MOTOR_LZ_GetCANManager(param->can);
    if (manager == NULL) return NULL;
    
    return MOTOR_LZ_FindMotorById(manager, param->motor_id);
}

int8_t MOTOR_LZ_Relax(MOTOR_LZ_Param_t *param) {
    return MOTOR_LZ_MotionControl(param, &lz_relax_param);
}

int8_t MOTOR_LZ_Offline(MOTOR_LZ_Param_t *param) {
    MOTOR_LZ_t *motor = MOTOR_LZ_GetMotor(param);
    if (motor) {
        motor->motor.header.online = false;
        return DEVICE_OK;
    }
    return DEVICE_ERR_NO_DEV;
}

/* -------------------------------------------------------------------------- */
/* C++ motor 适配接口：protocol/motor_t 使用的外部实例与原始反馈读取。 */
/* -------------------------------------------------------------------------- */

/* C++ 驱动层将外部持有的 vendor instance 绑定到 C 管理器。 */
/* MOTOR_CPP_ADAPTER_IMPL_BEGIN: used by User/device/motor/protocol/lz_protocol.cpp. */
int8_t MOTOR_LZ_AttachExternal(MOTOR_LZ_Param_t *param, MOTOR_LZ_t *external_motor) {
    if (param == NULL || external_motor == NULL) return DEVICE_ERR_NULL;
    if (MOTOR_LZ_CreateCANManager(param->can) != DEVICE_OK) return DEVICE_ERR;
    MOTOR_LZ_CANManager_t *manager = MOTOR_LZ_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR;
    return MOTOR_LZ_BindExternalMotor(manager, param, external_motor);
}

/* C++ 驱动层读取底层原始反馈缓存。 */
const MOTOR_LZ_RawFeedback_t* MOTOR_LZ_GetRawFeedback(MOTOR_LZ_Param_t *param) {
    MOTOR_LZ_t *motor = MOTOR_LZ_GetMotor(param);
    if (motor == NULL) {
        return NULL;
    }
    return &motor->motor.raw_feedback;
}
/* MOTOR_CPP_ADAPTER_IMPL_END */
