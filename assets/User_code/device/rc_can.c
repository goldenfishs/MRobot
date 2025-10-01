/* Includes ----------------------------------------------------------------- */
#include "device/rc_can.h"
#include "bsp/time.h"
#include "device/device.h"
/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

/* Private constants -------------------------------------------------------- */

/* USER DEFINE BEGIN */

/* USER DEFINE END */

/* Private macro ------------------------------------------------------------ */
/* Private types ------------------------------------------------------------ */
/* Private variables -------------------------------------------------------- */

/* USER VARIABLE BEGIN */

/* USER VARIABLE END */

/* USER FUNCTION BEGIN */

/* USER FUNCTION END */

/* Private function prototypes ---------------------------------------------- */
static int8_t RC_CAN_ValidateParams(const RC_CAN_Param_t *param);
static int8_t RC_CAN_RegisterIds(RC_CAN_t *rc_can);

/* Exported functions ------------------------------------------------------- */

/**
 * @brief 初始化RC CAN发送模块
 * @param rc_can RC_CAN结构体指针
 * @param param 初始化参数
 * @return DEVICE_OK 成功，其他值失败
 */
int8_t RC_CAN_Init(RC_CAN_t *rc_can, RC_CAN_Param_t *param) {
  if (rc_can == NULL || param == NULL) {
    return DEVICE_ERR_NULL;
  }

  // 参数验证
  if (RC_CAN_ValidateParams(param) != DEVICE_OK) {
    return DEVICE_ERR;
  }

  rc_can->param = *param;

  // 初始化header
  rc_can->header.online = false;
  rc_can->header.last_online_time = 0;

  // 手动初始化数据结构
  rc_can->data.joy.ch_l_x = 0.0f;
  rc_can->data.joy.ch_l_y = 0.0f;
  rc_can->data.joy.ch_r_x = 0.0f;
  rc_can->data.joy.ch_r_y = 0.0f;
  rc_can->data.sw.sw_l = RC_CAN_SW_ERR;
  rc_can->data.sw.sw_r = RC_CAN_SW_ERR;
  rc_can->data.sw.ch_res = 0.0f;
  rc_can->data.mouse.x = 0.0f;
  rc_can->data.mouse.y = 0.0f;
  rc_can->data.mouse.z = 0.0f;
  rc_can->data.mouse.mouse_l = false;
  rc_can->data.mouse.mouse_r = false;
  rc_can->data.keyboard.key_value = 0;
  for (int i = 0; i < 6; i++) {
    rc_can->data.keyboard.keys[i] = RC_CAN_KEY_NONE;
  }

  // 注册CAN ID队列（从机模式需要接收数据）
  if (rc_can->param.mode == RC_CAN_MODE_SLAVE) {
    return RC_CAN_RegisterIds(rc_can);
  }

  return DEVICE_OK;
}

/**
 * @brief 更新并发送数据到CAN总线
 * @param rc_can RC_CAN结构体指针
 * @param data_type 数据类型
 * @return DEVICE_OK 成功，其他值失败
 */
int8_t RC_CAN_SendData(RC_CAN_t *rc_can, RC_CAN_DataType_t data_type) {
  if (rc_can == NULL) {
    return DEVICE_ERR_NULL;
  }
  if (rc_can->param.mode != RC_CAN_MODE_MASTER) {
    return DEVICE_ERR;
  }
  BSP_CAN_StdDataFrame_t frame;
  frame.dlc = 8;
  // 边界裁剪宏
  #define RC_CAN_CLAMP(x, min, max) ((x) < (min) ? (min) : ((x) > (max) ? (max) : (x)))
  switch (data_type) {
  case RC_CAN_DATA_JOYSTICK: {
    frame.id = rc_can->param.joy_id;
    float l_x = RC_CAN_CLAMP(rc_can->data.joy.ch_l_x, -0.999969f, 0.999969f);
    float l_y = RC_CAN_CLAMP(rc_can->data.joy.ch_l_y, -0.999969f, 0.999969f);
    float r_x = RC_CAN_CLAMP(rc_can->data.joy.ch_r_x, -0.999969f, 0.999969f);
    float r_y = RC_CAN_CLAMP(rc_can->data.joy.ch_r_y, -0.999969f, 0.999969f);
    int16_t l_x_i = (int16_t)(l_x * 32768.0f);
    int16_t l_y_i = (int16_t)(l_y * 32768.0f);
    int16_t r_x_i = (int16_t)(r_x * 32768.0f);
    int16_t r_y_i = (int16_t)(r_y * 32768.0f);
    frame.data[0] = (uint8_t)(l_x_i & 0xFF);
    frame.data[1] = (uint8_t)((l_x_i >> 8) & 0xFF);
    frame.data[2] = (uint8_t)(l_y_i & 0xFF);
    frame.data[3] = (uint8_t)((l_y_i >> 8) & 0xFF);
    frame.data[4] = (uint8_t)(r_x_i & 0xFF);
    frame.data[5] = (uint8_t)((r_x_i >> 8) & 0xFF);
    frame.data[6] = (uint8_t)(r_y_i & 0xFF);
    frame.data[7] = (uint8_t)((r_y_i >> 8) & 0xFF);
    break;
  }
  case RC_CAN_DATA_SWITCH: {
    frame.id = rc_can->param.sw_id;
    frame.data[0] = (uint8_t)(rc_can->data.sw.sw_l);
    frame.data[1] = (uint8_t)(rc_can->data.sw.sw_r);
    float ch_res = RC_CAN_CLAMP(rc_can->data.sw.ch_res, -0.999969f, 0.999969f);
    int16_t ch_res_i = (int16_t)(ch_res * 32768.0f);
    frame.data[2] = (uint8_t)(ch_res_i & 0xFF);
    frame.data[3] = (uint8_t)((ch_res_i >> 8) & 0xFF);
    frame.data[4] = 0; // 保留字节
    frame.data[5] = 0; // 保留字节
    frame.data[6] = 0; // 保留字节
    frame.data[7] = 0; // 保留字节
    break;
  }
  case RC_CAN_DATA_MOUSE: {
    frame.id = rc_can->param.mouse_id;
    // 鼠标x/y/z一般为增量，若有极限也可加clamp
    int16_t x = (int16_t)(rc_can->data.mouse.x);
    int16_t y = (int16_t)(rc_can->data.mouse.y);
    int16_t z = (int16_t)(rc_can->data.mouse.z);
    frame.data[0] = (uint8_t)(x & 0xFF);
    frame.data[1] = (uint8_t)((x >> 8) & 0xFF);
    frame.data[2] = (uint8_t)(y & 0xFF);
    frame.data[3] = (uint8_t)((y >> 8) & 0xFF);
    frame.data[4] = (uint8_t)(z & 0xFF);
    frame.data[5] = (uint8_t)((z >> 8) & 0xFF);
    frame.data[6] = (uint8_t)(rc_can->data.mouse.mouse_l ? 1 : 0);
    frame.data[7] = (uint8_t)(rc_can->data.mouse.mouse_r ? 1 : 0);
    break;
  }
  case RC_CAN_DATA_KEYBOARD: {
    frame.id = rc_can->param.keyboard_id;
    frame.data[0] = (uint8_t)(rc_can->data.keyboard.key_value & 0xFF);
    frame.data[1] = (uint8_t)((rc_can->data.keyboard.key_value >> 8) & 0xFF);
    for (int i = 0; i < 6; i++) {
      frame.data[2 + i] = (i < 6) ? (uint8_t)(rc_can->data.keyboard.keys[i]) : 0;
    }
    break;
  }
  default:
    return DEVICE_ERR;
  }
  #undef RC_CAN_CLAMP
  if (BSP_CAN_Transmit(rc_can->param.can, BSP_CAN_FORMAT_STD_DATA, frame.id,
                       frame.data, frame.dlc) != BSP_OK) {
    return DEVICE_ERR;
  }
  return DEVICE_OK;
}

/**
 * @brief 接收并更新CAN数据
 * @param rc_can RC_CAN结构体指针
 * @param data_type 数据类型
 * @return DEVICE_OK 成功，其他值失败
 */
int8_t RC_CAN_Update(RC_CAN_t *rc_can, RC_CAN_DataType_t data_type) {
  if (rc_can == NULL) {
    return DEVICE_ERR_NULL;
  }

  // 只有从机模式才能接收数据
  if (rc_can->param.mode != RC_CAN_MODE_SLAVE) {
    return DEVICE_ERR;
  }
  BSP_CAN_Message_t msg;
  
  switch (data_type) {
  case RC_CAN_DATA_JOYSTICK:
    if (BSP_CAN_GetMessage(rc_can->param.can, rc_can->param.joy_id, &msg,
                           BSP_CAN_TIMEOUT_IMMEDIATE) != BSP_OK) {
      return DEVICE_ERR;
    }
    // 解包数据
    int16_t ch_l_x = (int16_t)((msg.data[1] << 8) | msg.data[0]);
    int16_t ch_l_y = (int16_t)((msg.data[3] << 8) | msg.data[2]);
    int16_t ch_r_x = (int16_t)((msg.data[5] << 8) | msg.data[4]);
    int16_t ch_r_y = (int16_t)((msg.data[7] << 8) | msg.data[6]);

    // 转换为浮点数（范围：-1.0到1.0）
    rc_can->data.joy.ch_l_x = (float)ch_l_x / 32768.0f;
    rc_can->data.joy.ch_l_y = (float)ch_l_y / 32768.0f;
    rc_can->data.joy.ch_r_x = (float)ch_r_x / 32768.0f;
    rc_can->data.joy.ch_r_y = (float)ch_r_y / 32768.0f;
    break;
  case RC_CAN_DATA_SWITCH:
    if (BSP_CAN_GetMessage(rc_can->param.can, rc_can->param.sw_id, &msg,
                           BSP_CAN_TIMEOUT_IMMEDIATE) != BSP_OK) {
      return DEVICE_ERR;
    }
    // 解包数据
    rc_can->data.sw.sw_l = (RC_CAN_SW_t)msg.data[0];
    rc_can->data.sw.sw_r = (RC_CAN_SW_t)msg.data[1];

    int16_t ch_res = (int16_t)((msg.data[3] << 8) | msg.data[2]);
    rc_can->data.sw.ch_res = (float)ch_res / 32768.0f;
    break;
  case RC_CAN_DATA_MOUSE:
    if (BSP_CAN_GetMessage(rc_can->param.can, rc_can->param.mouse_id, &msg,
                           BSP_CAN_TIMEOUT_IMMEDIATE) != BSP_OK) {
      return DEVICE_ERR;
    }
    // 解包数据
    int16_t x = (int16_t)((msg.data[1] << 8) | msg.data[0]);
    int16_t y = (int16_t)((msg.data[3] << 8) | msg.data[2]);
    int16_t z = (int16_t)((msg.data[5] << 8) | msg.data[4]);
    rc_can->data.mouse.x = (float)x;
    rc_can->data.mouse.y = (float)y;
    rc_can->data.mouse.z = (float)z;
    rc_can->data.mouse.mouse_l = (msg.data[6] & 0x01) ? true : false;
    rc_can->data.mouse.mouse_r = (msg.data[7] & 0x01) ? true : false;
    break;
  case RC_CAN_DATA_KEYBOARD:
    if (BSP_CAN_GetMessage(rc_can->param.can, rc_can->param.keyboard_id, &msg,
                           BSP_CAN_TIMEOUT_IMMEDIATE) != BSP_OK) {
      return DEVICE_ERR;
    }
    if (msg.dlc < 2) {
      return DEVICE_ERR;
    }
    // 解包数据
    rc_can->data.keyboard.key_value =
        (uint16_t)((msg.data[1] << 8) | msg.data[0]);
    for (int i = 0; i < 6 && (i + 2) < msg.dlc; i++) {
      rc_can->data.keyboard.keys[i] = (RC_CAN_Key_t)(msg.data[2 + i]);
    }
    // 清空未使用的按键位置
    for (int i = (msg.dlc > 2 ? msg.dlc - 2 : 0); i < 6; i++) {
      rc_can->data.keyboard.keys[i] = RC_CAN_KEY_NONE;
    }
    break;
  default:
    return DEVICE_ERR;
  }

  // 更新header状态
  rc_can->header.online = true;
  rc_can->header.last_online_time = BSP_TIME_Get_us();

  return DEVICE_OK;
}

/* Private functions -------------------------------------------------------- */

/**
 * @brief 验证RC_CAN参数
 * @param param 参数指针
 * @return DEVICE_OK 成功，其他值失败
 */
static int8_t RC_CAN_ValidateParams(const RC_CAN_Param_t *param) {
  if (param == NULL) {
    return DEVICE_ERR_NULL;
  }

  // 检查CAN总线有效性
  if (param->can >= BSP_CAN_NUM) {
    return DEVICE_ERR;
  }

  // 检查工作模式有效性
  if (param->mode != RC_CAN_MODE_MASTER && param->mode != RC_CAN_MODE_SLAVE) {
    return DEVICE_ERR;
  }

  // 检查CAN ID是否重复
  if (param->joy_id == param->sw_id || param->joy_id == param->mouse_id ||
      param->joy_id == param->keyboard_id || param->sw_id == param->mouse_id ||
      param->sw_id == param->keyboard_id ||
      param->mouse_id == param->keyboard_id) {
    return DEVICE_ERR;
  }

  return DEVICE_OK;
}

/**
 * @brief 注册CAN ID
 * @param rc_can RC_CAN结构体指针
 * @return DEVICE_OK 成功，其他值失败
 */
static int8_t RC_CAN_RegisterIds(RC_CAN_t *rc_can) {
  if (BSP_CAN_RegisterId(rc_can->param.can, rc_can->param.joy_id, 0) !=
      BSP_OK) {
    return DEVICE_ERR;
  }
  if (BSP_CAN_RegisterId(rc_can->param.can, rc_can->param.sw_id, 0) != BSP_OK) {
    return DEVICE_ERR;
  }
  if (BSP_CAN_RegisterId(rc_can->param.can, rc_can->param.mouse_id, 0) !=
      BSP_OK) {
    return DEVICE_ERR;
  }
  if (BSP_CAN_RegisterId(rc_can->param.can, rc_can->param.keyboard_id, 0) !=
      BSP_OK) {
    return DEVICE_ERR;
  }

  return DEVICE_OK;
}

int8_t RC_CAN_OFFLINE(RC_CAN_t *rc_can){
    if (rc_can == NULL) {
        return DEVICE_ERR_NULL;
    }
    rc_can->header.online = false;
    return DEVICE_OK;
}
/* USER CODE BEGIN */

/* USER CODE END */
