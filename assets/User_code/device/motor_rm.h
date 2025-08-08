#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include "device/device.h"
#include "device/motor.h"
#include "bsp/can.h"

/* Exported constants ------------------------------------------------------- */
#define MOTOR_RM_MAX_MOTORS 11 /* 最大电机数量 */

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
/*注册电机时候每个电机需要的参数*/
typedef struct {
    BSP_CAN_t can;
    uint16_t id;  // 实际CAN ID，如0x201, 0x205等
    MOTOR_RM_Module_t module;
    bool reverse;
} MOTOR_RM_Param_t;

typedef struct MOTOR_RM_t {
    MOTOR_RM_Param_t param;
    MOTOR_t motor;
} MOTOR_RM_t;

typedef struct {
    BSP_CAN_t can;
    MOTOR_RM_MsgOutput_t output_msg;
    MOTOR_RM_t *motors[MOTOR_RM_MAX_MOTORS];  // 最多15个电机
    uint8_t motor_count;
} MOTOR_RM_CANManager_t;




/* Exported functions prototypes -------------------------------------------- */
/**
 * @brief 注册一个RM电机
 * @param param 电机参数
 * @return 0 成功，其他值失败
 */
int8_t MOTOR_RM_Register(MOTOR_RM_Param_t *param);

/**
 * @brief 更新单个电机数据
 * @param can CAN通道
 * @param id 电机实际CAN ID
 * @return 0 成功，其他值失败
 */
int8_t MOTOR_RM_Update(BSP_CAN_t can, uint16_t id);

/**
 * @brief 更新所有注册了的电机数据
 * @return 0 成功，其他值失败
 */
int8_t MOTOR_RM_UpdateAll(void);

/**
 * @brief 设置电机输出值
 * @param can CAN通道
 * @param id 电机实际CAN ID
 * @param value 输出值（归一化，-1.0到1.0）
 * @return 0 成功，其他值失败
 */
int8_t MOTOR_RM_SetOutput(BSP_CAN_t can, uint16_t id, float value);

/**
 * @brief 发送电机控制命令
 * @param can CAN通道
 * @param ctrl_id 控制帧ID（0x200, 0x1ff, 0x2ff）
 * @return 0 成功，其他值失败
 */
int8_t MOTOR_RM_Ctrl(BSP_CAN_t can, uint16_t ctrl_id);

/**
 * @brief 获取电机实例
 * @param can CAN通道
 * @param id 电机实际CAN ID
 * @return 电机实例指针，失败返回NULL
 */
MOTOR_RM_t* MOTOR_RM_GetMotor(BSP_CAN_t can, uint16_t id);

/**
 * @brief 使电机松弛（设置输出为0）
 * @param can CAN通道
 * @param id 电机实际CAN ID
 * @return 0 成功，其他值失败
 */
int8_t MOTOR_RM_Relax(BSP_CAN_t can, uint16_t id);

/**
 * @brief 使电机离线（输出为0并标记为不在线）
 * @param can CAN通道
 * @param id 电机实际CAN ID
 * @return 0 成功，其他值失败
 */
int8_t MOTOR_RM_Offine(BSP_CAN_t can, uint16_t id);

#ifdef __cplusplus
}
#endif