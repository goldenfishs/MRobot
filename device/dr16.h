#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include <cmsis_os2.h>

#include "component/user_math.h"
#include "device.h"

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

/* USER DEFINE BEGIN */

/* USER DEFINE END */

/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */
typedef struct __packed {
  uint16_t ch_r_x : 11;
  uint16_t ch_r_y : 11;
  uint16_t ch_l_x : 11;
  uint16_t ch_l_y : 11;
  uint8_t sw_r : 2;
  uint8_t sw_l : 2;
  int16_t x;
  int16_t y;
  int16_t z;
  uint8_t press_l;
  uint8_t press_r;
  uint16_t key;
  uint16_t res;
} DR16_RawData_t;

typedef enum {
  DR16_SW_ERR = 0,
  DR16_SW_UP = 1,
  DR16_SW_MID = 3,
  DR16_SW_DOWN = 2,
} DR16_SwitchPos_t;

/* 键盘按键值 */
typedef enum {
  DR16_KEY_W = 0,
  DR16_KEY_S,
  DR16_KEY_A,
  DR16_KEY_D,
  DR16_KEY_SHIFT,
  DR16_KEY_CTRL,
  DR16_KEY_Q,
  DR16_KEY_E,
  DR16_KEY_R,
  DR16_KEY_F,
  DR16_KEY_G,
  DR16_KEY_Z,
  DR16_KEY_X,
  DR16_KEY_C,
  DR16_KEY_V,
  DR16_KEY_B,
  DR16_L_CLICK,
  DR16_R_CLICK,
  DR16_KEY_NUM,
} DR16_Key_t;

typedef struct {
  float ch_l_x; /* 遥控器左侧摇杆横轴值，上为正 */
  float ch_l_y; /* 遥控器左侧摇杆纵轴值，右为正 */
  float ch_r_x; /* 遥控器右侧摇杆横轴值，上为正 */
  float ch_r_y; /* 遥控器右侧摇杆纵轴值，右为正 */

  float ch_res; /* 第五通道值 */

   DR16_SwitchPos_t sw_r; /* 右侧拨杆位置 */
   DR16_SwitchPos_t sw_l; /* 左侧拨杆位置 */

  struct {
    int16_t x;
    int16_t y;
    int16_t z;
    bool l_click; /* 左键 */
    bool r_click; /* 右键 */
  } mouse;        /* 鼠标值 */

  union {
    bool key[DR16_KEY_NUM]; /* 键盘按键值 */
    uint16_t value;        /* 键盘按键值的位映射 */
  } keyboard;

  uint16_t res; /* 保留，未启用 */
} DR16_Data_t;


typedef struct {
  DEVICE_Header_t header;
  DR16_RawData_t raw_data;
  DR16_Data_t data;
} DR16_t;

/* Exported functions prototypes -------------------------------------------- */
int8_t DR16_Init(DR16_t *dr16);
int8_t DR16_Restart(void);
int8_t DR16_StartDmaRecv(DR16_t *dr16);
bool DR16_WaitDmaCplt(uint32_t timeout);
int8_t DR16_ParseData(DR16_t *dr16);
int8_t DR16_Offline(DR16_t *dr16);

/* USER FUNCTION BEGIN */

/* USER FUNCTION END */

#ifdef __cplusplus
}
#endif
