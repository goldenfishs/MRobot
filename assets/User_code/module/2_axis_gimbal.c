/*
 * 云台模组
 */

/* Includes ----------------------------------------------------------------- */
#include "bsp/can.h"
#include "bsp/time.h"
#include "component/filter.h"
#include "component/pid.h"
#include "device/motor_dm.h"
#include "device/motor_rm.h"
#include "gimbal.h"
#include <math.h>

/* Private typedef ---------------------------------------------------------- */
/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private variables -------------------------------------------------------- */
/* Private function  -------------------------------------------------------- */

/**
 * \brief 设置云台模式
 *
 * \param c 包含云台数据的结构体
 * \param mode 要设置的模式
 *
 * \return 函数运行结果
 */
static int8_t Gimbal_SetMode(Gimbal_t *g, Gimbal_Mode_t mode) {
  if (g == NULL)
    return -1;
  if (mode == g->mode)
    return GIMBAL_OK;

  PID_Reset(&g->pid.yaw_angle);
  PID_Reset(&g->pid.yaw_omega);
  PID_Reset(&g->pid.pit_angle);
  PID_Reset(&g->pid.pit_omega);
  LowPassFilter2p_Reset(&g->filter_out.yaw, 0.0f);
  LowPassFilter2p_Reset(&g->filter_out.pit, 0.0f);

  MOTOR_DM_Enable(&(g->param->yaw_motor));

  AHRS_ResetEulr(&(g->setpoint.eulr)); /* 切换模式后重置设定值 */
  // if (g->mode == GIMBAL_MODE_RELAX) {
  //   if (mode == GIMBAL_MODE_ABSOLUTE) {
  //     g->setpoint.eulr.yaw = g->feedback.imu.eulr.yaw;
  //   } else if (mode == GIMBAL_MODE_RELATIVE) {
  //     g->setpoint.eulr.yaw = g->feedback.imu.eulr.yaw;
  //   }
  // }
  g->setpoint.eulr.pit = g->feedback.imu.eulr.rol;
  g->setpoint.eulr.yaw = g->feedback.imu.eulr.yaw;

  g->mode = mode;
  return 0;
}

/* Exported functions ------------------------------------------------------- */

/**
 * \brief 初始化云台
 *
 * \param g 包含云台数据的结构体
 * \param param 包含云台参数的结构体指针
 * \param target_freq 任务预期的运行频率
 *
 * \return 函数运行结果
 */
int8_t Gimbal_Init(Gimbal_t *g, const Gimbal_Params_t *param,
                   float target_freq) {
  if (g == NULL)
    return -1;

  g->param = param;
  g->mode = GIMBAL_MODE_RELAX; /* 设置默认模式 */

  /* 初始化云台电机控制PID和LPF */
  PID_Init(&(g->pid.yaw_angle), KPID_MODE_NO_D, target_freq,
           &(g->param->pid.yaw_angle));
  PID_Init(&(g->pid.yaw_omega), KPID_MODE_CALC_D, target_freq,
           &(g->param->pid.yaw_omega));
  PID_Init(&(g->pid.pit_angle), KPID_MODE_NO_D, target_freq,
           &(g->param->pid.pit_angle));
  PID_Init(&(g->pid.pit_omega), KPID_MODE_CALC_D, target_freq,
           &(g->param->pid.pit_omega));

  LowPassFilter2p_Init(&g->filter_out.yaw, target_freq,
                       g->param->low_pass_cutoff_freq.out);
  LowPassFilter2p_Init(&g->filter_out.pit, target_freq,
                       g->param->low_pass_cutoff_freq.out);
  g->limit.yaw.max = g->param->mech_zero.yaw + g->param->travel.yaw;
  g->limit.yaw.min = g->param->mech_zero.yaw;
  g->limit.pit.max = g->param->mech_zero.pit + g->param->travel.pit;
  g->limit.pit.min = g->param->mech_zero.pit;
  BSP_CAN_Init();

  MOTOR_RM_Register(&(g->param->pit_motor));
  MOTOR_DM_Register(&(g->param->yaw_motor));

  MOTOR_DM_Enable(&(g->param->yaw_motor));
  return 0;
}

/**
 * \brief 通过CAN设备更新云台反馈信息
 *
 * \param gimbal 云台
 * \param can CAN设备
 *
 * \return 函数运行结果
 */
int8_t Gimbal_UpdateFeedback(Gimbal_t *gimbal) {
  if (gimbal == NULL)
    return -1;

  /* 更新RM电机反馈数据（pitch轴） */
  MOTOR_RM_Update(&(gimbal->param->pit_motor));
  MOTOR_RM_t *rm_motor = MOTOR_RM_GetMotor(&(gimbal->param->pit_motor));
  if (rm_motor != NULL) {
    gimbal->feedback.motor.pit = rm_motor->feedback;
  }

  /* 更新DM电机反馈数据（yaw轴） */
  MOTOR_DM_Update(&(gimbal->param->yaw_motor));
  MOTOR_DM_t *dm_motor = MOTOR_DM_GetMotor(&(gimbal->param->yaw_motor));
  if (dm_motor != NULL) {
    gimbal->feedback.motor.yaw = dm_motor->motor.feedback;
  }

  return 0;
}

int8_t Gimbal_UpdateIMU(Gimbal_t *gimbal, const Gimbal_IMU_t *imu) {

  if (gimbal == NULL) {
    return -1;
  }
  gimbal->feedback.imu.gyro = imu->gyro;
  gimbal->feedback.imu.eulr = imu->eulr;
}

/**
 * \brief 运行云台控制逻辑
 *
 * \param g 包含云台数据的结构体
 * \param g_cmd 云台控制指令
 *
 * \return 函数运行结果
 */
int8_t Gimbal_Control(Gimbal_t *g, Gimbal_CMD_t *g_cmd) {
  if (g == NULL || g_cmd == NULL) {
    return -1;
  }

  g->dt = (BSP_TIME_Get_us() - g->lask_wakeup) / 1000000.0f;
  g->lask_wakeup = BSP_TIME_Get_us();

  Gimbal_SetMode(g, g_cmd->mode);

  /* 处理yaw控制命令，软件限位 - 使用电机绝对角度 */
  float delta_yaw = g_cmd->delta_yaw * g->dt * 1.5f;
  if (g->param->travel.yaw > 0) {
    /* 计算当前电机角度与IMU角度的偏差 */
    float motor_imu_offset =
        g->feedback.motor.yaw.rotor_abs_angle - g->feedback.imu.eulr.yaw;
    /* 处理跨越±π的情况 */
    if (motor_imu_offset > M_PI)
      motor_imu_offset -= M_2PI;
    if (motor_imu_offset < -M_PI)
      motor_imu_offset += M_2PI;

    /* 计算到限位边界的距离 */
    const float delta_max = CircleError(
        g->limit.yaw.max, (g->setpoint.eulr.yaw + motor_imu_offset + delta_yaw),
        M_2PI);
    const float delta_min = CircleError(
        g->limit.yaw.min, (g->setpoint.eulr.yaw + motor_imu_offset + delta_yaw),
        M_2PI);

    /* 限制控制命令 */
    if (delta_yaw > delta_max)
      delta_yaw = delta_max;
    if (delta_yaw < delta_min)
      delta_yaw = delta_min;
  }
  CircleAdd(&(g->setpoint.eulr.yaw), delta_yaw, M_2PI);

  /* 处理pitch控制命令，软件限位 - 使用电机绝对角度 */
  float delta_pit = g_cmd->delta_pit * g->dt;
  if (g->param->travel.pit > 0) {
    /* 计算当前电机角度与IMU角度的偏差 */
    float motor_imu_offset =
        g->feedback.motor.pit.rotor_abs_angle - g->feedback.imu.eulr.rol;
    /* 处理跨越±π的情况 */
    if (motor_imu_offset > M_PI)
      motor_imu_offset -= M_2PI;
    if (motor_imu_offset < -M_PI)
      motor_imu_offset += M_2PI;

    /* 计算到限位边界的距离 */
    const float delta_max = CircleError(
        g->limit.pit.max, (g->setpoint.eulr.pit + motor_imu_offset + delta_pit),
        M_2PI);
    const float delta_min = CircleError(
        g->limit.pit.min, (g->setpoint.eulr.pit + motor_imu_offset + delta_pit),
        M_2PI);

    /* 限制控制命令 */
    if (delta_pit > delta_max)
      delta_pit = delta_max;
    if (delta_pit < delta_min)
      delta_pit = delta_min;
  }
  CircleAdd(&(g->setpoint.eulr.pit), delta_pit, M_2PI);

  /* 控制相关逻辑 */
  float yaw_omega_set_point, pit_omega_set_point;
  switch (g->mode) {
  case GIMBAL_MODE_RELAX:
    g->out.yaw = 0.0f;
    g->out.pit = 0.0f;
    break;

  case GIMBAL_MODE_ABSOLUTE:
    yaw_omega_set_point = PID_Calc(&(g->pid.yaw_angle), g->setpoint.eulr.yaw,
                                   g->feedback.imu.eulr.yaw, 0.0f, g->dt);
    g->out.yaw = PID_Calc(&(g->pid.pit_omega), yaw_omega_set_point,
                          g->feedback.imu.gyro.z, 0.f, g->dt);

    pit_omega_set_point = PID_Calc(&(g->pid.pit_angle), g->setpoint.eulr.pit,
                                   g->feedback.imu.eulr.rol, 0.0f, g->dt);
    g->out.pit = PID_Calc(&(g->pid.pit_omega), pit_omega_set_point,
                          g->feedback.imu.gyro.y, 0.f, g->dt);

    break;

    /* 输出滤波 */
    g->out.yaw = LowPassFilter2p_Apply(&g->filter_out.yaw, g->out.yaw);
    g->out.pit = LowPassFilter2p_Apply(&g->filter_out.pit, g->out.pit);

    return 0;
  }
}

/**
 * \brief 云台输出
 *
 * \param s 包含云台数据的结构体
 * \param out CAN设备云台输出结构体
 */
void Gimbal_Output(Gimbal_t *g) {
  MOTOR_RM_SetOutput(&g->param->pit_motor, g->out.pit);
  MOTOR_MIT_Output_t output = {0};
  output.torque = g->out.yaw * 5.0f; // 乘以减速比
  output.kd = 0.3f;
  MOTOR_RM_Ctrl(&g->param->pit_motor);
  MOTOR_DM_MITCtrl(&g->param->yaw_motor, &output);
}
