
/*
 底盘任务
*/
/*
舵轮底盘模组
example：
Chassis_t chassis;
Chassis_CMD_t cmd_chassis;

chassis_init(&chassis,&Config_GetRobotParam()->chassis,CHASSIS_FREQ);

 osMessageQueueGet(task_runtime.msgq.imu.eulr, &chassis.pos088.imu_eulr, NULL, 0);
 osMessageQueueGet(task_runtime.msgq.imu.gyro, &chassis.pos088.bmi088.gyro, NULL, 0);
 这个是用来调防翻的，可以不用，而且需要c板放在地盘不能在云台上面

 osMessageQueueGet(task_runtime.msgq.gimbal.yaw6020,&chassis.motorfeedback.gimbal_yaw_encoder,NULL,0);
    
    if(osMessageQueueGet(task_runtime.msgq.cmd.chassis, &cmd_chassis, NULL, 0)==osOK)
    {
      Chassis_update(&chassis);
      Chassis_Control(&chassis, &cmd_chassis,tick);
    }else
{
	 Chassis_CMD_t safe_cmd = {.mode = STOP, .Vx = 0, .Vy = 0, .Vw = 0};
    Chassis_Control(&chassis, &safe_cmd);
}
    Chassis_Setoutput(&chassis);


*/



/* Includes ----------------------------------------------------------------- */
#include "chassis.h"
#include "device/motor_rm.h"
#include "bsp/time.h"
#include "bsp/can.h"
#include "math.h"
#include "component/pid.h"
#include "component/filter.h"
#include "stdlib.h"
/*舵轮舵向校准方法：注释掉关于6020反馈角度的处理以及6020数据的发送这两处(define.h里有快捷方法)，
进debug将四个轮子编码器朝右（左右无所谓，可能会导致5065方向反，在解算里加个负号就行）
查看6020反馈值，将6020反馈值放入motor_offset中*/

/*chassis_t结构体中的内容现在有 move_vec (最终输出速度)
hopemotorout(期望的底盘输出值)舵轮解算出的各个电机的期望输出值 包括四个6020 和四个3508
final_out;(经PID计算后的实际发送给电机的实时输出值)  四个6020 四个3508
motorfeedback(电机反馈数据) 四个3508 四个6020
pid 各个电机的pid参数
ChassisImu_t pos088;  088的实时姿态
 MotorOffset_t motoroffset;	      //6020校准数据
const	Chassis_Param_t *param;     //一些固定的参数
fp32 vofa_send[8];                //vofa输出数据
  LowPassFilter2p_t filled[9];      //低通滤波器
  float keep_angle[4];              // 保持的 6020 角度
*/

/* Private typedef ---------------------------------------------------------- */
#define CHASSIS_ROTOR_OMEGA 0.001
#define CHASSIS_ROTOR_WZ_MIN 0.6f          /* 小陀螺旋转位移下界 */
#define CHASSIS_ROTOR_WZ_MAX 0.8f          /* 小陀螺旋转位移上界 */
#define ONE_MINUTE 60.0f          /* 一分钟时间 */

static int8_t Chassis_SetMode(Chassis_t *c, Chassis_Mode_t mode ,uint32_t now)
{
  if (c == NULL)
    return CHASSIS_ERR_NULL; /* 主结构体不能为空 */
  if (mode == c->mode) return CHASSIS_OK; /* 模式未改变直接返回 */

 if (mode == CHASSIS_MODE_ROTOR && c->mode != CHASSIS_MODE_ROTOR) {
    srand(now);
    c->wz_multi =1;
    // c->wz_multi = (rand() % 2) ? -1 : 1;
  }
  for (int i = 0; i < 4; i++)
  {
    PID_Reset(&c->pid.Radder_DIR_omega[i]);
    PID_Reset(&c->pid.Radder_DIR_angle[i]);
    PID_Reset(&c->pid.Wheel_DIR_omega[i]);
    PID_Reset(&c->pid.Radder_DIR_omega[i]);		
  }
  c->mode = mode;
  return CHASSIS_OK;
}

/**
 * @brief 产生小陀螺wz随机速度
 *
 * @param min wz产生最小速度
 * @param max wz产生最大速度
 * @param now ctrl_chassis的tick数
 * @return float
 */
static float Chassis_CalcWz(const float min, const float max, uint32_t now) {
  /* wz在min和max之间，上限0.6f */
  float wz_vary = fabs(0.2f * sinf(CHASSIS_ROTOR_OMEGA * (float)now)) + min;
  return wz_vary > 0.8f ? max : wz_vary;
}

/*底盘初始化*/

int8_t chassis_init(Chassis_t *c, Chassis_Param_t *param, float target_freq)
{
  if (c == NULL || param == NULL || target_freq <= 0.0f)
  {
    return CHASSIS_ERR; // 参数错误
  }
  c->param = param;
  c->mode = CHASSIS_MODE_RELAX; // 默认模式为停止锁死底盘
  c->mech_zero = c->param->mech_zero;/*云台6020的机械中点*/
  c->travel = c->param->travel ;/*云台6020的机械行程*/
//  c->mech_zero_4310 = c->param->mech_zero_4310;/*云台4310的机械中点*/
  /*初始化can*/
  BSP_CAN_Init();
  /*注册轮向电机*/
  for (int i = 0; i < 4; i++)
  {
    MOTOR_RM_Register(&(c->param->motor.Wheel_DIR[i]));
  }
  /*注册舵向电机*/
  for (int i = 0; i < 4; i++)
  {
    MOTOR_RM_Register(&(c->param->motor.Radder_DIR[i]));
  }

  // 舵轮安装时的6020机械误差，机械校准时1号轮在左前方，所有轮的编码器朝向右面
  MotorOffset_t motor_offset = {{5.24851561/M_PI * 180.0f, 1.00092244/ M_PI * 180.0f, 
                                 5.8199234/ M_PI * 180.0f, 4.74536991/ M_PI * 180.0f}}; // 右右右右
  c->motoroffset = motor_offset;
																 
																 
																 
  /*对3508的速度环和6020的角速度以及位置环pid进行初始化*/
  for (int i = 0; i < 4; i++)
  {
    PID_Init(&c->pid.Wheel_DIR_omega[i], KPID_MODE_NO_D, target_freq, &c->param->pid.Wheel_DIR_Omega);
  }
  for (int i = 0; i < 4; i++)
  {
    PID_Init(&c->pid.Radder_DIR_omega[i], KPID_MODE_CALC_D, target_freq, &c->param->pid.Radder_DIR_Omega);
    PID_Init(&c->pid.Radder_DIR_angle[i], KPID_MODE_CALC_D, target_freq, &c->param->pid.Radder_DIR_Angle);
  }

  LowPassFilter2p_Init(&c->filled[0], target_freq, 20.0f); // vx
  LowPassFilter2p_Init(&c->filled[1], target_freq, 20.0f); // vy
  LowPassFilter2p_Init(&c->filled[2], target_freq, 20.0f); // vw

  LowPassFilter2p_Init(&c->filled[3], target_freq, 20.0f); // 3508-1
  LowPassFilter2p_Init(&c->filled[4], target_freq, 20.0f); // 3508-2
  LowPassFilter2p_Init(&c->filled[5], target_freq, 20.0f); // 3508-3  
  LowPassFilter2p_Init(&c->filled[6], target_freq, 20.0f); // 3508-4

  LowPassFilter2p_Init(&c->filled[7], target_freq, 20.0f); // 6020-1
  LowPassFilter2p_Init(&c->filled[8], target_freq, 20.0f); // 6020-2
  LowPassFilter2p_Init(&c->filled[9], target_freq, 20.0f); // 6020-3
  LowPassFilter2p_Init(&c->filled[10], target_freq, 20.0f); // 6020-4 
	
  return CHASSIS_OK;
}



// 底盘解算
void Chassis_speed_calculate(Chassis_t *c, Chassis_CMD_t *c_cmd)
{

  // RC模式下松开遥控器防止6020回到默认位置导致侧翻
  if (c->mode == RC && fabs(c->move_vec.Vx) < 0.1 && fabs(c->move_vec.Vy) < 0.1 && fabs(c->move_vec.Vw) < 0.1)
  {
    // 如果之前不处于保持模式，则记录当前角度
    if (!c->keeping_angle_flag)
    {
      c->keeping_angle_flag = 1; // 进入保持模式
    }
    // 使用保持的角度，而不是实时反馈值,速度为0
    for (uint8_t i = 0; i < 4; i++)
    {
      c->hopemotorout.Radder_DIR_Solving_1[i] = c->keep_angle[i];
      c->hopemotorout.Wheel_DIR_Solving_1[i] = 0;
    }
      // c->hopemotorout.Radder_DIR_Solving_1[0] = 315;
      // c->hopemotorout.Radder_DIR_Solving_1[1] = 45;
      // c->hopemotorout.Radder_DIR_Solving_1[2] = 315;
      // c->hopemotorout.Radder_DIR_Solving_1[3] = 45;
  }
  else
  {
    // 如果有速度输入，则退出保持模式
    c->keeping_angle_flag = 0;
    // 让保持角度实时等于进入保持阈值前的最后一次角度值
    for (uint8_t i = 0; i < 4; i++)
    {
     c->keep_angle[i] = c->hopemotorout.Radder_DIR_Solving_1[i];
    }
		
    switch (c->mode)
    {
    case RC:
    case CHASSIS_MODE_ROTOR:
    case CHASSIS_MODE_FOLLOW_GIMBAL:
      
      // const double radians = atan(1.0f * 330 / 330);

      c->hopemotorout.Wheel_DIR_Solving_1[0] = sqrt(
          (c->move_vec.Vx + c->move_vec.Vw * sin(radians)) * (c->move_vec.Vx + c->move_vec.Vw * sin(radians)) + (c->move_vec.Vy + c->move_vec.Vw * cos(radians)) * (c->move_vec.Vy + c->move_vec.Vw * cos(radians)));

      c->hopemotorout.Wheel_DIR_Solving_1[1] = sqrt(
          (c->move_vec.Vx + c->move_vec.Vw * sin(radians)) * (c->move_vec.Vx + c->move_vec.Vw * sin(radians)) + (c->move_vec.Vy - c->move_vec.Vw * cos(radians)) * (c->move_vec.Vy - c->move_vec.Vw * cos(radians)));

      c->hopemotorout.Wheel_DIR_Solving_1[2] = sqrt(
          (c->move_vec.Vx - c->move_vec.Vw * sin(radians)) * (c->move_vec.Vx - c->move_vec.Vw * sin(radians)) + (c->move_vec.Vy - c->move_vec.Vw * cos(radians)) * (c->move_vec.Vy - c->move_vec.Vw * cos(radians)));

      c->hopemotorout.Wheel_DIR_Solving_1[3] = sqrt(
          (c->move_vec.Vx - c->move_vec.Vw * sin(radians)) * (c->move_vec.Vx - c->move_vec.Vw * sin(radians)) + (c->move_vec.Vy + c->move_vec.Vw * cos(radians)) * (c->move_vec.Vy + c->move_vec.Vw * cos(radians)));

      c->hopemotorout.Radder_DIR_Solving_1[0] = atan2((c->move_vec.Vy + c->move_vec.Vw * cos(radians)),
                                                     (c->move_vec.Vx + c->move_vec.Vw * sin(radians))) *
                                               (180.0f / M_PI);
      c->hopemotorout.Radder_DIR_Solving_1[1] = atan2((c->move_vec.Vy - c->move_vec.Vw * cos(radians)),
                                                     (c->move_vec.Vx + c->move_vec.Vw * sin(radians))) *
                                               (180.0f / M_PI);
      c->hopemotorout.Radder_DIR_Solving_1[2] = atan2((c->move_vec.Vy - c->move_vec.Vw * cos(radians)),
                                                     (c->move_vec.Vx - c->move_vec.Vw * sin(radians))) *
                                               (180.0f / M_PI);
      c->hopemotorout.Radder_DIR_Solving_1[3] = atan2((c->move_vec.Vy + c->move_vec.Vw * cos(radians)),
                                                     (c->move_vec.Vx - c->move_vec.Vw * sin(radians))) *
                                               (180.0f / M_PI);
      break;

    case CHASSIS_MODE_BREAK:
    case STOP:
    case CHASSIS_MODE_RELAX:

      for (int i = 0; i < 4; i++)
      {
        c->hopemotorout.Wheel_DIR_Solving_1[i] = 0.0f;
      }
      //      c->hopemotorout.Radder_DIR_Solving_1[0] = 6.26554489/M_PI*180.0f;
      //      c->hopemotorout.Radder_DIR_Solving_1[1] = 2.1099906/M_PI*180.0f;
      //      c->hopemotorout.Radder_DIR_Solving_1[2] = 2.08391285/M_PI*180.0f;
      //      c->hopemotorout.Radder_DIR_Solving_1[3] = 5.26845694/M_PI*180.0f;
      // c->hopemotorout.Radder_DIR_Solving_1[0] = 315;
      // c->hopemotorout.Radder_DIR_Solving_1[1] = 45;
      // c->hopemotorout.Radder_DIR_Solving_1[2] = 315;
      // c->hopemotorout.Radder_DIR_Solving_1[3] = 45;

      c->hopemotorout.Radder_DIR_Solving_1[0] = 0;
      c->hopemotorout.Radder_DIR_Solving_1[1] = 0;
      c->hopemotorout.Radder_DIR_Solving_1[2] = 0;
      c->hopemotorout.Radder_DIR_Solving_1[3] = 0;
      break;

  
    }
  }
  // 角度归化到0°——360°

  for (uint8_t i = 0; i < 4; i++)
  {
    if (c->hopemotorout.Radder_DIR_Solving_1[i] < 0)
    {
      c->hopemotorout.Radder_DIR_Solving_1[i] += 360;
    }
  }

  for (uint8_t i = 0; i < 4; i++)
  {
    float angle_error[4]; // 角度误差
     angle_error[i] = c->hopemotorout.Radder_DIR_Solving_1[i] - c->feedback.motor_transformation.Radder_DIR_Angle[i];
    // 误差角度归化到-180°——+180°
    while (angle_error[i] > 180)
      angle_error[i] -= 360;
    while (angle_error[i] < -180)
      angle_error[i] += 360;
    /*这里发现如果下面的c->motorfeedback.rotor_angle6020[i]+angle_error[i]变为
        c->hopemotorout.Radder_DIR_Solving_1[i]会导致6020出现故障*/
    if (angle_error[i] > 90 && angle_error[i] <= 180)
    {
      c->hopemotorout.Wheel_DIR_Solving_2[i] = c->hopemotorout.Wheel_DIR_Solving_1[i];
      c->hopemotorout.Radder_DIR_Solving_2[i] = c->feedback.motor_transformation.Radder_DIR_Angle[i] + angle_error[i] - 180;
    }
    else if (angle_error[i] < -90 && angle_error[i] >= -180)
    {
      c->hopemotorout.Wheel_DIR_Solving_2[i] = c->hopemotorout.Wheel_DIR_Solving_1[i];
      c->hopemotorout.Radder_DIR_Solving_2[i] = c->feedback.motor_transformation.Radder_DIR_Angle[i] + angle_error[i] + 180;
    }
    else
    {
      c->hopemotorout.Wheel_DIR_Solving_2[i] = -c->hopemotorout.Wheel_DIR_Solving_1[i];
      c->hopemotorout.Radder_DIR_Solving_2[i] = c->feedback.motor_transformation.Radder_DIR_Angle[i] + angle_error[i];
    }
  }
}

/*
更新底盘电机反馈，并且进行归一化处理，但是这里的归一化是我自己测的电机最大转速
近似于一进行处理，并不是准确的-1到1
*/

int8_t Chassis_update(Chassis_t *c)
{
  if (c == NULL)
  {
    return CHASSIS_ERR_NULL; // 参数错误
  }

	MOTOR_RM_t *Wheel_DIR_MOTOR[4];
	MOTOR_RM_t *Radder_DIR_MOTOR[4];
  /*更新电机反馈*/
  for (int i = 0; i < 4; i++)
  {
		/* 轮向电机更新 */		
	MOTOR_RM_Update(&(c->param->motor.Wheel_DIR[i]));
	Wheel_DIR_MOTOR[i]= MOTOR_RM_GetMotor(&(c->param->motor.Wheel_DIR[i]));
	c->feedback.motor.Wheel_DIR[i] = Wheel_DIR_MOTOR[i]->feedback;

		/* 舵向电机 */		
	MOTOR_RM_Update(&(c->param->motor.Radder_DIR[i]));
	Radder_DIR_MOTOR[i]= MOTOR_RM_GetMotor(&(c->param->motor.Radder_DIR[i]));
	c->feedback.motor.Radder_DIR[i] = Radder_DIR_MOTOR[i]->feedback;
		
		
		/* 单位转换 */
	c->feedback.motor_transformation.Radder_DIR_Angle[i]=c->feedback.motor.Radder_DIR[i].rotor_abs_angle/ M_PI * 180.0f;
	c->feedback.motor_transformation.Radder_DIR_Omega[i]=	c->feedback.motor.Radder_DIR[i].rotor_speed/320;	
	c->feedback.motor_transformation.Wheel_DIR_Omega[i]=	c->feedback.motor.Wheel_DIR[i].rotor_speed/10000;
	c->feedback.motor_transformation.Radder_DIR_Angle[i] = fmod(c->feedback.motor_transformation.Radder_DIR_Angle[i] - c->motoroffset.MOTOR_OFFSET[i], 360.0);
		
		if (c->feedback.motor_transformation.Radder_DIR_Angle[i] < 0)
		{
			c->feedback.motor_transformation.Radder_DIR_Angle[i] += 360;
		}		
		 
	}


  return CHASSIS_OK;
}

// 防止侧翻
/*具体开始上车实验之后在进行编写修改，先暂时不使用*/
void ChassisrolPrevent(Chassis_t *c)
{
}

int8_t Chassis_Control(Chassis_t *c, Chassis_CMD_t *c_cmd,uint32_t now)
{

  if (c == NULL || c_cmd == NULL)
  {
    return CHASSIS_ERR_NULL; // 参数错误
  }

  // c->dt = (BSP_TIME_Get_us() - c->last_wakeup) / 1000000.0f; /* 计算两次调用的时间间隔，单位秒 */
  // c->last_wakeup = BSP_TIME_Get_us();
  c->dt = (float)(now - c->last_wakeup) / 1000.0f; /* 计算两次调用的时间间隔，单位秒 */
  c->last_wakeup = now;

  /*设置底盘模式*/
  if (Chassis_SetMode(c, c_cmd->mode,now) != CHASSIS_OK)
  {
    return CHASSIS_ERR_MODE; /* 设置模式失败 */
  }
	
	float beta;
  
  /*根据底盘模式进行不同的控制*/
  switch (c->mode)
  {
  case CHASSIS_MODE_BREAK:
  case CHASSIS_MODE_RELAX:
  case STOP:
    // 停止模式
    c->move_vec.Vx = 0.0f;
    c->move_vec.Vy = 0.0f;
    c->move_vec.Vw = 0.0f;
    break;

  case RC:
    // 遥控模式
    // c->move_vec.Vx = c_cmd->Vx * c_cmd->throttle * 1000.0f;
    // c->move_vec.Vy = c_cmd->Vy * c_cmd->throttle * 1000.0f;

    c->move_vec.Vx = c_cmd->Vx * c_cmd->throttle;
    c->move_vec.Vy = c_cmd->Vy * c_cmd->throttle;
    c->move_vec.Vw = c_cmd->Vw * c_cmd->throttle;
    c->move_vec.mul = c_cmd->throttle;
    break;

    case CHASSIS_MODE_ROTOR:
    // 小陀螺模式

    beta =  (c->feedback.motor.gimbal_yaw.rotor_abs_angle / 180.0f * M_PI) - c->mech_zero; // 云台当前角度转弧度
    float cos_beta = cosf(beta);
    float sin_beta = sinf(beta);

    c->move_vec.Vx =cos_beta * c_cmd->x_l - sin_beta * c_cmd->y_l;
    c->move_vec.Vy =sin_beta* c_cmd->x_l + cos_beta * c_cmd->y_l;
    c->move_vec.Vw =c->wz_multi* Chassis_CalcWz(CHASSIS_ROTOR_WZ_MIN,CHASSIS_ROTOR_WZ_MAX, now);
    break;

    case CHASSIS_MODE_FOLLOW_GIMBAL:
    // 跟随云台模式
    c->move_vec.Vx =-c_cmd->y_l;
    c->move_vec.Vy =-c_cmd->x_l;
    c->move_vec.Vw = PID_Calc(&c->pid.chassis_follow_gimbal_pid, 2.06f ,c->feedback.motor.gimbal_yaw.rotor_abs_angle, 0.0f, c->dt);

 //    c->move_vec.Vw = -PID_Calc(&c->pid.chassis_follow_gimbal_pid, c->motorfeedback.gimbal_yaw_encoder-2.07694483f ,c->motorfeedback.gimbal_yaw_encoder, 0.0f, c->dt);
    break;



  default:
    return CHASSIS_ERR_MODE; /* 未知模式 */
  }

  /*给输出的Vx，Vy，Vw进行滤波*/
  c->move_vec.Vx = LowPassFilter2p_Apply(&c->filled[0], c->move_vec.Vx);
  c->move_vec.Vy = LowPassFilter2p_Apply(&c->filled[1], c->move_vec.Vy);
  c->move_vec.Vw = LowPassFilter2p_Apply(&c->filled[2], c->move_vec.Vw);

  Chassis_speed_calculate(c, c_cmd);

  for (int i = 0; i < 4; i++)
  {
    float chassis6020_detangle[4]; // 6020解算出的角度                  
    c->hopemotorout.Radder_DIR_target[i] = c->hopemotorout.Radder_DIR_Solving_2[i];
    chassis6020_detangle[i] = PID_Calc(&(c->pid.Radder_DIR_angle[i]), c->hopemotorout.Radder_DIR_target[i],
																				c->feedback.motor_transformation.Radder_DIR_Angle[i], 0.0f, c->dt);
    // c->final_out.final_6020out[i] = chassis6020_detangle[i] ; //单环控制就用这个
		c->chassis6020_detangle[i]=chassis6020_detangle[i];
    c->final_out.final_Radder_DIR[i] = PID_Calc(&(c->pid.Radder_DIR_omega[i]), chassis6020_detangle[i],
                                             c->feedback.motor_transformation.Radder_DIR_Omega[i], 0.0f, c->dt);

    c->out.Radder_DIR[i] = LowPassFilter2p_Apply(&c->filled[7+i], c->final_out.final_Radder_DIR[i]);
    c->hopemotorout.Wheel_DIR_target[i] = c->hopemotorout.Wheel_DIR_Solving_2[i];
    c->final_out.final_Wheel_DIR[i] = PID_Calc(&(c->pid.Wheel_DIR_omega[i]), c->hopemotorout.Wheel_DIR_target[i],
                                             c->feedback.motor_transformation.Wheel_DIR_Omega[i], 0.0f, c->dt);
    c->out.Wheel_DIR[i] = LowPassFilter2p_Apply(&c->filled[3+i], c->final_out.final_Wheel_DIR[i]);
		
  }
  return CHASSIS_OK;
}

/*电机输出设定和发送*/
void Chassis_Setoutput(Chassis_t *c)
{
    for (uint8_t i = 0; i < 4; i++) {		
		MOTOR_RM_SetOutput(&(c->param->motor.Wheel_DIR[i]), c->out.Wheel_DIR[i]);	
		MOTOR_RM_SetOutput(&(c->param->motor.Radder_DIR[i]), c->out.Radder_DIR[i]);
    }
		MOTOR_RM_Ctrl(&(c->param->motor.Wheel_DIR[0]));	
		MOTOR_RM_Ctrl(&(c->param->motor.Radder_DIR[0]));			


}

