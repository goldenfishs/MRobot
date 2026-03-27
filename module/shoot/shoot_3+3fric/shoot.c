/*
 * far♂蛇模块
 */
 
/********************************* 使用示例 **********************************/
/*1.配置config参数以及Config_ShootInit函数参数*/
/*2.
COMP_AT9S_CMD_t shoot_ctrl_cmd_rc;
Shoot_t shoot;
Shoot_CMD_t shoot_cmd;

void Task(void *argument) {

	Config_ShootInit();
	Shoot_Init(&shoot,&Config_GetRobotParam()->shoot_param,SHOOT_CTRL_FREQ);
	Shoot_SetMode(&shoot,SHOOT_MODE_SINGLE);					关于模式选择：初始化一个模式
	
  while (1) {
  
	  shoot_cmd.online	=shoot_ctrl_cmd_rc.online;
	  shoot_cmd.ready	=shoot_ctrl_cmd_rc.shoot.ready;
	  shoot_cmd.firecmd	=shoot_ctrl_cmd_rc.shoot.firecmd;
	  
	  shoot.mode		=shoot_ctrl_cmd_rc.mode;			    关于模式选择：或者用遥控器随时切换模式，二选一
	  
	  Chassis_UpdateFeedback(&shoot);
	  Shoot_Control(&shoot,&shoot_cmd);
  }
}
*******************************************************************************/


/* Includes ----------------------------------------------------------------- */
#include <math.h>
#include <string.h>
#include "shoot.h"
#include "bsp/mm.h"
#include "bsp/time.h"
#include "component/filter.h"
#include "component/user_math.h"
/* Private typedef ---------------------------------------------------------- */
/* Private define ----------------------------------------------------------- */
#define MAX_FRIC_RPM 7000.0f
#define MAX_TRIG_RPM 1500.0f//这里可能也会影响最高发射频率，待测试
/* Private macro ------------------------------------------------------------ */
/* Private variables -------------------------------------------------------- */
static bool last_firecmd;

float maxTrigrpm=1500.0f;
/* Private function  -------------------------------------------------------- */

/**
 * \brief 设置射击模式
 *
 * \param s 包含射击数据的结构体
 * \param mode 要设置的模式
 *
 * \return 函数运行结果
 */
int8_t Shoot_SetMode(Shoot_t *s, Shoot_Mode_t mode)
{
    if (s == NULL) {
        return SHOOT_ERR_NULL; // 参数错误
    }
    s->mode=mode;
    return SHOOT_OK;
}

/**
 * \brief 重置PID积分
 *
 * \param s 包含射击数据的结构体
 *
 * \return 函数运行结果
 */
int8_t Shoot_ResetIntegral(Shoot_t *s)
{
    if (s == NULL) {
        return SHOOT_ERR_NULL; // 参数错误
    }
    uint8_t fric_num = s->param->basic.fric_num;
    for(int i=0;i<fric_num;i++)
    {	
        PID_ResetIntegral(&s->pid.fric_follow[i]);
        PID_ResetIntegral(&s->pid.fric_err[i]);
    }
    PID_ResetIntegral(&s->pid.trig);
    PID_ResetIntegral(&s->pid.trig_omg);
    return SHOOT_OK;
}

/**
 * \brief 重置计算模块
 *
 * \param s 包含射击数据的结构体
 *
 * \return 函数运行结果
 */
int8_t Shoot_ResetCalu(Shoot_t *s)
{
    if (s == NULL) {
        return SHOOT_ERR_NULL; // 参数错误
    }
    uint8_t fric_num = s->param->basic.fric_num;
    for(int i=0;i<fric_num;i++)
    {	
        PID_Reset(&s->pid.fric_follow[i]);
        PID_Reset(&s->pid.fric_err[i]);
        LowPassFilter2p_Reset(&s->filter.fric.in[i], 0.0f);
        LowPassFilter2p_Reset(&s->filter.fric.out[i], 0.0f);
    }
    PID_Reset(&s->pid.trig);
    PID_Reset(&s->pid.trig_omg);
    LowPassFilter2p_Reset(&s->filter.trig.in, 0.0f);
    LowPassFilter2p_Reset(&s->filter.trig.out, 0.0f);
    return SHOOT_OK;
}

/**
 * \brief 重置输出
 *
 * \param s 包含射击数据的结构体
 *
 * \return 函数运行结果
 */
int8_t Shoot_ResetOutput(Shoot_t *s)
{
    if (s == NULL) {
        return SHOOT_ERR_NULL; // 参数错误
    }
    uint8_t fric_num = s->param->basic.fric_num;
    for(int i=0;i<fric_num;i++)
    {	
        s->output.out_follow[i]=0.0f;
        s->output.out_err[i]=0.0f;
        s->output.out_fric[i]=0.0f;
        s->output.lpfout_fric[i]=0.0f;
    }
	s->output.outagl_trig=0.0f;
	s->output.outomg_trig=0.0f;
    s->output.outlpf_trig=0.0f;
    return SHOOT_OK;
}
//float last_angle=0.0f;
//float speed=0.0f;
//int8_t Shoot_CalufeedbackRPM(Shoot_t *s)
//{
//    if (s == NULL) {
//        return SHOOT_ERR_NULL; // 参数错误
//    }
////    static 
//    float err;
//    err=CircleError(s->feedback.fric[0].rotor_abs_angle,last_angle,M_2PI);
//    speed=err/s->dt/M_2PI*60.0f;
//    last_angle=s->feedback.fric->rotor_abs_angle;


//    return SHOOT_OK;
//}

/**
 * \brief 根据目标弹丸速度计算摩擦轮目标转速
 *
 * \param s 包含射击数据的结构体
 * \param target_speed 目标弹丸速度，单位m/s
 *
 * \return 函数运行结果
 */
int8_t Shoot_CaluTargetRPM(Shoot_t *s, float target_speed)
{
    if (s == NULL) {
        return SHOOT_ERR_NULL; // 参数错误
    }
	switch(s->param->basic.projectileType)
	{
		case SHOOT_PROJECTILE_17MM:
		s->target_variable.fric_rpm=5000.0f;
		break;
		case SHOOT_PROJECTILE_42MM:
		s->target_variable.fric_rpm=4000.0f;
		break;	
	}
    return SHOOT_OK;
}

/**
 * \brief 根据发射弹丸数量及发射频率计算拨弹电机目标角度
 *
 * \param s 包含发射数据的结构体
 * \param cmd 包含射击指令的结构体
 * 
 * \return 函数运行结果
 */
int8_t Shoot_CaluTargetAngle(Shoot_t *s, Shoot_CMD_t *cmd)
{
    if (s == NULL  || s->var_trig.num_toShoot == 0) {
        return SHOOT_ERR_NULL; 
    }
    float dt = s->timer.now - s->var_trig.time_lastShoot;
	float dpos;
    dpos = CircleError(s->target_variable.trig_angle, s->var_trig.trig_agl, M_2PI);
    if(dt >= 1.0f/s->param->basic.shot_freq && cmd->firecmd && dpos<=1.0f)
    {
        s->var_trig.time_lastShoot=s->timer.now;
        CircleAdd(&s->target_variable.trig_angle, M_2PI/s->param->basic.num_trig_tooth, M_2PI);
		s->var_trig.num_toShoot--;
    }
    return SHOOT_OK;
}

static float Shoot_CaluCoupledWeight(Shoot_t *s, uint8_t fric_index)
{
    if (s == NULL) {
        return SHOOT_ERR_NULL; // 参数错误
    }

    float Threshold;
    switch (s->param->basic.projectileType) {
        case SHOOT_PROJECTILE_17MM:
            Threshold=50.0f;
            break;
        case SHOOT_PROJECTILE_42MM:
            Threshold=400.0f;
            break;
        default:
            return 0.0f;
    }

    float err;
    err=fabs((s->param->basic.ratio_multilevel[fric_index]
                *s->target_variable.fric_rpm)
                -s->feedback.fric[fric_index].rotor_speed);
    if (err<Threshold)
    {
        s->var_fric.coupled_control_weights=1.0f-(err*err)/(Threshold*Threshold);
    }
    else
    {
        s->var_fric.coupled_control_weights=0.0f;
    }
    return s->var_fric.coupled_control_weights;
}

/**
 * \brief 更新射击模块的电机反馈信息
 *
 * \param s 包含射击数据的结构体
 *
 * \return 函数运行结果
 */
int8_t Shoot_UpdateFeedback(Shoot_t *s)
{
    if (s == NULL) {
        return SHOOT_ERR_NULL; // 参数错误
    }
    uint8_t fric_num = s->param->basic.fric_num;
    for(int i = 0; i < fric_num; i++) {
        /* 更新摩擦轮电机反馈 */
        MOTOR_RM_Update(&s->param->motor.fric[i].param);
		MOTOR_RM_t *motor_fed = MOTOR_RM_GetMotor(&s->param->motor.fric[i].param);
		if(motor_fed!=NULL)
		{
			s->feedback.fric[i]=motor_fed->motor.feedback;
		}
        /* 滤波摩擦轮电机转速反馈 */
        s->var_fric.fil_rpm[i] = LowPassFilter2p_Apply(&s->filter.fric.in[i], s->feedback.fric[i].rotor_speed);
        /* 归一化摩擦轮电机转速反馈 */
        s->var_fric.normalized_fil_rpm[i] = s->var_fric.fil_rpm[i] / MAX_FRIC_RPM;
        if(s->var_fric.normalized_fil_rpm[i]>1.0f)s->var_fric.normalized_fil_rpm[i]=1.0f;
        if(s->var_fric.normalized_fil_rpm[i]<-1.0f)s->var_fric.normalized_fil_rpm[i]=-1.0f;
        /* 计算平均摩擦轮电机转速反馈 */
        s->var_fric.normalized_fil_avgrpm[s->param->motor.fric[i].level-1]+=s->var_fric.normalized_fil_rpm[i];
    }
    for (int i=1; i<MAX_NUM_MULTILEVEL; i++)
    {
        s->var_fric.normalized_fil_avgrpm[i]=s->var_fric.normalized_fil_avgrpm[i]/fric_num/MAX_NUM_MULTILEVEL;
    }
	/* 更新拨弹电机反馈 */
    MOTOR_RM_Update(&s->param->motor.trig);
	s->feedback.trig = *MOTOR_RM_GetMotor(&s->param->motor.trig); 
	s->var_trig.trig_agl=s->param->basic.extra_deceleration_ratio*s->feedback.trig.gearbox_total_angle; 
	while(s->var_trig.trig_agl<0)s->var_trig.trig_agl+=M_2PI;
	while(s->var_trig.trig_agl>=M_2PI)s->var_trig.trig_agl-=M_2PI;
	if (s->feedback.trig.motor.reverse) {
        s->var_trig.trig_agl = M_2PI - s->var_trig.trig_agl;
	}
    s->var_trig.fil_trig_rpm = LowPassFilter2p_Apply(&s->filter.trig.in, s->feedback.trig.feedback.rotor_speed);
    s->var_trig.trig_rpm = s->feedback.trig.feedback.rotor_speed / maxTrigrpm;
    if(s->var_trig.trig_rpm>1.0f)s->var_trig.trig_rpm=1.0f;
    if(s->var_trig.trig_rpm<-1.0f)s->var_trig.trig_rpm=-1.0f;
    
    s->errtosee = s->feedback.fric[0].rotor_speed - s->feedback.fric[1].rotor_speed;
	return SHOOT_OK;
}

/**
 * \brief 射击模块运行状态机
 *
 * \param s 包含射击数据的结构体
 * \param cmd 包含射击指令的结构体
 *
 * \return 函数运行结果
 */float a;
int8_t Shoot_RunningFSM(Shoot_t *s, Shoot_CMD_t *cmd)
{
    if (s == NULL || cmd == NULL) {
        return SHOOT_ERR_NULL; // 参数错误
    }
    uint8_t fric_num = s->param->basic.fric_num;
    static float pos;
    if(s->mode==SHOOT_MODE_SAFE){
      for(int i=0;i<fric_num;i++)
      {	
          MOTOR_RM_Relax(&s->param->motor.fric[i].param);
      }
      MOTOR_RM_Relax(&s->param->motor.trig);\
      pos=s->target_variable.trig_angle=s->var_trig.trig_agl;
    }
    else{
        switch(s->running_state)
        {
            case SHOOT_STATE_IDLE:/*熄火等待*/
                for(int i=0;i<fric_num;i++) 
                {	/* 转速归零 */
                    PID_ResetIntegral(&s->pid.fric_follow[i]);
                    s->output.out_follow[i]=PID_Calc(&s->pid.fric_follow[i],0.0f,s->var_fric.normalized_fil_rpm[i],0,s->timer.dt);
                    s->output.out_fric[i]=s->output.out_follow[i];
                    s->output.lpfout_fric[i] = LowPassFilter2p_Apply(&s->filter.fric.out[i], s->output.out_fric[i]);
                    MOTOR_RM_SetOutput(&s->param->motor.fric[i].param, s->output.lpfout_fric[i]);
                }
                
                s->output.outagl_trig   =PID_Calc(&s->pid.trig,pos,s->var_trig.trig_agl,0,s->timer.dt);
                s->output.outomg_trig  	=PID_Calc(&s->pid.trig_omg,s->output.outagl_trig,s->var_trig.trig_rpm,0,s->timer.dt);
                s->output.outlpf_trig   =LowPassFilter2p_Apply(&s->filter.trig.out, s->output.outomg_trig);
                MOTOR_RM_SetOutput(&s->param->motor.trig, s->output.outlpf_trig);

                /* 检查状态机 */
                if(cmd->ready)
                    {   
                        Shoot_ResetCalu(s);
                        Shoot_ResetIntegral(s);
                        Shoot_ResetOutput(s);
                        s->running_state=SHOOT_STATE_READY;
                    }
                break;
                
            case SHOOT_STATE_READY:/*准备射击*/
					for(int i=0;i<fric_num;i++)
					{	
						uint8_t level=s->param->motor.fric[i].level-1;
                        float target_rpm=s->param->basic.ratio_multilevel[level]
                                    *s->target_variable.fric_rpm/MAX_FRIC_RPM;
						/* 计算耦合控制权重 */
                        float w=Shoot_CaluCoupledWeight(s,i);
                        /* 计算跟随输出、计算修正输出 */
						s->output.out_follow[i]=PID_Calc(&s->pid.fric_follow[i],
														target_rpm,
														s->var_fric.normalized_fil_rpm[i],
														0,
														s->timer.dt);
						s->output.out_err[i]=w*PID_Calc(&s->pid.fric_err[i],
														s->var_fric.normalized_fil_avgrpm[s->param->motor.fric[i].level-1],
														s->var_fric.normalized_fil_rpm[i],
														0,
														s->timer.dt);
						/* 按比例缩放并加和输出 */
						ScaleSumTo1(&s->output.out_follow[i], &s->output.out_err[i]);                    
						s->output.out_fric[i]=s->output.out_follow[i]+s->output.out_err[i];
						/* 滤波 */
						s->output.lpfout_fric[i] = LowPassFilter2p_Apply(&s->filter.fric.out[i], s->output.out_fric[i]);
						/* 设置输出 */
						MOTOR_RM_SetOutput(&s->param->motor.fric[i].param, s->output.lpfout_fric[i]);
					}
                /* 设置拨弹电机输出 */
                s->output.outagl_trig   =PID_Calc(&s->pid.trig,
													pos,
													s->var_trig.trig_agl,
													0,
													s->timer.dt);
                s->output.outomg_trig   =PID_Calc(&s->pid.trig_omg,
													s->output.outagl_trig,
													s->var_trig.trig_rpm,
													0,
													s->timer.dt);
                s->output.outlpf_trig   =LowPassFilter2p_Apply(&s->filter.trig.out, s->output.outomg_trig);
                MOTOR_RM_SetOutput(&s->param->motor.trig, s->output.outlpf_trig);
                
                /* 检查状态机 */
                if(!cmd->ready)
                    {
                        Shoot_ResetCalu(s);
                        Shoot_ResetOutput(s);
                        s->running_state=SHOOT_STATE_IDLE;
                    }
                else if(last_firecmd==false&&cmd->firecmd==true)
                    {
                        s->running_state=SHOOT_STATE_FIRE;
                        /* 根据模式设置待发射弹数 */
                        switch(s->mode)
                        {
                            case SHOOT_MODE_SINGLE:
                                s->var_trig.num_toShoot=1;
                                break;
                            case SHOOT_MODE_BURST:
                                s->var_trig.num_toShoot=s->param->basic.shot_burst_num;
                                break;
                            case SHOOT_MODE_CONTINUE:
                                s->var_trig.num_toShoot=6666;
                                break;
                            default:
                                s->var_trig.num_toShoot=0;
                                break;
                        }
                    }
                break;

            case SHOOT_STATE_FIRE:/*射击*/
				Shoot_CaluTargetAngle(s, cmd);
                for(int i=0;i<fric_num;i++)
                {	
					uint8_t level=s->param->motor.fric[i].level-1;
                    float target_rpm=s->param->basic.ratio_multilevel[level]
                                    *s->target_variable.fric_rpm/MAX_FRIC_RPM;
					/* 计算耦合控制权重 */
                    float w=Shoot_CaluCoupledWeight(s,i);
                    /* 计算跟随输出、计算修正输出 */ 
                    s->output.out_follow[i]=PID_Calc(&s->pid.fric_follow[i],
														target_rpm,
														s->var_fric.normalized_fil_rpm[i],
														0,
														s->timer.dt);
					s->output.out_err[i]=w*PID_Calc(&s->pid.fric_err[i],
														s->var_fric.normalized_fil_avgrpm[s->param->motor.fric[i].level-1],
														s->var_fric.normalized_fil_rpm[i],
														0,
														s->timer.dt);
                    /* 按比例缩放并加和输出 */
                    ScaleSumTo1(&s->output.out_follow[i], &s->output.out_err[i]);
                    s->output.out_fric[i]=s->output.out_follow[i]+s->output.out_err[i];
                    /* 滤波 */
                    s->output.lpfout_fric[i] = LowPassFilter2p_Apply(&s->filter.fric.out[i], s->output.out_fric[i]);
                    /* 设置输出 */
                    MOTOR_RM_SetOutput(&s->param->motor.fric[i].param, s->output.lpfout_fric[i]);
                }
                /* 设置拨弹电机输出 */
                s->output.outagl_trig   =PID_Calc(&s->pid.trig,
													s->target_variable.trig_angle,
													s->var_trig.trig_agl,
													0,
													s->timer.dt);
                s->output.outomg_trig   =PID_Calc(&s->pid.trig_omg,
													s->output.outagl_trig,
													s->var_trig.trig_rpm,
													0,
													s->timer.dt);
                s->output.outlpf_trig   =LowPassFilter2p_Apply(&s->filter.trig.out, s->output.outomg_trig);
                MOTOR_RM_SetOutput(&s->param->motor.trig, s->output.outlpf_trig);

                /* 检查状态机 */
                if(!cmd->firecmd)
                    {
                      s->running_state=SHOOT_STATE_READY;
						          pos=s->var_trig.trig_agl;
                      s->var_trig.num_toShoot=0;
                    }
                break;

            default:
                s->running_state=SHOOT_STATE_IDLE;
                break;
        }
    }
    /* 输出 */
	MOTOR_RM_Ctrl(&s->param->motor.fric[0].param);
    if(s->param->basic.fric_num>4)
    {
        MOTOR_RM_Ctrl(&s->param->motor.fric[4].param);
    }
    MOTOR_RM_Ctrl(&s->param->motor.trig);
    last_firecmd = cmd->firecmd;
    return SHOOT_OK;
}

/**
 * \brief 射击模块堵塞检测状态机
 *
 * \param s 包含射击数据的结构体
 * \param cmd 包含射击指令的结构体
 *
 * \return 函数运行结果
 */
int8_t Shoot_JamDetectionFSM(Shoot_t *s, Shoot_CMD_t *cmd)
{
    if (s == NULL) {
        return SHOOT_ERR_NULL; // 参数错误
    }
    if(s->param->jamDetection.enable){
        switch (s->jamdetection.fsmState) {
            case SHOOT_JAMFSM_STATE_NORMAL:/* 正常运行 */
                /* 检测电流是否超过阈值 */
                if (s->feedback.trig.feedback.torque_current/1000.0f > s->param->jamDetection.threshold) {
                    s->jamdetection.fsmState = SHOOT_JAMFSM_STATE_SUSPECTED;
                    s->jamdetection.lastTime = s->timer.now; /* 记录怀疑开始时间 */
                }
                /* 正常运行射击状态机 */
                Shoot_RunningFSM(s, cmd);
                break;
            case SHOOT_JAMFSM_STATE_SUSPECTED:/* 怀疑堵塞 */
                /* 检测电流是否低于阈值 */
                if (s->feedback.trig.feedback.torque_current/1000.0f < s->param->jamDetection.threshold) {
                    s->jamdetection.fsmState = SHOOT_JAMFSM_STATE_NORMAL;
                    break;
                } 
                /* 检测高阈值状态是否超过设定怀疑时间 */
                else if ((s->timer.now - s->jamdetection.lastTime) >= s->param->jamDetection.suspectedTime) {
                    s->jamdetection.detected =true;
	    			s->jamdetection.fsmState = SHOOT_JAMFSM_STATE_CONFIRMED;
                    break;
                }
                /* 正常运行射击状态机 */
                Shoot_RunningFSM(s, cmd);
                break;
            case SHOOT_JAMFSM_STATE_CONFIRMED:/* 确认堵塞 */
                /* 清空待发射弹 */
                s->var_trig.num_toShoot=0;
                /* 修改拨弹盘目标角度 */
                s->target_variable.trig_angle = s->var_trig.trig_agl-(M_2PI/s->param->basic.num_trig_tooth);
                /* 切换状态 */
                s->jamdetection.fsmState = SHOOT_JAMFSM_STATE_DEAL;
                /* 记录处理开始时间 */
                s->jamdetection.lastTime = s->timer.now; 
            case SHOOT_JAMFSM_STATE_DEAL:/* 堵塞处理 */
                /* 正常运行射击状态机 */
                Shoot_RunningFSM(s, cmd);
                /* 给予0.3秒响应时间并检测电流小于20A，认为堵塞已解除 */
                if ((s->timer.now - s->jamdetection.lastTime)>=0.3f&&s->feedback.trig.feedback.torque_current/1000.0f < 20.0f) { 
                    s->jamdetection.fsmState = SHOOT_JAMFSM_STATE_NORMAL;
                }
                break;
            default:
                s->jamdetection.fsmState = SHOOT_JAMFSM_STATE_NORMAL;
                break;
        }
    }
    else{   
        s->jamdetection.fsmState = SHOOT_JAMFSM_STATE_NORMAL;
        s->jamdetection.detected = false;
        Shoot_RunningFSM(s, cmd);
    }

    return SHOOT_OK;
}
/* Exported functions ------------------------------------------------------- */
/**
 * \brief 初始化射击模块
 *
 * \param s 包含射击数据的结构体
 * \param param 包含射击参数的结构体
 * \param target_freq 控制循环频率，单位Hz
 *
 * \return 函数运行结果
 */
int8_t Shoot_Init(Shoot_t *s, Shoot_Params_t *param, float target_freq)
{
    if (s == NULL || param == NULL || target_freq <= 0.0f) {
        return SHOOT_ERR_NULL; // 参数错误
    }
    uint8_t fric_num = param->basic.fric_num;
    s->param=param;
    BSP_CAN_Init();
    /* 初始化摩擦轮PID和滤波器 */
    for(int i=0;i<fric_num;i++){
	    MOTOR_RM_Register(&param->motor.fric[i].param);
        PID_Init(&s->pid.fric_follow[i], 
            KPID_MODE_CALC_D, 
            target_freq,
            &param->pid.fric_follow);
	    PID_Init(&s->pid.fric_err[i], 
            KPID_MODE_CALC_D, 
            target_freq,
            &param->pid.fric_err);
        LowPassFilter2p_Init(&s->filter.fric.in[i], 
            target_freq, 
            s->param->filter.fric.in);
        LowPassFilter2p_Init(&s->filter.fric.out[i], 
            target_freq, 
            s->param->filter.fric.out);
    }
    /* 初始化拨弹PID和滤波器 */
	MOTOR_RM_Register(&param->motor.trig);
    switch(s->param->motor.trig.module)
    {
        case MOTOR_M3508:
            PID_Init(&s->pid.trig, 
                KPID_MODE_CALC_D, 
                target_freq,
                &param->pid.trig_3508);
            PID_Init(&s->pid.trig_omg, 
                KPID_MODE_CALC_D, 
                target_freq,
                &param->pid.trig_omg_3508);
            break;
        case MOTOR_M2006:
            PID_Init(&s->pid.trig, 
                KPID_MODE_CALC_D, 
                target_freq,
                &param->pid.trig_2006);
            PID_Init(&s->pid.trig_omg, 
                KPID_MODE_CALC_D, 
                target_freq,
                &param->pid.trig_omg_2006);
            break;
        default:
            return SHOOT_ERR_MOTOR;
        break;
    }
    LowPassFilter2p_Init(&s->filter.trig.in, 
        target_freq, 
        s->param->filter.trig.in);
    LowPassFilter2p_Init(&s->filter.trig.out, 
        target_freq, 
        s->param->filter.trig.out);

	/* 归零变量 */
    memset(&s->var_trig,0,sizeof(s->var_trig));
	return SHOOT_OK;
}

/**
 * \brief 射击模块控制主函数
 *
 * \param s 包含射击数据的结构体
 * \param cmd 包含射击指令的结构体
 *
 * \return 函数运行结果
 */
int8_t Shoot_Control(Shoot_t *s, Shoot_CMD_t *cmd)
{
    if (s == NULL || cmd == NULL) {
        return SHOOT_ERR_NULL; // 参数错误
    }
    s->timer.now = BSP_TIME_Get_us() / 1000000.0f;
    s->timer.dt = (BSP_TIME_Get_us() - s->timer.lask_wakeup) / 1000000.0f;
    s->timer.lask_wakeup = BSP_TIME_Get_us();
    Shoot_CaluTargetRPM(s,233);

    Shoot_JamDetectionFSM(s, cmd);
//    Shoot_CalufeedbackRPM(s);
    return SHOOT_OK;
}








