#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include "device/device.h"
#include "device/motor.h"
#include "bsp/can.h"

/* Exported constants ------------------------------------------------------- */
#define MOTOR_DM_MAX_MOTORS 32

/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */
typedef enum {
    MOTOR_DM_J10010,
    MOTOR_DM_J10010L,
    MOTOR_DM_J10422P,
    MOTOR_DM_J3507,
    MOTOR_DM_J4310,
    MOTOR_DM_J4310P,
    MOTOR_DM_J4340,
    MOTOR_DM_J4340P,
    MOTOR_DM_J6006,
    MOTOR_DM_J6248P,
    MOTOR_DM_J8006,
    MOTOR_DM_J8009,
    MOTOR_DM_J8009P,
    MOTOR_DM_H3510,
} MOTOR_DM_Module_t;

typedef enum {
    MOTOR_DM_STATUS_DISABLED = 0x0,
    MOTOR_DM_STATUS_ENABLED = 0x1,
    MOTOR_DM_STATUS_OVERVOLTAGE = 0x8,
    MOTOR_DM_STATUS_UNDERVOLTAGE = 0x9,
    MOTOR_DM_STATUS_OVERCURRENT = 0xA,
    MOTOR_DM_STATUS_MOS_OVERTEMP = 0xB,
    MOTOR_DM_STATUS_COIL_OVERTEMP = 0xC,
    MOTOR_DM_STATUS_COMM_LOST = 0xD,
    MOTOR_DM_STATUS_OVERLOAD = 0xE,
    MOTOR_DM_STATUS_UNKNOWN = 0xFF,
} MOTOR_DM_Status_t;

/*每个电机需要的参数*/
typedef struct {
    BSP_CAN_t can;
    uint16_t master_id;    /* 反馈ID，用于接收电机反馈 */
    uint16_t can_id;       /* 主站ID，用于发送控制命令 */
    MOTOR_DM_Module_t module;
    bool reverse;
} MOTOR_DM_Param_t;

/*电机实例*/
typedef struct{
    MOTOR_DM_Param_t param;
    MOTOR_t motor;
    /* MOTOR_CPP_ADAPTER_STATE_BEGIN: protocol status consumed by dm_protocol.cpp. */
    uint8_t feedback_id;
    MOTOR_DM_Status_t status;
    uint8_t status_raw;
    uint8_t mos_temp;
    uint8_t rotor_temp;
    /* MOTOR_CPP_ADAPTER_STATE_END */
} MOTOR_DM_t;

/* MOTOR_CPP_ADAPTER_DATA: raw protocol feedback alias used by C++ DM wrapper. */
typedef MOTOR_RawFeedback_t MOTOR_DM_RawFeedback_t;

/*CAN管理器，管理一个CAN总线上所有的电机*/
typedef struct {
    BSP_CAN_t can;
    MOTOR_DM_t *motors[MOTOR_DM_MAX_MOTORS];
    uint8_t motor_count;
    /* C++ motor 适配层：由 C++ 对象持有生命周期的外部实例。 */
    /* MOTOR_CPP_ADAPTER_STATE_BEGIN: external instances owned by C++ wrappers. */
    MOTOR_DM_t *external_motors[MOTOR_DM_MAX_MOTORS];
    uint8_t external_motor_count;
    /* MOTOR_CPP_ADAPTER_STATE_END */
} MOTOR_DM_CANManager_t;

/* Exported functions prototypes -------------------------------------------- */

/* -------------------------------------------------------------------------- */
/* 原生 C 驱动接口：注册、反馈更新、协议控制帧与状态控制。 */
/* -------------------------------------------------------------------------- */

/**
 * @brief 注册一个LK电机
 * @param param 电机参数
 * @return 
 */
int8_t MOTOR_DM_Register(MOTOR_DM_Param_t *param);

/**
 * @brief 更新指定电机数据
 * @param param 电机参数
 * @return 
 */
int8_t MOTOR_DM_Update(MOTOR_DM_Param_t *param);

/**
 * @brief 更新所有电机数据
 * @return 
 */
int8_t MOTOR_DM_UpdateAll(void);

int8_t MOTOR_DM_MITCtrl(MOTOR_DM_Param_t *param, MOTOR_MIT_Output_t *output);

int8_t MOTOR_DM_PosVelCtrl(MOTOR_DM_Param_t *param, float target_pos, float target_vel);

int8_t MOTOR_DM_VelCtrl(MOTOR_DM_Param_t *param, float target_vel);

int8_t MOTOR_DM_HybridCtrl(MOTOR_DM_Param_t *param, MOTOR_Hybrid_Output_t *output);

/**
 * @brief 获取指定电机的实例指针
 * @param param 电机参数
 * @return 
 */
MOTOR_DM_t* MOTOR_DM_GetMotor(MOTOR_DM_Param_t *param);

int8_t MOTOR_DM_Enable(MOTOR_DM_Param_t *param);

int8_t MOTOR_DM_Disable(MOTOR_DM_Param_t *param);

/**
 * @brief 使电机松弛（设置输出为0）
 * @param param 
 * @return 
 */
int8_t MOTOR_DM_Relax(MOTOR_DM_Param_t *param);

/**
 * @brief 使电机离线（设置在线状态为false）
 * @param param 
 * @return 
 */
int8_t MOTOR_DM_Offine(MOTOR_DM_Param_t *param);

/**
 * @brief 重新设置角度零点（将当前位置设为电机零位）
 * @param param 电机参数指针
 * @return DEVICE_OK 成功，DEVICE_ERR 失败
 */
int8_t MOTOR_DM_SetZero(MOTOR_DM_Param_t *param);

/**
 * @brief 清除电机错误状态 (DM-H3510)
 * @param param 电机参数指针
 * @return DEVICE_OK 成功，DEVICE_ERR 失败
 */
int8_t MOTOR_DM_ClearFault(MOTOR_DM_Param_t *param);

/* -------------------------------------------------------------------------- */
/* C++ motor 适配接口：protocol/motor_t 使用的外部实例与原始反馈读取。 */
/* -------------------------------------------------------------------------- */

/**
 * @brief 将外部分配的 DM 电机实例附着到底层驱动
 * @param param 电机参数
 * @param external_motor 外部实例存储，生命周期需覆盖整个使用期
 * @return 设备状态码
 * @note C++ motor 框架专用；外部实例由 C++ 对象持有，不由 C 驱动分配/释放。
 */
/* MOTOR_CPP_ADAPTER_API_BEGIN: used by User/device/motor/protocol/dm_protocol.cpp. */
int8_t MOTOR_DM_AttachExternal(MOTOR_DM_Param_t *param, MOTOR_DM_t *external_motor);

const MOTOR_DM_RawFeedback_t* MOTOR_DM_GetRawFeedback(MOTOR_DM_Param_t *param);
/* MOTOR_CPP_ADAPTER_API_END */



#ifdef __cplusplus
}
#endif
