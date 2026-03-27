#pragma once

#ifdef __cplusplus
extern "C"
{
#endif

#include "struct_typedef.h"
#include "component/filter.h"
#include "component/pid.h"
#include "component/ahrs.h"
//#include "device/buzzer.h"
#include "component/user_math.h"
#include "component/filter.h"
#include "device/motor_rm.h"

typedef struct {
    float max_velocity;
    float acceleration;
    float deceleration;
} TrapezoidalProfile;

#define CHASSIS_OK (0)
#define CHASSIS_ERR (-1)
#define CHASSIS_ERR_NULL (-2)
#define CHASSIS_ERR_MODE (-3) /*CMD_ChassisMode_t */
#define CHASSIS_ERR_TYPE (-4) /*Chassis_Type_t */


//     纵向/横向
#define radians atan(1.0f * 390 /390) // 角度制


/*底盘姿态模式*/
typedef enum
{
	STOP_MODE,/* 急停模式 */
	EXPAND_MODE,/* 展开模式 */
  REDUCE_MODE,/* 收缩模式 */
} CHASSIS_ATTITUDE_MODE_t;

/*底盘状态*/
typedef enum
{
	STOP_STATE,/* 急停状态 */
	EXPAND_STATE,/* 展开状态 */
  REDUCE_STATE,/* 收缩状态 */
} CHASSIS_STATE_t;

/*底盘模式*/
typedef enum
{
    STOP, // 底盘平行
    RC,   // 遥控模式
    CHASSIS_MODE_BREAK, /* 刹车模式，电机闭环控制保持静止。用于机器人停止状态 */
     CHASSIS_MODE_RELAX, /* 放松模式，电机不输出。一般情况底盘初始化之后的模式 */
     CHASSIS_MODE_FOLLOW_GIMBAL, /* 通过闭环控制使车头方向跟随云台 */
     CHASSIS_MODE_ROTOR, /* 小陀螺模式，通过闭环控制使底盘不停旋转 */
    
} Chassis_Mode_t;

typedef struct
{
    int cmd_power_on_safe; // 上电安全标志
    Chassis_Mode_t mode;
		CHASSIS_ATTITUDE_MODE_t attitude_mode;
    // 遥控器输出值
    fp32 Vx;      
    fp32 Vy;
    fp32 Vw;
    fp32 throttle;

    fp32 x_l;
    fp32 y_l;
} Chassis_CMD_t;

	// 四个舵轮的安装误差
	typedef struct
	{
		fp32 MOTOR_OFFSET[4];
	} MotorOffset_t;
	
	typedef struct
	{
		fp32 TELESCOPE_MOTOR_OFFSET[2];
	} TelescopeMotorOffset_t;
	
	typedef struct
	{
		/*可通过该枚举类型来决定Imu的数据量纲*/
		enum
		{
			IMU_DEGREE, // 角度值（0-360）
			IMU_RADIAN	// 弧度制（0-2pi)
		} angle_mode;

//		AHRS_Eulr_t imu_eulr; // 解算后存放欧拉角（弧度制）
	} ChassisImu_t;

	/*底盘参数结构体*/
	typedef struct
	{
		
	


		struct{
		/*该部分决定PID的参数整定在config中修改*/
		KPID_Params_t Radder_DIR_Omega;
		KPID_Params_t Radder_DIR_Angle;
		KPID_Params_t Wheel_DIR_Omega;
		KPID_Params_t chassis_follow_gimbal;
		}pid;
		
		struct{
		MOTOR_RM_Param_t Wheel_DIR[4]; // 四个轮向电机
		MOTOR_RM_Param_t Radder_DIR[4]; // 四个舵向电机
		MOTOR_RM_Param_t chassis_follow_gimbal; // 底盘跟随云台

		}motor;
		float mech_zero;/*云台6020的机械中点*/
		float travel ;/*云台6020的机械行程*/
		float mech_zero_4310;/*云台4310的机械中点*/
	} Chassis_Param_t;

	typedef struct
	{
		fp32 Vx;
		fp32 Vy;
		fp32 Vw;
		fp32 mul; // 油门倍率
	} ChassisMove_Vec;

	typedef struct
	{
		float Wheel_DIR[4];
		float Radder_DIR[4];
	} Chassis_out_t;

	typedef struct
	{
		
		uint32_t last_wakeup;
		float dt;
		float chassis6020_detangle[4];
		Chassis_Mode_t mode;
		ChassisMove_Vec move_vec; // 最终输入速度
		TrapezoidalProfile telescope_profile; 		
		/* 设立角度和跟随角度 */
		float Set_TelescopeAngle;
		float Last_Set_TelescopeAngle;		
		float Follow_TelescopeAngle;		
		float feedfrward;
		float Telescope_err;
		/*期望的底盘输出值(此处为舵轮解算出的各个电机的期望输出值)ֵ*/
		struct{
		uint32_t last_wakeup;
		float dt;
		}accl_time;
		
		struct
		{
			fp32 Wheel_DIR_Solving_1[4];
			fp32 Wheel_DIR_Solving_2[4];
			fp32 Radder_DIR_Solving_1[4];
			fp32 Radder_DIR_Solving_2[4];
			// fp32 rotor6020_elur_yaw;

			fp32 Radder_DIR_target[4];
			fp32 Wheel_DIR_target[4];

		} hopemotorout;

		struct
		{
			fp32 final_Telescope;
			fp32 final_Radder_DIR[4];
			fp32 final_Wheel_DIR[4];
		} final_out;
		/* 原始数据 */
		struct
		{
			struct{				

				MOTOR_Feedback_t Wheel_DIR[4]; // 四个轮向电机
				MOTOR_Feedback_t Radder_DIR[4];
				MOTOR_Feedback_t gimbal_yaw;
			}motor;
			/* 转化数据 */
			struct{	
			
				float Radder_DIR_Angle[4];				
				float Radder_DIR_Omega[4];				
				float Wheel_DIR_Angle[4];				
				float Wheel_DIR_Omega[4];		
			}motor_transformation;			
			
		} feedback;

		struct
		{	
			KPID_t Radder_DIR_angle[4];
			KPID_t Radder_DIR_omega[4];
			KPID_t Wheel_DIR_omega[4];
			KPID_t chassis_follow_gimbal_pid;
		} pid;

		uint8_t keeping_angle_flag; // 是否处于保持角度模式

		// AHRS_Eulr_t set_point; // 底盘纠正目标角
		// fp32 angle_current;	   // 当前角度
		// fp32 angle_piancha;	   // 偏差角度
		// fp32 yaw_out;		   // 角度pid输出值

		ChassisImu_t pos088;		 // 088的实时姿态
		MotorOffset_t motoroffset;	 // 5065校准数据
		TelescopeMotorOffset_t telescope_motor_offset;
		
		
		Chassis_Param_t *param;		 // 一些固定的参数
		LowPassFilter2p_t filled[11]; // 低通滤波器
		LowPassFilter2p_t accl_filled[2]; // 加速度滤波器		
		float keep_angle[4];		 // 保持的 舵向 角度

		Chassis_out_t out;

		float wz_multi; /* 小陀螺模式旋转方向 */
		float mech_zero;/*云台6020的机械中点*/
		float travel ;/*云台6020的机械行程*/
//		float mech_zero_4310;/*云台4310的机械中点*/
	} Chassis_t;


	int8_t chassis_init(Chassis_t *c,  Chassis_Param_t *param, float target_freq);
	int8_t Chassis_update(Chassis_t *c);
	int8_t Chassis_Control(Chassis_t *c,  Chassis_CMD_t *c_cmd,uint32_t now);
	void Chassis_Setoutput(Chassis_t *c);
#ifdef __cplusplus
}
#endif
