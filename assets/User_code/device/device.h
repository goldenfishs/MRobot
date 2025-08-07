#pragma once

#ifdef __cplusplus
extern "C" {
#endif

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

#ifdef __cplusplus
}
#endif
