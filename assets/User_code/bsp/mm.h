#pragma once

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ----------------------------------------------------------------- */
#include <stddef.h>
#include <stdint.h>

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* USER DEFINE BEGIN */

/* USER DEFINE END */

/* Exported types ----------------------------------------------------------- */
/* Exported functions prototypes -------------------------------------------- */
void *BSP_Malloc(size_t size);
void BSP_Free(void *pv);

/* USER FUNCTION BEGIN */

/* USER FUNCTION END */

#ifdef __cplusplus
}
#endif
