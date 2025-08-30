/*
  LK电机驱动
*/
/* Includes ----------------------------------------------------------------- */
#include "motor_lk.h"
#include <stdbool.h>
#include <string.h>
#include "bsp/can.h"
#include "bsp/mm.h"
#include "bsp/time.h"
#include "component/user_math.h"

/* Private define ----------------------------------------------------------- */
#define LK_CTRL_ID_BASE        (0x140)
#define LK_FB_ID_BASE          (0x240)

// LK电机命令字节定义
#define LK_CMD_FEEDBACK        (0x9C)    // 反馈命令字节
#define LK_CMD_MOTOR_OFF       (0x80)    // 电机关闭命令
#define LK_CMD_MOTOR_ON        (0x88)    // 电机运行命令
#define LK_CMD_TORQUE_CTRL     (0xA1)    // 转矩闭环控制命令

// LK电机参数定义
#define LK_CURR_LSB_MF         (33.0f / 4096.0f)   // MF电机转矩电流分辨率 A/LSB
#define LK_CURR_LSB_MG         (66.0f / 4096.0f)   // MG电机转矩电流分辨率 A/LSB
#define LK_POWER_RANGE_MS      (1000)              // MS电机功率范围 ±1000
#define LK_TORQUE_RANGE        (2048)              // 转矩控制值范围 ±2048
#define LK_TORQUE_CURRENT_MF   (16.5f)             // MF电机最大转矩电流 A
#define LK_TORQUE_CURRENT_MG   (33.0f)             // MG电机最大转矩电流 A

#define MOTOR_TX_BUF_SIZE      (8)
#define MOTOR_RX_BUF_SIZE      (8)

// 编码器分辨率定义
#define LK_ENC_14BIT_MAX       (16383)   // 14位编码器最大值
#define LK_ENC_15BIT_MAX       (32767)   // 15位编码器最大值  
#define LK_ENC_16BIT_MAX       (65535)   // 16位编码器最大值

/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */
static MOTOR_LK_CANManager_t *can_managers[BSP_CAN_NUM] = {NULL};

/* Private functions -------------------------------------------------------- */
static float MOTOR_LK_GetCurrentLSB(MOTOR_LK_Module_t module) {
    switch (module) {
        case MOTOR_LK_MF9025:
        case MOTOR_LK_MF9035:
            return LK_CURR_LSB_MF;
        default:
            return LK_CURR_LSB_MG;  // 默认使用MG的分辨率
    }
}

static uint16_t MOTOR_LK_GetEncoderMax(MOTOR_LK_Module_t module) {
    // 根据电机型号返回编码器最大值，这里假设都使用16位编码器
    // 实际使用时需要根据具体电机型号配置
    return LK_ENC_16BIT_MAX;
}

static MOTOR_LK_CANManager_t* MOTOR_LK_GetCANManager(BSP_CAN_t can) {
    if (can >= BSP_CAN_NUM) return NULL;
    return can_managers[can];
}

static int8_t MOTOR_LK_CreateCANManager(BSP_CAN_t can) {
    if (can >= BSP_CAN_NUM) return DEVICE_ERR;
    if (can_managers[can] != NULL) return DEVICE_OK;
    
    can_managers[can] = (MOTOR_LK_CANManager_t*)BSP_Malloc(sizeof(MOTOR_LK_CANManager_t));
    if (can_managers[can] == NULL) return DEVICE_ERR;
    
    memset(can_managers[can], 0, sizeof(MOTOR_LK_CANManager_t));
    can_managers[can]->can = can;
    return DEVICE_OK;
}

static void MOTOR_LK_Decode(MOTOR_LK_t *motor, BSP_CAN_Message_t *msg) {
    // 检查命令字节是否为反馈命令
    if (msg->data[0] != LK_CMD_FEEDBACK) {
        return;
    }
    
    // 解析温度 (DATA[1])
    motor->motor.feedback.temp = (int8_t)msg->data[1];
    
    // 解析转矩电流值或功率值 (DATA[2], DATA[3])
    int16_t raw_current_or_power = (int16_t)((msg->data[3] << 8) | msg->data[2]);
    
    // 根据电机类型解析电流或功率
    switch (motor->param.module) {
        case MOTOR_LK_MF9025:
        case MOTOR_LK_MF9035:
            // MF/MG电机：转矩电流值
            motor->motor.feedback.torque_current = raw_current_or_power * MOTOR_LK_GetCurrentLSB(motor->param.module);
            break;
        default:
            // MS电机：功率值（范围-1000~1000）
            motor->motor.feedback.torque_current = (float)raw_current_or_power;  // 将功率存储在torque_current字段中
            break;
    }
    
    // 解析转速 (DATA[4], DATA[5]) - 单位：1dps/LSB
    motor->motor.feedback.rotor_speed = (int16_t)((msg->data[5] << 8) | msg->data[4]);
    
    // 解析编码器值 (DATA[6], DATA[7])
    uint16_t raw_encoder = (uint16_t)((msg->data[7] << 8) | msg->data[6]);
    uint16_t encoder_max = MOTOR_LK_GetEncoderMax(motor->param.module);
    
    // 将编码器值转换为弧度 (0 ~ 2π)
    motor->motor.feedback.rotor_abs_angle = (float)raw_encoder / (float)encoder_max * M_2PI;
}

/* Exported functions ------------------------------------------------------- */

int8_t MOTOR_LK_Register(MOTOR_LK_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    
    if (MOTOR_LK_CreateCANManager(param->can) != DEVICE_OK) return DEVICE_ERR;
    MOTOR_LK_CANManager_t *manager = MOTOR_LK_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR;
    
    // 检查是否已注册
    for (int i = 0; i < manager->motor_count; i++) {
        if (manager->motors[i] && manager->motors[i]->param.id == param->id) {
            return DEVICE_ERR_INITED;
        }
    }
    
    // 检查数量
    if (manager->motor_count >= MOTOR_LK_MAX_MOTORS) return DEVICE_ERR;
    
    // 创建新电机实例
    MOTOR_LK_t *new_motor = (MOTOR_LK_t*)BSP_Malloc(sizeof(MOTOR_LK_t));
    if (new_motor == NULL) return DEVICE_ERR;
    
    memcpy(&new_motor->param, param, sizeof(MOTOR_LK_Param_t));
    memset(&new_motor->motor, 0, sizeof(MOTOR_t));
    new_motor->motor.reverse = param->reverse;
    
    // 计算反馈ID（假设为控制ID + 0x40）
    uint16_t feedback_id = param->id + 0x40;
    
    // 注册CAN接收ID
    if (BSP_CAN_RegisterId(param->can, feedback_id, 3) != BSP_OK) {
        BSP_Free(new_motor);
        return DEVICE_ERR;
    }
    
    manager->motors[manager->motor_count] = new_motor;
    manager->motor_count++;
    return DEVICE_OK;
}

int8_t MOTOR_LK_Update(MOTOR_LK_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    
    MOTOR_LK_CANManager_t *manager = MOTOR_LK_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR_NO_DEV;
    
    for (int i = 0; i < manager->motor_count; i++) {
        MOTOR_LK_t *motor = manager->motors[i];
        if (motor && motor->param.id == param->id) {
            // 计算反馈ID
            uint16_t feedback_id = param->id + 0x100;
            
            BSP_CAN_Message_t rx_msg;
            if (BSP_CAN_GetMessage(param->can, feedback_id, &rx_msg, BSP_CAN_TIMEOUT_IMMEDIATE) != BSP_OK) {
                uint64_t now_time = BSP_TIME_Get();
                if (now_time - motor->motor.header.last_online_time > 1000) {
                    motor->motor.header.online = false;
                    return DEVICE_ERR_NO_DEV;
                }
                return DEVICE_ERR;
            }
            
            motor->motor.header.online = true;
            motor->motor.header.last_online_time = BSP_TIME_Get();
            MOTOR_LK_Decode(motor, &rx_msg);
            return DEVICE_OK;
        }
    }
    return DEVICE_ERR_NO_DEV;
}

int8_t MOTOR_LK_UpdateAll(void) {
    int8_t ret = DEVICE_OK;
    for (int can = 0; can < BSP_CAN_NUM; can++) {
        MOTOR_LK_CANManager_t *manager = MOTOR_LK_GetCANManager((BSP_CAN_t)can);
        if (manager == NULL) continue;
        
        for (int i = 0; i < manager->motor_count; i++) {
            MOTOR_LK_t *motor = manager->motors[i];
            if (motor != NULL) {
                if (MOTOR_LK_Update(&motor->param) != DEVICE_OK) {
                    ret = DEVICE_ERR;
                }
            }
        }
    }
    return ret;
}

int8_t MOTOR_LK_SetOutput(MOTOR_LK_Param_t *param, float value) {
    if (param == NULL) return DEVICE_ERR_NULL;
    
    MOTOR_LK_CANManager_t *manager = MOTOR_LK_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR_NO_DEV;
    
    // 限制输出值范围
    if (value > 1.0f) value = 1.0f;
    if (value < -1.0f) value = -1.0f;
    
    MOTOR_LK_t *motor = MOTOR_LK_GetMotor(param);
    if (motor == NULL) return DEVICE_ERR_NO_DEV;
    
    // 转矩闭环控制命令 - 将输出值转换为转矩控制值
    int16_t torque_control = (int16_t)(value * (float)LK_TORQUE_RANGE);
    
    // 构建CAN帧
    BSP_CAN_StdDataFrame_t tx_frame;
    tx_frame.id = param->id;
    tx_frame.dlc = MOTOR_TX_BUF_SIZE;
    
    // 设置转矩闭环控制命令数据
    tx_frame.data[0] = LK_CMD_TORQUE_CTRL;  // 命令字节
    tx_frame.data[1] = 0x00;                // NULL
    tx_frame.data[2] = 0x00;                // NULL
    tx_frame.data[3] = 0x00;                // NULL
    tx_frame.data[4] = (uint8_t)(torque_control & 0xFF);        // 转矩电流控制值低字节
    tx_frame.data[5] = (uint8_t)((torque_control >> 8) & 0xFF); // 转矩电流控制值高字节
    tx_frame.data[6] = 0x00;                // NULL
    tx_frame.data[7] = 0x00;                // NULL
    
    return BSP_CAN_TransmitStdDataFrame(param->can, &tx_frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}

int8_t MOTOR_LK_Ctrl(MOTOR_LK_Param_t *param) {
    // 对于LK电机，每次设置输出时就直接发送控制命令
    // 这个函数可以用于发送其他控制命令，如电机开启/关闭
    return DEVICE_OK;
}

int8_t MOTOR_LK_MotorOn(MOTOR_LK_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    
    BSP_CAN_StdDataFrame_t tx_frame;
    tx_frame.id = param->id;
    tx_frame.dlc = MOTOR_TX_BUF_SIZE;
    
    // 电机运行命令
    tx_frame.data[0] = LK_CMD_MOTOR_ON;     // 命令字节
    tx_frame.data[1] = 0x00;
    tx_frame.data[2] = 0x00;
    tx_frame.data[3] = 0x00;
    tx_frame.data[4] = 0x00;
    tx_frame.data[5] = 0x00;
    tx_frame.data[6] = 0x00;
    tx_frame.data[7] = 0x00;
    
    return BSP_CAN_TransmitStdDataFrame(param->can, &tx_frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}

int8_t MOTOR_LK_MotorOff(MOTOR_LK_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    
    BSP_CAN_StdDataFrame_t tx_frame;
    tx_frame.id = param->id;
    tx_frame.dlc = MOTOR_TX_BUF_SIZE;
    
    // 电机关闭命令
    tx_frame.data[0] = LK_CMD_MOTOR_OFF;    // 命令字节
    tx_frame.data[1] = 0x00;
    tx_frame.data[2] = 0x00;
    tx_frame.data[3] = 0x00;
    tx_frame.data[4] = 0x00;
    tx_frame.data[5] = 0x00;
    tx_frame.data[6] = 0x00;
    tx_frame.data[7] = 0x00;
    
    return BSP_CAN_TransmitStdDataFrame(param->can, &tx_frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}

MOTOR_LK_t* MOTOR_LK_GetMotor(MOTOR_LK_Param_t *param) {
    if (param == NULL) return NULL;
    
    MOTOR_LK_CANManager_t *manager = MOTOR_LK_GetCANManager(param->can);
    if (manager == NULL) return NULL;
    
    for (int i = 0; i < manager->motor_count; i++) {
        MOTOR_LK_t *motor = manager->motors[i];
        if (motor && motor->param.id == param->id) {
            return motor;
        }
    }
    return NULL;
}

int8_t MOTOR_LK_Relax(MOTOR_LK_Param_t *param) {
    return MOTOR_LK_SetOutput(param, 0.0f);
}

int8_t MOTOR_LK_Offine(MOTOR_LK_Param_t *param) {
    MOTOR_LK_t *motor = MOTOR_LK_GetMotor(param);
    if (motor) {
        motor->motor.header.online = false;
        return DEVICE_OK;
    }
    return DEVICE_ERR_NO_DEV;
}