/*
  atti_esti Task
  带有pwm温控的纯陀螺仪（BMI088）姿态解算任务（无磁力计，赛场环境一般不适用）。
  控制IMU加热到指定温度防止温漂，收集IMU数据给AHRS算法。
  收集BMI088的数据，解算后得到四元数，转换为欧拉角之后放到消息队列中，
  等待其他任务取用。
  陀螺仪使用前需要校准，校准结果保存在bmi088_cali结构体中，需要自行实现。
*/

/* Includes ----------------------------------------------------------------- */
#include "task/user_task.h"
/* USER INCLUDE BEGIN */

#include "bsp/mm.h"
#include "bsp/pwm.h"
#include "component/ahrs.h"
#include "component/pid.h"
#include "device/bmi088.h"
/* USER INCLUDE END */

/* Private typedef ---------------------------------------------------------- */
/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private variables -------------------------------------------------------- */
/* USER STRUCT BEGIN */
BMI088_t bmi088;
AHRS_t gimbal_ahrs;
AHRS_Magn_t magn;
AHRS_Eulr_t eulr_to_send;
KPID_t imu_temp_ctrl_pid;

/*默认校准参数*/
BMI088_Cali_t cali_bmi088 = {
    .gyro_offset = {0.0f, 0.0f, 0.0f},
};

static const KPID_Params_t imu_temp_ctrl_pid_param = {
    .k = 0.15f,
    .p = 1.0f,
    .i = 0.0f,
    .d = 0.0f,
    .i_limit = 1.0f,
    .out_limit = 1.0f,
};

/* USER STRUCT END */

/* Private function --------------------------------------------------------- */
/* Exported functions ------------------------------------------------------- */
void Task_atti_esti(void *argument) {
  (void)argument; /* 未使用argument，消除警告 */

  
  osDelay(ATTI_ESTI_INIT_DELAY); /* 延时一段时间再开启任务 */

  /* USER CODE INIT BEGIN */
  BMI088_Init(&bmi088, &cali_bmi088);
  AHRS_Init(&gimbal_ahrs, &magn, BMI088_GetUpdateFreq(&bmi088));
  PID_Init(&imu_temp_ctrl_pid, KPID_MODE_NO_D,
           1.0f / BMI088_GetUpdateFreq(&bmi088), &imu_temp_ctrl_pid_param);
  BSP_PWM_Start(BSP_PWM_IMU_HEAT);

  /* USER CODE INIT END */

  while (1) {
    /* USER CODE BEGIN */
    BMI088_WaitNew();
    BMI088_AcclStartDmaRecv();
    BMI088_AcclWaitDmaCplt();

    BMI088_GyroStartDmaRecv();
    BMI088_GyroWaitDmaCplt();

    /* 锁住RTOS内核防止数据解析过程中断，造成错误 */
    osKernelLock();
    /* 接收完所有数据后，把数据从原始字节加工成方便计算的数据 */
    BMI088_ParseAccl(&bmi088);
    BMI088_ParseGyro(&bmi088);

    /* 根据设备接收到的数据进行姿态解析 */
    AHRS_Update(&gimbal_ahrs, &bmi088.accl, &bmi088.gyro, &magn);

    /* 根据解析出来的四元数计算欧拉角 */
    AHRS_GetEulr(&eulr_to_send, &gimbal_ahrs);
    osKernelUnlock();

    /* 在此处用消息队列传递imu数据 */
    /* osMessageQueuePut( ... ); */
  
    /* 控制IMU加热器 */
    BSP_PWM_SetComp(BSP_PWM_IMU_HEAT, PID_Calc(&imu_temp_ctrl_pid, 40.5f,
                                               bmi088.temp, 0.0f, 0.0f));
    /* USER CODE END */
  }
  
}