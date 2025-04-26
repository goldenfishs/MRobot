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
        osThreadId_t can; /* CAN任务 */
        osThreadId_t disp; /* ADC任务 */
        osThreadId_t pc; /* PC任务 */
        osThreadId_t monitor; /* 监控任务 */
    } thread;
  
    struct {
        struct {
            struct {
              osMessageQueueId_t sick;
            } output;
            struct {
              osMessageQueueId_t sick;
            } feedback;
          } can;

        osMessageQueueId_t pc; /* PC消息队列 */
    } msgq;
  

    struct {
        uint32_t can; /* CAN使用 */
        uint32_t disp; /* ADC使用 */
        uint32_t pc; /* PC使用 */
        uint32_t monitor; /* 监控使用 */
    } heap_water_mark; /* heap使用 */

    struct {
        float can; /* CAN任务运行频率 */
        float disp; /* ADC任务运行频率 */
        float pc; /* PC任务运行频率 */
        float monitor; /* 监控任务运行频率 */
    } freq; /* 任务运行频率 */
  
    struct {
        uint32_t can; /* CAN任务运行时间 */
        uint32_t disp; /* ADC任务运行时间 */
        uint32_t pc; /* PC任务运行时间 */
        uint32_t monitor; /* 监控任务运行时间 */
    } last_up_time; /* 任务最近运行时间 */
  } Task_Runtime_t;
  


// 任务频率和初始化延时
#define TASK_FREQ_CAN (100u)
#define TASK_FREQ_DISP (1u)
#define TASK_FREQ_MONITOR (1u)
#define TASK_FREQ_PC (100u)


#define TASK_INIT_DELAY_INFO (500u)

// 任务句柄
typedef struct {
    osThreadId_t can;
    osThreadId_t disp;
    osThreadId_t monitor;
    osThreadId_t pc;
} Task_Handles_t;

extern Task_Runtime_t task_runtime;


extern const osThreadAttr_t attr_init;

extern const osThreadAttr_t attr_can;
extern const osThreadAttr_t attr_disp;
extern const osThreadAttr_t attr_monitor;
extern const osThreadAttr_t attr_pc;

void Task_Init(void *argument);
void Task_Can(void *argument);
void Task_Disp(void *argument);
void Task_Monitor(void *argument);
void Task_PC(void *argument);

#ifdef __cplusplus
}
#endif
