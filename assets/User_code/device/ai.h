/*
  AI
*/

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include "component/ahrs.h"
#include "component/filter.h"
#include "component/user_math.h"
#include "device/device.h"
#include <cmsis_os2.h>
#include <stdbool.h>
#include <stdint.h>

/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
#define AI_ID_MCU (0xC4)
#define AI_ID_REF (0xA8)
#define AI_ID_AI (0xA1)
/* Exported types ----------------------------------------------------------- */

typedef enum {
  AI_ARMOR_HERO = 0, /*英雄机器人*/
  AI_ARMOR_INFANTRY, /*步兵机器人*/
  AI_ARMOR_SENTRY,   /*哨兵机器人*/
  AI_ARMOR_ENGINEER, /*工程机器人*/
  AI_ARMOR_OUTPOST,  /*前哨占*/
  AI_ARMOR_BASE,     /*基地*/
  AI_ARMOR_NORMAL,   /*由AI自动选择*/
} AI_ArmorsType_t;

typedef enum {
  AI_STATUS_OFF = 0, /* 关闭 */
  AI_STATUS_AUTOAIM, /* 自瞄 */
  AI_STATUS_AUTOPICK, /* 自动取矿 */
  AI_STATUS_AUTOPUT,  /* 自动兑矿 */
  AI_STATUS_AUTOHITBUFF,  /* 自动打符 */
  AI_STATUS_AUTONAV,
} AI_Status_t;

typedef enum { 
  AI_NOTICE_NONE = 0,
  AI_NOTICE_SEARCH,
  AI_NOTICE_FIRE,
}AI_Notice_t;

/* 电控 -> 视觉 MCU数据结构体*/
typedef struct __packed {
  AHRS_Quaternion_t quat; /* 四元数 */
  // struct {
  //   AI_ArmorsType_t armor_type;
  //   AI_Status_t status;
  // }notice; /* 控制命令 */
  uint8_t notice;
} AI_Protucol_UpDataMCU_t;

/* 电控 -> 视觉 裁判系统数据结构体*/
typedef struct __packed {
  /* USER REFEREE BEGIN */
  uint16_t team; /* 本身队伍 */
  uint16_t time; /* 比赛开始时间 */
  /* USER REFEREE END */
} AI_Protocol_UpDataReferee_t;

/* 视觉 -> 电控 数据包结构体*/
typedef struct __packed {
  AHRS_Eulr_t eulr;      /* 欧拉角 */
  MoveVector_t move_vec; /* 运动向量 */
  uint8_t notice;        /* 控制命令 */
} AI_Protocol_DownData_t;

/* 电控 -> 视觉 裁判系统数据包 */
typedef struct __packed {
  uint8_t id;                          /* 包ID */
  AI_Protocol_UpDataReferee_t package; /* 数据包 */
  uint16_t crc16;                      /* CRC16校验 */
} AI_UpPackageReferee_t;

/* 电控 -> 视觉 MUC数据包 */
typedef struct __packed {
  uint8_t id;
  AI_Protucol_UpDataMCU_t package;
  uint16_t crc16;
} AI_UpPackageMCU_t;

/* 视觉 -> 电控 数据包 */
typedef struct __packed {
  uint8_t id;                     /* 包ID */
  AI_Protocol_DownData_t package; /* 数据包 */
  uint16_t crc16;                 /* CRC16校验 */
} AI_DownPackage_t;

typedef struct __packed {
  DEVICE_Header_t header; /* 设备通用头部 */
  AI_DownPackage_t from_host;
  AI_Status_t status;
  struct {
    AI_UpPackageReferee_t ref;
    AI_UpPackageMCU_t mcu;
  } to_host;
} AI_t;

/* Exported functions prototypes -------------------------------------------- */

int8_t AI_Init(AI_t *ai);

int8_t AI_Restart(AI_t *ai);

int8_t AI_StartReceiving(AI_t *ai);

bool AI_WaitDmaCplt(void);

int8_t AI_ParseHost(AI_t *ai);

int8_t AI_PackMCU(AI_t *ai, const AHRS_Quaternion_t *quat);

int8_t AI_PackRef(AI_t *ai, const AI_UpPackageReferee_t *data);

int8_t AI_HandleOffline(AI_t *ai);

int8_t AI_StartSend(AI_t *ai, bool ref_online);

#ifdef __cplusplus
}
#endif
