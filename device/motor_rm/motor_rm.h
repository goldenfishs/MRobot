#pragma once

#include "motor.h"
#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include "device/device.h"
#include "device/motor.h"
#include "bsp/can.h"

/* Exported constants ------------------------------------------------------- */
#define MOTOR_RM_MAX_MOTORS 11

/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */
typedef enum {
    MOTOR_M2006,
    MOTOR_M3508,
    MOTOR_GM6020,
} MOTOR_RM_Module_t;

typedef enum {
    MOTOR_RM_C610_ERROR_NONE = 0,
    MOTOR_RM_C610_ERROR_SUPPLY_OVERVOLTAGE = 2,
    MOTOR_RM_C610_ERROR_PHASE_LOSS = 3,
    MOTOR_RM_C610_ERROR_SENSOR_LOST = 4,
    MOTOR_RM_C610_ERROR_STALL = 6,
    MOTOR_RM_C610_ERROR_CALIBRATION_FAILED = 7,
} MOTOR_RM_C610_ErrorCode_t;

/*一个can最多控制11个电机*/
typedef union {
  int16_t output[MOTOR_RM_MAX_MOTORS];
  struct {
    int16_t m3508_m2006_id201;
    int16_t m3508_m2006_id202;
    int16_t m3508_m2006_id203;
    int16_t m3508_m2006_id204;
    int16_t m3508_m2006_gm6020_id205;
    int16_t m3508_m2006_gm6020_id206;
    int16_t m3508_m2006_gm6020_id207;
    int16_t m3508_m2006_gm6020_id208;
    int16_t gm6020_id209;
    int16_t gm6020_id20A;
    int16_t gm6020_id20B;
  } named;
} MOTOR_RM_MsgOutput_t;

/*每个电机需要的参数*/
typedef struct {
    BSP_CAN_t can;
    uint16_t id;
    MOTOR_RM_Module_t module;
    bool reverse;
    bool gear;
} MOTOR_RM_Param_t;

typedef MOTOR_Feedback_t MOTOR_RM_Feedback_t;

/* MOTOR_CPP_ADAPTER_DATA: raw protocol feedback alias used by C++ RM wrapper. */
typedef MOTOR_RawFeedback_t MOTOR_RM_RawFeedback_t;

typedef struct {
    MOTOR_RM_Param_t param;
    MOTOR_RM_Feedback_t feedback;
    MOTOR_t motor;
    // 多圈相关变量，仅gear模式下有效
    uint16_t last_raw_angle;
    bool angle_inited;
    int32_t gearbox_round_count;
    int32_t gearbox_total_raw_count;
    float gearbox_total_angle;
    uint32_t angle_lost_count;
    uint32_t last_feedback_time;
} MOTOR_RM_t;

/*CAN管理器，管理一个CAN总线上所有的电机*/
typedef struct {
    BSP_CAN_t can;
    MOTOR_RM_MsgOutput_t output_msg;
    /* 缓存后统一发送：记录哪些 RM 控制帧组已写入缓存。 */
    uint8_t pending_tx_groups;
    MOTOR_RM_t *motors[MOTOR_RM_MAX_MOTORS];
    uint8_t motor_count;
  /* C++ motor 适配层：由 C++ 对象持有生命周期的外部实例。 */
    /* MOTOR_CPP_ADAPTER_STATE_BEGIN: external instances owned by C++ wrappers. */
    MOTOR_RM_t *external_motors[MOTOR_RM_MAX_MOTORS];
    uint8_t external_motor_count;
    /* MOTOR_CPP_ADAPTER_STATE_END */
} MOTOR_RM_CANManager_t;

/* MOTOR_CPP_ADAPTER_DEBUG_BEGIN: transmit snapshots consumed by C++ tests/tools. */
typedef struct {
    uint8_t valid;
    BSP_CAN_t can;
    uint16_t source_motor_id;
    uint16_t tx_frame_id;
    int8_t logical_index;
    int16_t requested_current;
    int16_t grouped_output[MOTOR_RM_MAX_MOTORS];
    uint8_t tx_data[8];
    uint8_t pending_tx_groups;
    uint32_t flush_count;
} MOTOR_RM_TxDebug_t;

  typedef struct {
    uint8_t valid;
    BSP_CAN_t can;
    uint16_t tx_frame_id;
    int8_t logical_index;
    int16_t output_value;
    uint8_t tx_data[8];
  } MOTOR_RM_SlotTxDebug_t;

  extern MOTOR_RM_SlotTxDebug_t g_motor_rm_slot_tx_debug[MOTOR_RM_MAX_MOTORS];
/* MOTOR_CPP_ADAPTER_DEBUG_END */

/* Exported functions prototypes -------------------------------------------- */

/* -------------------------------------------------------------------------- */
/* 原生 C 驱动接口：注册、反馈更新、兼容输出、直接组帧发送与状态控制。 */
/* -------------------------------------------------------------------------- */

/**
 * @brief 注册一个RM电机
 * @param param 电机参数
 * @return 
 */
int8_t MOTOR_RM_Register(MOTOR_RM_Param_t *param);

/**
 * @brief 更新指定电机数据
 * @param param 电机参数
 * @return 
 */
int8_t MOTOR_RM_Update(MOTOR_RM_Param_t *param);

/**
 * @brief 设置一个电机的归一化输出（底层兼容接口）
 * @param param 电机参数
 * @param value 输出值，范围[-1.0, 1.0]
 * @note 该接口只写入 CAN 管理器的输出缓存；随后调用 MOTOR_RM_Ctrl()
 *       或 MOTOR_RM_FlushGroup()/MOTOR_RM_FlushCAN() 发送对应控制帧组。
 * @return 
 */
int8_t MOTOR_RM_SetOutput(MOTOR_RM_Param_t *param, float value);

/**
 * @brief 发送控制命令到电机，注意一个CAN可以控制多个电机，所以只需要发送一次即可
 * @param param 电机参数
 * @note 兼容旧代码的立即发送接口。多个 RM 电机同周期控制时，推荐先调用
 *       MOTOR_RM_SetOutput()/MOTOR_RM_SetTorqueCurrent() 写完同组缓存，再调用
 *       MOTOR_RM_FlushGroup()/MOTOR_RM_FlushCAN() 统一发送。
 * @return 
 */
int8_t MOTOR_RM_Ctrl(MOTOR_RM_Param_t *param);

/**
 * @brief 按 C 驱动缓存发送方式，发送指定电机所属 RM 控制帧组的缓存命令。
 * @param param 电机参数，用于定位 CAN 与控制帧组
 * @return 设备状态码
 */
int8_t MOTOR_RM_FlushGroup(MOTOR_RM_Param_t *param);

/**
 * @brief 按 C 驱动缓存发送方式，发送指定 CAN 上所有待发送的 RM 控制帧组。
 * @param can CAN 总线
 * @return 设备状态码
 */
int8_t MOTOR_RM_FlushCAN(BSP_CAN_t can);

/**
 * @brief 按 C 驱动缓存发送方式，发送所有 CAN 上所有待发送的 RM 控制帧组。
 * @return 设备状态码
 */
int8_t MOTOR_RM_FlushAll(void);

/**
 * @brief 获取指定电机的实例指针
 * @param param 电机参数
 * @return 
 */
MOTOR_RM_t* MOTOR_RM_GetMotor(MOTOR_RM_Param_t *param);

/**
 * @brief 使电机松弛（设置输出为0）
 * @param param 
 * @return 
 */
int8_t MOTOR_RM_Relax(MOTOR_RM_Param_t *param);

/**
 * @brief 使电机离线（设置在线状态为false）
 * @param param 
 * @return 
 */
int8_t MOTOR_RM_Offine(MOTOR_RM_Param_t *param);

/**
 * @brief 
 * @param  
 * @return 
 */
int8_t MOTOR_RM_UpdateAll(void);

/* -------------------------------------------------------------------------- */
/* C++ motor 适配接口：protocol/motor_t 使用的外部实例、物理量命令、Flush 与调试。 */
/* -------------------------------------------------------------------------- */

/**
 * @brief 将外部分配的 RM 电机实例附着到底层驱动
 * @param param 电机参数
 * @param external_motor 外部实例存储，生命周期需覆盖整个使用期
 * @return 设备状态码
 * @note C++ motor 框架专用；外部实例由 C++ 对象持有，不由 C 驱动分配/释放。
 */
/* MOTOR_CPP_ADAPTER_API_BEGIN: used by User/device/motor/protocol/rm_protocol.cpp. */
int8_t MOTOR_RM_AttachExternal(MOTOR_RM_Param_t *param, MOTOR_RM_t *external_motor);

/**
 * @brief 设置一个电机的转子侧电流命令（C++ 力矩控制主入口）
 * @param param 电机参数
 * @param current_a 转子侧目标电流，单位 A
 * @note C++ RM 驱动会先将目标输出轴力矩按转矩常数、减速比、外部传动比
 *       换算为转子侧电流（A），本接口再统一完成 A -> RM raw 指令值 的换算。
 * @return
 */
int8_t MOTOR_RM_SetTorqueCurrent(MOTOR_RM_Param_t *param, float current_a);

const MOTOR_RM_RawFeedback_t* MOTOR_RM_GetRawFeedback(MOTOR_RM_Param_t *param);

const MOTOR_RM_TxDebug_t* MOTOR_RM_GetTxDebug(void);

const MOTOR_RM_SlotTxDebug_t* MOTOR_RM_GetSlotTxDebug(uint8_t logical_index);
/* MOTOR_CPP_ADAPTER_API_END */

#ifdef __cplusplus
}
#endif
