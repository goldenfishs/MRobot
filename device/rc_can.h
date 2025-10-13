#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include "bsp/can.h"
#include "device/device.h"
#include <stdint.h>
#include <stdbool.h>

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

/* USER DEFINE BEGIN */

/* USER DEFINE END */

/* Exported constants ------------------------------------------------------- */

/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */
typedef enum {
  RC_CAN_SW_ERR = 0,
  RC_CAN_SW_UP = 1,
  RC_CAN_SW_MID = 3,
  RC_CAN_SW_DOWN = 2,
} RC_CAN_SW_t;

typedef enum {
    RC_CAN_MODE_MASTER = 0, // 主机模式
    RC_CAN_MODE_SLAVE = 1, // 从机模式
} RC_CAN_Mode_t;

typedef enum {
    RC_CAN_DATA_JOYSTICK = 0,
    RC_CAN_DATA_SWITCH,
    RC_CAN_DATA_MOUSE,
    RC_CAN_DATA_KEYBOARD
} RC_CAN_DataType_t;

typedef enum {
  RC_CAN_KEY_NONE = 0xFF,  // 无按键
  RC_CAN_KEY_W = 0,
  RC_CAN_KEY_S,
  RC_CAN_KEY_A,
  RC_CAN_KEY_D,
  RC_CAN_KEY_SHIFT,
  RC_CAN_KEY_CTRL,
  RC_CAN_KEY_Q,
  RC_CAN_KEY_E,
  RC_CAN_KEY_R,
  RC_CAN_KEY_F,
  RC_CAN_KEY_G,
  RC_CAN_KEY_Z,
  RC_CAN_KEY_X,
  RC_CAN_KEY_C,
  RC_CAN_KEY_V,
  RC_CAN_KEY_B,
  RC_CAN_KEY_NUM,
} RC_CAN_Key_t;

// 遥杆数据包
typedef struct {
    float ch_l_x;
    float ch_l_y;
    float ch_r_x;
    float ch_r_y;
} RC_CAN_JoyData_t;

// 拨杆数据包
typedef struct {
    RC_CAN_SW_t sw_l;     // 左拨杆状态
    RC_CAN_SW_t sw_r;     // 右拨杆状态 
    float ch_res;   // 第五通道
} RC_CAN_SwitchData_t;

// 鼠标数据包
typedef struct {
    float x;  // 鼠标X轴移动
    float y;  // 鼠标Y轴移动
    float z;  // 鼠标Z轴(滚轮)
    bool mouse_l;  // 鼠标左键
    bool mouse_r;  // 鼠标右键
} RC_CAN_MouseData_t;

// 键盘数据包
typedef struct {
    uint16_t key_value; // 键盘按键位映射
    RC_CAN_Key_t keys[16];
} RC_CAN_KeyboardData_t;


typedef struct {
    RC_CAN_JoyData_t joy;
    RC_CAN_SwitchData_t sw;
    RC_CAN_MouseData_t mouse;
    RC_CAN_KeyboardData_t keyboard;
} RC_CAN_Data_t;

// RC_CAN 参数结构
typedef struct {
    BSP_CAN_t can;         // 使用的CAN总线
    RC_CAN_Mode_t mode;    // 工作模式
    uint16_t joy_id;      // 遥杆CAN ID
    uint16_t sw_id;   // 拨杆CAN ID
    uint16_t mouse_id; // 鼠标CAN ID
    uint16_t keyboard_id; // 键盘CAN ID
} RC_CAN_Param_t;

// RC_CAN 主结构
typedef struct {
    DEVICE_Header_t header;
    RC_CAN_Param_t param;
    RC_CAN_Data_t data;
} RC_CAN_t;

/* USER STRUCT BEGIN */

/* USER STRUCT END */

/* Exported functions prototypes -------------------------------------------- */

/**
 * @brief 初始化RC CAN发送模块
 * @param rc_can RC_CAN结构体指针
 * @param param 初始化参数
 * @return DEVICE_OK 成功，其他值失败
 */
int8_t RC_CAN_Init(RC_CAN_t *rc_can, RC_CAN_Param_t *param);

/**
 * @brief 更新并发送数据到CAN总线
 * @param rc_can RC_CAN结构体指针
 * @param data_type 数据类型
 * @return DEVICE_OK 成功，其他值失败
 */
int8_t RC_CAN_SendData(RC_CAN_t *rc_can, RC_CAN_DataType_t data_type);

/**
 * @brief 接收并更新CAN数据
 * @param rc_can RC_CAN结构体指针
 * @param data_type 数据类型
 * @return DEVICE_OK 成功，其他值失败
 */
int8_t RC_CAN_Update(RC_CAN_t *rc_can , RC_CAN_DataType_t data_type);

int8_t RC_CAN_OFFLINE(RC_CAN_t *rc_can);
/* USER FUNCTION BEGIN */

/* USER FUNCTION END */

#ifdef __cplusplus
}
#endif
