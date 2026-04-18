/*
    VESC 电机驱动

    功能说明：
    1. 管理单条 CAN 总线上的多个 VESC 电机实例；
    2. 通过扩展帧接收 VESC 状态反馈；
    3. 按不同控制模式发送占空比 / 电流 / 转速 / 位置控制命令。
*/
/* Includes ----------------------------------------------------------------- */
#include "motor_vesc.h"

#include <stdbool.h>
#include <string.h>

#include "bsp/can.h"
#include "bsp/mm.h"
#include "bsp/time.h"
#include "component/user_math.h"

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

/* Private define ----------------------------------------------------------- */
/* USER DEFINE BEGIN */

/* USER DEFINE END */

/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* USER STRUCT BEGIN */

/* USER STRUCT END */

/* Private variables -------------------------------------------------------- */
/*
 * 按 CAN 编号保存对应的 VESC 管理器。
 * 一条 CAN 总线对应一个管理器，管理器内部维护该总线上的所有 VESC 实例。
 */
static VESC_CANManager_t *can_managers[BSP_CAN_NUM] = {NULL};

/*
 * 接收缓存。
 * 当前实现中用于读取指定扩展帧的最新消息。
 */
static BSP_CAN_Message_t rx_msg;

/* Private function  -------------------------------------------------------- */
/* USER FUNCTION BEGIN */

/* USER FUNCTION END */

/**************************************
 * 参数限幅函数
 *
 * 不同控制模式下，VESC 命令的量纲和最大值不同。
 * 这些辅助函数用于在发送命令前对输入值做安全裁剪，
 * 防止上层传入异常值导致驱动器输出超范围。
 **************************************/
static void assert_param_duty(float *duty) {
    /* 如果 duty 是 -1.0 ~ 1.0，则最大值用 wtrcfg_VESC_COMMAND_DUTY_MAX / 100 */
    float max_duty = wtrcfg_VESC_COMMAND_DUTY_MAX / 100.0f;
    if (fabsf(*duty) > max_duty) {
        *duty = (*duty > 0) ? max_duty : -max_duty;
    }
}

static void assert_param_current(float *current) {
	if (fabsf(*current) > wtrcfg_VESC_COMMAND_CURRENT_MAX) {
		*current = *current > 0 ? wtrcfg_VESC_COMMAND_CURRENT_MAX : -wtrcfg_VESC_COMMAND_CURRENT_MAX;
	}
}

static void assert_param_rpm(float *rpm) {
	if (fabsf(*rpm) > wtrcfg_VESC_COMMAND_ERPM_MAX) {
		*rpm = *rpm > 0 ? wtrcfg_VESC_COMMAND_ERPM_MAX : -wtrcfg_VESC_COMMAND_ERPM_MAX;
	}
}

static void assert_param_pos(float *pos) {
	if (fabsf(*pos) > wtrcfg_VESC_COMMAND_POS_MAX) {
		*pos = *pos > 0 ? wtrcfg_VESC_COMMAND_POS_MAX : -wtrcfg_VESC_COMMAND_POS_MAX;
	}
}

/*
 * @brief 根据 VESC 节点 ID 计算状态回传扩展帧 ID
 *
 * VESC 状态帧格式：
 * - 高 8 位：帧类型（如 CAN_PACKET_STATUS）
 * - 低 8 位：电机节点 ID
 */
static uint32_t VESC_GetStatusExtId(uint16_t id) {
    return ((uint32_t)CAN_PACKET_STATUS << 8) | id;
}

/*
 * @brief 获取指定 CAN 总线的电机管理器
 * @param can CAN 总线编号
 * @return 管理器指针，若 CAN 编号非法则返回 NULL
 */
static VESC_CANManager_t *MOTOR_GetCANManager(BSP_CAN_t can) {
    if (can >= BSP_CAN_NUM) return NULL;
    return can_managers[can];
}

/*
 * @brief 为指定 CAN 总线创建管理器
 * @param can CAN 总线编号
 * @return DEVICE_OK 表示成功，DEVICE_ERR 表示失败
 *
 * 若管理器已存在则直接返回成功。
 */
static int8_t MOTOR_CreateCANManager(BSP_CAN_t can) {
    if (can >= BSP_CAN_NUM) return DEVICE_ERR;
    if (can_managers[can] != NULL) return DEVICE_OK;
    can_managers[can] = (VESC_CANManager_t *)BSP_Malloc(sizeof(VESC_CANManager_t));
    if (can_managers[can] == NULL) return DEVICE_ERR;
    memset(can_managers[can], 0, sizeof(VESC_CANManager_t));
    can_managers[can]->can = can;
    return DEVICE_OK;
}

/*
 * @brief 解析 VESC 状态反馈帧
 * @param motor 目标电机实例
 * @param msg   CAN 接收报文
 *
 * 当前解析内容：
 * - data[0:3]：转速 rotor_speed
 * - data[4:5]：转矩电流 torque_current
 * - data[6:7]：占空比 duty_cycle（当前仅预留，未写入 feedback）
 */
static void Motor_VESC_Decode(VESC_t *motor, BSP_CAN_Message_t *msg) {
    if (motor == NULL || msg == NULL) return;

    /* 前 4 字节为 32 位转速反馈，按大端格式拼接 */
    motor->motor.feedback.rotor_speed = ((int32_t)msg->data[0] << 24) |
                                        ((int32_t)msg->data[1] << 16) |
                                        ((int32_t)msg->data[2] << 8) |
                                        ((int32_t)msg->data[3]);

    /* torque_current: 低 2 字节 (data[4], data[5]) */
    int16_t raw_current = (int16_t)((msg->data[5] << 8) | msg->data[4]);
    motor->motor.feedback.torque_current = raw_current / 1000.0f; /* 从 0.1A -> A */

    /* duty_cycle: 后 2 字节 (data[6], data[7])，当前仅保留解析入口 */
    int16_t raw_duty = (int16_t)((msg->data[7] << 8) | msg->data[6]);
    (void)raw_duty;
    /* motor->motor.feedback.duty_cycle = raw_duty / 1000.0f; */
}


/* Exported functions ------------------------------------------------------- */

/*
 * @brief 注册一个新的 VESC 电机实例
 * @param param 电机参数
 * @return DEVICE_OK 表示注册成功
 *
 * 主要流程：
 * 1. 确保对应 CAN 管理器已创建；
 * 2. 检查电机是否重复注册；
 * 3. 分配电机实例内存并保存参数；
 * 4. 注册该电机对应的状态反馈扩展帧 ID。
 */
int8_t VESC_Register(VESC_Param_t *param) {
    if (param == NULL) return DEVICE_ERR_NULL;
    if (MOTOR_CreateCANManager(param->can) != DEVICE_OK) return DEVICE_ERR;
    VESC_CANManager_t *manager = MOTOR_GetCANManager(param->can);
    if (manager == NULL) return DEVICE_ERR;

    /* 检查是否重复注册同一节点 ID */
    for (int i = 0; i < manager->motor_count; i++) {
        if (manager->motors[i] && manager->motors[i]->param.id == param->id) {
            return DEVICE_ERR_INITED;
        }
    }

    /* 检查当前总线下电机数量是否超限 */
    if (manager->motor_count >= VESC_MAX_MOTORS) return DEVICE_ERR;

    /* 创建新电机实例 */
    VESC_t *new_motor = (VESC_t *)BSP_Malloc(sizeof(VESC_t));
    if (new_motor == NULL) return DEVICE_ERR;
    memcpy(&new_motor->param, param, sizeof(VESC_Param_t));
    memset(&new_motor->motor, 0, sizeof(MOTOR_t));
    new_motor->motor.reverse = param->reverse;

    /* 注册 CAN 接收 ID（VESC 状态反馈使用扩展帧） */
    if (BSP_CAN_RegisterId(param->can, VESC_GetStatusExtId(param->id), 3) != BSP_OK) {
        BSP_Free(new_motor);
        return DEVICE_ERR;
    }
    manager->motors[manager->motor_count] = new_motor;
    manager->motor_count++;
    return DEVICE_OK;
}

/*
 * @brief 更新指定电机的反馈数据
 * @param param 电机参数
 * @return DEVICE_OK 表示更新成功
 *
 * 若当前未收到新报文：
 * - 超过一定时间未在线，则将电机置为离线；
 * - 否则返回一般错误，表示本次未拿到新数据。
 */
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

    /* 根据电机 ID 计算对应状态帧扩展 ID */
    uint32_t ext_id = VESC_GetStatusExtId(param->id);
    
    if (BSP_CAN_GetMessage(param->can, ext_id, &rx_msg, BSP_CAN_TIMEOUT_IMMEDIATE) != BSP_OK) {
        uint64_t now_time = BSP_TIME_Get();

        /* 超时未收到反馈，标记为离线 */
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

/*
 * @brief 更新所有 CAN 总线上的全部 VESC 电机反馈
 * @return int8_t 只要有一个电机更新失败，就返回 DEVICE_ERR
 */
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

/*
 * @brief 根据参数查找已注册的电机实例
 * @param param 电机参数
 * @return 匹配到的电机实例指针，失败返回 NULL
 */
VESC_t *VESC_GetMotor(VESC_Param_t *param) {
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

/*
 * @brief 将 32 位整数按大端序写入 4 字节缓冲区
 * @param buf 目标缓冲区
 * @param val 待写入的值
 */
static void VESC_PutInt32BE(uint8_t *buf, int32_t val) {
    buf[0] = (uint8_t)(val >> 24);
    buf[1] = (uint8_t)(val >> 16);
    buf[2] = (uint8_t)(val >> 8);
    buf[3] = (uint8_t)(val);
}

/*
 * @brief 设置指定电机的输出值
 * @param param 电机参数
 * @param value 输出值，具体含义由控制模式决定
 * @return DEVICE_OK 表示发送成功
 *
 * 数据封装规则：
 * - 扩展帧 ID = (命令号 << 8) | 电机 ID
 * - 数据区使用 4 字节大端格式承载命令值
 */
int8_t VESC_SetOutput(VESC_Param_t *param, float value)
{
    if (param == NULL) return DEVICE_ERR_NULL;
    BSP_CAN_ExtDataFrame_t tx_frame = {0};
    uint16_t command_id;

    /* 若配置为反向，则统一对输出取反 */
    if (param->reverse) {
        value = -value;
    }

    switch (param->mode)
    {
        case DUTY_CONTROL: {
            /* 占空比控制：输入一般为 [-1.0, 1.0]，协议要求放大后发送 */
            assert_param_duty(&value);
            command_id = CAN_PACKET_SET_DUTY;
            int32_t duty_val = (int32_t)(value * 1e5f);
            VESC_PutInt32BE(tx_frame.data, duty_val);
            tx_frame.dlc = 4;
            break;
        }
        case RPM_CONTROL: {
            /* 转速控制：单位 eRPM，直接发送整数值 */
            assert_param_rpm(&value); 
            command_id = CAN_PACKET_SET_RPM;
            int32_t rpm_val = (int32_t)value;
            VESC_PutInt32BE(tx_frame.data, rpm_val);
            tx_frame.dlc = 4;
            break;
        }
        case CURRENT_CONTROL: {
            /* 电流控制：单位 A，协议中通常按 1e3 放大 */
            assert_param_current(&value); 
            command_id = CAN_PACKET_SET_CURRENT;
            int32_t cur_val = (int32_t)(value * 1e3f);
            VESC_PutInt32BE(tx_frame.data, cur_val);
            tx_frame.dlc = 4;
            break;
        }
        case POSITION_CONTROL: {
            /* 位置控制：单位 deg，协议中通常按 1e6 放大 */
            assert_param_pos(&value); 
            command_id = CAN_PACKET_SET_POS;
            int32_t pos_val = (int32_t)(value * 1e6f);
            VESC_PutInt32BE(tx_frame.data, pos_val);
            tx_frame.dlc = 4;
            break;
        }
        default:
            return DEVICE_ERR;
    }
    tx_frame.id = ((uint32_t)command_id << 8) | param->id;
    return BSP_CAN_TransmitExtDataFrame(param->can, &tx_frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}

/*
 * @brief 使电机松弛
 *
 * 本质上是向当前控制模式发送 0 输出。
 */
int8_t VESC_Relax(VESC_Param_t *param) {
    return VESC_SetOutput(param, 0.0f);
}

/*
 * @brief 手动将电机标记为离线
 * @param param 电机参数
 * @return DEVICE_OK 表示处理成功
 */
int8_t VESC_Offine(VESC_Param_t *param) {
    VESC_t *motor = VESC_GetMotor(param);
    if (motor) {
        motor->motor.header.online = false;
        return DEVICE_OK;
    }
    return DEVICE_ERR_NO_DEV;
}