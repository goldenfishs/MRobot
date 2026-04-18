/*
 µ×ÅÌÄ£×é
 */
#pragma once


#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include <cmsis_os2.h>
#include "bsp/fdcan.h"
#include "component/filter/filter.h"
#include "component/mixer.h"
#include "component/pid.h"
#include "component/ahrs/ahrs.h"
#include "device/motor_rm.h"
/* Exported constants ------------------------------------------------------- */
#define CHASSIS_OK (0)        /* ÔËÐÐÕý³£ */
#define CHASSIS_ERR (-1)      /* ÔËÐÐÊ±³öÏÖÁËÒ»Ð©Ð¡´íÎó */
#define CHASSIS_ERR_NULL (-2) /* ÔËÐÐÊ±·¢ÏÖNULLÖ¸Õë */
#define CHASSIS_ERR_MODE (-3) /* ÔËÐÐÊ±³öÅäÖÃÁË´íÎóµÄChassisMode_t */
#define CHASSIS_ERR_TYPE (-4) /* ÔËÐÐÊ±³öÅäÖÃÁË´íÎóµÄChassis_Type_t */
	
#define MAX_MOTOR_CURRENT 20.0f 
/* µ×ÅÌ¿ØÖÆÄ£Ê½ */
typedef enum { 
  CHASSIS_MODE_RELAX, /* ·ÅËÉÄ£Ê½,µç»ú²»Êä³ö¡£Ò»°ãÇé¿öµ×ÅÌ³õÊ¼»¯Ö®ºóµÄÄ£Ê½ */
  CHASSIS_MODE_BREAK, /* É²³µÄ£Ê½£¬µç»ú±Õ»·¿ØÖÆ¾²Ö¹¡£ÓÃÓÚ»úÆ÷ÈËÍ£Ö¹×´Ì¬ */
  CHASSIS_MODE_FOLLOW_GIMBAL, /* Í¨¹ý±Õ»·¿ØÖÆÊ¹³µÍ··½Ïò¸úËæÔÆÌ¨ */
  CHASSIS_MODE_FOLLOW_GIMBAL_35, /* Í¨¹ý±Õ»·¿ØÖÆÊ¹³µÍ··½Ïò35¡ã¸úËæÔÆÌ¨ */
  CHASSIS_MODE_ROTOR, /* Ð¡ÍÓÂÝÄ£Ê½£¬Í¨¹ý±Õ»·¿ØÖÆÊ¹µ×ÅÌ²»Í£Ðý×ª */
  CHASSIS_MODE_INDEPENDENT, /*¶ÀÁ¢Ä£Ê½¡£µ×ÅÌÔËÐÐ²»ÊÜÔÆÌ¨Ó°Ïì */
  CHASSIS_MODE_OPEN, /* ¿ª»·Ä£Ê½¡£µ×ÅÌÔËÐÐ²»ÊÜPID¿ØÖÆ£¬Ö±½ÓÊä³öµ½µç»ú */
} Chassis_Mode_t;
	
/* Ð¡ÍÓÂÝ×ª¶¯Ä£Ê½ */
typedef enum {
  ROTOR_MODE_CW,   /* Ë³Ê±Õë×ª¶¯ */
  ROTOR_MODE_CCW,  /* ÄæÊ±Õë×ª¶¯ */
  ROTOR_MODE_RAND, /* Ëæ»ú×ª¶¯ */
} Chassis_RotorMode_t;

/* UI 导出结构（供 referee 系统绘制） */
typedef struct {
  Chassis_Mode_t mode;
  float angle;
} Chassis_RefereeUI_t;

/* µ×ÅÌ¿ØÖÆÃüÁî */
typedef struct {
  Chassis_Mode_t mode;     /* µ×ÅÌÔËÐÐÄ£Ê½ */
  Chassis_RotorMode_t mode_rotor; /* Ð¡ÍÓÂÝ×ª¶¯Ä£Ê½ */
  MoveVector_t ctrl_vec;      /* µ×ÅÌ¿ØÖÆÏòÁ¿ */
} Chassis_CMD_t;

/* ÏÞÎ» */
typedef struct {
  float max;
  float min;
} Chassis_Limit_t;

	/* µ×ÅÌÀàÐÍ£¨µ×ÅÌµÄÎïÀíÉè¼Æ£© */
typedef enum {
  CHASSIS_TYPE_MECANUM,    /* Âó¿ËÄÉÄ·ÂÖ */
  CHASSIS_TYPE_PARLFIX4,   /* Æ½ÐÐ°Ú·ÅµÄËÄ¸öÇý¶¯ÂÖ */
  CHASSIS_TYPE_PARLFIX2,   /* Æ½ÐÐ°Ú·ÅµÄÁ½¸öÇý¶¯ÂÖ */
  CHASSIS_TYPE_OMNI_CROSS, /* ²æÐÍ°Ú·ÅµÄËÄ¸öÈ«ÏòÂÖ */
  CHASSIS_TYPE_OMNI_PLUS,  /* Ê®×ÖÐÍ°ÚÉèµÄËÄ¸öÈ«ÏòÂÖ */
  CHASSIS_TYPE_DRONE,      /* ÎÞÈË»úµ×ÅÌ */
  CHASSIS_TYPE_SINGLE,     /* µ¥¸öÄ¦²ÁÂÖ */
} Chassis_Type_t;


/* µ×ÅÌ²ÎÊý½á¹¹Ìå,ALL³õÊ¼»¯²ÎÊý */
typedef struct {
	MOTOR_RM_Param_t motor_param[4];
	  struct {
    KPID_Params_t motor_pid_param;  /* µ×ÅÌµç»úPID²ÎÊý */
    KPID_Params_t follow_pid_param; /* ¸úËæÔÆÌ¨PID²ÎÊý */
  } pid;
  Chassis_Type_t type; /* µ×ÅÌÀàÐÍ£¬µ×ÅÌµÄ»úÐµÉè¼ÆºÍÂÖ×ÓÑ¡ÐÍ */

  /* µÍÍ¨ÂË²¨Æ÷½ØÖÁÆµÂÊ*/
  struct {
    float in;  /* ÊäÈë */
    float out; /* Êä³ö */
  } low_pass_cutoff_freq;

  /* µç»ú·´×°£¬Ó¦¸ÃºÍÔÆÌ¨ÉèÖÃÏàÍ¬*/
  struct {
    bool yaw;
  } reverse;
	struct {
        float max_vx, max_vy, max_wz;
        float max_current; 
    } limit; 
} Chassis_Params_t;

typedef struct {
  AHRS_Gyro_t gyro;
  AHRS_Eulr_t eulr;
} Chassis_IMU_t;

typedef struct {
  MOTOR_Feedback_t motor[4];          // ËÄ¸ö 3508µç»ú ·´À¡
	float encoder_gimbalYawMotor;
} Chassis_Feedback_t;

/* µ×ÅÌÊä³ö½á¹¹Ìå*/
typedef struct {
	float motor[4];  
} Chassis_Output_t;

/*
 * ÔËÐÐµÄÖ÷½á¹¹Ìå£þ
 * °üº¬³õÊ¼»¯²ÎÊý,ÖÐ¼ä±äÁ¿,Êä³ö±äÁ¿
 */
typedef struct {
  uint64_t last_wakeup;
  float dt;

  Chassis_Params_t *param; /* µ×ÅÌ²ÎÊý,ÓÃChassis_InitÉè¶¨ */

  /* Ä£¿éÍ¨ÓÃ */
  Chassis_Mode_t mode; /* µ×ÅÌÄ£Ê½ */


  /* µ×ÅÌÉè¼Æ */
  int8_t num_wheel; /* µ×ÅÌÂÖ×ÓÊýÁ¿ */
  Mixer_t mixer;    /* »ìºÏÆ÷,ÒÆ¶¯ÏòÁ¿->µç»úÄ¿±êÖµ */
  MoveVector_t move_vec; /* µ×ÅÌÊµ¼ÊµÄÔË¶¯ÏòÁ¿ */
  MOTOR_RM_t *motors[4];/*Ö¸Ïòµ×ÅÌÃ¿¸öµç»ú²ÎÊý*/
	float mech_zero;
  float wz_multi; /* Ð¡ÍÓÂÝÐý×ªÄ£Ê½ */

  /* PID¼ÆËãÄ¿±êÖµ */
  struct {
    float motor_rpm[4]; /* µç»ú×ªËÙµÄ¶¯Ì¬Êý×é,µ¥Î»:RPM */
  } setpoint;

  /* ·´À¡¿ØÖÆÓÃµÄPID */
  struct {
    KPID_t motor[4]; /* ¿ØÖÆÂÖ×Óµç»úÓÃµÄPIDµÄ¶¯Ì¬Êý×é */
    KPID_t follow; /* ¸úËæÔÆÌ¨ÓÃµÄPID */
  } pid;
 
	struct {
        Chassis_Limit_t vx, vy, wz; 
    } limit; 
	
  /* ÂË²¨Æ÷ */
  struct {
    LowPassFilter2p_t in[4];  /* ·´À¡ÖµÂË²¨Æ÷ */
    LowPassFilter2p_t out[4]; /* Êä³öÖµÂË²¨Æ÷ */
  } filter;

  Chassis_Output_t out; /* µç»úÊä³ö */
	Chassis_Feedback_t feedback;
	//float out_motor[4];
} Chassis_t;

/* Exported functions prototypes -------------------------------------------- */

/**
 * \brief µ×ÅÌ³õÊ¼»¯
 *
 * \param c °üº¬µ×ÅÌÊý¾ÝµÄ½á¹¹Ìå
 * \param param °üº¬µ×ÅÌ²ÎÊýµÄ½á¹¹ÌåÖ¸Õë
 * \param target_freq ÈÎÎñÔ¤ÆÚµÄÔËÐÐÆµÂÊ
 *
 * \return ÔËÐÐ½á¹û
 */
int8_t Chassis_Init(Chassis_t *c, const Chassis_Params_t *param,
                    float target_freq);

/**
 * \brief ¸üÐÂµ×ÅÌ·´À¡ÐÅÏ¢
 *
 * \param c °üº¬µ×ÅÌÊý¾ÝµÄ½á¹¹Ìå
 * \param can CANÉè±¸½á¹¹Ìå
 *
 * \return ÔËÐÐ½á¹û
 */
int8_t Chassis_UpdateFeedback(Chassis_t *c);

/**
 * \brief ÔËÐÐµ×ÅÌ¿ØÖÆÂß¼­
 *
 * \param c °üº¬µ×ÅÌÊý¾ÝµÄ½á¹¹Ìå
 * \param c_cmd µ×ÅÌ¿ØÖÆÖ¸Áî
 * \param dt_sec Á½´Îµ÷ÓÃµÄÊ±¼ä¼ä¸ô
 *
 * \return ÔËÐÐ½á¹û
 */
int8_t Chassis_Control(Chassis_t *c, const Chassis_CMD_t *c_cmd,
                       uint32_t now);


/**
 * \brief ¸´ÖÆµ×ÅÌÊä³öÖµ
 *
 * \param s °üº¬µ×ÅÌÊý¾ÝµÄ½á¹¹Ìå
 * \param out CANÉè±¸µ×ÅÌÊä³ö½á¹¹Ìå
 */
void Chassis_Output(Chassis_t *c);

/**
 * \brief Çå¿ÕChassisÊä³öÊý¾Ý
 *
 * \param out CANÉè±¸µ×ÅÌÊä³ö½á¹¹Ìå
 */
void Chassis_ResetOutput(Chassis_t *c);


void Chassis_Power_Control(Chassis_t *c,float max_power);
/**
 * @brief µ×ÅÌ¹¦ÂÊÏÞÖÆ
 *
 * @param c µ×ÅÌÊý¾Ý
 * @param cap µçÈÝÊý¾Ý
 * @param ref ²ÃÅÐÏµÍ³Êý¾Ý
 * @return º¯ÊýÔËÐÐ½á¹û
 */
//»¹Ã»ÓÐ¼ÓÈë£¬waiting¡£¡£¡£¡£¡£¡£int8_t Chassis_PowerLimit(Chassis_t *c, const CAN_Capacitor_t *cap,
//                          const Referee_ForChassis_t *ref);


/**
 * @brief µ¼³öµ×ÅÌÊý¾Ý
 *
 * @param chassis µ×ÅÌÊý¾Ý½á¹¹Ìå
 * @param ui UIÊý¾Ý½á¹¹Ìå
 */
//void Chassis_DumpUI(const Chassis_t *c, Chassis_RefereeUI_t *ui);

void Chassis_DumpUI(const Chassis_t *c, Chassis_RefereeUI_t *ui);

#ifdef __cplusplus
}
#endif




