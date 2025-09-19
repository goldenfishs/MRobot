/* Includes ----------------------------------------------------------------- */
#include "bsp/mm.h"

#include "FreeRTOS.h"

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* USER DEFINE BEGIN */

/* USER DEFINE END */

/* Private variables -------------------------------------------------------- */
/* USER STRUCT BEGIN */

/* USER STRUCT END */

/* Private function  -------------------------------------------------------- */
/* Exported functions ------------------------------------------------------- */
inline void *BSP_Malloc(size_t size) { return pvPortMalloc(size); }

inline void BSP_Free(void *pv) { vPortFree(pv); }

/* USER FUNCTION BEGIN */

/* USER FUNCTION END */
