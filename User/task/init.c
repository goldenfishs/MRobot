/*
  初始化任务
*/

/* Includes ----------------------------------------------------------------- */
#include "task\user_task.h"
#include "device\can.h"
/* Private typedef ---------------------------------------------------------- */
/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private variables -------------------------------------------------------- */

/* Private function --------------------------------------------------------- */
/* Exported functions ------------------------------------------------------- */

/**
 * \brief 初始化
 *
 * \param argument 未使用
 */
void Task_Init(void *argument) {
  (void)argument; /* 未使用argument，消除警告 */

  osKernelLock(); // 锁定内核，防止任务切换

  // 创建任务，确保任务创建成功
  task_runtime.thread.disp = osThreadNew(Task_Disp, NULL, &attr_disp);
  task_runtime.thread.can = osThreadNew(Task_Can, NULL, &attr_can);
  task_runtime.thread.monitor = osThreadNew(Task_Monitor, NULL, &attr_monitor);
  task_runtime.thread.pc = osThreadNew(Task_PC, NULL, &attr_pc);

  //创建消息队列
  task_runtime.msgq.can.feedback.sick = osMessageQueueNew(2u, sizeof(CAN_t), NULL);
  task_runtime.msgq.pc = osMessageQueueNew(2u, sizeof(CAN_t), NULL);
  
  osKernelUnlock(); // 解锁内核
  osThreadTerminate(osThreadGetId()); // 任务完成后结束自身
}

