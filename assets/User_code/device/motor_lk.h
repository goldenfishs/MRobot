#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include "device/device.h"
#include "device/motor.h"
#include "bsp/can.h"

/* Exported constants ------------------------------------------------------- */
#define MOTOR_LK_MAX_MOTORS 32

/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */
typedef enum {
    MOTOR_MF9025,
    MOTOR_MF9035,
} MOTOR_LK_Module_t;


/*每个电机需要的参数*/
typedef struct {
    BSP_CAN_t can;
    uint16_t id;
    MOTOR_LK_Module_t module;
    bool reverse;
} MOTOR_LK_Param_t;

/*电机实例*/
typedef struct{
    MOTOR_LK_Param_t param;
    MOTOR_t motor;
} MOTOR_LK_t;

/*CAN管理器，管理一个CAN总线上所有的电机*/
typedef struct {
    BSP_CAN_t can;
    MOTOR_LK_t *motors[MOTOR_LK_MAX_MOTORS];
    uint8_t motor_count;
} MOTOR_LK_CANManager_t;

/* Exported functions prototypes -------------------------------------------- */

/**
 * @brief 注册一个LK电机
 * @param param 电机参数
 * @return 
 */
int8_t MOTOR_LK_Register(MOTOR_LK_Param_t *param);

/**
 * @brief 更新指定电机数据
 * @param param 电机参数
 * @return 
 */
int8_t MOTOR_LK_Update(MOTOR_LK_Param_t *param);

/**
 * @brief 设置一个电机的输出
 * @param param 电机参数
 * @param value 输出值，范围[-1.0, 1.0]
 * @return 
 */
int8_t MOTOR_LK_SetOutput(MOTOR_LK_Param_t *param, float value);

/**
 * @brief 发送控制命令到电机，注意一个CAN可以控制多个电机，所以只需要发送一次即可
 * @param param 电机参数
 * @return 
 */
int8_t MOTOR_LK_Ctrl(MOTOR_LK_Param_t *param);

/**
 * @brief 发送电机开启命令
 * @param param 电机参数
 * @return 
 */
int8_t MOTOR_LK_MotorOn(MOTOR_LK_Param_t *param);

/**
 * @brief 发送电机关闭命令
 * @param param 电机参数
 * @return 
 */
int8_t MOTOR_LK_MotorOff(MOTOR_LK_Param_t *param);

/**
 * @brief 获取指定电机的实例指针
 * @param param 电机参数
 * @return 
 */
MOTOR_LK_t* MOTOR_LK_GetMotor(MOTOR_LK_Param_t *param);

/**
 * @brief 使电机松弛（设置输出为0）
 * @param param 
 * @return 
 */
int8_t MOTOR_LK_Relax(MOTOR_LK_Param_t *param);

/**
 * @brief 使电机离线（设置在线状态为false）
 * @param param 
 * @return 
 */
int8_t MOTOR_LK_Offine(MOTOR_LK_Param_t *param);

/**
 * @brief 
 * @param  
 * @return 
 */
int8_t MOTOR_LK_UpdateAll(void);

#ifdef __cplusplus
}
#endif