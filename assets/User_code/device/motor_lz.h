#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include "device/device.h"
#include "device/motor.h"
#include "bsp/can.h"

/* Exported constants ------------------------------------------------------- */
#define MOTOR_LZ_MAX_MOTORS 32

/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */
typedef enum {
    MOTOR_LZ_RSO0,
    MOTOR_LZ_RSO1,
    MOTOR_LZ_RSO2,
    MOTOR_LZ_RSO3,
    MOTOR_LZ_RSO4,
    MOTOR_LZ_RSO5,
    MOTOR_LZ_RSO6,
} MOTOR_LZ_Module_t;

/* 灵足电机控制模式 */
typedef enum {
    MOTOR_LZ_MODE_MOTION = 0x1,     /* 运控模式 */
    MOTOR_LZ_MODE_CURRENT = 0x2,    /* 电流模式 */
    MOTOR_LZ_MODE_VELOCITY = 0x3,   /* 速度模式 */
    MOTOR_LZ_MODE_POSITION = 0x4,   /* 位置模式 */
} MOTOR_LZ_ControlMode_t;

/* 灵足电机通信类型 */
typedef enum {
    MOTOR_LZ_CMD_MOTION = 0x1,      /* 运控模式控制 */
    MOTOR_LZ_CMD_FEEDBACK = 0x2,    /* 电机反馈数据 */
    MOTOR_LZ_CMD_ENABLE = 0x3,      /* 电机使能运行 */
    MOTOR_LZ_CMD_DISABLE = 0x4,     /* 电机停止运行 */
    MOTOR_LZ_CMD_SET_ZERO = 0x6,    /* 设置电机机械零位 */
} MOTOR_LZ_CmdType_t;

/* 灵足电机运行状态 */
typedef enum {
    MOTOR_LZ_STATE_RESET = 0,       /* Reset模式[复位] */
    MOTOR_LZ_STATE_CALI = 1,        /* Cali模式[标定] */
    MOTOR_LZ_STATE_MOTOR = 2,       /* Motor模式[运行] */
} MOTOR_LZ_State_t;

/* 灵足电机故障信息 */
typedef struct {
    bool uncalibrated;      /* bit21: 未标定 */
    bool stall_overload;    /* bit20: 堵转过载故障 */
    bool encoder_fault;     /* bit19: 磁编码故障 */
    bool over_temp;         /* bit18: 过温 */
    bool driver_fault;      /* bit17: 驱动故障 */
    bool under_voltage;     /* bit16: 欠压故障 */
} MOTOR_LZ_Fault_t;

/* 灵足电机运控参数 */
typedef struct {
    float target_angle;     /* 目标角度 (-12.57f~12.57f rad) */
    float target_velocity;  /* 目标角速度 (-20~20 rad/s) */
    float kp;               /* 位置增益 (0.0~5000.0) */
    float kd;               /* 微分增益 (0.0~100.0) */
    float torque;           /* 力矩 (-60~60 Nm) */
} MOTOR_LZ_MotionParam_t;

/*每个电机需要的参数*/
typedef struct {
    BSP_CAN_t can;              /* CAN总线 */
    uint8_t motor_id;           /* 电机CAN ID */
    uint8_t host_id;            /* 主机CAN ID */
    MOTOR_LZ_Module_t module;   /* 电机型号 */
    bool reverse;               /* 是否反向 */
    MOTOR_LZ_ControlMode_t mode; /* 控制模式 */
} MOTOR_LZ_Param_t;

/*电机反馈信息扩展*/
typedef struct {
    float current_angle;        /* 当前角度 (-12.57f~12.57f rad) */
    float current_velocity;     /* 当前角速度 (-20~20 rad/s) */
    float current_torque;       /* 当前力矩 (-60~60 Nm) */
    float temperature;          /* 当前温度 (摄氏度) */
    MOTOR_LZ_State_t state;     /* 运行状态 */
    MOTOR_LZ_Fault_t fault;     /* 故障信息 */
    uint8_t motor_can_id;       /* 当前电机CAN ID */
} MOTOR_LZ_Feedback_t;

/*电机实例*/
typedef struct {
    MOTOR_LZ_Param_t param;
    MOTOR_t motor;
    MOTOR_LZ_Feedback_t lz_feedback;    /* 灵足电机特有反馈信息 */
    MOTOR_LZ_MotionParam_t motion_param; /* 运控模式参数 */
} MOTOR_LZ_t;

/*CAN管理器，管理一个CAN总线上所有的电机*/
typedef struct {
    BSP_CAN_t can;
    MOTOR_LZ_t *motors[MOTOR_LZ_MAX_MOTORS];
    uint8_t motor_count;
} MOTOR_LZ_CANManager_t;

/* Exported functions prototypes -------------------------------------------- */

/**
 * @brief 初始化灵足电机驱动系统
 * @return 设备状态码
 */
int8_t MOTOR_LZ_Init(void);

/**
 * @brief 反初始化灵足电机驱动系统
 * @return 设备状态码
 */
int8_t MOTOR_LZ_DeInit(void);

/**
 * @brief 注册一个灵足电机
 * @param param 电机参数
 * @return 设备状态码
 */
int8_t MOTOR_LZ_Register(MOTOR_LZ_Param_t *param);

/**
 * @brief 更新指定电机数据
 * @param param 电机参数
 * @return 设备状态码
 */
int8_t MOTOR_LZ_Update(MOTOR_LZ_Param_t *param);

/**
 * @brief 更新所有电机数据
 * @return 设备状态码
 */
int8_t MOTOR_LZ_UpdateAll(void);

/**
 * @brief 运控模式控制电机
 * @param param 电机参数
 * @param motion_param 运控参数
 * @return 设备状态码
 */
int8_t MOTOR_LZ_MotionControl(MOTOR_LZ_Param_t *param, MOTOR_LZ_MotionParam_t *motion_param);

/**
 * @brief 电流(力矩)模式控制电机
 * @param param 电机参数
 * @param torque 目标力矩 (-60~60 Nm)
 * @return 设备状态码
 */
int8_t MOTOR_LZ_TorqueControl(MOTOR_LZ_Param_t *param, float torque);

/**
 * @brief 位置模式控制电机
 * @param param 电机参数
 * @param target_angle 目标角度 (-12.57~12.57 rad)
 * @param max_velocity 最大速度 (0~20 rad/s)
 * @return 设备状态码
 */
int8_t MOTOR_LZ_PositionControl(MOTOR_LZ_Param_t *param, float target_angle, float max_velocity);

/**
 * @brief 速度模式控制电机
 * @param param 电机参数
 * @param target_velocity 目标速度 (-20~20 rad/s)
 * @return 设备状态码
 */
int8_t MOTOR_LZ_VelocityControl(MOTOR_LZ_Param_t *param, float target_velocity);

/**
 * @brief 电机使能运行
 * @param param 电机参数
 * @return 设备状态码
 */
int8_t MOTOR_LZ_Enable(MOTOR_LZ_Param_t *param);

/**
 * @brief 电机停止运行
 * @param param 电机参数
 * @param clear_fault 是否清除故障
 * @return 设备状态码
 */
int8_t MOTOR_LZ_Disable(MOTOR_LZ_Param_t *param, bool clear_fault);

/**
 * @brief 设置电机机械零位
 * @param param 电机参数
 * @return 设备状态码
 */
int8_t MOTOR_LZ_SetZero(MOTOR_LZ_Param_t *param);

/**
 * @brief 获取指定电机的实例指针
 * @param param 电机参数
 * @return 电机实例指针，失败返回NULL
 */
MOTOR_LZ_t* MOTOR_LZ_GetMotor(MOTOR_LZ_Param_t *param);

/**
 * @brief 使电机松弛（发送停止命令）
 * @param param 电机参数
 * @return 设备状态码
 */
int8_t MOTOR_LZ_Relax(MOTOR_LZ_Param_t *param);

/**
 * @brief 使电机离线（设置在线状态为false）
 * @param param 电机参数
 * @return 设备状态码
 */
int8_t MOTOR_LZ_Offline(MOTOR_LZ_Param_t *param);

/**
 * @brief 获取指定电机的反馈信息
 * @param param 电机参数
 * @return 电机反馈信息指针，失败返回NULL
 */
MOTOR_LZ_Feedback_t* MOTOR_LZ_GetFeedback(MOTOR_LZ_Param_t *param);

#ifdef __cplusplus
}
#endif