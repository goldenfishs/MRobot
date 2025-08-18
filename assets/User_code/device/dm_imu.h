#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include "device/device.h"
#include "component/ahrs.h"
#include "bsp/can.h"
/* Exported constants ------------------------------------------------------- */

#define DM_IMU_CAN_ID 0x6FF
#define DM_IMU_ID 0x42
#define DM_IMU_MST_ID 0x43

/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */
typedef enum {
  RID_ACCL = 0x01, // 加速度计
  RID_GYRO = 0x02, // 陀螺仪
  RID_EULER = 0x03, // 欧拉角
  RID_QUATERNION = 0x04, // 四元数
} DM_IMU_RID_t;

typedef struct {
  AHRS_Accl_t accl; // 加速度计
  AHRS_Gyro_t gyro; // 陀螺仪
  AHRS_Eulr_t euler; // 欧拉角
  AHRS_Quaternion_t quat; // 四元数
  float temp; // 温度
} DM_IMU_Data_t;

typedef struct {
  DEVICE_Header_t header;
  BSP_CAN_t can;
  DM_IMU_Data_t data; // IMU数据
} DM_IMU_t;

/* Exported functions prototypes -------------------------------------------- */

/**
 * @brief 初始化DM IMU设备
 * @param imu DM IMU设备结构体指针
 * @return DEVICE_OK 成功，其他值失败
 */
int8_t DM_IMU_Init(DM_IMU_t *imu, BSP_CAN_t can);

/**
 * @brief 请求IMU数据
 * @param imu DM IMU设备结构体指针
 * @param rid 请求的数据类型
 * @return DEVICE_OK 成功，其他值失败
 */
int8_t DM_IMU_Request(DM_IMU_t *imu, DM_IMU_RID_t rid);


/**
 * @brief 更新IMU数据（从CAN中获取所有数据并解析）
 * @param imu DM IMU设备结构体指针
 * @return DEVICE_OK 成功，其他值失败
 */
int8_t DM_IMU_Update(DM_IMU_t *imu);

/**
 * @brief 自动更新IMU所有数据（包括加速度计、陀螺仪、欧拉角和四元数,最高1khz，运行4次才有完整数据）
 * @param imu DM IMU设备结构体指针
 * @return DEVICE_OK 成功，其他值失败
 */
int8_t DM_IMU_AutoUpdateAll(DM_IMU_t *imu);

/**
 * @brief 检查设备是否在线
 * @param imu DM IMU设备结构体指针
 * @return true 在线，false 离线
 */
bool DM_IMU_IsOnline(DM_IMU_t *imu);


#ifdef __cplusplus
}
#endif
