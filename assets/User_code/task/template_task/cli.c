/*
    cli Task
    
*/

/* Includes ----------------------------------------------------------------- */
#include "task/user_task.h"
/* USER INCLUDE BEGIN */
#include "device/mrobot.h"
/* USER INCLUDE END */

/* Private typedef ---------------------------------------------------------- */
/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private variables -------------------------------------------------------- */
/* USER STRUCT BEGIN */

/* USER STRUCT END */

/* Private function --------------------------------------------------------- */
/* USER PRIVATE CODE BEGIN */
/**
 * @brief hello 命令回调
 * @note 命令回调必须返回 0 (pdFALSE) 表示完成，返回非0会继续调用
 */
static long Cli_Hello(char *buffer, size_t size, const char *cmd) {
  (void)cmd; /* 未使用cmd，消除警告 */
  MRobot_Snprintf(buffer, size, "Ciallo～(∠・ω< )⌒★\r\n");
  return 0;  /* 返回0表示命令执行完成 */
}
/* USER PRIVATE CODE END */
/* Exported functions ------------------------------------------------------- */
void Task_cli(void *argument) {
  (void)argument; /* 未使用argument，消除警告 */

  
  osDelay(CLI_INIT_DELAY); /* 延时一段时间再开启任务 */

  /* USER CODE INIT BEGIN */
  /* 初始化 MRobot CLI 系统 */
  MRobot_Init();
  MRobot_RegisterCommand("hello", " --hello: 打印问候语\r\n", Cli_Hello, -1);
  /* USER CODE INIT END */

  while (1) {
    /* USER CODE BEGIN */
    /* 运行 MRobot 主循环 */
    MRobot_Run();
    /* USER CODE END */
  }
  
}