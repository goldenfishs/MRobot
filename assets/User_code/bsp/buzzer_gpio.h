#pragma once

/* Includes ----------------------------------------------------------------- */
#include <stdint.h>

/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */

/* 设置BUZZER状态 */
typedef enum
{
    BSP_BUZZER_ON,
    BSP_BUZZER_OFF,
    BSP_BUZZER_TAGGLE,
} BSP_Buzzer_Status_t;

/* Exported functions prototypes -------------------------------------------- */

int8_t BSP_Buzzer_Set(BSP_Buzzer_Status_t s);
