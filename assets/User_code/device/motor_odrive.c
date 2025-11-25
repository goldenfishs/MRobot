/*
  Odrive电机驱动
*/
/* Includes ----------------------------------------------------------------- */
#include "motor_odrive.h"
#include <stdbool.h>
#include <string.h>
#include "bsp/can.h"
#include "bsp/mm.h"
#include "bsp/time.h"
#include "component/user_math.h"

/* Private define ----------------------------------------------------------- */


/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */
static ODrive_CANManager_t *can_managers[BSP_CAN_NUM] = {NULL};


// 获取指定CAN总线的电机管理器指针
static ODrive_CANManager_t* MOTOR_GetCANManager(BSP_CAN_t can) {
    if (can >= BSP_CAN_NUM) return NULL;
    return can_managers[can];
}

// 为指定CAN总线创建电机管理器
static int8_t MOTOR_CreateCANManager(BSP_CAN_t can) {
    if (can >= BSP_CAN_NUM) return DEVICE_ERR;
    if (can_managers[can] != NULL) return DEVICE_OK;
    can_managers[can] = (ODrive_CANManager_t*)BSP_Malloc(sizeof(ODrive_CANManager_t));
    if (can_managers[can] == NULL) return DEVICE_ERR;
    memset(can_managers[can], 0, sizeof(ODrive_CANManager_t));
    can_managers[can]->can = can;
    return DEVICE_OK;
}

// 解析CAN报文，更新电机反馈信息
static void Motor_Decode(ODrive_t *motor, BSP_CAN_Message_t *msg)
{
    uint8_t axis_id = (msg->original_id >> 5) & 0x3F;   // 提取电机号（0~63）
    uint8_t cmd_id  = msg->original_id & 0x1F;          // 提取命令 ID（低 5 位）

    motor->param.id = axis_id; // 保存电机 ID

    // 解析帧类型（数据帧或远程帧）
    if (msg->frame_type == BSP_CAN_FRAME_STD_DATA) {
        // 数据帧处理
        switch (cmd_id)
        {
        case ODRIVE_HEARTBEAT_MESSAGE: // 0x001 ODrive心跳消息
            // motor->motor.feedback.axis_error      = (msg->data[0] | msg->data[1]<<8 | msg->data[2]<<16 | msg->data[3]<<24);
            // motor->motor.feedback.axis_state      = msg->data[4];
            // motor->motor.feedback.controller_status = msg->data[5];
            break;

        case ENCODER_ESTIMATES: // 0x009
            {
                uint32_t raw_pos = (msg->data[0] | msg->data[1]<<8 | msg->data[2]<<16 | msg->data[3]<<24);
                uint32_t raw_vel = (msg->data[4] | msg->data[5]<<8 | msg->data[6]<<16 | msg->data[7]<<24);
                memcpy(&motor->motor.feedback.rotor_abs_angle, &raw_pos, sizeof(float));
                memcpy(&motor->motor.feedback.rotor_speed, &raw_vel, sizeof(float));
            }
            break;

        case GET_ENCODER_COUNT: // 0x014
            // motor->motor.feedback.encoder_shadow = (msg->data[0] | msg->data[1]<<8 | msg->data[2]<<16 | msg->data[3]<<24);
            // motor->motor.feedback.encoder_cpr    = (msg->data[4] | msg->data[5]<<8 | msg->data[6]<<16 | msg->data[7]<<24);
            break;

        case GET_BUS_VOLTAGE_CURRENT: // 0x017
            {
                uint32_t raw_vbus, raw_ibus;
                raw_vbus = (msg->data[0] | msg->data[1]<<8 | msg->data[2]<<16 | msg->data[3]<<24);
                raw_ibus = (msg->data[4] | msg->data[5]<<8 | msg->data[6]<<16 | msg->data[7]<<24);
                // memcpy(&motor->motor.feedback.bus_voltage, &raw_vbus, sizeof(float));
                memcpy(&motor->motor.feedback.torque_current, &raw_ibus, sizeof(float));
            }
            break;

        case GET_IQ: // 0x018
            {
                uint32_t raw_iq_set, raw_iq_meas;
                raw_iq_set  = (msg->data[0] | msg->data[1]<<8 | msg->data[2]<<16 | msg->data[3]<<24);
                raw_iq_meas = (msg->data[4] | msg->data[5]<<8 | msg->data[6]<<16 | msg->data[7]<<24);
                // memcpy(&motor->motor.feedback.iq_setpoint, &raw_iq_set, sizeof(float));
                // memcpy(&motor->motor.feedback.iq_measured, &raw_iq_meas, sizeof(float));
            }
            break;

        default:
            
            break;
        }
    }
}


/* Exported functions ------------------------------------------------------- */

// 注册一个新的电机实例到管理器
int8_t ODrive_Register(ODrive_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    if (MOTOR_CreateCANManager(param->can) != DEVICE_OK) return DEVICE_ERR;
    ODrive_CANManager_t *manager = MOTOR_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR;
    // 检查是否已注册
    for (int i = 0; i < manager->motor_count; i++) {
        if (manager->motors[i] && manager->motors[i]->param.id == param->id) {
            return DEVICE_ERR_INITED;
        }
    }
    // 检查数量
    if (manager->motor_count >= ODRIVE_MAX_MOTORS) return DEVICE_ERR;
    // 创建新电机实例
    ODrive_t *new_motor = (ODrive_t*)BSP_Malloc(sizeof(ODrive_t));
    if (new_motor == NULL) return DEVICE_ERR;
    memcpy(&new_motor->param, param, sizeof(ODrive_Param_t));
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

// 更新指定电机的反馈数据
int8_t ODrive_Update(ODrive_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    ODrive_CANManager_t *manager = MOTOR_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR_NO_DEV;
    for (int i = 0; i < manager->motor_count; i++) {
        ODrive_t *motor = manager->motors[i];
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
            Motor_Decode(motor, &rx_msg);
            return DEVICE_OK;
        }
    }
    return DEVICE_ERR_NO_DEV;
}

// 更新所有CAN总线下所有电机的反馈数据
int8_t ODrive_UpdateAll(void) {
    int8_t ret = DEVICE_OK;
    for (int can = 0; can < BSP_CAN_NUM; can++) {
        ODrive_CANManager_t *manager = MOTOR_GetCANManager((BSP_CAN_t)can);
        if (manager == NULL) continue;
        for (int i = 0; i < manager->motor_count; i++) {
            ODrive_t *motor = manager->motors[i];
            if (motor != NULL) {
                if (ODrive_Update(&motor->param) != DEVICE_OK) {
                    ret = DEVICE_ERR;
                }
            }
        }
    }
    return ret;
}

// 获取指定参数对应的电机实例指针
ODrive_t* ODrive_GetMotor(ODrive_Param_t *param) {
    if (param == NULL) return NULL;
    ODrive_CANManager_t *manager = MOTOR_GetCANManager(param->can);
    if (manager == NULL) return NULL;
    for (int i = 0; i < manager->motor_count; i++) {
        ODrive_t *motor = manager->motors[i];
        if (motor && motor->param.id == param->id) {
            return motor;
        }
    }
    return NULL;
}

// 设置指定电机的输出值
int8_t ODrive_SetOutput(ODrive_Param_t *param, float value) {
    if (param == NULL) return DEVICE_ERR_NULL;

    // 如果电机反转标志为 true，则反向值
    if (param->reverse) {
        value = -value;
    }

    BSP_CAN_StdDataFrame_t tx_frame;
    uint16_t command_id;
    uint8_t *pVal = (uint8_t *)&value;

    // 选择命令 ID 和数据打包方式
    switch (param->mode) {
        case POSITION_CONTROL: {
            command_id = SET_INPUT_POS;
            float pos = value;
            int16_t vel_ff = 0;     // 可扩展为参数传入  0就行
            int16_t torque_ff = 0;  // 可扩展为参数传入  0就行
            uint8_t *pPos = (uint8_t *)&pos;
            uint8_t *pVel = (uint8_t *)&vel_ff;
            uint8_t *pTor = (uint8_t *)&torque_ff;
            memcpy(&tx_frame.data[0], pPos, 4);
            memcpy(&tx_frame.data[4], pVel, 2);
            memcpy(&tx_frame.data[6], pTor, 2);
            tx_frame.dlc = 8;
            break;
        }
        case VELOCITY_CONTROL: {
            command_id = SET_INPUT_VEL;
            float vel = value;
            float torque_ff = 0.0f; // 可扩展为参数传入
            uint8_t *pVel = (uint8_t *)&vel;
            uint8_t *pTor = (uint8_t *)&torque_ff;
            memcpy(&tx_frame.data[0], pVel, 4);
            memcpy(&tx_frame.data[4], pTor, 4);
            tx_frame.dlc = 8;
            break;
        }
        case TORQUE_CONTROL: {
            command_id = SET_INPUT_TORQUE;
            memcpy(&tx_frame.data[0], pVal, 4);
            tx_frame.dlc = 4;
            break;
        }
        case VOLTAGE_CONTROL:
        default:
            return DEVICE_ERR; // 暂不支持电压模式
    }

    // 组装 CAN ID（标准帧）
    tx_frame.id = (param->id << 5) | command_id;

    // 标准数据帧
    return BSP_CAN_TransmitStdDataFrame(param->can, &tx_frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}

// 设置加速度和减速度
int8_t ODrive_SetAccel(ODrive_Param_t *param, float accel, float decel) {
    if (param == NULL) return DEVICE_ERR_NULL;

    BSP_CAN_StdDataFrame_t tx_frame;
    uint16_t command_id = SET_TRAJ_ACCEL_LIMITS;

    uint8_t *pAccel = (uint8_t *)&accel;
    uint8_t *pDecel = (uint8_t *)&decel;
    memcpy(&tx_frame.data[0], pAccel, 4);
    memcpy(&tx_frame.data[4], pDecel, 4);
    tx_frame.dlc = 8;

    tx_frame.id = (param->id << 5) | command_id;
    return BSP_CAN_TransmitStdDataFrame(param->can, &tx_frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}

// 获取位置和速度反馈
int8_t ODrive_RequestEncoderEstimates(ODrive_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;

    BSP_CAN_StdDataFrame_t tx_frame;
    uint16_t command_id = ENCODER_ESTIMATES;  // 请求编码器估计值命令
    uint8_t zero_data[8] = {0};               // 发送全 0 数据（ODrive 协议要求）

    memcpy(tx_frame.data, zero_data, 8);
    tx_frame.dlc = 8;
    tx_frame.id = (param->id << 5) | command_id;

    return BSP_CAN_TransmitStdDataFrame(param->can, &tx_frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}

// 设置轴请求状态（一般用来重启 ODrive 的某个轴）
// ODrive_SetAxisRequestedState(odrive_axis[0], CLOSED_LOOP_CONTROL);
int8_t ODrive_SetAxisRequestedState(ODrive_Param_t *param, Axis_State state) {
    if (param == NULL) return DEVICE_ERR_NULL;

    BSP_CAN_StdDataFrame_t tx_frame;
    uint16_t command_id = SET_AXIS_REQUESTED_STATE;

    // 将 state 转为 4 字节
    memcpy(tx_frame.data, &state, 4);
    memset(&tx_frame.data[4], 0, 4);  
    tx_frame.dlc = 4;

    // 组装 CAN ID
    tx_frame.id = (param->id << 5) | command_id;

    return BSP_CAN_TransmitStdDataFrame(param->can, &tx_frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}

// 清除错误
int8_t ODrive_ClearErrors(ODrive_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;

    BSP_CAN_StdDataFrame_t tx_frame;
    uint16_t command_id = CLEAR_ERRORS;

    memset(tx_frame.data, 0, 8);  
    tx_frame.dlc = 0;

    tx_frame.id = (param->id << 5) | command_id;

    return BSP_CAN_TransmitStdDataFrame(param->can, &tx_frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}

// 重启 ODrive
int8_t ODrive_Reboot(ODrive_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;

    BSP_CAN_StdDataFrame_t tx_frame;
    uint16_t command_id = REBOOT_ODRIVE;

    memset(tx_frame.data, 0, 8); 
    tx_frame.dlc = 0;

    tx_frame.id = (param->id << 5) | command_id;

    return BSP_CAN_TransmitStdDataFrame(param->can, &tx_frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}
