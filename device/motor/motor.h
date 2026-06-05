#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include "device/device.h"

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

/* USER DEFINE BEGIN */

/* USER DEFINE END */

/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */
/* MOTOR_CPP_ADAPTER_* marks C ABI/data kept for wrappers under User/device/motor/. */
typedef struct {
    float rotor_abs_angle; /* 兼容旧接口：单圈角度，范围 [0, 2pi) */
    float rotor_single_angle; /* 单圈角度，范围 [0, 2pi) */
    float rotor_total_angle; /* 连续多圈角度 */
    float rotor_speed; /* 实际转子转速 */
    float torque_current; /* 转矩电流 */
    float temp; /* 温度 */
    bool angle_valid; /* 连续角度是否可信 */
    uint32_t angle_lost_count; /* 疑似跨零/反馈丢失计数 */
    uint32_t last_update_time; /* 最近反馈更新时间，单位由底层驱动决定 */
} MOTOR_Feedback_t;

/* MOTOR_CPP_ADAPTER_DATA_BEGIN
 * Raw protocol feedback cache for the C++ motor protocol layer.
 * Native C modules should prefer MOTOR_Feedback_t unless they need raw frames.
 */
typedef struct {
    uint16_t raw_angle;      /* 原始编码器角度 */
    int16_t raw_speed;       /* 原始转速反馈 */
    int16_t raw_current;     /* 原始电流反馈 */
    uint8_t raw_temp;        /* 原始温度反馈 */
    uint8_t raw_error_code;  /* Raw protocol error code, 0 means no error. */
} MOTOR_RawFeedback_t;
/* MOTOR_CPP_ADAPTER_DATA_END */

/**
 * @brief mit电机输出参数结构体
 */
typedef struct {
    float torque;      /* 目标力矩 */
    float velocity;    /* 目标速度 */
    float angle;       /* 目标位置 */
    float kp;         /* 位置环增益 */
    float kd;         /* 速度环增益 */
} MOTOR_MIT_Output_t;

typedef struct {
    float warning_c;
    float limit_c;
    bool auto_relax_on_limit;
} MOTOR_TemperatureProtectionConfig_t;

extern const MOTOR_TemperatureProtectionConfig_t kMotorDefaultTemperatureProtection;

/**
 * @brief 力位混控模式参数结构体 (DM-H3510)
 */
typedef struct {
    float target_angle;     /* 目标角度 (rad) */
    float max_velocity;     /* 限速值 (rad/s) */
    float current_limit;    /* 电流限定标幺值 (0-1.0) */
} MOTOR_Hybrid_Output_t;

/**
 * @brief 转矩电流控制模式参数结构体
 */
typedef struct {
    float current;    /* 目标电流 */
} MOTOR_Current_Output_t;

typedef struct {
    DEVICE_Header_t header;
    bool reverse; /* 是否反装 true表示反装 */
    /* MOTOR_CPP_ADAPTER_DATA: cached raw frame decoded by vendor drivers. */
    MOTOR_RawFeedback_t raw_feedback;
    MOTOR_Feedback_t feedback;
} MOTOR_t;

/* USER STRUCT BEGIN */

/* USER STRUCT END */

/* Exported functions prototypes -------------------------------------------- */
float MOTOR_GetRotorAbsAngle(const MOTOR_t *motor);
float MOTOR_GetRotorSingleAngle(const MOTOR_t *motor);
float MOTOR_GetRotorTotalAngle(const MOTOR_t *motor);
bool MOTOR_IsAngleValid(const MOTOR_t *motor);
uint32_t MOTOR_GetAngleLostCount(const MOTOR_t *motor);
float MOTOR_GetRotorSpeed(const MOTOR_t *motor);
float MOTOR_GetTorqueCurrent(const MOTOR_t *motor);
float MOTOR_GetTemp(const MOTOR_t *motor);
/* MOTOR_CPP_ADAPTER_API: exposes raw protocol feedback to C++ wrappers. */
const MOTOR_RawFeedback_t* MOTOR_GetRawFeedback(const MOTOR_t *motor);
MOTOR_TemperatureProtectionConfig_t MOTOR_NormalizeTemperatureProtection(
    MOTOR_TemperatureProtectionConfig_t config);

/* USER FUNCTION BEGIN */

/* USER FUNCTION END */

#ifdef __cplusplus
}
#endif
