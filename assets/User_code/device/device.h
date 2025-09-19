#pragma once

#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>
#include <stdint.h>

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

/* USER DEFINE BEGIN */

/* USER DEFINE END */

#define DEVICE_OK (0)
#define DEVICE_ERR (-1)
#define DEVICE_ERR_NULL (-2)
#define DEVICE_ERR_INITED (-3)
#define DEVICE_ERR_NO_DEV (-4)

/* AUTO GENERATED SIGNALS BEGIN */

/* AUTO GENERATED SIGNALS END */

/* USER SIGNALS BEGIN */

/* USER SIGNALS END */
/*设备层通用Header*/
typedef struct {
    bool online;
    uint64_t last_online_time;
} DEVICE_Header_t;

/* USER STRUCT BEGIN */

/* USER STRUCT END */

/* USER FUNCTION BEGIN */

/* USER FUNCTION END */

#ifdef __cplusplus
}
#endif
