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
const MOTOR_TemperatureProtectionConfig_t kMotorDefaultTemperatureProtection = {
  .warning_c = 70.0f,
  .limit_c = 80.0f,
  .auto_relax_on_limit = true,
};

/* Private function  -------------------------------------------------------- */
/* USER FUNCTION BEGIN */

/* USER FUNCTION END */

/* Exported functions ------------------------------------------------------- */
float MOTOR_GetRotorAbsAngle(const MOTOR_t *motor) {
  if (motor == NULL) return DEVICE_ERR_NULL;
  return motor->feedback.rotor_abs_angle;
}

float MOTOR_GetRotorSingleAngle(const MOTOR_t *motor) {
  if (motor == NULL) return DEVICE_ERR_NULL;
  return motor->feedback.rotor_single_angle;
}

float MOTOR_GetRotorTotalAngle(const MOTOR_t *motor) {
  if (motor == NULL) return DEVICE_ERR_NULL;
  return motor->feedback.rotor_total_angle;
}

bool MOTOR_IsAngleValid(const MOTOR_t *motor) {
  if (motor == NULL) return false;
  return motor->feedback.angle_valid;
}

uint32_t MOTOR_GetAngleLostCount(const MOTOR_t *motor) {
  if (motor == NULL) return 0U;
  return motor->feedback.angle_lost_count;
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

/* MOTOR_CPP_ADAPTER_API: exposes raw protocol feedback to C++ wrappers. */
const MOTOR_RawFeedback_t* MOTOR_GetRawFeedback(const MOTOR_t *motor) {
  if (motor == NULL) return NULL;
  return &motor->raw_feedback;
}

MOTOR_TemperatureProtectionConfig_t MOTOR_NormalizeTemperatureProtection(
    MOTOR_TemperatureProtectionConfig_t config) {
  if (config.warning_c <= 0.0f) {
    config.warning_c = kMotorDefaultTemperatureProtection.warning_c;
  }
  if (config.limit_c <= 0.0f) {
    config.limit_c = kMotorDefaultTemperatureProtection.limit_c;
  }
  if (config.warning_c > config.limit_c) {
    config.warning_c = config.limit_c;
  }
  return config;
}
