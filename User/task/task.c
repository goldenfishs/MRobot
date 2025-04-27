/*
    {{task_name}} Task
*/

/* Includes ----------------------------------------------------------------- */
#include "task\user_task.h"

/* Private typedef ---------------------------------------------------------- */
/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private variables -------------------------------------------------------- */
/* Private function --------------------------------------------------------- */
/* Exported functions ------------------------------------------------------- */

/**
 * \brief {{task_name}} Task
 *
 * \param argument 未使用
 */
void {{task_function}}(void *argument) {
  (void)argument; /* 未使用argument，消除警告 */

  /* 计算任务运行到指定频率需要等待的tick数 */
  const uint32_t delay_tick = osKernelGetTickFreq() / {{task_frequency}};

  osDelay({{task_delay}}); /* 延时一段时间再开启任务 */

  uint32_t tick = osKernelGetTickCount(); /* 控制任务运行频率的计时 */
  while (1) {
    /* 记录任务所使用的的栈空间 */
    task_runtime.stack_water_mark.{{task_variable}} = osThreadGetStackSpace(osThreadGetId());

    tick += delay_tick; /* 计算下一个唤醒时刻 */
    
    /*User code begin*/

    /*User code end*/

    osDelayUntil(tick); /* 运行结束，等待下一次唤醒 */
  }
}