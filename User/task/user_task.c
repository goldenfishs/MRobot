#include "task/user_task.h"

Task_Runtime_t task_runtime;

const osThreadAttr_t attr_init = {
    .name = "Task_Init",
    .priority = osPriorityRealtime,
    .stack_size = 256 * 4,
};

//用户自定义任务

const osThreadAttr_t attr_user_task = {
    .name = "Task_User",
    .priority = osPriorityRealtime,
    .stack_size = 128 * 4,
};
