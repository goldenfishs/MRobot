#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <cmsis_os2.h>
#include "FreeRTOS.h"
#include "task.h"

// 定义任务运行时结构体
typedef struct {
    /* 各任务，也可以叫做线程 */
    struct {
        osThreadId_t user_task;
    } thread;
  
    struct {
        osMessageQueueId_t pc; 
    } msgq;
  

    struct {
        uint32_t user_task;
    } heap_water_mark; /* heap使用 */

    struct {
        float user_task; /* 用户自定义任务运行频率 */
    } freq; /* 任务运行频率 */
  
    struct {
        uint32_t user_task;
    } last_up_time; /* 任务最近运行时间 */
  } Task_Runtime_t;
  


// 任务频率和初始化延时
#define TASK_FREQ_USER_TASK (100u) // 用户自定义任务频率


#define TASK_INIT_DELAY_INFO (100u)

// 任务句柄
typedef struct {
    osThreadId_t user_task; /* 用户自定义任务 */
} Task_Handles_t;

// 任务运行时结构体
extern Task_Runtime_t task_runtime;

// 初始化任务句柄
extern const osThreadAttr_t attr_init;

// 用户自定义任务句柄
extern const osThreadAttr_t attr_user_task

// 任务函数声明
//初始化任务
void Task_Init(void *argument);
//用户自定义任务
void Task_UserTask(void *argument);


#ifdef __cplusplus
}
#endif
