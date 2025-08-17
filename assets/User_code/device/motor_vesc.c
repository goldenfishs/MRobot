/*
  CAN总线上的设备
  将所有CAN总线上挂载的设备抽象成一个设备进行配置和控制
*/
/* Includes ----------------------------------------------------------------- */
#include "motor_vesc.h"
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

/**************************************
 * 限幅函数
 **************************************/
void assert_param_duty(float *duty){
    // 如果 duty 是 -1.0 ~ 1.0，则最大值用 wtrcfg_VESC_COMMAND_DUTY_MAX / 100
    float max_duty = wtrcfg_VESC_COMMAND_DUTY_MAX / 100.0f;
    if (fabsf(*duty) > max_duty) {
        *duty = (*duty > 0) ? max_duty : -max_duty;
    }
}

void assert_param_current(float *current){
	if( fabsf(*current) > wtrcfg_VESC_COMMAND_CURRENT_MAX )
		*current = *current > 0 ? wtrcfg_VESC_COMMAND_CURRENT_MAX : - wtrcfg_VESC_COMMAND_CURRENT_MAX ;
}
void assert_param_rpm(float *rpm){
	if( fabsf(*rpm) > wtrcfg_VESC_COMMAND_ERPM_MAX )
		*rpm = *rpm > 0 ? wtrcfg_VESC_COMMAND_ERPM_MAX : - wtrcfg_VESC_COMMAND_ERPM_MAX ;
}
void assert_param_pos(float *pos){
	if( fabsf(*pos) > wtrcfg_VESC_COMMAND_POS_MAX )
		*pos = *pos > 0 ? wtrcfg_VESC_COMMAND_POS_MAX : - wtrcfg_VESC_COMMAND_POS_MAX ;
}

static VESC_CANManager_t *can_managers[BSP_CAN_NUM] = {NULL};


// 获取指定CAN总线的电机管理器指针
static VESC_CANManager_t* MOTOR_GetCANManager(BSP_CAN_t can) {
    if (can >= BSP_CAN_NUM) return NULL;
    return can_managers[can];
}

// 为指定CAN总线创建电机管理器
static int8_t MOTOR_CreateCANManager(BSP_CAN_t can) {
    if (can >= BSP_CAN_NUM) return DEVICE_ERR;
    if (can_managers[can] != NULL) return DEVICE_OK;
    can_managers[can] = (VESC_CANManager_t*)BSP_Malloc(sizeof(VESC_CANManager_t));
    if (can_managers[can] == NULL) return DEVICE_ERR;
    memset(can_managers[can], 0, sizeof(VESC_CANManager_t));
    can_managers[can]->can = can;
    return DEVICE_OK;
}

// 解析CAN报文，更新电机反馈信息
static void Motor_VESC_Decode(VESC_t *motor, BSP_CAN_Message_t *msg)
{
    if (motor == NULL || msg == NULL) return;
    motor->motor.feedback.rotor_speed = 
        ((int32_t)msg->data[0] << 24) |
        ((int32_t)msg->data[1] << 16) |
        ((int32_t)msg->data[2] << 8)  |
        ((int32_t)msg->data[3]);

    // torque_current: 低 2 字节 (data[4], data[5])
    int16_t raw_current = (int16_t)((msg->data[5] << 8) | msg->data[4]);
    motor->motor.feedback.torque_current = raw_current / 1000.0f;  // 从 0.1A -> A

    // duty_cycle: 低 2 字节 (data[6], data[7])
    int16_t raw_duty = (int16_t)((msg->data[7] << 8) | msg->data[6]);
    //motor->motor.feedback.duty_cycle = raw_duty / 1000.0f;  // 从千分之一 -> (-1.0 ~ 1.0)

}


/* Exported functions ------------------------------------------------------- */

// 注册一个新的电机实例到管理器
int8_t VESC_Register(VESC_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    if (MOTOR_CreateCANManager(param->can) != DEVICE_OK) return DEVICE_ERR;
    VESC_CANManager_t *manager = MOTOR_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR;
    // 检查是否已注册
    for (int i = 0; i < manager->motor_count; i++) {
        if (manager->motors[i] && manager->motors[i]->param.id == param->id) {
            return DEVICE_ERR_INITED;
        }
    }
    // 检查数量
    if (manager->motor_count >= VESC_MAX_MOTORS) return DEVICE_ERR;
    // 创建新电机实例
    VESC_t *new_motor = (VESC_t*)BSP_Malloc(sizeof(VESC_t));
    if (new_motor == NULL) return DEVICE_ERR;
    memcpy(&new_motor->param, param, sizeof(VESC_Param_t));
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

// 更新指定电机的反馈数据（扩展帧方式）
int8_t VESC_Update(VESC_Param_t *param)
{
    if (param == NULL) return DEVICE_ERR_NULL;
    VESC_CANManager_t *manager = MOTOR_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR_NO_DEV;
    VESC_t *motor = NULL;
    for (int i = 0; i < manager->motor_count; i++) {
        if (manager->motors[i] && manager->motors[i]->param.id == param->id) {
            motor = manager->motors[i];
            break;
        }
    }
    if (motor == NULL) return DEVICE_ERR_NO_DEV;
    // 根据电机 ID 获取对应扩展帧 ID
    uint32_t ext_id = 0;
    switch (param->id) {
        case VESC_1: ext_id = CAN_VESC5065_M1_MSG1; break;
        case VESC_2: ext_id = CAN_VESC5065_M2_MSG1; break;
        case VESC_4: ext_id = CAN_VESC5065_M3_MSG1; break;
        default: return DEVICE_ERR_NO_DEV;
    }
    BSP_CAN_Message_t rx_msg;
    if (BSP_CAN_GetMessage(param->can, ext_id, &rx_msg, BSP_CAN_TIMEOUT_IMMEDIATE) != BSP_OK) {
        uint64_t now_time = BSP_TIME_Get();
        if (now_time - motor->motor.header.last_online_time > 1000) {
            motor->motor.header.online = false;
            return DEVICE_ERR_NO_DEV;
        }
        return DEVICE_ERR;
    }
    motor->motor.header.online = true;
    motor->motor.header.last_online_time = BSP_TIME_Get();
    Motor_VESC_Decode(motor, &rx_msg);
    return DEVICE_OK;
}

// 更新所有CAN总线下所有电机的反馈数据
int8_t VESC_UpdateAll(void) {
    int8_t ret = DEVICE_OK;
    for (int can = 0; can < BSP_CAN_NUM; can++) {
        VESC_CANManager_t *manager = MOTOR_GetCANManager((BSP_CAN_t)can);
        if (manager == NULL) continue;
        for (int i = 0; i < manager->motor_count; i++) {
            VESC_t *motor = manager->motors[i];
            if (motor != NULL) {
                if (VESC_Update(&motor->param) != DEVICE_OK) {
                    ret = DEVICE_ERR;
                }
            }
        }
    }
    return ret;
}

// 获取指定参数对应的电机实例指针
VESC_t* VESC_GetMotor(VESC_Param_t *param) {
    if (param == NULL) return NULL;
    VESC_CANManager_t *manager = MOTOR_GetCANManager(param->can);
    if (manager == NULL) return NULL;
    for (int i = 0; i < manager->motor_count; i++) {
        VESC_t *motor = manager->motors[i];
        if (motor && motor->param.id == param->id) {
            return motor;
        }
    }
    return NULL;
}

// 设置指定电机的输出值
int8_t VESC_SetOutput(VESC_Param_t *param, float value)
{
    if (param == NULL) return DEVICE_ERR_NULL;
    BSP_CAN_StdDataFrame_t tx_frame;
    uint16_t command_id;

    if (param->reverse) {
        value = -value;
    }

    switch (param->mode)
    {
        case DUTY_CONTROL: {
            assert_param_duty(&value); // 调用你现有的限幅函数
            command_id = CAN_PACKET_SET_DUTY;
            int32_t duty_val = (int32_t)(value * 1e5f); // duty 放大 1e5
            memcpy(&tx_frame.data[0], &duty_val, 4);
            tx_frame.dlc = 4;
            break;
        }
        case RPM_CONTROL: {
            assert_param_rpm(&value); 
            command_id = CAN_PACKET_SET_RPM;
            int32_t rpm_val = (int32_t)value;
            memcpy(&tx_frame.data[0], &rpm_val, 4);
            tx_frame.dlc = 4;
            break;
        }
        case CURRENT_CONTROL: {
            assert_param_current(&value); 
            command_id = CAN_PACKET_SET_CURRENT;
            int32_t cur_val = (int32_t)(value * 1e3f); // A -> mA （0-50A）
            memcpy(&tx_frame.data[0], &cur_val, 4);
            tx_frame.dlc = 4;
            break;
        }
        case POSITION_CONTROL: {
            assert_param_pos(&value); 
            command_id = CAN_PACKET_SET_POS;
            memcpy(&tx_frame.data[0], &value, 4); 
            tx_frame.dlc = 4;
            break;
        }
        default:
            return DEVICE_ERR;
    }
    tx_frame.id = (param->id << 5) | command_id;
    return BSP_CAN_TransmitStdDataFrame(param->can, &tx_frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
  }

int8_t VESC_Relax(VESC_Param_t *param) {
    return VESC_SetOutput(param, 0.0f);
}


int8_t VESC_Offine(VESC_Param_t *param) {
    VESC_t *motor = VESC_GetMotor(param);
    if (motor) {
        motor->motor.header.online = false;
        return DEVICE_OK;
    }
    return DEVICE_ERR_NO_DEV;
}