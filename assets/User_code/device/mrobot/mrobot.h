/**
 * @file mrobot.h
 * @brief MRobot CLI - 基于 FreeRTOS CLI 的嵌入式调试命令行系统
 * 
 * 功能特性:
 * - 设备注册与监控（IMU、电机、传感器等）
 * - 类 Unix 文件系统命令（cd, ls, pwd）
 * - htop 风格的任务监控
 * - 自定义命令扩展
 * - 线程安全设计
 * 
 * @example IMU 设备注册示例
 * @code
 * // 1. 定义 IMU 数据结构
 * typedef struct {
 *     bool online;
 *     float accl[3];
 *     float gyro[3];
 *     float euler[3];  // roll, pitch, yaw (deg)
 *     float temp;
 * } MyIMU_t;
 * 
 * MyIMU_t my_imu;
 * 
 * // 2. 实现打印回调
 * static int print_imu(const void *data, char *buf, size_t size) {
 *     const MyIMU_t *imu = (const MyIMU_t *)data;
 *     return MRobot_Snprintf(buf, size,
 *         "  Status: %s\r\n"
 *         "  Accel : X=%.3f Y=%.3f Z=%.3f\r\n"
 *         "  Euler : R=%.2f P=%.2f Y=%.2f\r\n"
 *         "  Temp  : %.1f C\r\n",
 *         imu->online ? "Online" : "Offline",
 *         imu->accl[0], imu->accl[1], imu->accl[2],
 *         imu->euler[0], imu->euler[1], imu->euler[2],
 *         imu->temp);
 * }
 * 
 * // 3. 注册设备
 * MRobot_RegisterDevice("imu", &my_imu, print_imu);
 * @endcode
 * 
 * @example 电机设备注册示例
 * @code
 * typedef struct {
 *     bool online;
 *     float angle;    // deg
 *     float speed;    // RPM
 *     float current;  // A
 * } MyMotor_t;
 * 
 * MyMotor_t motor[4];
 * 
 * static int print_motor(const void *data, char *buf, size_t size) {
 *     const MyMotor_t *m = (const MyMotor_t *)data;
 *     return MRobot_Snprintf(buf, size,
 *         "  Status : %s\r\n"
 *         "  Angle  : %.2f deg\r\n"
 *         "  Speed  : %.1f RPM\r\n"
 *         "  Current: %.3f A\r\n",
 *         m->online ? "Online" : "Offline",
 *         m->angle, m->speed, m->current);
 * }
 * 
 * // 注册 4 个电机
 * MRobot_RegisterDevice("motor0", &motor[0], print_motor);
 * MRobot_RegisterDevice("motor1", &motor[1], print_motor);
 * MRobot_RegisterDevice("motor2", &motor[2], print_motor);
 * MRobot_RegisterDevice("motor3", &motor[3], print_motor);
 * @endcode
 * 
 * @example 自定义校准命令示例
 * @code
 * // 校准数据
 * static float gyro_offset[3] = {0};
 * 
 * // 命令回调: cali gyro / cali accel / cali save
 * static long cmd_cali(char *buf, size_t size, const char *cmd) {
 *     const char *param = FreeRTOS_CLIGetParameter(cmd, 1, NULL);
 *     
 *     if (param == NULL) {
 *         return MRobot_Snprintf(buf, size, "Usage: cali <gyro|accel|save>\r\n");
 *     }
 *     if (strncmp(param, "gyro", 4) == 0) {
 *         // 采集 1000 次陀螺仪数据求平均
 *         MRobot_Snprintf(buf, size, "Calibrating gyro... keep IMU still!\r\n");
 *         // ... 校准逻辑 ...
 *         return 0;
 *     }
 *     if (strncmp(param, "save", 4) == 0) {
 *         // 保存到 Flash
 *         MRobot_Snprintf(buf, size, "Calibration saved to flash.\r\n");
 *         return 0;
 *     }
 *     return MRobot_Snprintf(buf, size, "Unknown: %s\r\n", param);
 * }
 * 
 * // 注册命令
 * MRobot_RegisterCommand("cali", "cali <gyro|accel|save>: IMU calibration\r\n", cmd_cali, -1);
 * @endcode
 */

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include "bsp/uart.h"

/* Configuration ------------------------------------------------------------ */
/* 可在编译时通过 -D 选项覆盖这些默认值 */

#ifndef MROBOT_MAX_DEVICES
#define MROBOT_MAX_DEVICES          64      /* 最大设备数 */
#endif

#ifndef MROBOT_MAX_CUSTOM_COMMANDS
#define MROBOT_MAX_CUSTOM_COMMANDS  16      /* 最大自定义命令数 */
#endif

#ifndef MROBOT_CMD_BUFFER_SIZE
#define MROBOT_CMD_BUFFER_SIZE      128     /* 命令缓冲区大小 */
#endif

#ifndef MROBOT_OUTPUT_BUFFER_SIZE
#define MROBOT_OUTPUT_BUFFER_SIZE   512     /* 输出缓冲区大小 */
#endif

#ifndef MROBOT_DEVICE_NAME_LEN
#define MROBOT_DEVICE_NAME_LEN      32      /* 设备名最大长度 */
#endif

#ifndef MROBOT_PATH_MAX_LEN
#define MROBOT_PATH_MAX_LEN         64      /* 路径最大长度 */
#endif

#ifndef MROBOT_HTOP_REFRESH_MS
#define MROBOT_HTOP_REFRESH_MS      200     /* htop 刷新间隔 (ms) */
#endif

#ifndef MROBOT_UART_PORT
#define MROBOT_UART_PORT            BSP_UART_VOFA  /* 默认 UART 端口 */
#endif

#ifndef MROBOT_USER_NAME
#define MROBOT_USER_NAME            "root"         /* CLI 用户名 */
#endif

#ifndef MROBOT_HOST_NAME
#define MROBOT_HOST_NAME            "MRobot"       /* CLI 主机名 */
#endif

/* Error codes -------------------------------------------------------------- */
typedef enum {
    MROBOT_OK               =  0,   /* 成功 */
    MROBOT_ERR_FULL         = -1,   /* 容量已满 */
    MROBOT_ERR_NULL_PTR     = -2,   /* 空指针 */
    MROBOT_ERR_INVALID_ARG  = -3,   /* 无效参数 */
    MROBOT_ERR_NOT_FOUND    = -4,   /* 未找到 */
    MROBOT_ERR_ALLOC        = -5,   /* 内存分配失败 */
    MROBOT_ERR_BUSY         = -6,   /* 设备忙 */
    MROBOT_ERR_NOT_INIT     = -7,   /* 未初始化 */
} MRobot_Error_t;

/* CLI 运行状态 */
typedef enum {
    MROBOT_STATE_IDLE,              /* 空闲状态，等待输入 */
    MROBOT_STATE_HTOP,              /* htop 模式 */
    MROBOT_STATE_PROCESSING,        /* 正在处理命令 */
} MRobot_State_t;

/* Callback types ----------------------------------------------------------- */

/**
 * @brief 设备打印回调函数类型
 * @param device_data 用户注册时传入的设备数据指针
 * @param buffer 输出缓冲区
 * @param buffer_size 缓冲区大小
 * @return 实际写入的字节数
 * @note 用户需要自行实现此函数来格式化设备数据
 */
typedef int (*MRobot_PrintCallback_t)(const void *device_data, char *buffer, size_t buffer_size);

/**
 * @brief 命令处理回调函数类型（与 FreeRTOS CLI 兼容）
 */
typedef long (*MRobot_CommandCallback_t)(char *pcWriteBuffer, size_t xWriteBufferLen, const char *pcCommandString);

/* Device structure --------------------------------------------------------- */
typedef struct {
    char name[MROBOT_DEVICE_NAME_LEN];  /* 设备名称 */
    void *data;                         /* 用户设备数据指针 */
    MRobot_PrintCallback_t print_cb;    /* 用户打印回调函数 */
} MRobot_Device_t;

/* Public API --------------------------------------------------------------- */

/**
 * @brief 初始化 MRobot CLI 系统
 * @note 必须在 FreeRTOS 调度器启动后调用
 */
void MRobot_Init(void);

/**
 * @brief 反初始化 MRobot CLI 系统，释放资源
 */
void MRobot_DeInit(void);

/**
 * @brief 获取当前 CLI 状态
 * @return MRobot_State_t 当前状态
 */
MRobot_State_t MRobot_GetState(void);

/**
 * @brief 注册设备到 MRobot 系统
 * @param name 设备名称（会被截断到 MROBOT_DEVICE_NAME_LEN-1）
 * @param data 设备数据指针（不能为 NULL）
 * @param print_cb 打印回调函数（可为 NULL，但无法用 show 命令查看）
 * @return MRobot_Error_t 错误码
 */
MRobot_Error_t MRobot_RegisterDevice(const char *name, void *data, MRobot_PrintCallback_t print_cb);

/**
 * @brief 注销设备
 * @param name 设备名称
 * @return MRobot_Error_t 错误码
 */
MRobot_Error_t MRobot_UnregisterDevice(const char *name);

/**
 * @brief 注册自定义命令
 * @param command 命令名称
 * @param help_text 帮助文本
 * @param callback 命令回调函数
 * @param param_count 参数个数（-1 表示可变参数）
 * @return MRobot_Error_t 错误码
 */
MRobot_Error_t MRobot_RegisterCommand(const char *command, const char *help_text,
                                       MRobot_CommandCallback_t callback, int8_t param_count);

/**
 * @brief 获取已注册设备数量
 * @return 设备数量
 */
uint8_t MRobot_GetDeviceCount(void);

/**
 * @brief 根据名称查找设备
 * @param name 设备名称
 * @return 设备指针，未找到返回 NULL
 */
const MRobot_Device_t *MRobot_FindDevice(const char *name);

/**
 * @brief MRobot 主循环，在 CLI 任务中周期性调用
 * @note 建议调用周期 10ms
 */
void MRobot_Run(void);

/**
 * @brief 格式化输出到 CLI 终端（线程安全，支持浮点数）
 * @param fmt 格式字符串
 * @param ... 可变参数
 * @return 实际输出的字符数，失败返回负数
 * 
 * @note 支持的格式说明符:
 *   - %d, %i, %u, %x, %X, %ld, %lu, %lx  : 整数
 *   - %s, %c   : 字符串/字符
 *   - %f       : 浮点数 (默认2位小数)
 *   - %.Nf     : 浮点数 (N位小数, N=0-6)
 *   - %%       : 百分号
 * 
 * @example
 *   MRobot_Printf("Euler: R=%.2f P=%.2f Y=%.2f\\r\\n", roll, pitch, yaw);
 */
int MRobot_Printf(const char *fmt, ...);

/**
 * @brief 格式化到缓冲区（用于回调函数，支持浮点数）
 * @note 格式说明符同 MRobot_Printf
 * 
 * @example
 *   static int print_imu(const void *data, char *buf, size_t size) {
 *       const BMI088_t *imu = (const BMI088_t *)data;
 *       return MRobot_Snprintf(buf, size,
 *           "  Accel: X=%.3f Y=%.3f Z=%.3f\\r\\n",
 *           imu->accl.x, imu->accl.y, imu->accl.z);
 *   }
 */
int MRobot_Snprintf(char *buf, size_t size, const char *fmt, ...);

/* Utility functions -------------------------------------------------------- */

/**
 * @brief 格式化浮点数为字符串（嵌入式环境不支持 %f）
 * @param buf 输出缓冲区
 * @param size 缓冲区大小
 * @param val 要格式化的浮点数
 * @param precision 小数位数 (0-6)
 * @return 写入的字符数
 * 
 * @example
 *   char buf[16];
 *   MRobot_FormatFloat(buf, sizeof(buf), 3.14159f, 2);  // "3.14"
 *   MRobot_FormatFloat(buf, sizeof(buf), -0.001f, 4);   // "-0.0010"
 */
int MRobot_FormatFloat(char *buf, size_t size, float val, int precision);

#ifdef __cplusplus
}
#endif