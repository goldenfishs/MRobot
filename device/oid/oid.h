#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include "device/device.h"
#include "bsp/can.h"
#include "component/user_math.h"

/* Exported constants ------------------------------------------------------- */
#define OID_MAX_NUM 32
#define OID_RESOLUTION 1024 //编码器分辨率
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */

/**
 * @brief 编码器工作模式枚举
 */
typedef enum {
    OID_MODE_QUERY          = 0x00,  // 查询模式
    OID_MODE_AUTO_SPEED     = 0x02,  // 自动返回编码器角速度值
    OID_MODE_AUTO_POSITION  = 0xAA   // 自动返回编码器值
} OID_Mode_t;

/**
 * @brief 编码器方向枚举
 */
typedef enum {
    OID_DIR_CW  = 0x00,  // 顺时针
    OID_DIR_CCW = 0x01   // 逆时针
} OID_Direction_t;

/**
 * @brief 编码器波特率枚举
 * 当编码器的ID和波特率更改后，闪灯的颜色会相应变化，状态灯颜色参照表及代表的意义如下：
 * 
 * 颜色及其数值定义关系：
 * - 蓝色(0)  : 500K（默认）
 * - 青色(1)  : 1M
 * - 橙色(2)  : 250K
 * - 紫色(3)  : 125K
 * - 绿色(4)  : 100K
 * - 红色(5)  : 保留
 */
typedef enum {
    OID_BAUD_500K  = 0x00,  // 蓝色 - 500K（默认）
    OID_BAUD_1M    = 0x01,  // 青色 - 1M
    OID_BAUD_250K  = 0x02,  // 橙色 - 250K
    OID_BAUD_125K  = 0x03,  // 紫色 - 125K
    OID_BAUD_100K  = 0x04   // 绿色 - 100K
} OID_Baudrate_t;

typedef struct {
    BSP_CAN_t can;
    uint16_t id;
		
} OID_Param_t;

typedef struct {
	//0x01 编码器值反馈
	float angle_fbk; 
    float angle_360; 
	float angle_2PI;
	//0x0A 速度反馈
    float speed_fbk;
	float speed_rpm;
	
} OID_Feedback_t;

typedef struct {
	DEVICE_Header_t header;
    OID_Param_t param;
    OID_Feedback_t feedback;
} OID_t;

/*CAN管理器，管理一个CAN总线上所有的编码器*/
typedef struct {
    BSP_CAN_t can;
    OID_t *encoders[OID_MAX_NUM];
    uint8_t encoder_count;
} OID_CANManager_t;


/**
 * @brief 更新指定编码器数据
 * @param param 编码器参数指针
 * @return 操作结果
 *         - DEVICE_OK: 成功
 *         - DEVICE_ERR_NULL: 参数为空
 *         - DEVICE_ERR_NO_DEV: 编码器未找到
 *         - DEVICE_ERR: 其他错误
 */
int8_t OID_Update(OID_Param_t *param);

/**
 * @brief 更新所有已注册编码器数据
 * @return 操作结果
 *         - DEVICE_OK: 全部成功
 *         - DEVICE_ERR: 部分或全部失败
 */
int8_t OID_UpdateAll(void);

/**
 * @brief 注册一个欧艾迪编码器
 * @param param 编码器参数指针
 * @return 注册结果
 *         - DEVICE_OK: 注册成功
 *         - DEVICE_ERR_NULL: 参数为空
 *         - DEVICE_ERR_INITED: 已注册
 *         - DEVICE_ERR: 其他错误
 */
int8_t OID_Register(OID_Param_t *param);

/**
 * @brief 设置编码器离线状态
 * @param param 编码器参数指针
 * @return 操作结果
 *         - DEVICE_OK: 成功
 *         - DEVICE_ERR_NULL: 参数为空
 *         - DEVICE_ERR_NO_DEV: 编码器未找到
 */
int8_t OID_Offline(OID_Param_t *param);

/**
 * @brief 获取指定编码器实例指针
 * @param param 编码器参数指针
 * @return 编码器实例指针，失败返回NULL
 */
OID_t* OID_GetEncoder(OID_Param_t *param);

/**
 * @brief 设置编码器ID
 * @param param 当前编码器参数
 * @param param_new 新编码器参数（包含新ID）
 * @return 操作结果
 *         - DEVICE_OK: 成功
 *         - DEVICE_ERR: 失败
 */
int8_t  OID_Set_ID(OID_Param_t *param, OID_Param_t *param_new);

/**
 * @brief 设置编码器CAN通信波特率
 * @param param 编码器参数
 * @param encoder_vaud_rate 波特率设置
 *         - 0x00: 500K（默认）
 *         - 0x01: 1M
 *         - 0x02: 250K
 *         - 0x03: 125K
 *         - 0x04: 100K
 * @return 操作结果
 *         - DEVICE_OK: 成功
 *         - DEVICE_ERR: 失败
 */
int8_t  OID_Set_Baudrate(OID_Param_t *param, OID_Baudrate_t encoder_vaud_rate);

/**
 * @brief 设置编码器工作模式
 * @param param 编码器参数
 * @param encoder_mode 工作模式
 *         - 0x00: 查询模式
 *         - 0x02: 自动返回编码器角速度值
 *         - 0xAA: 自动返回编码器值
 * @return 操作结果
 *         - DEVICE_OK: 成功
 *         - DEVICE_ERR: 失败
 */
int8_t  OID_Set_Mode(OID_Param_t *param, OID_Mode_t encoder_mode);

/**
 * @brief 设置编码器自动回传时间
 * @param param 编码器参数
 * @param encoder_time 自动回传时间（单位：微秒）
 *         数值范围：50~65535（16位无符号整数）
 * @note 注意：设置太短的返回时间后，通过编码器上位机再设置其他参数很容易失败，谨慎使用！
 * @return 操作结果
 *         - DEVICE_OK: 成功
 *         - DEVICE_ERR: 失败
 */
int8_t  OID_Set_AutoFeedbackTime(OID_Param_t *param, uint8_t encoder_time);

/**
 * @brief 设置当前位置为零点
 * @param param 编码器参数
 * @return 操作结果
 *         - DEVICE_OK: 成功
 *         - DEVICE_ERR: 失败
 */
int8_t  OID_Set_ZeroPoint(OID_Param_t *param);

/**
 * @brief 设置编码器值递增方向
 * @param param 编码器参数
 * @param encoder_direction 方向设置
 *         - 0x00: 顺时针
 *         - 0x01: 逆时针
 * @return 操作结果
 *         - DEVICE_OK: 成功
 *         - DEVICE_ERR: 失败
 */
int8_t  OID_Set_Polarity(OID_Param_t *param, OID_Direction_t encoder_direction);

/**
 * @brief 设置编码器角速度采样时间
 * @param param 编码器参数
 * @param encoder_time 采样时间（单位：毫秒）
 * @note 掉电记忆功能
 * @return 操作结果
 *         - DEVICE_OK: 成功
 *         - DEVICE_ERR: 失败
 */
int8_t  OID_Set_AngularVelocitySamplingTime(OID_Param_t *param, uint8_t encoder_time);

/**
 * @brief 设置编码器中点位置
 * @param param 编码器参数
 * @note 设定当前编码器值为 M（M 为单圈分辨率 × 圈数 / 2）
 * @return 操作结果
 *         - DEVICE_OK: 成功
 *         - DEVICE_ERR: 失败
 */
int8_t  OID_Set_Midpoint(OID_Param_t *param);

/**
 * @brief 设置编码器当前位置值
 * @param param 编码器参数
 * @param encoder_direction 位置值
 *         数值范围：0~X（X 为单圈分辨率 × 圈数 - 1）
 * @return 操作结果
 *         - DEVICE_OK: 成功
 *         - DEVICE_ERR: 失败
 */
int8_t  OID_Set_CurrentPosition(OID_Param_t *param, uint8_t encoder_direction);

/**
 * @brief 设置编码器当前值为5圈值
 * @param param 编码器参数
 * @note 即当前编码器值为 Z（Z 为单圈分辨率 × 5）
 * @return 操作结果
 *         - DEVICE_OK: 成功
 *         - DEVICE_ERR: 失败
 */
int8_t  OID_Set_CurrentValue5Turns(OID_Param_t *param);

/**
 * @brief 读取编码器角速度值
 * @param param 编码器参数
 * @note 编码器旋转速度 = 编码器角速度值 / 单圈精度 / 转速计算时间（单位：转/分钟）
 *       例如：编码器角速度值回传为1000，单圈精度为32768，转速采样时间为100ms(0.1/60min)
 *       编码器旋转速度 = 1000 / 32768 / (0.1/60) = 1000 × 0.0183 = 18.31转/分钟
 * @return 操作结果
 *         - DEVICE_OK: 成功
 *         - DEVICE_ERR: 失败
 */
int8_t  OID_Read_AngularVelocity(OID_Param_t *param);

/**
 * @brief 读取编码器值
 * @param param 编码器参数
 * @return 操作结果
 *         - DEVICE_OK: 成功
 *         - DEVICE_ERR: 失败
 */
int8_t  OID_Read_Value(OID_Param_t *param);

#ifdef __cplusplus
}
#endif
