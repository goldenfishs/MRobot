#pragma once

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
} MOTOR_RM_Param_t;

/*电机实例*/
typedef struct MOTOR_RM_t {
    MOTOR_RM_Param_t param;
    MOTOR_t motor;
} MOTOR_RM_t;

/*CAN管理器，管理一个CAN总线上所有的电机*/
typedef struct {
    BSP_CAN_t can;
    MOTOR_RM_MsgOutput_t output_msg;
    MOTOR_RM_t *motors[MOTOR_RM_MAX_MOTORS];
    uint8_t motor_count;
} MOTOR_RM_CANManager_t;

/* Exported functions prototypes -------------------------------------------- */

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
 * @brief 设置一个电机的输出
 * @param param 电机参数
 * @param value 输出值，范围[-1.0, 1.0]
 * @return 
 */
int8_t MOTOR_RM_SetOutput(MOTOR_RM_Param_t *param, float value);

/**
 * @brief 发送控制命令到电机，注意一个CAN可以控制多个电机，所以只需要发送一次即可
 * @param param 电机参数
 * @return 
 */
int8_t MOTOR_RM_Ctrl(MOTOR_RM_Param_t *param);

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

#ifdef __cplusplus
}
#endif