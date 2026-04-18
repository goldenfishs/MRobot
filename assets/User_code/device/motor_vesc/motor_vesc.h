#pragma once

#include "motor.h"

#ifdef __cplusplus
extern "C"
{
#endif

/* Includes ----------------------------------------------------------------- */
#include "device/device.h"
#include "device/motor.h"
#include "bsp/can.h"

/* Exported constants ------------------------------------------------------- */
/* VESC 占空比控制命令上限，100 表示 100% */
#define wtrcfg_VESC_COMMAND_DUTY_MAX 100

/* VESC 电流控制命令上限，单位 A */
#define wtrcfg_VESC_COMMAND_CURRENT_MAX 10

/* VESC 位置控制命令上限，单位 deg */
#define wtrcfg_VESC_COMMAND_POS_MAX 360

/* VESC 转速控制命令上限，单位 eRPM */
#define wtrcfg_VESC_COMMAND_ERPM_MAX 35000

/* UART 超时配置，当前头文件中仅保留定义供其他模块复用 */
#define wtrcfg_VESC_UART_TIMEOUT 0xff

/* VESC 数量根据实际情况调整 */
#define VESC_MAX_MOTORS 4

/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */

/**
 * @brief VESC CAN 节点 ID 与状态帧扩展 ID 定义
 *
 * `VESC_1 ~ VESC_4` 为常用驱动器节点 ID。
 * `CAN_VESC5065_Mx_MSG1` 为对应状态回传扩展帧 ID，可用于调试或抓包分析。
 */
typedef enum {
	VESC_1 = 31,
	VESC_2 = 32,
	VESC_3 = 33,
	VESC_4 = 34,
	CAN_VESC5065_M1_MSG1 = 0x91F, /* VESC 的数据回传使用扩展 ID，[0:7] 为驱动器 ID，[8:15] 为帧类型 */
	CAN_VESC5065_M2_MSG1 = 0x920,
	CAN_VESC5065_M3_MSG1 = 0x921,
	CAN_VESC5065_M4_MSG1 = 0x922,
} VESC_ID;

/**
 * @brief VESC CAN 协议中的数据包类型
 *
 * 该枚举对应 VESC CAN 通信协议中的命令号，发送控制命令时会组合到扩展帧 ID 中。
 */
typedef enum {
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

/**
 * @brief VESC 控制模式
 *
 * 不同模式下，`VESC_SetOutput()` 的 `value` 含义不同：
 * - `DUTY_CONTROL`：占空比，范围通常为 [-1.0, 1.0]
 * - `RPM_CONTROL`：目标转速，单位 eRPM
 * - `CURRENT_CONTROL`：目标电流，单位 A
 * - `POSITION_CONTROL`：目标位置，单位 deg
 */
typedef enum {
	DUTY_CONTROL = 0x0,
	RPM_CONTROL = 0x1,
	CURRENT_CONTROL = 0x2,
	POSITION_CONTROL = 0x3
} Control_Mode;

/**
 * @brief 单个 VESC 电机的注册参数
 */
typedef struct {
	/* 挂载的 CAN 总线 */
	BSP_CAN_t can;

	/* VESC 节点 ID */
	uint16_t id;

	/* 控制模式，取值见 `Control_Mode` */
	uint16_t mode;

	/* 输出方向是否取反 */
	bool reverse;
} VESC_Param_t;

/**
 * @brief VESC 电机实例
 *
 * 包含用户配置参数和通用电机对象，反馈数据保存在 `motor.feedback` 中。
 */
typedef struct ODrive_t {
	VESC_Param_t param;
	MOTOR_t motor;
} VESC_t;

/**
 * @brief VESC CAN 管理器
 *
 * 一个 CAN 管理器对应一条 CAN 总线，用于统一管理该总线上的所有 VESC 电机实例。
 */
typedef struct {
	BSP_CAN_t can;
	VESC_t *motors[VESC_MAX_MOTORS];
	uint8_t motor_count;
} VESC_CANManager_t;

/* Exported functions prototypes -------------------------------------------- */

/**
 * @brief 注册一个 VESC 电机
 * @param param 电机参数指针
 * @return int8_t 设备状态码，成功返回 `DEVICE_OK`
 */
int8_t VESC_Register(VESC_Param_t *param);

/**
 * @brief 更新指定电机数据
 * @param param 电机参数指针
 * @return int8_t 设备状态码，成功返回 `DEVICE_OK`
 */
int8_t VESC_Update(VESC_Param_t *param);

/**
 * @brief 更新所有电机数据
 * @return int8_t 设备状态码，全部更新成功返回 `DEVICE_OK`
 */
int8_t VESC_UpdateAll(void);

/**
 * @brief 设置一个电机的输出
 * @param param 电机参数指针
 * @param value 输出值，其含义由 `param->mode` 决定
 * @return int8_t 设备状态码，发送成功返回 `DEVICE_OK`
 */
int8_t VESC_SetOutput(VESC_Param_t *param, float value);

/**
 * @brief 获取指定电机的实例指针
 * @param param 电机参数指针
 * @return VESC_t* 成功返回电机实例指针，失败返回 `NULL`
 */
VESC_t *VESC_GetMotor(VESC_Param_t *param);

/**
 * @brief 使电机松弛（设置输出为0）
 * @param param 电机参数指针
 * @return int8_t 设备状态码，成功返回 `DEVICE_OK`
 */
int8_t VESC_Relax(VESC_Param_t *param);

/**
 * @brief 使电机离线（设置在线状态为false）
 * @param param 电机参数指针
 * @return int8_t 设备状态码，成功返回 `DEVICE_OK`
 */
int8_t VESC_Offine(VESC_Param_t *param);

#ifdef __cplusplus
}
#endif