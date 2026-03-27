/*
 * far♂蛇模块
 */

#pragma once

#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif

#include "main.h"
#include "component/pid.h"
#include "device/motor_rm.h"
/* Exported constants ------------------------------------------------------- */
#define MAX_FRIC_NUM 6
#define MAX_NUM_MULTILEVEL 2 /* 多级发射级数 */

#define SHOOT_OK (0)        /* 运行正常 */
#define SHOOT_ERR_NULL (-1) /* 运行时发现NULL指针 */    
#define SHOOT_ERR_ERR (-2)  /* 运行时发现了其他错误 */
#define SHOOT_ERR_MODE (-3) /* 运行时配置了错误的Mode */
#define SHOOT_ERR_MOTOR (-4) /* 运行时配置了不存在的电机类型 */
#define SHOOT_ERR_MALLOC (-5) /* 内存分配失败 */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */
typedef enum {
    SHOOT_JAMFSM_STATE_NORMAL = 0,/* 常规状态 */
    SHOOT_JAMFSM_STATE_SUSPECTED, /* 怀疑状态 */
    SHOOT_JAMFSM_STATE_CONFIRMED, /* 确认状态 */
    SHOOT_JAMFSM_STATE_DEAL       /* 处理状态 */
}Shoot_JamDetectionFSM_State_t;
typedef enum {
    SHOOT_STATE_IDLE = 0,/* 熄火 */
    SHOOT_STATE_READY,   /* 准备射击 */
    SHOOT_STATE_FIRE     /* 射击 */
}Shoot_Running_State_t;

typedef enum {
    SHOOT_MODE_SAFE = 0,/* 安全模式 */
    SHOOT_MODE_SINGLE,  /* 单发模式 */
    SHOOT_MODE_BURST,   /* 多发模式 */
    SHOOT_MODE_CONTINUE,/* 连发模式 */
    SHOOT_MODE_NUM
}Shoot_Mode_t;

typedef enum {
	SHOOT_PROJECTILE_17MM,
	SHOOT_PROJECTILE_42MM,
}Shoot_Projectile_t;

typedef struct{
	MOTOR_RM_Param_t param;
	uint8_t level; /* 电机属于第几级发射；1起始 */
}Shoot_MOTOR_RM_Param_t;

typedef struct {
  MOTOR_Feedback_t fric[MAX_FRIC_NUM];/* 摩擦轮电机反馈 */
  MOTOR_RM_t trig;                    /* 拨弹电机反馈 */
  
}Shoot_Feedback_t;

typedef struct{
  float fil_rpm[MAX_FRIC_NUM]; /* 滤波后的摩擦轮原始转速 */
  float normalized_fil_rpm[MAX_FRIC_NUM]; /* 归一化摩擦轮转速 */
  float normalized_fil_avgrpm[MAX_NUM_MULTILEVEL];            /* 归一化摩擦轮平均转速 */
  float coupled_control_weights; /* 耦合控制权重 */
}Shoot_VARSForFricCtrl_t;

typedef struct{
  float time_lastShoot;/* 上次射击时间 */
  uint16_t num_toShoot;/* 剩余待发射弹数 */
  uint16_t num_shooted;/* 已发射弹数 */

  float trig_agl;	     /*计算所有减速比后的拨弹盘的角度*/
  float fil_trig_rpm;  /* 滤波后的拨弹电机转速*/
  float trig_rpm;      /* 归一化拨弹电机转速 */
}Shoot_VARSForTrigCtrl_t;

typedef struct {
  bool detected; /* 卡弹检测结果 */
  float lastTime;/* 用于记录怀疑状态或处理状态的开始时间 */
  Shoot_JamDetectionFSM_State_t fsmState; /* 卡弹检测状态机 */
}Shoot_JamDetection_t;
typedef struct {
  float out_follow[MAX_FRIC_NUM];
  float out_err[MAX_FRIC_NUM];
  float out_fric[MAX_FRIC_NUM];
  float lpfout_fric[MAX_FRIC_NUM];

  float outagl_trig;
  float outomg_trig;
  float outlpf_trig;
}Shoot_Output_t;

typedef struct {
  Shoot_Mode_t mode;/* 射击模式 */
  bool ready;       /* 准备射击 */
  bool firecmd;     /* 射击 */
}Shoot_CMD_t;
/* 底盘参数的结构体，包含所有初始化用的参数，通常是const，存好几组 */
typedef struct {
  struct{
    Shoot_Projectile_t projectileType; /* 发射弹丸类型 */;
    size_t fric_num;                   /* 摩擦轮电机数量 */
    float ratio_multilevel[MAX_NUM_MULTILEVEL]; /* 多级发射各级速度比例 */
    float extra_deceleration_ratio;	            /*电机出轴到拨盘的额外减速比；没有写1*/
    size_t num_trig_tooth;  /* 拨弹盘每圈弹丸数量 */
    float shot_freq;        /* 射击频率，单位Hz */
    size_t shot_burst_num;  /* 多发模式一次射击的数量 */
  }basic;/* 发射基础参数 */
  struct {
    bool  enable;       /* 是否启用卡弹检测 */ 
    float threshold;    /* 卡弹检测阈值，单位A (dji2006建议设置为120A，dji3508建议设置为235A,根据实际测试调整)*/
    float suspectedTime;/* 卡弹怀疑时间，单位秒 */
  }jamDetection;/* 卡弹检测参数 */
  struct {
  Shoot_MOTOR_RM_Param_t fric[MAX_FRIC_NUM];
  MOTOR_RM_Param_t trig;
  }motor; /* 电机参数 */
  struct{
    KPID_Params_t fric_follow;  /* 摩擦轮电机PID控制参数，用于跟随目标速度 */
    KPID_Params_t fric_err;     /* 摩擦轮电机PID控制参数，用于消除转速误差 */
    KPID_Params_t trig_2006;    /* 拨弹电机PID控制参数 */
    KPID_Params_t trig_omg_2006;/* 拨弹电机PID控制参数 */
    KPID_Params_t trig_3508;    /* 拨弹电机PID控制参数 */
    KPID_Params_t trig_omg_3508;/* 拨弹电机PID控制参数 */
  }pid; /* PID参数 */
  struct {
    struct{
    float in;  /* 反馈值滤波器截止频率 */
    float out; /* 输出值滤波器截止频率 */
    }fric;
    struct{
    float in;  /* 反馈值滤波器截止频率 */
    float out; /* 输出值滤波器截止频率 */
    }trig;
  } filter;/* 滤波器截止频率参数 */
} Shoot_Params_t;

typedef struct {
  float now;            /* 当前时间，单位秒 */
  uint64_t lask_wakeup; /* 上次唤醒时间，单位微秒 */
  float dt;             /* 两次唤醒间隔时间，单位秒 */
}Shoot_Timer_t;

/*
 * 运行的主结构体，所有这个文件里的函数都在操作这个结构体
 * 包含了初始化参数，中间变量，输出变量
 */
typedef struct {
  Shoot_Timer_t timer; /* 计时器 */
  Shoot_Params_t *param; /* 发射参数 */
  /* 模块通用 */           
  Shoot_Mode_t mode; /* 射击模式 */
  /* 反馈信息 */           
  Shoot_Feedback_t feedback;
  /* 控制信息*/         
  Shoot_Running_State_t running_state; /* 运行状态机 */ 
  Shoot_JamDetection_t jamdetection; /* 卡弹检测控制信息 */
  Shoot_VARSForFricCtrl_t var_fric; /* 摩擦轮控制信息 */
  Shoot_VARSForTrigCtrl_t var_trig; /* 角度计算控制信息 */
  Shoot_Output_t output; /* 输出信息 */
  /* 目标控制量 */           
  struct {           
    float fric_rpm;  /* 目标摩擦轮转速 */
    float trig_angle;/* 目标拨弹位置 */
  }target_variable;

  /* 反馈控制用的PID */
  struct {
    KPID_t fric_follow[MAX_FRIC_NUM];/* 摩擦轮PID主结构体 */
    KPID_t fric_err[MAX_FRIC_NUM];   /* 摩擦轮PID主结构体 */
    KPID_t trig;                     /* 拨弹PID主结构体 */
    KPID_t trig_omg;                 /* 拨弹PID主结构体 */
  } pid;

  /* 滤波器 */
  struct {
    struct{
    LowPassFilter2p_t in[MAX_FRIC_NUM]; /* 反馈值滤波器 */
    LowPassFilter2p_t out[MAX_FRIC_NUM];/* 输出值滤波器 */
    }fric;
    struct{
    LowPassFilter2p_t in; /* 反馈值滤波器 */
    LowPassFilter2p_t out;/* 输出值滤波器 */
    }trig;
  } filter;

  float errtosee; /*调试用*/

} Shoot_t;

/* Exported functions prototypes -------------------------------------------- */

/**
 * \brief 初始化发射
 *
 * \param s 包含发射数据的结构体
 * \param param 包含发射参数的结构体指针
 * \param target_freq 任务预期的运行频率
 *
 * \return 函数运行结果
 */
int8_t Shoot_Init(Shoot_t *s, Shoot_Params_t *param, float target_freq);

/**
 * \brief 设置发射模式
 *
 * \param s 包含发射数据的结构体
 * \param mode 包含发射模式的枚举
 *
 * \return 函数运行结果
 */
int8_t Shoot_SetMode(Shoot_t *s, Shoot_Mode_t mode);

/**
 * \brief 更新反馈
 *
 * \param s 包含发射数据的结构体
 *
 * \return 函数运行结果
 */
int8_t Shoot_UpdateFeedback(Shoot_t *s);

/**
 * \brief 初始化发射
 *
 * \param s 包含发射数据的结构体
 * \param cmd 包含发射命令的结构体
 *
 * \return 函数运行结果
 */
int8_t Shoot_Control(Shoot_t *s, Shoot_CMD_t *cmd);



#ifdef __cplusplus
}
#endif



