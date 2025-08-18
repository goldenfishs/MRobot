/*
    DM_IMU数据获取
*/

/* Includes ----------------------------------------------------------------- */
#include "dm_imu.h"

#include "bsp/can.h"
#include "bsp/time.h"
#include <string.h>

/* Private define ----------------------------------------------------------- */
#define DM_IMU_OFFLINE_TIMEOUT      1000    // 设备离线判定时间1000ms

#define ACCEL_CAN_MAX (58.8f)
#define ACCEL_CAN_MIN	(-58.8f)
#define GYRO_CAN_MAX	(34.88f)
#define GYRO_CAN_MIN	(-34.88f)
#define PITCH_CAN_MAX	(90.0f)
#define PITCH_CAN_MIN	(-90.0f)
#define ROLL_CAN_MAX	(180.0f)
#define ROLL_CAN_MIN	(-180.0f)
#define YAW_CAN_MAX		(180.0f)
#define YAW_CAN_MIN 	(-180.0f)
#define TEMP_MIN			(0.0f)
#define TEMP_MAX			(60.0f)
#define Quaternion_MIN	(-1.0f)
#define Quaternion_MAX	(1.0f)


/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */
/* Private function --------------------------------------------------------- */

static uint8_t count = 0; // 计数器，用于判断设备是否离线
/**
 * @brief: 无符号整数转换为浮点数函数
 */
static float uint_to_float(int x_int, float x_min, float x_max, int bits)
{
    float span = x_max - x_min;
    float offset = x_min;
    return ((float)x_int)*span/((float)((1<<bits)-1)) + offset;
}

/**
 * @brief 解析加速度计数据
 */
static int8_t DM_IMU_ParseAccelData(DM_IMU_t *imu, uint8_t *data, uint8_t len) {
    if (imu == NULL || data == NULL || len < 8) {
        return DEVICE_ERR;
    }
    int8_t temp = data[1];
    uint16_t acc_x_raw = (data[3] << 8) | data[2];
    uint16_t acc_y_raw = (data[5] << 8) | data[4];
    uint16_t acc_z_raw = (data[7] << 8) | data[6];
    imu->data.temp = (float)temp;
    imu->data.accl.x = uint_to_float(acc_x_raw, ACCEL_CAN_MIN, ACCEL_CAN_MAX, 16);
    imu->data.accl.y = uint_to_float(acc_y_raw, ACCEL_CAN_MIN, ACCEL_CAN_MAX, 16);
    imu->data.accl.z = uint_to_float(acc_z_raw, ACCEL_CAN_MIN, ACCEL_CAN_MAX, 16);
    return DEVICE_OK;
}
/**
 * @brief 解析陀螺仪数据
 */
static int8_t DM_IMU_ParseGyroData(DM_IMU_t *imu, uint8_t *data, uint8_t len) {
    if (imu == NULL || data == NULL || len < 8) {
        return DEVICE_ERR;
    }
    uint16_t gyro_x_raw = (data[3] << 8) | data[2];
    uint16_t gyro_y_raw = (data[5] << 8) | data[4];
    uint16_t gyro_z_raw = (data[7] << 8) | data[6];
    imu->data.gyro.x = uint_to_float(gyro_x_raw, GYRO_CAN_MIN, GYRO_CAN_MAX, 16);
    imu->data.gyro.y = uint_to_float(gyro_y_raw, GYRO_CAN_MIN, GYRO_CAN_MAX, 16);
    imu->data.gyro.z = uint_to_float(gyro_z_raw, GYRO_CAN_MIN, GYRO_CAN_MAX, 16);
    return DEVICE_OK;
}
/**
 * @brief 解析欧拉角数据
 */
static int8_t DM_IMU_ParseEulerData(DM_IMU_t *imu, uint8_t *data, uint8_t len) {
    if (imu == NULL || data == NULL || len < 8) {
        return DEVICE_ERR;
    }
    uint16_t pit_raw = (data[3] << 8) | data[2];
    uint16_t yaw_raw = (data[5] << 8) | data[4];
    uint16_t rol_raw = (data[7] << 8) | data[6];
    imu->data.euler.pit = uint_to_float(pit_raw, PITCH_CAN_MIN, PITCH_CAN_MAX, 16);
    imu->data.euler.yaw = uint_to_float(yaw_raw, YAW_CAN_MIN, YAW_CAN_MAX, 16);
    imu->data.euler.rol = uint_to_float(rol_raw, ROLL_CAN_MIN, ROLL_CAN_MAX, 16);
    return DEVICE_OK;
}


/**
 * @brief 解析四元数数据
 */
static int8_t DM_IMU_ParseQuaternionData(DM_IMU_t *imu, uint8_t *data, uint8_t len) {
    if (imu == NULL || data == NULL || len < 8) {
        return DEVICE_ERR;
    }
    int w = (data[1] << 6) | ((data[2] & 0xF8) >> 2);
    int x = ((data[2] & 0x03) << 12) | (data[3] << 4) | ((data[4] & 0xF0) >> 4);
    int y = ((data[4] & 0x0F) << 10) | (data[5] << 2) | ((data[6] & 0xC0) >> 6);
    int z = ((data[6] & 0x3F) << 8) | data[7];
    imu->data.quat.q0 = uint_to_float(w, Quaternion_MIN, Quaternion_MAX, 14);
    imu->data.quat.q1 = uint_to_float(x, Quaternion_MIN, Quaternion_MAX, 14);
    imu->data.quat.q2 = uint_to_float(y, Quaternion_MIN, Quaternion_MAX, 14);
    imu->data.quat.q3 = uint_to_float(z, Quaternion_MIN, Quaternion_MAX, 14);
    return DEVICE_OK;
}


/* Exported functions ------------------------------------------------------- */

/**
 * @brief 初始化DM IMU设备
 */
int8_t DM_IMU_Init(DM_IMU_t *imu, BSP_CAN_t can) {
    if (imu == NULL) {
        return DEVICE_ERR_NULL;
    }
    
    // 初始化设备头部
    imu->header.online = false;
    imu->header.last_online_time = 0;
    imu->can = can;
    
    // 清零数据
    memset(&imu->data, 0, sizeof(DM_IMU_Data_t));
    
    // 注册CAN接收队列，用于接收回复报文
    int8_t result = BSP_CAN_RegisterId(imu->can, DM_IMU_MST_ID, 10);
    if (result != BSP_OK) {
        return DEVICE_ERR;
    }

    return DEVICE_OK;
}

/**
 * @brief 请求IMU数据
 */
int8_t DM_IMU_Request(DM_IMU_t *imu, DM_IMU_RID_t rid) {
    if (imu == NULL) {
        return DEVICE_ERR_NULL;
    }
    
    // 构造发送数据：id_L, id_H(DM_IMU_ID), RID, 0xcc
    uint8_t tx_data[4] = {
        DM_IMU_ID & 0xFF,        // id_L
        (DM_IMU_ID >> 8) & 0xFF, // id_H
        (uint8_t)rid,            // RID
        0xCC                     // 固定值
    };
    
    // 发送标准数据帧
    BSP_CAN_StdDataFrame_t frame = {
        .id = DM_IMU_CAN_ID,
        .dlc = 4,
    };
    memcpy(frame.data, tx_data, 4);
    
    int8_t result = BSP_CAN_TransmitStdDataFrame(imu->can, &frame);
    return (result == BSP_OK) ? DEVICE_OK : DEVICE_ERR;
}

/**
 * @brief 更新IMU数据（从CAN中获取所有数据并解析）
 */
int8_t DM_IMU_Update(DM_IMU_t *imu) {
    if (imu == NULL) {
        return DEVICE_ERR_NULL;
    }
    
    BSP_CAN_Message_t msg;
    int8_t result;
    bool data_received = false;
    
    // 持续接收所有可用消息
    while ((result = BSP_CAN_GetMessage(imu->can, DM_IMU_MST_ID, &msg, BSP_CAN_TIMEOUT_IMMEDIATE)) == BSP_OK) {
        // 验证回复数据格式（至少检查数据长度）
        if (msg.dlc < 3) {
            continue; // 跳过无效消息
        }
        
        // 根据数据位的第0位确定反馈报文类型
        uint8_t rid = msg.data[0] & 0x0F; // 取第0位的低4位作为RID
        
        // 根据RID类型解析数据
        int8_t parse_result = DEVICE_ERR;
        switch (rid) {
            case 0x01: // RID_ACCL
                parse_result = DM_IMU_ParseAccelData(imu, msg.data, msg.dlc);
                break;
            case 0x02: // RID_GYRO
                parse_result = DM_IMU_ParseGyroData(imu, msg.data, msg.dlc);
                break;
            case 0x03: // RID_EULER
                parse_result = DM_IMU_ParseEulerData(imu, msg.data, msg.dlc);
                break;
            case 0x04: // RID_QUATERNION
                parse_result = DM_IMU_ParseQuaternionData(imu, msg.data, msg.dlc);
                break;
            default:
                continue; // 跳过未知类型的消息
        }
        
        // 如果解析成功，标记为收到数据
        if (parse_result == DEVICE_OK) {
            data_received = true;
        }
    }
    
    // 如果收到任何有效数据，更新设备状态
    if (data_received) {
        imu->header.online = true;
        imu->header.last_online_time = BSP_TIME_Get_ms();
        return DEVICE_OK;
    }
    
    return DEVICE_ERR;
}

/** 
 * @brief 自动更新IMU所有数据（包括加速度计、陀螺仪、欧拉角和四元数,最高1khz）
 */ 
int8_t DM_IMU_AutoUpdateAll(DM_IMU_t *imu){
    if (imu == NULL) {
        return DEVICE_ERR_NULL;
    }
    switch (count) {
        case 0:
            DM_IMU_Request(imu, RID_ACCL);
            break;
        case 1:
            DM_IMU_Request(imu, RID_GYRO);
            break;
        case 2:
            DM_IMU_Request(imu, RID_EULER);
            break;
        case 3:
            DM_IMU_Request(imu, RID_QUATERNION);
            DM_IMU_Update(imu); // 更新所有数据
            break;
    }
    count++;
    if (count >= 4) {
        count = 0; // 重置计数器
    }
    return DEVICE_OK;
}

/**
 * @brief 检查设备是否在线
 */
bool DM_IMU_IsOnline(DM_IMU_t *imu) {
    if (imu == NULL) {
        return false;
    }
    
    uint32_t current_time = BSP_TIME_Get_ms();
    return imu->header.online && 
           (current_time - imu->header.last_online_time < DM_IMU_OFFLINE_TIMEOUT);
}
