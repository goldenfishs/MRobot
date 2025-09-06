#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include "device/device.h"
#include "device/motor.h"
#include "bsp/can.h"

/* Private define ----------------------------------------------------------- */

//ODrive型号根据实际情况调整
#define ODRIVE_MAX_MOTORS 2

//COMMAND ID
#define ODRIVE_HEARTBEAT_MESSAGE		0x001 // ODrive心跳消息
#define SET_AXIS_NODE_ID				0x006 // 设置电机节点ID
#define GET_ENCODER_ESTIMATES			0x008 // 获取编码器估计值
#define GET_ENCODER_COUNT				0x00A // 获取编码器计数
#define SET_AXIS_REQUESTED_STATE 		0x007 // 设置电机请求状态
#define ENCODER_ESTIMATES				0x009 // 编码器估计值
#define GET_ENCODER_COUNT				0x00A // 获取编码器计数
#define SET_CONTROLLER_MODES			0x00B // 设置控制器模式
#define SET_INPUT_POS					0x00C // 设置输入位置
#define SET_INPUT_VEL					0x00D // 设置输入速度
#define SET_INPUT_TORQUE				0x00E // 设置输入转矩
#define SET_LIMITS						0x00F // 设置限制
#define GET_IQ							0x014 // 获取电流
#define REBOOT_ODRIVE					0x016 // 重启ODrive
#define GET_BUS_VOLTAGE_CURRENT			0x017 // 获取总线电压和电流
#define CLEAR_ERRORS					0x018 // 清除错误
#define SET_POSITION_GAIN				0x01A // 设置位置增益
#define SET_VEL_GAINS					0x01B // 设置速度增益
#define SET_TRAJ_ACCEL_LIMITS      0x012 // 设置轨迹加速度限制
/* Exported constants ------------------------------------------------------- */


/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */

//Axis States
typedef enum {
    UNDEFINED = 0x0,
    IDLE = 0x1,
    STARTUP_SEQUENCE = 0x2,
    FULL_CALIBRATION_SEQUENCE = 0x3,
    MOTOR_CALIBRATION = 0x4,
    ENCODER_INDEX_SEARCH = 0x6,
    ENCODER_OFFSET_CALIBRATION = 0x7,
    CLOSED_LOOP_CONTROL = 0x8,
    LOCKIN_SPIN = 0x9,
    ENCODER_DIR_FIND = 0xA,
    HOMING = 0xB,
    ENCODER_HALL_POLARITY_CALIBRATION = 0xC,
    ENCODER_HALL_PHASE_CALIBRATION = 0xD
} Axis_State;

//Control Modes
typedef enum{
	VOLTAGE_CONTROL = 0x0,
	TORQUE_CONTROL = 0x1,
	VELOCITY_CONTROL = 0x2,
	POSITION_CONTROL = 0x3
} Control_Mode;


/*每个电机需要的参数*/
typedef struct {
    BSP_CAN_t can;
    uint16_t id;
    uint16_t mode;
    bool reverse;
} ODrive_Param_t;

/*电机实例*/
typedef struct ODrive_t {
    ODrive_Param_t param;
    MOTOR_t motor;
} ODrive_t;

/*CAN管理器，管理一个CAN总线上所有的电机*/
typedef struct {
    BSP_CAN_t can;
    ODrive_t *motors[ODRIVE_MAX_MOTORS];
    uint8_t motor_count;
} ODrive_CANManager_t;

/* Exported functions prototypes -------------------------------------------- */

/**
 * @brief 注册一个odrive电机
 * @param param 电机参数
 * @return 
 */
int8_t ODrive_Register(ODrive_Param_t *param);

/**
 * @brief 更新指定电机数据
 * @param param 电机参数
 * @return 
 */

int8_t ODrive_Update(ODrive_Param_t *param);

/** * @brief 更新所有ODrive电机状态
 * @return 
 */
int8_t ODrive_UpdateAll(void);

/**
 * @brief 设置一个电机的输出
 * @param param 电机参数
 * @param value 输出值
 * @return 
 */
int8_t ODrive_SetOutput(ODrive_Param_t *param, float value);

/** * @brief 设置电机加速度和减速度限制
 * @param param 电机参数
 * @param accel 加速度  
 * @param decel 减速度
 * @return 
 */
int8_t ODrive_SetAccel(ODrive_Param_t *param, float accel, float decel);

/**
 * @brief 获取指定电机的实例指针
 * @param param 电机参数
 * @return 
 */
ODrive_t* ODrive_GetMotor(ODrive_Param_t *param);

/** * @brief 获取指定电机的编码器估计值
 * @param param 电机参数
 * @return 
 */
int8_t ODrive_RequestEncoderEstimates(ODrive_Param_t *param); 


/** * @brief 设置轴请求状态（一般用来重启 ODrive 的某个轴）
 * @param param 电机参数
 * @return 
 */
int8_t ODrive_SetAxisRequestedState(ODrive_Param_t *param, Axis_State state);

/** * @brief 清除错误
 * @param param 电机参数
 * @return 
 */
int8_t ODrive_ClearErrors(ODrive_Param_t *param); 

/**  * @brief 重启 ODrive
 * @param param 电机参数
 * @return 
 */
int8_t ODrive_Reboot(ODrive_Param_t *param);

#ifdef __cplusplus
}
#endif