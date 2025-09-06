#pragma once

#ifdef __cplusplus
extern "C"
{
#endif

/* Includes ----------------------------------------------------------------- */
#include "device/device.h"
#include "device/motor.h"
#include "bsp/can.h"

/* Private define ----------------------------------------------------------- */
#define wtrcfg_VESC_COMMAND_DUTY_MAX 100
#define wtrcfg_VESC_COMMAND_CURRENT_MAX 10
#define wtrcfg_VESC_COMMAND_POS_MAX 360
#define wtrcfg_VESC_COMMAND_ERPM_MAX 35000
#define wtrcfg_VESC_UART_TIMEOUT 0xff

// VESC数量根据实际情况调整
#define VESC_MAX_MOTORS 4

/* Exported constants ------------------------------------------------------- */

/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */

typedef enum
{
	VESC_1 = 1,
	VESC_2 = 2,
	VESC_3 = 3,
	VESC_4 = 4,
	CAN_VESC5065_M1_MSG1 = 0x901, // vesc的数据回传使用了扩展id，[0:7]为驱动器id，[8:15]为帧类型
	CAN_VESC5065_M2_MSG1 = 0x902,
	CAN_VESC5065_M3_MSG1 = 0x903,
	CAN_VESC5065_M4_MSG1 = 0x904, 
}VESC_ID;

typedef enum
{
	CAN_PACKET_SET_DUTY = 0,
	CAN_PACKET_SET_CURRENT = 1,
	CAN_PACKET_SET_CURRENT_BRAKE = 2,
	CAN_PACKET_SET_RPM = 3,
	CAN_PACKET_SET_POS = 4,
	CAN_PACKET_FILL_RX_BUFFER = 5,
	CAN_PACKET_FILL_RX_BUFFER_LONG = 6,
	CAN_PACKET_PROCESS_RX_BUFFER = 7,
	CAN_PACKET_PROCESS_SHORT_BUFFER = 8,
	CAN_PACKET_STATUS = 9,
	CAN_PACKET_SET_CURRENT_REL = 10,
	CAN_PACKET_SET_CURRENT_BRAKE_REL = 11,
	CAN_PACKET_SET_CURRENT_HANDBRAKE = 12,
	CAN_PACKET_SET_CURRENT_HANDBRAKE_REL = 13
} CAN_PACKET_ID;

// Control Modes
typedef enum
{
	DUTY_CONTROL = 0x0,
	RPM_CONTROL = 0x1,
	CURRENT_CONTROL = 0x2,
	POSITION_CONTROL = 0x3
} Control_Mode;

/*每个电机需要的参数*/
typedef struct
{
	BSP_CAN_t can;
	uint16_t id;
	uint16_t mode;
	bool reverse;
} VESC_Param_t;

/*电机实例*/
typedef struct ODrive_t
{
	VESC_Param_t param;
	MOTOR_t motor;
} VESC_t;

/*CAN管理器，管理一个CAN总线上所有的电机*/
typedef struct
{
	BSP_CAN_t can;
	VESC_t *motors[VESC_MAX_MOTORS];
	uint8_t motor_count;
} VESC_CANManager_t;

/* Exported functions prototypes -------------------------------------------- */

/**
 * @brief 注册一个vesc电机
 * @param param 电机参数
 * @return
 */
int8_t VESC_Register(VESC_Param_t *param);

/**
 * @brief 更新指定电机数据
 * @param param 电机参数
 * @return
 */
int8_t VESC_Update(VESC_Param_t *param);

/**
 * @brief 更新所有电机数据
 * @return
 */
int8_t VESC_UpdateAll(void);

/**
 * @brief 设置一个电机的输出
 * @param param 电机参数
 * @param value 输出值
 * @return
 */

int8_t VESC_SetOutput(VESC_Param_t *param, float value);

/**
 * @brief 获取指定电机的实例指针
 * @param param 电机参数
 * @return
 */

VESC_t* VESC_GetMotor(VESC_Param_t *param);

/**
 * @brief 使电机松弛（设置输出为0）
 * @param param
 * @return
 */
int8_t VESC_Relax(VESC_Param_t *param);
/**
 * @brief 使电机离线（设置在线状态为false）
 * @param param
 * @return
 */
int8_t VESC_Offine(VESC_Param_t *param);


#ifdef __cplusplus
}
#endif