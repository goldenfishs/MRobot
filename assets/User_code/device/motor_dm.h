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
    MOTOR_DM_J4310,
} MOTOR_DM_Module_t;

/*每个电机需要的参数*/
typedef struct {
    BSP_CAN_t can;
    uint16_t master_id;    /* 主站ID，用于发送控制命令 */
    uint16_t can_id;       /* 反馈ID，用于接收电机反馈 */
    MOTOR_DM_Module_t module;
    bool reverse;
} MOTOR_DM_Param_t;

/*电机实例*/
typedef struct{
    MOTOR_DM_Param_t param;
    MOTOR_t motor;
} MOTOR_DM_t;

/*CAN管理器，管理一个CAN总线上所有的电机*/
typedef struct {
    BSP_CAN_t can;
    MOTOR_DM_t *motors[MOTOR_DM_MAX_MOTORS];
    uint8_t motor_count;
} MOTOR_DM_CANManager_t;

/* Exported functions prototypes -------------------------------------------- */

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

/**
 * @brief 获取指定电机的实例指针
 * @param param 电机参数
 * @return 
 */
MOTOR_DM_t* MOTOR_DM_GetMotor(MOTOR_DM_Param_t *param);

int8_t MOTOR_DM_Enable(MOTOR_DM_Param_t *param);

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



#ifdef __cplusplus
}
#endif