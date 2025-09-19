/*
    电机通用函数
*/

/* Includes ----------------------------------------------------------------- */
#include "motor.h"

#include <string.h>

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */


/* Private define ----------------------------------------------------------- */
/* USER DEFINE BEGIN */

/* USER DEFINE END */

/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* USER STRUCT BEGIN */

/* USER STRUCT END */

/* Private variables -------------------------------------------------------- */

/* Private function  -------------------------------------------------------- */
/* USER FUNCTION BEGIN */

/* USER FUNCTION END */

/* Exported functions ------------------------------------------------------- */
float MOTOR_GetRotorAbsAngle(const MOTOR_t *motor) {
  if (motor == NULL) return DEVICE_ERR_NULL;
  return motor->feedback.rotor_abs_angle;
}

float MOTOR_GetRotorSpeed(const MOTOR_t *motor) {
  if (motor == NULL) return DEVICE_ERR_NULL;
  return motor->feedback.rotor_speed;
}

float MOTOR_GetTorqueCurrent(const MOTOR_t *motor) {
  if (motor == NULL) return DEVICE_ERR_NULL;
  return motor->feedback.torque_current;
}

float MOTOR_GetTemp(const MOTOR_t *motor) {
  if (motor == NULL) return DEVICE_ERR_NULL;
  return motor->feedback.temp;
}
