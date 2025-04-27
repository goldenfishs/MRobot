/*
  初始化任务
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
 * \brief 初始化
 *
 * \param argument 未使用
 */
void Task_Init(void *argument) {
  (void)argument; /* 未使用argument，消除警告 */

  osKernelLock(); // 锁定内核，防止任务切换

  task_runtime.thread.user_task = osThreadNew(Task_UserTask, NULL, &attr_user_task);

  //创建消息队列
  task_runtime.msgq.user_msg= osMessageQueueNew(2u, 10, NULL);

  osKernelUnlock(); // 解锁内核
  osThreadTerminate(osThreadGetId()); // 任务完成后结束自身
}

