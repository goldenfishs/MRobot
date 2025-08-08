/*
        DR16接收机
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
  if (motor->reverse) {
    return -motor->feedback.rotor_abs_angle;
  }else{
    return motor->feedback.rotor_abs_angle;
  }
}

float MOTOR_GetRotorSpeed(const MOTOR_t *motor) {
  if (motor == NULL) return DEVICE_ERR_NULL;
  if (motor->reverse) {
    return -motor->feedback.rotor_speed;
  }else{
    return motor->feedback.rotor_speed;
  }
}

float MOTOR_GetTorqueCurrent(const MOTOR_t *motor) {
  if (motor == NULL) return DEVICE_ERR_NULL;
  if (motor->reverse) {
    return -motor->feedback.torque_current;
  }else{
    return motor->feedback.torque_current;
  }
}

float MOTOR_GetTemp(const MOTOR_t *motor) {
  if (motor == NULL) return DEVICE_ERR_NULL;
  return motor->feedback.temp;
}
