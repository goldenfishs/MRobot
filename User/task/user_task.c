#include "task/user_task.h"

Task_Runtime_t task_runtime;

// 定义任务属性
const osThreadAttr_t attr_init = {
    .name = "Task_Init",
    .priority = osPriorityRealtime,
    .stack_size = 256 * 4,
};

const osThreadAttr_t attr_can = {
    .name = "Task_Can",
    .priority = osPriorityRealtime,
    .stack_size = 128 * 4,
};

const osThreadAttr_t attr_disp = {
    .name = "Task_Disp",
    .priority = osPriorityRealtime,
    .stack_size = 1024 * 4,
};

const osThreadAttr_t attr_monitor = {
    .name = "Task_Monitor",
    .priority = osPriorityRealtime,
    .stack_size = 128 * 4,
};

const osThreadAttr_t attr_pc = {
    .name = "Task_PC",
    .priority = osPriorityRealtime,
    .stack_size = 128 * 4,
};
