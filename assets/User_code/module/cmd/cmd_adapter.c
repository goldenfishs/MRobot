/*
 * CMD 模块 V2 - 输入适配器实现
 */
#include "cmd_adapter.h"
#include <string.h>

/* ========================================================================== */
/*                           适配器存储                                         */
/* ========================================================================== */
// static CMD_InputAdapter_t *g_adapters[CMD_SRC_NUM] = {0};
CMD_InputAdapter_t *g_adapters[CMD_SRC_NUM] = {0};
/* ========================================================================== */
/*                        DR16 抽象实现                                       */
/* ========================================================================== */
#if CMD_RC_DEVICE_TYPE == 0

int8_t CMD_DR16_Init(void *data) {
    DR16_t *dr16 = (DR16_t *)data;
    return DR16_Init(dr16);
}

int8_t CMD_DR16_RC_GetInput(void *data, CMD_RawInput_t *output) {
    DR16_t *dr16 = (DR16_t *)data;
    
    memset(&output->rc, 0, sizeof(CMD_RawInput_RC_t));
    
    output->online[CMD_SRC_RC] = dr16->header.online;
    
    /* 遥控器摇杆映射 */
    output->rc.joy_left.x  = dr16->data.rc.ch_l_x;
    output->rc.joy_left.y  = dr16->data.rc.ch_l_y;
    output->rc.joy_right.x = dr16->data.rc.ch_r_x;
    output->rc.joy_right.y = dr16->data.rc.ch_r_y;
    
    /* 拨杆映射 */
    switch (dr16->data.rc.sw_l) {
        case DR16_SW_UP:   output->rc.sw[0] = CMD_SW_UP;   break;
        case DR16_SW_MID:  output->rc.sw[0] = CMD_SW_MID;  break;
        case DR16_SW_DOWN: output->rc.sw[0] = CMD_SW_DOWN; break;
        default:           output->rc.sw[0] = CMD_SW_ERR;  break;
    }
    switch (dr16->data.rc.sw_r) {
        case DR16_SW_UP:   output->rc.sw[1] = CMD_SW_UP;   break;
        case DR16_SW_MID:  output->rc.sw[1] = CMD_SW_MID;  break;
        case DR16_SW_DOWN: output->rc.sw[1] = CMD_SW_DOWN; break;
        default:           output->rc.sw[1] = CMD_SW_ERR;  break;
    }
    
    /* 拨轮映射 */
    output->rc.dial = dr16->data.rc.ch_res;
    
    return CMD_OK;
}

int8_t CMD_DR16_PC_GetInput(void *data, CMD_RawInput_t *output) {
    DR16_t *dr16 = (DR16_t *)data;
    
    memset(&output->pc, 0, sizeof(CMD_RawInput_PC_t));
    
    output->online[CMD_SRC_PC] = dr16->header.online;
    
    /* PC端鼠标映射 */
    output->pc.mouse.x = dr16->data.pc.mouse.x;
    output->pc.mouse.y = dr16->data.pc.mouse.y;
    output->pc.mouse.l_click = dr16->data.pc.mouse.l_click;
    output->pc.mouse.r_click = dr16->data.pc.mouse.r_click;
    
    /* 键盘映射 */
    output->pc.keyboard.bitmap = dr16->raw_data.key;
    
    return CMD_OK;
}

bool CMD_DR16_IsOnline(void *data) {
    DR16_t *dr16 = (DR16_t *)data;
    return dr16->header.online;
}
extern DR16_t cmd_dr16;
/* 定义适配器实例 */
CMD_DEFINE_ADAPTER(DR16_RC, cmd_dr16, CMD_SRC_RC, CMD_DR16_Init, CMD_DR16_RC_GetInput, CMD_DR16_IsOnline)
CMD_DEFINE_ADAPTER(DR16_PC, cmd_dr16, CMD_SRC_PC, CMD_DR16_Init, CMD_DR16_PC_GetInput, CMD_DR16_IsOnline)

#endif /* CMD_RC_DEVICE_TYPE == 0 */

/* ========================================================================== */
/*                        AT9S 抽象实现 (示例框架)                            */
/* ========================================================================== */
#if CMD_RC_DEVICE_TYPE == 1

int8_t CMD_AT9S_Init(void *data) {
    AT9S_t *at9s = (AT9S_t *)data;
    return AT9S_Init(at9s);
}

int8_t CMD_AT9S_GetInput(void *data, CMD_RawInput_t *output) {
    AT9S_t *at9s = (AT9S_t *)data;
    
    memset(output, 0, sizeof(CMD_RawInput_RC_t));
    
    output->online[CMD_SRC_RC] = at9s->header.online;
    
    /* TODO: 按照AT9S的数据格式进行映射 */
    output->joy_left.x  = at9s->data.rc.ch_l_x;
    output->joy_left.y  = at9s->data.rc.ch_l_y;
    output->joy_right.x = at9s->data.rc.ch_r_x;
    output->joy_right.y = at9s->data.rc.ch_r_y;
    
    /* 拨杆映射需要根据AT9S的实际定义 */
    
    return CMD_OK;
}

bool CMD_AT9S_IsOnline(void *data) {
    AT9S_t *at9s = (AT9S_t *)data;
    return at9s->header.online;
}

CMD_DEFINE_ADAPTER(AT9S, at9s, CMD_SRC_RC, CMD_AT9S_Init, CMD_AT9S_GetInput, CMD_AT9S_IsOnline)

#endif /* CMD_RC_DEVICE_TYPE == 1 */

/* ========================================================================== */
/*                           适配器管理实现                                     */
/* ========================================================================== */

int8_t CMD_Adapter_Register(CMD_InputAdapter_t *adapter) {
    if (adapter == NULL || adapter->source >= CMD_SRC_NUM) {
        return CMD_ERR_NULL;
    }
    g_adapters[adapter->source] = adapter;
    return CMD_OK;
}

int8_t CMD_Adapter_InitAll(void) {
    /* 注册编译时选择的RC设备适配器 */
#if CMD_RC_DEVICE_TYPE == 0
    /* DR16 支持 RC 和 PC 输入 */
    CMD_Adapter_Register(&g_adapter_DR16_RC);
    CMD_Adapter_Register(&g_adapter_DR16_PC);
#elif CMD_RC_DEVICE_TYPE == 1
    /* AT9S 目前只支持 RC 输入 */
    CMD_Adapter_Register(&g_adapter_AT9S);
#endif
    
    /* 注册NUC适配器 */

    /* 注册REF适配器 */
    
    /* 初始化所有已注册的适配器 */
    for (int i = 0; i < CMD_SRC_NUM; i++) {
        if (g_adapters[i] != NULL && g_adapters[i]->init != NULL) {
            g_adapters[i]->init(g_adapters[i]->device_data);
        }
    }
    
    return CMD_OK;
}

int8_t CMD_Adapter_GetInput(CMD_InputSource_t source, CMD_RawInput_t *output) {
    if (source >= CMD_SRC_NUM || output == NULL) {
        return CMD_ERR_NULL;
    }
    
    CMD_InputAdapter_t *adapter = g_adapters[source];
    if (adapter == NULL || adapter->get_input == NULL) {
        output->online[adapter->source] = false;
        return CMD_ERR_NO_INPUT;
    }
    
    return adapter->get_input(adapter->device_data, output);
}

bool CMD_Adapter_IsOnline(CMD_InputSource_t source) {
    if (source >= CMD_SRC_NUM) {
        return false;
    }
    
    CMD_InputAdapter_t *adapter = g_adapters[source];
    if (adapter == NULL || adapter->is_online == NULL) {
        return false;
    }
    
    return adapter->is_online(adapter->device_data);
}
