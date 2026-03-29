/*
 * 摩擦轮发射模块核心算法实现，包含射频计算、发射检测、热量控制等功能
 */
 
/*******************************************************************************
 * 文件名：shoot.c
 * 描述：射击模块主文件，包含核心算法实现
 * 作者：小M
 * 日期：2026-03-25

  文件架构：
    -热量控制FSM （Shoot_CaluTargetAngle自动累加热量，观测摩擦轮掉速判断本次发射是否有效，根据剩余热量拟合射频，并通过safe_shots发射余量进一步防超热量）
    -卡弹FSM  
    |-主运行FSM 


  * 版本：V1.0
  * 修改记录：添加热量控制和发射检测。缺少弹速拟合计算


*******************************************************************************/


/* Includes ----------------------------------------------------------------- */
#include <math.h>
#include <string.h>
#include "shoot.h"
#include "bsp/mm.h"
#include "bsp/time.h"
#include "component/filter/filter.h"
#include "component/user_math.h"
/* Private typedef ---------------------------------------------------------- */
/* Private define ----------------------------------------------------------- */
#define MAX_FRIC_RPM 7000.0f
#define MAX_TRIG_RPM 2500.0f//这里可能也会影响最高发射频率，待测试

/* 发射检测参数 */
#define SHOT_DETECT_RPM_DROP_THRESHOLD 100.0f  /* 摩擦轮转速下降阈值，单位rpm */
#define SHOT_DETECT_SUSPECTED_TIME 0.0005f      /* 发射嫌疑持续时间阈值，单位秒 */
#define FRIC_READY_RPM_RATIO 0.95f             /* 摩擦轮准备好的转速比例 */

/* Private macro ------------------------------------------------------------ */
/* Private variables -------------------------------------------------------- */
static bool last_firecmd;


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
		s->target_variable.fric_rpm=6800.0f;
		break;
		case SHOOT_PROJECTILE_42MM:
		s->target_variable.fric_rpm=4000.0f;//6500
		break;	 
	}
    return SHOOT_OK;
}

/**
 * \brief 更新热量控制数据（使用融合后的热量值）
 *
 * \param s 包含发射数据的结构体
 *
 * \return 函数运行结果
 */
static int8_t Shoot_UpdateHeatControl(Shoot_t *s)
{
    if (s == NULL) {
        return SHOOT_ERR_NULL;
    }

    if (!s->param->heatControl.enable || !s->heatcontrol.ref_online) {
        s->heatcontrol.Hres = 0.0f;
        s->heatcontrol.ncd = s->param->basic.shot_freq;
        return SHOOT_OK;
    }
    
    /* 使用融合后的热量值计算剩余热量 */
    s->heatcontrol.Hres = s->heatcontrol.Hmax - s->heatcontrol.Hnow_fused;
    
    /* 计算冷却射频 ncd = Hcd / Hgen */   
    if (s->heatcontrol.Hgen > 0.0f) {
        s->heatcontrol.ncd = s->heatcontrol.Hcd / s->heatcontrol.Hgen;
    } else {
        s->heatcontrol.ncd = 0.0f;
    }      
    
    return SHOOT_OK;
}

/**
 * \brief 计算摩擦轮平均转速
 *
 * \param s 包含发射数据的结构体
 *
 * \return 平均转速
 */
static float Shoot_CalcAvgFricRpm(Shoot_t *s)
{
    if (s == NULL) {
        return 0.0f;
    }
    
    float sum = 0.0f;
    uint8_t fric_num = s->param->basic.fric_num;
    
    for (int i = 0; i < fric_num; i++) {
        sum += fabs(s->var_fric.fil_rpm[i]);
    }
    
    return (fric_num > 0) ? (sum / fric_num) : 0.0f;
}

/**
 * \brief 发射检测：通过摩擦轮掉速检测发射
 *
 * \param s 包含发射数据的结构体
 *
 * \return 是否检测到掉速超过阈值
 */
static bool Shoot_DetectShotByRpmDrop(Shoot_t *s)
{
    if (s == NULL) {
        return false;
    }
    
    /* 只在READY和FIRE状态下检测，避免停机时误判 */
    if (s->running_state != SHOOT_STATE_READY && 
        s->running_state != SHOOT_STATE_FIRE) {
        return false;
    }
    
    /* 计算当前摩擦轮平均转速 */
    s->heatcontrol.avgFricRpm = Shoot_CalcAvgFricRpm(s);
    
    /* 计算当前转速与目标转速的差值（掉速量） */
    s->heatcontrol.rpmDrop = s->target_variable.fric_rpm - s->heatcontrol.avgFricRpm;
    
    /* 判断是否发生明显掉速 */
    if (s->heatcontrol.rpmDrop > SHOT_DETECT_RPM_DROP_THRESHOLD) {
        return true;
    }
    
    return false;
}
                                                      
static float Shoot_ResolveHeatThreshold(float cfg, float Hmax)
{
    if (cfg <= 0.0f) {
        return 0.0f;
    }

    if (cfg <= 1.0f) {
        return cfg * Hmax;
    }

    return cfg;
}

static uint16_t Shoot_ResolveSafeShots(Shoot_t *s)
{
    if (s == NULL) {
        return 0U;
    }

    float cfg = s->param->heatControl.safe_shots;
    if (cfg <= 0.0f) {
        return 0U;
    }

    if (cfg <= 1.0f) {
        if (s->heatcontrol.Hmax <= 0.0f || s->heatcontrol.Hgen <= 0.0f) {
            return 0U;
        }

        float total_shots = s->heatcontrol.Hmax / s->heatcontrol.Hgen;
        float safe = ceilf(cfg * total_shots);
        if (safe < 1.0f) {
            safe = 1.0f;
        }
        if (safe > (float)UINT16_MAX) {
            safe = (float)UINT16_MAX;
        }
        return (uint16_t)safe;
    }

    if (cfg > (float)UINT16_MAX) {
        cfg = (float)UINT16_MAX;
    }
    return (uint16_t)cfg;
}


/**
 * \brief 热量数据融合：用裁判系统数据修正自主估计
 *
 * \param s 包含发射数据的结构体
 *
 * \return 函数运行结果
 * 
 * \note 裁判系统数据准确但更新慢，自主计算实时但可能误差累积
 *       只在裁判系统数据更新时才修正估计值，保证准确性和实时性
 */
static int8_t Shoot_FuseHeatData(Shoot_t *s)
{
    if (s == NULL) {
        return SHOOT_ERR_NULL;
    }

    if (!s->param->heatControl.enable || !s->heatcontrol.ref_online) {
        return SHOOT_OK;
    }
    
    /* 如果裁判系统数据有效（Hmax > 0） */
    if (s->heatcontrol.Hmax > 0.0f && s->heatcontrol.Hnow >= 0.0f) {
        /* 检测裁判系统数据是否有更新 */
        if (s->heatcontrol.Hnow != s->heatcontrol.Hnow_last) {
            /* 数据更新了，用裁判系统数据修正估计值 */
            s->heatcontrol.Hnow_estimated = s->heatcontrol.Hnow;
            s->heatcontrol.Hnow_last = s->heatcontrol.Hnow; /* 记录本次值 */
        }
        
        /* 连射场景下，裁判数据存在刷新延迟；取更保守的热量用于限热 */
        s->heatcontrol.Hnow_fused = fmaxf(s->heatcontrol.Hnow, s->heatcontrol.Hnow_estimated);
    } else {
        /* 裁判系统数据无效，仅使用自主估计值 */
        s->heatcontrol.Hnow_fused = s->heatcontrol.Hnow_estimated;
    }
    
    return SHOOT_OK;
}

/**
 * \brief 计算可发射弹数
 *
 * \param s 包含发射数据的结构体
 *
 * \return 函数运行结果
 */
static int8_t Shoot_CalcAvailableShots(Shoot_t *s)
{
    if (s == NULL) {
        return SHOOT_ERR_NULL;
    }

    if (!s->param->heatControl.enable || !s->heatcontrol.ref_online) {
        s->heatcontrol.shots_available = UINT16_MAX;
        return SHOOT_OK;
    }
    
    /* 计算剩余热量 */
    float heat_available = s->heatcontrol.Hmax - s->heatcontrol.Hnow_fused;
    
    /* 计算可发射弹数 */
    if (s->heatcontrol.Hgen > 0.0f && heat_available > 0.0f) {
        s->heatcontrol.shots_available = (uint16_t)(heat_available / s->heatcontrol.Hgen);
    } else {
        s->heatcontrol.shots_available = 0;
    }
    
    return SHOOT_OK;
}


/**
 * \brief 热量检测状态机
 *
 * \param s 包含发射数据的结构体
 *
 * \return 函数运行结果
 */
static int8_t Shoot_HeatDetectionFSM(Shoot_t *s)
{
    if (s == NULL) {
        return SHOOT_ERR_NULL;
    }

    if (!s->param->heatControl.enable || !s->heatcontrol.ref_online) {
        s->heatcontrol.detectState = SHOOT_HEAT_DETECT_IDLE;
        s->heatcontrol.shotDetected = false;
        return SHOOT_OK;
    }
    
    switch (s->heatcontrol.detectState) {
        case SHOOT_HEAT_DETECT_IDLE:
            /* 停机状态：等待摩擦轮启动并加速到目标速度附近 */
            if (s->running_state == SHOOT_STATE_READY || 
                s->running_state == SHOOT_STATE_FIRE) {
                /* 计算当前平均转速 */
                s->heatcontrol.avgFricRpm = Shoot_CalcAvgFricRpm(s);
                
                /* 检查摩擦轮是否达到目标转速的85%以上 */
                if (s->heatcontrol.avgFricRpm >= s->target_variable.fric_rpm * FRIC_READY_RPM_RATIO) {
                    s->heatcontrol.detectState = SHOOT_HEAT_DETECT_READY;
                    s->heatcontrol.lastAvgFricRpm = s->heatcontrol.avgFricRpm;
                }
            }
            break;
            
        case SHOOT_HEAT_DETECT_READY:
            /* 准备检测状态：监测摩擦轮掉速 */
            /* 检测掉速（当前转速低于目标转速超过阈值） */
            if (Shoot_DetectShotByRpmDrop(s)) {
                s->heatcontrol.detectState = SHOOT_HEAT_DETECT_SUSPECTED;
                s->heatcontrol.detectTime = s->timer.now; /* 记录进入嫌疑状态的时间 */
            }
            
            /* 如果摩擦轮停止 */
            if (s->running_state == SHOOT_STATE_IDLE) {
                s->heatcontrol.detectState = SHOOT_HEAT_DETECT_IDLE;
            }
            break;
            
        case SHOOT_HEAT_DETECT_SUSPECTED:
            /* 发射嫌疑状态：持续检测掉速 */
            /* 更新掉速量 */
            s->heatcontrol.avgFricRpm = Shoot_CalcAvgFricRpm(s);
            s->heatcontrol.rpmDrop = s->target_variable.fric_rpm - s->heatcontrol.avgFricRpm;
            
            /* 若掉速消失（转速恢复正常），回到准备状态 */
            if (s->heatcontrol.rpmDrop < SHOT_DETECT_RPM_DROP_THRESHOLD) {
                s->heatcontrol.detectState = SHOOT_HEAT_DETECT_READY;
            }
            /* 若嫌疑状态持续超过阈值时间，确认发射 */
            else if ((s->timer.now - s->heatcontrol.detectTime) >= SHOT_DETECT_SUSPECTED_TIME) {
                s->heatcontrol.detectState = SHOOT_HEAT_DETECT_CONFIRMED;
            }
            break;
            
        case SHOOT_HEAT_DETECT_CONFIRMED:
            /* 确认发射状态：仅记录检测计数。
             * 估计热量在实际下发拨弹时已预扣，避免重复累加。 */
            s->heatcontrol.shots_detected++;
            
            /* 返回准备检测状态 */
            s->heatcontrol.detectState = SHOOT_HEAT_DETECT_READY;
            break;
            
        default:
            s->heatcontrol.detectState = SHOOT_HEAT_DETECT_IDLE;
            break;
    }
    
    /* 善后工作：热量冷却（每个周期都执行） */
    if (s->heatcontrol.Hnow_estimated > 0.0f && s->heatcontrol.Hcd > 0.0f) {
        s->heatcontrol.Hnow_estimated -= s->heatcontrol.Hcd * s->timer.dt;
        if (s->heatcontrol.Hnow_estimated < 0.0f) {
            s->heatcontrol.Hnow_estimated = 0.0f;
        }
    }
    
    /* 数据融合 */
    Shoot_FuseHeatData(s);
    
    /* 计算可发射弹数 */
    Shoot_CalcAvailableShots(s);
    
    return SHOOT_OK;
}

/**
 * \brief 根据热量控制计算射频
 *
 * \param s 包含发射数据的结构体
 *
 * \return 计算出的射频值，单位Hz
 */
static float Shoot_CaluFreqByHeat(Shoot_t *s)
{
    if (s == NULL) {
        return 0.0f;
    }
    
    /* 如果热量控制未启用，返回配置的射频 */
    if (!s->param->heatControl.enable || !s->heatcontrol.ref_online) {
        return s->param->basic.shot_freq;
    }
    
    /* 检查Hmax和Hcd是否有效 */
    if (s->heatcontrol.Hmax <= 0.0f || s->heatcontrol.Hcd <= 0.0f) {
        return s->param->basic.shot_freq; /* 数据无效，使用默认射频 */
    }
    
    float Hres = s->heatcontrol.Hres;
    float Hwarn = Shoot_ResolveHeatThreshold(s->param->heatControl.Hwarn, s->heatcontrol.Hmax);
    float Hsatu = Shoot_ResolveHeatThreshold(s->param->heatControl.Hsatu, s->heatcontrol.Hmax);
    float Hthres = Shoot_ResolveHeatThreshold(s->param->heatControl.Hthres, s->heatcontrol.Hmax);
    float nmax = s->param->heatControl.nmax;
    float ncd = s->heatcontrol.ncd;

    if (nmax <= 0.0f) {
        nmax = s->param->basic.shot_freq;
    }
    if (ncd < 0.0f) {
        ncd = 0.0f;
    } else if (ncd > nmax) {
        ncd = nmax;
    }

    if (Hwarn <= 0.0f) {
        Hwarn = s->heatcontrol.Hmax * 0.7f;
    }
    if (Hsatu <= 0.0f || Hsatu >= Hwarn) {
        Hsatu = Hwarn * 0.5f;
    }
    if (Hthres <= 0.0f || Hthres >= Hsatu) {
        Hthres = fmaxf(Hsatu * 0.5f, s->heatcontrol.Hgen);
    }
    
    /* 剩余热量大于预警值：最大射频 */
    if (Hres > Hwarn) {
        return nmax;
    }
    /* 剩余热量在预警值和饱和值之间：线性映射 */
    else if (Hres > Hsatu) {
        /* 线性插值: n = ncd + (nmax - ncd) * (Hres - Hsatu) / (Hwarn - Hsatu) */
        float ratio = (Hres - Hsatu) / (Hwarn - Hsatu);
        return ncd + (nmax - ncd) * ratio;
    }
    /* 剩余热量在饱和值和阈值之间：冷却射频 */
    else if (Hres > Hthres) {
        return ncd;
    }
    /* 剩余热量小于阈值：停止射击 */
    else {
        return 0.0f;
    }
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
    if (s == NULL || cmd == NULL || s->var_trig.num_toShoot == 0 || s->param->basic.num_trig_tooth == 0) {
        return SHOOT_ERR_NULL; 
    }
    
    /* 更新热量控制数据 */
    Shoot_UpdateHeatControl(s);
    
    /* 根据热量控制计算实际射频 */
    float actual_freq = Shoot_CaluFreqByHeat(s);
    uint16_t safe_shots = Shoot_ResolveSafeShots(s);
    
    /* 检查可发射弹丸数是否满足安全余量 */
    if (s->param->heatControl.enable  &&
        s->heatcontrol.shots_available <= safe_shots) {
        actual_freq = 0.0f; /* 禁止发弹 */
    }

    float dt = s->timer.now - s->var_trig.time_lastShoot;
	  float dpos;
    float dpos_abs;
    dpos = CircleError(s->target_variable.trig_angle, s->var_trig.trig_agl, M_2PI);
    dpos_abs = fabsf(dpos);
    
    /* 使用热量控制计算出的射频，而不是配置的固定射频 */
    if(actual_freq > 0.0f && dt >= 1.0f/actual_freq && cmd->firecmd && dpos_abs <= 1.0f)
    {
        s->var_trig.time_lastShoot=s->timer.now;
        CircleAdd(&s->target_variable.trig_angle, M_2PI/s->param->basic.num_trig_tooth, M_2PI);
		s->var_trig.num_toShoot--;
    s->var_trig.num_shooted++;

        /* 实际发射指令下发时，立刻预扣估计热量，抑制裁判数据延迟导致的超热。 */
        if (s->param->heatControl.enable && s->heatcontrol.ref_online && s->heatcontrol.Hgen > 0.0f) {
            s->heatcontrol.Hnow_estimated += s->heatcontrol.Hgen;
            if (s->heatcontrol.Hnow_estimated > s->heatcontrol.Hmax) {
                s->heatcontrol.Hnow_estimated = s->heatcontrol.Hmax;
            }
        }
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
    s->var_trig.trig_rpm = s->feedback.trig.feedback.rotor_speed / MAX_TRIG_RPM;
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
                        s->target_variable.trig_angle = s->var_trig.trig_agl;
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
                                            s->target_variable.trig_angle = pos;
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
                s->target_variable.trig_angle = s->var_trig.trig_agl;
                CircleAdd(&s->target_variable.trig_angle,
                          -(M_2PI / s->param->basic.num_trig_tooth),
                          M_2PI);
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
    BSP_FDCAN_Init();
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

  /* 初始化热量控制 */
    memset(&s->heatcontrol, 0, sizeof(s->heatcontrol));

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

    /* 运行热量检测状态机 */
    Shoot_HeatDetectionFSM(s);

    /* 运行卡弹检测状态机 */
    Shoot_JamDetectionFSM(s, cmd);
//    Shoot_CalufeedbackRPM(s);
    return SHOOT_OK;
}

/**
 * @brief 导出射击UI数据
 *
 * @param s 射击结构体
 * @param ui UI结构体
 */
void Shoot_DumpUI(Shoot_t *s, Shoot_RefereeUI_t *ui) {
  ui->mode = s->mode;
  ui->fire = s->running_state;
}

void Shoot_DumpAI(Shoot_t *s, Shoot_AI_t *ai) {
    ai->num_shooted=s->var_trig.num_shooted;
    ai->bullet_speed=12.0f;
}
