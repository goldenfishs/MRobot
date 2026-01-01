#define MOTOR_DM_FLOAT_TO_INT_SIGNED(x, x_min, x_max, bits) \
    ((int32_t)roundf(((x) / ((x_max) - (x_min))) * (1 << (bits)) + (1 << ((bits) - 1))))

#define MOTOR_DM_INT_TO_FLOAT_SIGNED(x_int, x_min, x_max, bits) \
    (((float)((int32_t)(x_int) - (1 << ((bits) - 1))) * ((x_max) - (x_min)) / (float)(1 << (bits))))
/* Includes ----------------------------------------------------------------- */
#include "device/motor_dm.h"
#include "bsp/mm.h"
#include "bsp/time.h"
#include "component/user_math.h"
#include "string.h"
#include "math.h"

/* Private constants -------------------------------------------------------- */
/* DM电机数据映射范围 */
#define DM_P_MIN   (-12.56637f)
#define DM_P_MAX   (12.56637f)
#define DM_V_MIN   (-30.0f)
#define DM_V_MAX   (30.0f)
#define DM_T_MIN   (-12.0f)
#define DM_T_MAX   (12.0f)
#define DM_KP_MIN  (0.0f)
#define DM_KP_MAX  (500.0f)
#define DM_KD_MIN  (0.0f)
#define DM_KD_MAX  (5.0f)

/* CAN ID偏移量 */
#define DM_CAN_ID_OFFSET_POS_VEL  0x100
#define DM_CAN_ID_OFFSET_VEL      0x200

/* Private macro ------------------------------------------------------------ */
#define FLOAT_TO_UINT(x, x_min, x_max, bits) \
    (uint32_t)((x - x_min) * ((1 << bits) - 1) / (x_max - x_min))

#define UINT_TO_FLOAT(x_int, x_min, x_max, bits) \
    ((float)(x_int) * (x_max - x_min) / ((1 << bits) - 1) + x_min)


/* Private variables -------------------------------------------------------- */
static MOTOR_DM_CANManager_t *can_managers[BSP_CAN_NUM] = {NULL};

static int float_to_uint(float x_float, float x_min, float x_max, int bits)
{
	/* Converts a float to an unsigned int, given range and number of bits */
	float span = x_max - x_min;
	float offset = x_min;
	return (int) ((x_float-offset)*((float)((1<<bits)-1))/span);
}

static float uint_to_float(int x_int, float x_min, float x_max, int bits)
{
	/* converts unsigned int to float, given range and number of bits */
	float span = x_max - x_min;
	float offset = x_min;
	return ((float)x_int)*span/((float)((1<<bits)-1)) + offset;
}
/* Private function prototypes ---------------------------------------------- */
static int8_t MOTOR_DM_ParseFeedbackFrame(MOTOR_DM_t *motor, const uint8_t *data);
static int8_t MOTOR_DM_SendMITCmd(MOTOR_DM_t *motor, MOTOR_MIT_Output_t *output);
static int8_t MOTOR_DM_SendPosVelCmd(MOTOR_DM_t *motor, float pos, float vel);
static int8_t MOTOR_DM_SendVelCmd(MOTOR_DM_t *motor, float vel);
static MOTOR_DM_CANManager_t* MOTOR_DM_GetCANManager(BSP_CAN_t can);

/* Private functions -------------------------------------------------------- */

/**
 * @brief 解析DM电机反馈帧
 * @param motor 电机实例
 * @param data CAN数据
 * @return 解析结果
 */
static int8_t MOTOR_DM_ParseFeedbackFrame(MOTOR_DM_t *motor, const uint8_t *data) {
    if (motor == NULL || data == NULL) {
        return DEVICE_ERR_NULL;
    }
    uint16_t p_int=(data[1]<<8)|data[2];
    motor->motor.feedback.rotor_abs_angle = uint_to_float(p_int, DM_P_MIN, DM_P_MAX, 16); // (-12.5,12.5)
    uint16_t v_int=(data[3]<<4)|(data[4]>>4);
    motor->motor.feedback.rotor_speed = uint_to_float(v_int, DM_V_MIN, DM_V_MAX, 12); // (-30.0,30.0)
    uint16_t t_int=((data[4]&0xF)<<8)|data[5];
    motor->motor.feedback.torque_current = uint_to_float(t_int, DM_T_MIN, DM_T_MAX, 12);  // (-12.0,12.0)
    motor->motor.feedback.temp = (float)(data[6]);

    while (motor->motor.feedback.rotor_abs_angle < 0) {
        motor->motor.feedback.rotor_abs_angle += M_2PI;
    }
    while (motor->motor.feedback.rotor_abs_angle >= M_2PI) {
        motor->motor.feedback.rotor_abs_angle -= M_2PI;
    }

    if (motor->param.reverse) {
        motor->motor.feedback.rotor_abs_angle = M_2PI - motor->motor.feedback.rotor_abs_angle;
        motor->motor.feedback.rotor_speed = -motor->motor.feedback.rotor_speed;
        motor->motor.feedback.torque_current = -motor->motor.feedback.torque_current;
    }
    return DEVICE_OK;
}

/**
 * @brief 发送MIT模式控制命令
 * @param motor 电机实例
 * @param output MIT控制参数
 * @return 发送结果
 */
static int8_t MOTOR_DM_SendMITCmd(MOTOR_DM_t *motor, MOTOR_MIT_Output_t *output) {
    if (motor == NULL || output == NULL) {
        return DEVICE_ERR_NULL;
    }
    
	uint8_t data[8];
	uint16_t pos_tmp,vel_tmp,kp_tmp,kd_tmp,tor_tmp;
	uint16_t id = motor->param.can_id;

	pos_tmp = float_to_uint(output->angle, DM_P_MIN , DM_P_MAX, 16);
	vel_tmp = float_to_uint(output->velocity, DM_V_MIN , DM_V_MAX, 12);
	kp_tmp  = float_to_uint(output->kp,   DM_KP_MIN, DM_KP_MAX, 12);
	kd_tmp  = float_to_uint(output->kd,   DM_KD_MIN, DM_KD_MAX, 12);
	tor_tmp = float_to_uint(output->torque, DM_T_MIN , DM_T_MAX, 12);

    /* 打包数据 */
	data[0] = (pos_tmp >> 8);
	data[1] = pos_tmp;
	data[2] = (vel_tmp >> 4);
	data[3] = ((vel_tmp&0xF)<<4)|(kp_tmp>>8);
	data[4] = kp_tmp;
	data[5] = (kd_tmp >> 4);
	data[6] = ((kd_tmp&0xF)<<4)|(tor_tmp>>8);
	data[7] = tor_tmp;
    
    /* 发送CAN消息 */
    BSP_CAN_StdDataFrame_t frame;
    frame.id = motor->param.can_id;
    frame.dlc = 8;
    memcpy(frame.data, data, 8);
    

    return BSP_CAN_TransmitStdDataFrame(motor->param.can, &frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}

/**
 * @brief 发送位置速度模式控制命令
 * @param motor 电机实例
 * @param pos 目标位置
 * @param vel 目标速度
 * @return 发送结果
 */
static int8_t MOTOR_DM_SendPosVelCmd(MOTOR_DM_t *motor, float pos, float vel) {
    if (motor == NULL) {
        return DEVICE_ERR_NULL;
    }
    
    uint8_t data[8] = {0};

    
    /* 直接发送浮点数数据 */
    memcpy(&data[0], &pos, 4);  // 位置，低位在前
    memcpy(&data[4], &vel, 4);  // 速度，低位在前
    
    /* 发送CAN消息，ID为原ID+0x100 */
    uint32_t can_id = DM_CAN_ID_OFFSET_POS_VEL + motor->param.can_id;
    BSP_CAN_StdDataFrame_t frame;
    frame.id = can_id;
    frame.dlc = 8;
    memcpy(frame.data, data, 8);
    
    return BSP_CAN_TransmitStdDataFrame(motor->param.can, &frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}

/**
 * @brief 发送速度模式控制命令
 * @param motor 电机实例
 * @param vel 目标速度
 * @return 发送结果
 */
static int8_t MOTOR_DM_SendVelCmd(MOTOR_DM_t *motor, float vel) {
    if (motor == NULL) {
        return DEVICE_ERR_NULL;
    }
    
    uint8_t data[4] = {0};
    
    /* 直接发送浮点数数据 */
    memcpy(&data[0], &vel, 4);  // 速度，低位在前
    
    /* 发送CAN消息，ID为原ID+0x200 */
    uint32_t can_id = DM_CAN_ID_OFFSET_VEL + motor->param.can_id;
    BSP_CAN_StdDataFrame_t frame;
    frame.id = can_id;
    frame.dlc = 4;
    memcpy(frame.data, data, 4);
    
    return BSP_CAN_TransmitStdDataFrame(motor->param.can, &frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}

/**
 * @brief 获取指定CAN总线的管理器
 * @param can CAN总线
 * @return CAN管理器指针
 */
static MOTOR_DM_CANManager_t* MOTOR_DM_GetCANManager(BSP_CAN_t can) {
    if (can >= BSP_CAN_NUM) {
        return NULL;
    }
    
    return can_managers[can];
}

/**
 * @brief 创建CAN管理器
 * @param can CAN总线
 * @return 创建结果
 */
static int8_t MOTOR_DM_CreateCANManager(BSP_CAN_t can) {
    if (can >= BSP_CAN_NUM) return DEVICE_ERR;
    if (can_managers[can] != NULL) return DEVICE_OK;
    
    can_managers[can] = (MOTOR_DM_CANManager_t*)BSP_Malloc(sizeof(MOTOR_DM_CANManager_t));
    if (can_managers[can] == NULL) return DEVICE_ERR;
    
    memset(can_managers[can], 0, sizeof(MOTOR_DM_CANManager_t));
    can_managers[can]->can = can;
    return DEVICE_OK;
}

/* Exported functions ------------------------------------------------------- */

/**
 * @brief 注册一个DM电机
 * @param param 电机参数
 * @return 注册结果
 */
int8_t MOTOR_DM_Register(MOTOR_DM_Param_t *param) {
    if (param == NULL) {
        return DEVICE_ERR_NULL;
    }
    
    /* 创建CAN管理器 */
    if (MOTOR_DM_CreateCANManager(param->can) != DEVICE_OK) {
        return DEVICE_ERR;
    }
    
    /* 获取CAN管理器 */
    MOTOR_DM_CANManager_t *manager = MOTOR_DM_GetCANManager(param->can);
    if (manager == NULL) {
        return DEVICE_ERR;
    }
    
    /* 检查是否已注册 */
    for (int i = 0; i < manager->motor_count; i++) {
        if (manager->motors[i] && manager->motors[i]->param.master_id == param->master_id) {
            return DEVICE_ERR_INITED;
        }
    }
    
    /* 检查是否已达到最大数量 */
    if (manager->motor_count >= MOTOR_DM_MAX_MOTORS) {
        return DEVICE_ERR;
    }
    
    /* 分配内存 */
    MOTOR_DM_t *motor = (MOTOR_DM_t *)BSP_Malloc(sizeof(MOTOR_DM_t));
    if (motor == NULL) {
        return DEVICE_ERR;
    }
    
    /* 初始化电机 */
    memset(motor, 0, sizeof(MOTOR_DM_t));
    memcpy(&motor->param, param, sizeof(MOTOR_DM_Param_t));
    motor->motor.header.online = false;
    motor->motor.reverse = param->reverse;
    
    /* 注册CAN接收ID - DM电机使用Master ID接收反馈 */
    uint16_t feedback_id = param->master_id;
    if (BSP_CAN_RegisterId(param->can, feedback_id, 3) != BSP_OK) {
        BSP_Free(motor);
        return DEVICE_ERR;
    }
    
    /* 添加到管理器 */
    manager->motors[manager->motor_count] = motor;
    manager->motor_count++;
    
    return DEVICE_OK;
}

/**
 * @brief 更新指定电机数据
 * @param param 电机参数
 * @return 更新结果
 */
int8_t MOTOR_DM_Update(MOTOR_DM_Param_t *param) {
    if (param == NULL) {
        return DEVICE_ERR_NULL;
    }
    
    MOTOR_DM_CANManager_t *manager = MOTOR_DM_GetCANManager(param->can);
    if (manager == NULL) {
        return DEVICE_ERR_NO_DEV;
    }
    
    /* 查找电机 */
    MOTOR_DM_t *motor = NULL;
    for (int i = 0; i < manager->motor_count; i++) {
        if (manager->motors[i] && manager->motors[i]->param.master_id == param->master_id) {
            motor = manager->motors[i];
            break;
        }
    }
    
    if (motor == NULL) {
        return DEVICE_ERR_NO_DEV;
    }
    
    /* 主动接收CAN消息 */
    uint16_t feedback_id = param->master_id;
    BSP_CAN_Message_t rx_msg;
    if (BSP_CAN_GetMessage(param->can, feedback_id, &rx_msg, BSP_CAN_TIMEOUT_IMMEDIATE) != BSP_OK) {
        uint64_t now_time = BSP_TIME_Get();
        if (now_time - motor->motor.header.last_online_time > 100000) {  // 100ms超时，单位微秒
            motor->motor.header.online = false;
        }
        return DEVICE_ERR;
    }
    
    motor->motor.header.online = true;
    motor->motor.header.last_online_time = BSP_TIME_Get();
    MOTOR_DM_ParseFeedbackFrame(motor, rx_msg.data);
    
    return DEVICE_OK;
}

/**
 * @brief 更新所有电机数据
 * @return 更新结果
 */
int8_t MOTOR_DM_UpdateAll(void) {
    int8_t ret = DEVICE_OK;
    for (int can = 0; can < BSP_CAN_NUM; can++) {
        MOTOR_DM_CANManager_t *manager = MOTOR_DM_GetCANManager((BSP_CAN_t)can);
        if (manager == NULL) continue;
        
        for (int i = 0; i < manager->motor_count; i++) {
            MOTOR_DM_t *motor = manager->motors[i];
            if (motor != NULL) {
                if (MOTOR_DM_Update(&motor->param) != DEVICE_OK) {
                    ret = DEVICE_ERR;
                }
            }
        }
    }
    return ret;
}

/**
 * @brief MIT模式控制
 * @param param 电机参数
 * @param output MIT控制参数
 * @return 控制结果
 */
int8_t MOTOR_DM_MITCtrl(MOTOR_DM_Param_t *param, MOTOR_MIT_Output_t *output) {
    if (param == NULL || output == NULL) {
        return DEVICE_ERR_NULL;
    }
    
    MOTOR_DM_t *motor = MOTOR_DM_GetMotor(param);
    if (motor == NULL) {
        return DEVICE_ERR_NO_DEV;
    }
    
    return MOTOR_DM_SendMITCmd(motor, output);
}

/**
 * @brief 位置速度模式控制
 * @param param 电机参数
 * @param target_pos 目标位置
 * @param target_vel 目标速度
 * @return 控制结果
 */
int8_t MOTOR_DM_PosVelCtrl(MOTOR_DM_Param_t *param, float target_pos, float target_vel) {
    if (param == NULL) {
        return DEVICE_ERR_NULL;
    }
    
    MOTOR_DM_t *motor = MOTOR_DM_GetMotor(param);
    if (motor == NULL) {
        return DEVICE_ERR_NO_DEV;
    }
    
    return MOTOR_DM_SendPosVelCmd(motor, target_pos, target_vel);
}

/**
 * @brief 速度模式控制
 * @param param 电机参数
 * @param target_vel 目标速度
 * @return 控制结果
 */
int8_t MOTOR_DM_VelCtrl(MOTOR_DM_Param_t *param, float target_vel) {
    if (param == NULL) {
        return DEVICE_ERR_NULL;
    }
    
    MOTOR_DM_t *motor = MOTOR_DM_GetMotor(param);
    if (motor == NULL) {
        return DEVICE_ERR_NO_DEV;
    }
    
    return MOTOR_DM_SendVelCmd(motor, target_vel);
}

/**
 * @brief 获取指定电机的实例指针
 * @param param 电机参数
 * @return 电机实例指针
 */
MOTOR_DM_t* MOTOR_DM_GetMotor(MOTOR_DM_Param_t *param) {
    if (param == NULL) {
        return NULL;
    }
    
    MOTOR_DM_CANManager_t *manager = MOTOR_DM_GetCANManager(param->can);
    if (manager == NULL) {
        return NULL;
    }
    
    /* 查找对应的电机 */
    for (int i = 0; i < manager->motor_count; i++) {
        MOTOR_DM_t *motor = manager->motors[i];
        if (motor && motor->param.can == param->can && 
            motor->param.master_id == param->master_id) {
            return motor;
        }
    }
    
    return NULL;
}


int8_t MOTOR_DM_Enable(MOTOR_DM_Param_t *param){
    if (param == NULL) {
        return DEVICE_ERR_NULL;
    }
    
    MOTOR_DM_t *motor = MOTOR_DM_GetMotor(param);
    if (motor == NULL) {
        return DEVICE_ERR_NO_DEV;
    }

    BSP_CAN_StdDataFrame_t frame;
    frame.id = motor->param.can_id;
    frame.dlc = 8;
    frame.data[0] = 0XFF;
    frame.data[1] = 0xFF;
    frame.data[2] = 0xFF;
    frame.data[3] = 0xFF;
    frame.data[4] = 0xFF;
    frame.data[5] = 0xFF;
    frame.data[6] = 0xFF;
    frame.data[7] = 0xFC;

    return BSP_CAN_TransmitStdDataFrame(motor->param.can, &frame) == BSP_OK ? DEVICE_OK : DEVICE_ERR;
}

/**
 * @brief 使电机松弛（设置输出为0）
 * @param param 电机参数
 * @return 操作结果
 */
int8_t MOTOR_DM_Relax(MOTOR_DM_Param_t *param) {
    if (param == NULL) {
        return DEVICE_ERR_NULL;
    }
    
    MOTOR_MIT_Output_t output = {0};
    return MOTOR_DM_MITCtrl(param, &output);
}

/**
 * @brief 使电机离线（设置在线状态为false）
 * @param param 电机参数
 * @return 操作结果
 */
int8_t MOTOR_DM_Offine(MOTOR_DM_Param_t *param) {
    if (param == NULL) {
        return DEVICE_ERR_NULL;
    }
    
    MOTOR_DM_t *motor = MOTOR_DM_GetMotor(param);
    if (motor == NULL) {
        return DEVICE_ERR_NO_DEV;
    }
    
    motor->motor.header.online = false;
    return DEVICE_OK;
}
