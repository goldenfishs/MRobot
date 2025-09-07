/*
    电机通用函数
*/

/* Includes ----------------------------------------------------------------- */
#include "motor.h"

#include <string.h>


/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */

/* Private function  -------------------------------------------------------- */

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
