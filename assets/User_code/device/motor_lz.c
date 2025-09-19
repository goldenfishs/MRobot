/*
  灵足电机驱动
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
#define LZ_TORQUE_RANGE_NM          (60.0f)         /* 力矩范围 ±60 Nm */
#define LZ_KP_MAX                   (5000.0f)       /* Kp最大值 */
#define LZ_KD_MAX                   (100.0f)        /* Kd最大值 */

#define LZ_RAW_VALUE_MAX            (65535)         /* 16位原始值最大值 */
#define LZ_TEMP_SCALE               (10.0f)         /* 温度缩放因子 */

#define LZ_MAX_RECOVER_DIFF_RAD    (0.4f)
#define MOTOR_TX_BUF_SIZE           (8)
#define MOTOR_RX_BUF_SIZE           (8)

/* Private macro ------------------------------------------------------------ */

MOTOR_LZ_MotionParam_t lz_recover_param = {
    .target_angle = 0.0f,
    .target_velocity = 0.0f,
    .kp = 20.0f,
    .kd = 1.0f,
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
static int8_t MOTOR_LZ_SendExtFrame(BSP_CAN_t can, uint32_t ext_id, uint8_t *data, uint8_t dlc);
static uint32_t MOTOR_LZ_IdParser(uint32_t original_id, BSP_CAN_FrameType_t frame_type);

/* Private functions -------------------------------------------------------- */

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

/**
 * @brief 原始值转换为浮点值
 */
static float MOTOR_LZ_RawToFloat(uint16_t raw_value, float max_value) {
    // 将0~65535范围转换为-max_value~max_value
    return ((float)raw_value / (float)LZ_RAW_VALUE_MAX) * (2.0f * max_value) - max_value;
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
    BSP_CAN_WaitTxMailboxEmpty(can, 1); // 等待发送邮箱空闲

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
    
    // 检查是否为反馈数据帧 (通信类型2)
    // 需要使用原始ID来解析，因为parsed_id已经被IdParser处理过了
    uint8_t cmd_type = (msg->original_id >> 24) & 0x1F;
    if (cmd_type != MOTOR_LZ_CMD_FEEDBACK) return;
    
    // 解析原始ID中的数据区2 (bit23~8)
    uint16_t id_data2 = (msg->original_id >> 8) & 0xFFFF;
    uint8_t motor_can_id = id_data2 & 0xFF;          // Bit8~15: 当前电机CAN ID
    uint8_t fault_info = (id_data2 >> 8) & 0x3F;     // Bit16~21: 故障信息
    uint8_t mode_state = (id_data2 >> 14) & 0x03;    // Bit22~23: 模式状态
    
    // 更新电机CAN ID
    motor->lz_feedback.motor_can_id = motor_can_id;
    
    // 解析故障信息
    motor->lz_feedback.fault.under_voltage = (fault_info & 0x01) != 0;      // bit16
    motor->lz_feedback.fault.driver_fault = (fault_info & 0x02) != 0;       // bit17
    motor->lz_feedback.fault.over_temp = (fault_info & 0x04) != 0;          // bit18
    motor->lz_feedback.fault.encoder_fault = (fault_info & 0x08) != 0;      // bit19
    motor->lz_feedback.fault.stall_overload = (fault_info & 0x10) != 0;     // bit20
    motor->lz_feedback.fault.uncalibrated = (fault_info & 0x20) != 0;       // bit21
    
    // 解析模式状态
    motor->lz_feedback.state = (MOTOR_LZ_State_t)mode_state;
    
    // 解析数据区
    // Byte0~1: 当前角度 (高字节在前，低字节在后)
    uint16_t raw_angle = (uint16_t)((msg->data[0] << 8) | msg->data[1]);
    motor->lz_feedback.current_angle = MOTOR_LZ_RawToFloat(raw_angle, LZ_ANGLE_RANGE_RAD);
    
    // Byte2~3: 当前角速度 (高字节在前，低字节在后)
    uint16_t raw_velocity = (uint16_t)((msg->data[2] << 8) | msg->data[3]);
    motor->lz_feedback.current_velocity = MOTOR_LZ_RawToFloat(raw_velocity, LZ_VELOCITY_RANGE_RAD_S);
    
    // Byte4~5: 当前力矩 (高字节在前，低字节在后)
    uint16_t raw_torque = (uint16_t)((msg->data[4] << 8) | msg->data[5]);
    motor->lz_feedback.current_torque = MOTOR_LZ_RawToFloat(raw_torque, LZ_TORQUE_RANGE_NM);
    
    // Byte6~7: 当前温度 (温度*10) (高字节在前，低字节在后)
    uint16_t raw_temp = (uint16_t)((msg->data[6] << 8) | msg->data[7]);
    motor->lz_feedback.temperature = (float)raw_temp / LZ_TEMP_SCALE;
    
    // 更新通用电机反馈信息
    motor->motor.feedback.rotor_abs_angle = motor->lz_feedback.current_angle;
    motor->motor.feedback.rotor_speed = motor->lz_feedback.current_velocity * 180.0f / M_PI * 6.0f; // 转换为RPM
    motor->motor.feedback.torque_current = motor->lz_feedback.current_torque; // 使用力矩作为电流反馈
    motor->motor.feedback.temp = (int8_t)motor->lz_feedback.temperature;
    
    // 更新在线状态
    motor->motor.header.online = true;
    motor->motor.header.last_online_time = BSP_TIME_Get();
}

/* Exported functions ------------------------------------------------------- */

/**
 * @brief 初始化灵足电机驱动系统
 * @return 设备状态码
 */
int8_t MOTOR_LZ_Init(void) {
    // 注册灵足电机专用的ID解析器
    return BSP_CAN_RegisterIdParser(MOTOR_LZ_IdParser) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}

/**
 * @brief 反初始化灵足电机驱动系统
 * @return 设备状态码
 */
int8_t MOTOR_LZ_DeInit(void) {
    // 注销ID解析器
    return BSP_CAN_UnregisterIdParser() == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}

int8_t MOTOR_LZ_Register(MOTOR_LZ_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    
    if (MOTOR_LZ_CreateCANManager(param->can) != DEVICE_OK) return DEVICE_ERR;
    MOTOR_LZ_CANManager_t *manager = MOTOR_LZ_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR;
    
    // 检查是否已注册
    for (int i = 0; i < manager->motor_count; i++) {
        if (manager->motors[i] && manager->motors[i]->param.motor_id == param->motor_id) {
            return DEVICE_ERR; // 已注册
        }
    }
    
    // 检查数量
    if (manager->motor_count >= MOTOR_LZ_MAX_MOTORS) return DEVICE_ERR;
    
    // 创建新电机实例
    MOTOR_LZ_t *new_motor = (MOTOR_LZ_t*)BSP_Malloc(sizeof(MOTOR_LZ_t));
    if (new_motor == NULL) return DEVICE_ERR;
    
    memcpy(&new_motor->param, param, sizeof(MOTOR_LZ_Param_t));
    memset(&new_motor->motor, 0, sizeof(MOTOR_t));
    memset(&new_motor->lz_feedback, 0, sizeof(MOTOR_LZ_Feedback_t));
    memset(&new_motor->motion_param, 0, sizeof(MOTOR_LZ_MotionParam_t));
    
    new_motor->motor.reverse = param->reverse;
    
    // 注册CAN接收ID - 使用解析后的反馈数据ID
    // 构建反馈数据的原始扩展ID
    // 反馈数据：data2包含电机ID(bit8~15)，target_id是主机ID
    uint32_t original_feedback_id = MOTOR_LZ_BuildExtID(MOTOR_LZ_CMD_FEEDBACK, param->motor_id, param->host_id);
    // 通过ID解析器得到解析后的ID
    uint32_t parsed_feedback_id = MOTOR_LZ_IdParser(original_feedback_id, BSP_CAN_FRAME_EXT_DATA);
    
    if (BSP_CAN_RegisterId(param->can, parsed_feedback_id, 3) != BSP_OK) {
        BSP_Free(new_motor);
        return DEVICE_ERR;
    }
    
    manager->motors[manager->motor_count] = new_motor;
    manager->motor_count++;
    return DEVICE_OK;
}

int8_t MOTOR_LZ_Update(MOTOR_LZ_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    
    MOTOR_LZ_CANManager_t *manager = MOTOR_LZ_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR_NO_DEV;
    
    for (int i = 0; i < manager->motor_count; i++) {
        MOTOR_LZ_t *motor = manager->motors[i];
        if (motor && motor->param.motor_id == param->motor_id) {
            // 获取反馈数据 - 使用解析后的ID
            uint32_t original_feedback_id = MOTOR_LZ_BuildExtID(MOTOR_LZ_CMD_FEEDBACK, param->motor_id, param->host_id);
            uint32_t parsed_feedback_id = MOTOR_LZ_IdParser(original_feedback_id, BSP_CAN_FRAME_EXT_DATA);
            BSP_CAN_Message_t msg;
            
            while (BSP_CAN_GetMessage(param->can, parsed_feedback_id, &msg, 0) == BSP_OK) {
                MOTOR_LZ_Decode(motor, &msg);
            }
            return DEVICE_OK;
        }
    }
    return DEVICE_ERR_NO_DEV;
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
    }
    return ret;
}

int8_t MOTOR_LZ_MotionControl(MOTOR_LZ_Param_t *param, MOTOR_LZ_MotionParam_t *motion_param) {
    if (param == NULL || motion_param == NULL) return DEVICE_ERR_NULL;
    
    MOTOR_LZ_t *motor = MOTOR_LZ_GetMotor(param);
    if (motor == NULL) return DEVICE_ERR_NO_DEV;
    
    // 更新运控参数
    memcpy(&motor->motion_param, motion_param, sizeof(MOTOR_LZ_MotionParam_t));
    
    // 根据协议，bit23~8数据区2包含力矩信息
    // 力矩范围：-60Nm~60Nm 对应 0~65535
    uint16_t raw_torque = MOTOR_LZ_FloatToRaw(motion_param->torque, LZ_TORQUE_RANGE_NM);
    
    // 构建扩展ID - 运控模式控制指令
    // bit28~24: 0x1 (运控模式)
    // bit23~8:  力矩数据 (0~65535)，协议中描述为"Byte2:力矩"
    // bit7~0:   目标电机CAN_ID
    uint32_t ext_id = MOTOR_LZ_BuildExtID(MOTOR_LZ_CMD_MOTION, raw_torque, param->motor_id);
    
    // 准备8字节数据区
    uint8_t data[8];
    
    // Byte0~1: 目标角度 [0~65535] 对应 (-12.57f~12.57f rad) (高字节在前，低字节在后)
    uint16_t raw_angle = MOTOR_LZ_FloatToRaw(motion_param->target_angle, LZ_ANGLE_RANGE_RAD);
    data[0] = (raw_angle >> 8) & 0xFF;  // 高字节
    data[1] = raw_angle & 0xFF;         // 低字节
    
    // Byte2~3: 目标角速度 [0~65535] 对应 (-20rad/s~20rad/s) (高字节在前，低字节在后)
    uint16_t raw_velocity = MOTOR_LZ_FloatToRaw(motion_param->target_velocity, LZ_VELOCITY_RANGE_RAD_S);
    data[2] = (raw_velocity >> 8) & 0xFF;  // 高字节
    data[3] = raw_velocity & 0xFF;         // 低字节
    
    // Byte4~5: Kp [0~65535] 对应 (0.0~5000.0) (高字节在前，低字节在后)
    uint16_t raw_kp = MOTOR_LZ_FloatToRawPositive(motion_param->kp, LZ_KP_MAX);
    data[4] = (raw_kp >> 8) & 0xFF;     // 高字节
    data[5] = raw_kp & 0xFF;            // 低字节
    
    // Byte6~7: Kd [0~65535] 对应 (0.0~100.0) (高字节在前，低字节在后)
    uint16_t raw_kd = MOTOR_LZ_FloatToRawPositive(motion_param->kd, LZ_KD_MAX);
    data[6] = (raw_kd >> 8) & 0xFF;     // 高字节
    data[7] = raw_kd & 0xFF;            // 低字节
    
    return MOTOR_LZ_SendExtFrame(param->can, ext_id, data, 8);
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
    
    for (int i = 0; i < manager->motor_count; i++) {
        MOTOR_LZ_t *motor = manager->motors[i];
        if (motor && motor->param.motor_id == param->motor_id) {
            return motor;
        }
    }
    return NULL;
}

int8_t MOTOR_LZ_Relax(MOTOR_LZ_Param_t *param) {
    return MOTOR_LZ_Disable(param, false);
}

int8_t MOTOR_LZ_Offline(MOTOR_LZ_Param_t *param) {
    MOTOR_LZ_t *motor = MOTOR_LZ_GetMotor(param);
    if (motor) {
        motor->motor.header.online = false;
        return DEVICE_OK;
    }
    return DEVICE_ERR_NO_DEV;
}

static MOTOR_LZ_Feedback_t* MOTOR_LZ_GetFeedback(MOTOR_LZ_Param_t *param) {
    MOTOR_LZ_t *motor = MOTOR_LZ_GetMotor(param);
    if (motor && motor->motor.header.online) {
        return &motor->lz_feedback;
    }
    return NULL;
}

int8_t MOTOR_LZ_TorqueControl(MOTOR_LZ_Param_t *param, float torque) {
    if (param == NULL) return DEVICE_ERR_NULL;
    
    // 创建运控参数，只设置力矩，其他参数为0
    MOTOR_LZ_MotionParam_t motion_param = {0};
    motion_param.torque = torque;
    motion_param.target_angle = 0.0f;
    motion_param.target_velocity = 0.0f;
    motion_param.kp = 0.0f;
    motion_param.kd = 0.0f;
    
    return MOTOR_LZ_MotionControl(param, &motion_param);
}

int8_t MOTOR_LZ_PositionControl(MOTOR_LZ_Param_t *param, float target_angle, float max_velocity) {
    if (param == NULL) return DEVICE_ERR_NULL;
    
    // 创建运控参数，设置位置和速度限制
    MOTOR_LZ_MotionParam_t motion_param = {0};
    motion_param.target_angle = target_angle;
    motion_param.target_velocity = max_velocity;
    motion_param.torque = 0.0f;
    motion_param.kp = 100.0f;  // 默认位置增益
    motion_param.kd = 5.0f;    // 默认微分增益
    
    return MOTOR_LZ_MotionControl(param, &motion_param);
}

int8_t MOTOR_LZ_VelocityControl(MOTOR_LZ_Param_t *param, float target_velocity) {
    if (param == NULL) return DEVICE_ERR_NULL;
    
    // 创建运控参数，只设置速度
    MOTOR_LZ_MotionParam_t motion_param = {0};
    motion_param.target_angle = 0.0f;
    motion_param.target_velocity = target_velocity;
    motion_param.torque = 0.0f;
    motion_param.kp = 0.0f;
    motion_param.kd = 1.0f;    // 少量阻尼
    
    return MOTOR_LZ_MotionControl(param, &motion_param);
}

int8_t MOTOR_LZ_RecoverToZero(MOTOR_LZ_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    
    MOTOR_LZ_t *motor = MOTOR_LZ_GetMotor(param);
    if (motor == NULL) return DEVICE_ERR_NO_DEV;
    
    // 获取当前角度
    MOTOR_LZ_Feedback_t *feedback = MOTOR_LZ_GetFeedback(param);
    if (feedback == NULL) return DEVICE_ERR_NO_DEV;
    
    float current_angle = feedback->current_angle;
    
    // 计算目标角度为0时的最短路径
    float angle_diff = -current_angle; // 目标是0，所以差值就是-current_angle
    // 限制最大差值，防止过大跳变
    if (angle_diff > LZ_MAX_RECOVER_DIFF_RAD) angle_diff = LZ_MAX_RECOVER_DIFF_RAD;
    if (angle_diff < -LZ_MAX_RECOVER_DIFF_RAD) angle_diff = -LZ_MAX_RECOVER_DIFF_RAD;
    
    float target_angle = current_angle + angle_diff;
    
    // 创建运控参数，设置位置和速度限制
    MOTOR_LZ_MotionParam_t motion_param = lz_recover_param; // 使用预设的恢复参数
    motion_param.target_angle = target_angle;

    return MOTOR_LZ_MotionControl(param, &motion_param);
}