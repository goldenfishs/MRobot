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

/**
 * @brief 机器人参数配置
 * @note 在此配置机器人参数
 */
Config_RobotParam_t robot_config = {
    /* USER CODE BEGIN robot_config */
    .example_param = 0,  // 示例参数初始化
    
    // 在此添加您的配置参数初始化
    
    /* USER CODE END robot_config */
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