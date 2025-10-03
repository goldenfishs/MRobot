/*
 * 配置相关
 */

/* Includes ----------------------------------------------------------------- */
#include "module/config.h"


/* Private typedef ---------------------------------------------------------- */
/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private variables -------------------------------------------------------- */

/* Exported variables ------------------------------------------------------- */

// 机器人参数配置
Config_RobotParam_t robot_config = {


};

/* Private function prototypes ---------------------------------------------- */
/* Exported functions ------------------------------------------------------- */

/**
 * @brief 获取机器人配置参数
 * @return 机器人配置参数指针
 */
Config_RobotParam_t* Config_GetRobotParam(void) {
    return &robot_config;
}