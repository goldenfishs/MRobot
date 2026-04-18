/**
 * @file putty.c
 * @brief Putty CLI 实现
 */

/* Includes ----------------------------------------------------------------- */
#include "device/putty.h"
#include "component/freertos_cli.h"
#include "bsp/uart.h"
#include "bsp/mm.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <FreeRTOS.h>
#include <task.h>
#include <semphr.h>
#include <cmsis_os2.h>

/* Private constants -------------------------------------------------------- */
static const char *const CLI_WELCOME_MESSAGE =
    "\r\n"
    "  __  __ _____       _           _   \r\n"
    " |  \\/  |  __ \\     | |         | |  \r\n"
    " | \\  / | |__) |___ | |__   ___ | |_ \r\n"
    " | |\\/| |  _  // _ \\| '_ \\ / _ \\| __|\r\n"
    " | |  | | | \\ \\ (_) | |_) | (_) | |_ \r\n"
    " |_|  |_|_|  \\_\\___/|_.__/ \\___/ \\__|\r\n"
    " ------------------------------------\r\n"
    " Welcome to use MRobot CLI. Type 'help' to view a list of registered commands.\r\n"
    "\r\n";

/* ANSI 转义序列 */
#define ANSI_CLEAR_SCREEN   "\033[2J\033[H"
#define ANSI_CURSOR_HOME    "\033[H"
#define ANSI_BACKSPACE      "\b \b"

/* Private types ------------------------------------------------------------ */
/* CLI 上下文结构体 - 封装所有状态 */
typedef struct {
    /* 设备管理 */
    Putty_Device_t devices[PUTTY_MAX_DEVICES];
    uint8_t device_count;
    
    /* 自定义命令 */
    CLI_Command_Definition_t *custom_cmds[PUTTY_MAX_CUSTOM_COMMANDS];
    uint8_t custom_cmd_count;
    
    /* CLI 状态 */
    Putty_State_t state;
    char current_path[PUTTY_PATH_MAX_LEN];
    
    /* 命令缓冲区 */
    uint8_t cmd_buffer[PUTTY_CMD_BUFFER_SIZE];
    volatile uint8_t cmd_index;
    volatile bool cmd_ready;
    
    /* UART 相关 */
    uint8_t uart_rx_char;
    volatile bool tx_complete;
    volatile bool htop_exit;
    
    /* 输出缓冲区 */
    char output_buffer[PUTTY_OUTPUT_BUFFER_SIZE];
    
    /* 初始化标志 */
    bool initialized;
    
    /* 互斥锁 */
    SemaphoreHandle_t mutex;
} Putty_Context_t;

/* Private variables -------------------------------------------------------- */
static Putty_Context_t ctx = {
    .device_count = 0,
    .custom_cmd_count = 0,
    .state = PUTTY_STATE_IDLE,
    .current_path = "/",
    .cmd_index = 0,
    .cmd_ready = false,
    .tx_complete = true,
    .htop_exit = false,
    .initialized = false,
    .mutex = NULL
};

/* Private function prototypes ---------------------------------------------- */
static BaseType_t cmd_help(char *pcWriteBuffer, size_t xWriteBufferLen, const char *pcCommandString);
static BaseType_t cmd_htop(char *pcWriteBuffer, size_t xWriteBufferLen, const char *pcCommandString);
static BaseType_t cmd_cd(char *pcWriteBuffer, size_t xWriteBufferLen, const char *pcCommandString);
static BaseType_t cmd_ls(char *pcWriteBuffer, size_t xWriteBufferLen, const char *pcCommandString);
static BaseType_t cmd_show(char *pcWriteBuffer, size_t xWriteBufferLen, const char *pcCommandString);

/* 内部辅助函数 */
static void uart_tx_callback(void);
static void uart_rx_callback(void);
static void send_string(const char *str);
static void send_prompt(void);
static int format_float_va(char *buf, size_t size, const char *fmt, va_list args);

/* CLI 命令定义表 */
static const CLI_Command_Definition_t builtin_commands[] = {
    { "help", " --help: 显示所有可用命令\r\n", cmd_help, 0 },
    { "htop", " --htop: 动态显示 FreeRTOS 任务状态 (按 'q' 退出)\r\n", cmd_htop, 0 },
    { "cd",   " --cd <path>: 切换目录\r\n", cmd_cd, 1 },
    { "ls",   " --ls: 列出当前目录内容\r\n", cmd_ls, 0 },
    { "show", " --show [device] [count]: 显示设备信息\r\n", cmd_show, -1 },
};
#define BUILTIN_CMD_COUNT (sizeof(builtin_commands) / sizeof(builtin_commands[0]))

/* ========================================================================== */
/*                              辅助函数实现                                    */
/* ========================================================================== */

/**
 * @brief 发送字符串到 UART（阻塞等待完成）
 */
static void send_string(const char *str) {
    if (str == NULL || *str == '\0') return;
    
    ctx.tx_complete = false;
    BSP_UART_Transmit(BSP_UART_MROBOT, (uint8_t *)str, strlen(str), true);
    while (!ctx.tx_complete) { osDelay(1); }
}

/**
 * @brief 发送命令提示符
 */
static void send_prompt(void) {
    char prompt[PUTTY_PATH_MAX_LEN + 32];
    snprintf(prompt, sizeof(prompt), PUTTY_USER_NAME "@" PUTTY_HOST_NAME ":%s$ ", ctx.current_path);
    send_string(prompt);
}

/**
 * @brief UART 发送完成回调
 */
static void uart_tx_callback(void) {
    ctx.tx_complete = true;
}

/**
 * @brief UART 接收回调
 */
static void uart_rx_callback(void) {
    uint8_t ch = ctx.uart_rx_char;
    
    /* htop 模式下检查退出键 */
    if (ctx.state == PUTTY_STATE_HTOP) {
        if (ch == 'q' || ch == 'Q' || ch == 27) {
            ctx.htop_exit = true;
        }
        BSP_UART_Receive(BSP_UART_MROBOT, &ctx.uart_rx_char, 1, false);
        return;
    }
    
    /* 正常命令输入处理 */
    if (ch == '\r' || ch == '\n') {
        if (ctx.cmd_index > 0) {
            ctx.cmd_buffer[ctx.cmd_index] = '\0';
            ctx.cmd_ready = true;
            BSP_UART_Transmit(BSP_UART_MROBOT, (uint8_t *)"\r\n", 2, false);
        }
    } else if (ch == 127 || ch == 8) {  /* 退格键 */
        if (ctx.cmd_index > 0) {
            ctx.cmd_index--;
            BSP_UART_Transmit(BSP_UART_MROBOT, (uint8_t *)ANSI_BACKSPACE, 3, false);
        }
    } else if (ch >= 32 && ch < 127 && ctx.cmd_index < sizeof(ctx.cmd_buffer) - 1) {
        ctx.cmd_buffer[ctx.cmd_index++] = ch;
        /* 回显：使用静态变量地址，避免异步发送时局部变量已失效 */
        BSP_UART_Transmit(BSP_UART_MROBOT, &ctx.uart_rx_char, 1, false);
    }
    
    BSP_UART_Receive(BSP_UART_MROBOT, &ctx.uart_rx_char, 1, false);
}

/* ========================================================================== */
/*                             CLI 命令实现                                     */
/* ========================================================================== */

/**
 * @brief help 命令 - 显示帮助信息
 */
static BaseType_t cmd_help(char *pcWriteBuffer, size_t xWriteBufferLen, const char *pcCommandString) {
    (void)pcCommandString;
    
    int offset = snprintf(pcWriteBuffer, xWriteBufferLen,
        "Putty CLI v2.0\r\n"
        "================\r\n"
        "Built-in Commands:\r\n");
    
    for (size_t i = 0; i < BUILTIN_CMD_COUNT && offset < (int)xWriteBufferLen - 50; i++) {
        offset += snprintf(pcWriteBuffer + offset, xWriteBufferLen - offset,
            "  %s", builtin_commands[i].pcHelpString);
    }
    
    if (ctx.custom_cmd_count > 0) {
        offset += snprintf(pcWriteBuffer + offset, xWriteBufferLen - offset,
            "\r\nCustom Commands:\r\n");
        for (uint8_t i = 0; i < ctx.custom_cmd_count && offset < (int)xWriteBufferLen - 50; i++) {
            if (ctx.custom_cmds[i] != NULL) {
                offset += snprintf(pcWriteBuffer + offset, xWriteBufferLen - offset,
                    "  %s", ctx.custom_cmds[i]->pcHelpString);
            }
        }
    }
    
    return pdFALSE;
}

/**
 * @brief htop 命令 - 设置 htop 模式标志
 */
static BaseType_t cmd_htop(char *pcWriteBuffer, size_t xWriteBufferLen, const char *pcCommandString) {
    (void)pcCommandString;
    (void)pcWriteBuffer;
    (void)xWriteBufferLen;
    /* htop 模式在 Putty_Run 中处理 */
    return pdFALSE;
}

/**
 * @brief cd 命令 - 切换目录
 */
static BaseType_t cmd_cd(char *pcWriteBuffer, size_t xWriteBufferLen, const char *pcCommandString) {
    const char *param;
    BaseType_t param_len;
    
    param = FreeRTOS_CLIGetParameter(pcCommandString, 1, &param_len);
    
    if (param == NULL) {
        /* 无参数时切换到根目录 */
        strcpy(ctx.current_path, "/");
        snprintf(pcWriteBuffer, xWriteBufferLen, "Changed to: %s\r\n", ctx.current_path);
        return pdFALSE;
    }
    
    /* 安全复制路径参数 */
    char path[PUTTY_PATH_MAX_LEN];
    size_t copy_len = (size_t)param_len < sizeof(path) - 1 ? (size_t)param_len : sizeof(path) - 1;
    strncpy(path, param, copy_len);
    path[copy_len] = '\0';
    
    /* 路径解析 */
    if (strcmp(path, "/") == 0 || strcmp(path, "..") == 0 || strcmp(path, "~") == 0) {
        strcpy(ctx.current_path, "/");
    } else if (strcmp(path, "dev") == 0 || strcmp(path, "/dev") == 0) {
        strcpy(ctx.current_path, "/dev");
    } else if (strcmp(path, "modules") == 0 || strcmp(path, "/modules") == 0) {
        strcpy(ctx.current_path, "/modules");
    } else {
        snprintf(pcWriteBuffer, xWriteBufferLen, "Error: Directory '%s' not found\r\n", path);
        return pdFALSE;
    }
    
    snprintf(pcWriteBuffer, xWriteBufferLen, "Changed to: %s\r\n", ctx.current_path);
    return pdFALSE;
}

/**
 * @brief ls 命令 - 列出目录内容
 */
static BaseType_t cmd_ls(char *pcWriteBuffer, size_t xWriteBufferLen, const char *pcCommandString) {
    (void)pcCommandString;
    int offset = 0;
    
    if (strcmp(ctx.current_path, "/") == 0) {
        snprintf(pcWriteBuffer, xWriteBufferLen, 
            "dev/\r\n"
            "modules/\r\n");
    } else if (strcmp(ctx.current_path, "/dev") == 0) {
        offset = snprintf(pcWriteBuffer, xWriteBufferLen, 
            "Device List (%d devices)\r\n\r\n", 
            ctx.device_count);
        
        if (ctx.device_count == 0) {
            offset += snprintf(pcWriteBuffer + offset, xWriteBufferLen - offset, 
                              "  (No devices)\r\n");
        } else {
            /* 直接列出所有设备 */
            for (uint8_t i = 0; i < ctx.device_count && offset < (int)xWriteBufferLen - 50; i++) {
                offset += snprintf(pcWriteBuffer + offset, xWriteBufferLen - offset,
                    "  - %s\r\n", ctx.devices[i].name);
            }
        }
    } else if (strcmp(ctx.current_path, "/modules") == 0) {
        snprintf(pcWriteBuffer, xWriteBufferLen, 
            "Module functions not yet implemented\r\n");
    }
    
    return pdFALSE;
}

/**
 * @brief show 命令 - 显示设备信息
 */
static BaseType_t cmd_show(char *pcWriteBuffer, size_t xWriteBufferLen, const char *pcCommandString) {
    const char *param;
    const char *count_param;
    BaseType_t param_len, count_param_len;
    
    /* 使用局部静态变量跟踪多次打印状态 */
    static uint32_t print_count = 0;
    static uint32_t current_iter = 0;
    static char target_device[PUTTY_DEVICE_NAME_LEN] = {0};
    
    /* 首次调用时解析参数 */
    if (current_iter == 0) {
        /* 检查是否在 /dev 目录 */
        if (strcmp(ctx.current_path, "/dev") != 0) {
            snprintf(pcWriteBuffer, xWriteBufferLen, 
                "Error: 'show' command only works in /dev directory\r\n"
                "Hint: Use 'cd /dev' to switch to device directory\r\n");
            return pdFALSE;
        }
        
        param = FreeRTOS_CLIGetParameter(pcCommandString, 1, &param_len);
        count_param = FreeRTOS_CLIGetParameter(pcCommandString, 2, &count_param_len);
        
        /* 解析打印次数 */
        print_count = 1;
        if (count_param != NULL) {
            char count_str[16];
            size_t copy_len = (size_t)count_param_len < sizeof(count_str) - 1 ? 
                              (size_t)count_param_len : sizeof(count_str) - 1;
            strncpy(count_str, count_param, copy_len);
            count_str[copy_len] = '\0';
            int parsed = atoi(count_str);
            if (parsed > 0 && parsed <= 1000) {
                print_count = (uint32_t)parsed;
            }
        }
        
        /* 保存目标设备名称 */
        if (param != NULL) {
            size_t copy_len = (size_t)param_len < sizeof(target_device) - 1 ? 
                              (size_t)param_len : sizeof(target_device) - 1;
            strncpy(target_device, param, copy_len);
            target_device[copy_len] = '\0';
        } else {
            target_device[0] = '\0';
        }
    }
    
    int offset = 0;
    
    /* 连续打印模式：清屏 */
    if (print_count > 1) {
        offset = snprintf(pcWriteBuffer, xWriteBufferLen, "%s[%lu/%lu]\r\n",
                          ANSI_CLEAR_SCREEN,
                          (unsigned long)(current_iter + 1), 
                          (unsigned long)print_count);
    }
    
    if (target_device[0] == '\0') {
        /* 显示所有设备 */
        offset += snprintf(pcWriteBuffer + offset, xWriteBufferLen - offset,
                          "=== All Devices ===\r\n\r\n");
        
        for (uint8_t i = 0; i < ctx.device_count && offset < (int)xWriteBufferLen - 100; i++) {
            offset += snprintf(pcWriteBuffer + offset, xWriteBufferLen - offset,
                              "--- %s ---\r\n", ctx.devices[i].name);
            
            if (ctx.devices[i].print_cb != NULL) {
                int written = ctx.devices[i].print_cb(ctx.devices[i].data,
                                                       pcWriteBuffer + offset,
                                                       xWriteBufferLen - offset);
                offset += (written > 0) ? written : 0;
            } else {
                offset += snprintf(pcWriteBuffer + offset, xWriteBufferLen - offset,
                                  "  (No print function)\r\n");
            }
        }
        
        if (ctx.device_count == 0) {
            offset += snprintf(pcWriteBuffer + offset, xWriteBufferLen - offset,
                              "  (No devices registered)\r\n");
        }
    } else {
        /* 显示指定设备 */
        const Putty_Device_t *dev = Putty_FindDevice(target_device);
        
        if (dev == NULL) {
            snprintf(pcWriteBuffer, xWriteBufferLen, 
                    "Error: Device '%s' not found\r\n", 
                    target_device);
            current_iter = 0;
            return pdFALSE;
        }
        
        offset += snprintf(pcWriteBuffer + offset, xWriteBufferLen - offset,
                          "=== %s ===\r\n", dev->name);
        
        if (dev->print_cb != NULL) {
            dev->print_cb(dev->data, pcWriteBuffer + offset, xWriteBufferLen - offset);
        } else {
            snprintf(pcWriteBuffer + offset, xWriteBufferLen - offset,
                    "  (No print function)\r\n");
        }
    }
    
    /* 判断是否继续打印 */
    current_iter++;
    if (current_iter < print_count) {
        osDelay(PUTTY_HTOP_REFRESH_MS);
        return pdTRUE;
    } else {
        current_iter = 0;
        return pdFALSE;
    }
}

/* ============================================================================
 * htop 模式处理
 * ========================================================================== */
static void handle_htop_mode(void) {
    send_string(ANSI_CLEAR_SCREEN);
    send_string("=== Putty Task Monitor (Press 'q' to exit) ===\r\n\r\n");
    
    /* 获取任务列表 */
    char task_buffer[1024];
    char display_line[128];
    
    vTaskList(task_buffer);
    
    /* 表头 */
    send_string("Task Name         State    Prio  Stack  Num\r\n");
    send_string("------------------------------------------------\r\n");
    
    /* 解析并格式化任务列表 */
    char *line = strtok(task_buffer, "\r\n");
    while (line != NULL) {
        char name[17] = {0};
        char state_char = '?';
        int prio = 0, stack = 0, num = 0;
        
        if (sscanf(line, "%16s %c %d %d %d", name, &state_char, &prio, &stack, &num) == 5) {
            const char *state_str;
            switch (state_char) {
                case 'R': state_str = "Running"; break;
                case 'B': state_str = "Blocked"; break;
                case 'S': state_str = "Suspend"; break;
                case 'D': state_str = "Deleted"; break;
                case 'X': state_str = "Ready  "; break;
                default:  state_str = "Unknown"; break;
            }
            
            snprintf(display_line, sizeof(display_line),
                    "%-16s %-8s %-4d %-8d %-4d\r\n",
                    name, state_str, prio, stack, num);
            send_string(display_line);
        }
        line = strtok(NULL, "\r\n");
    }
    
    /* 显示系统信息 */
    snprintf(display_line, sizeof(display_line),
            "------------------------------------------------\r\n"
            "System Tick: %lu | Free Heap: %lu bytes\r\n",
            (unsigned long)xTaskGetTickCount(),
            (unsigned long)xPortGetFreeHeapSize());
    send_string(display_line);
    
    /* 检查退出 */
    if (ctx.htop_exit) {
        ctx.state = PUTTY_STATE_IDLE;
        ctx.htop_exit = false;
        send_string(ANSI_CLEAR_SCREEN);
        send_prompt();
    }
    
    osDelay(PUTTY_HTOP_REFRESH_MS);
}

/* ========================================================================== */
/*                              公共 API 实现                                   */
/* ========================================================================== */

void Putty_Init(void) {
    if (ctx.initialized) return;
    
    /* 创建互斥锁 */
    ctx.mutex = xSemaphoreCreateMutex();
    
    /* 初始化状态（保留已注册的设备） */
    // 注意：不清除 devices 和 device_count，因为其他任务可能已经注册了设备
    ctx.custom_cmd_count = 0;
    ctx.state = PUTTY_STATE_IDLE;
    strcpy(ctx.current_path, "/");
    ctx.cmd_index = 0;
    ctx.cmd_ready = false;
    ctx.tx_complete = true;
    ctx.htop_exit = false;
    
    /* 注册内置命令 */
    for (size_t i = 0; i < BUILTIN_CMD_COUNT; i++) {
        FreeRTOS_CLIRegisterCommand(&builtin_commands[i]);
    }
    
    /* 注册 UART 回调 */
    BSP_UART_RegisterCallback(BSP_UART_MROBOT, BSP_UART_RX_CPLT_CB, uart_rx_callback);
    BSP_UART_RegisterCallback(BSP_UART_MROBOT, BSP_UART_TX_CPLT_CB, uart_tx_callback);
    
    /* 启动 UART 接收 */
    BSP_UART_Receive(BSP_UART_MROBOT, &ctx.uart_rx_char, 1, false);
    
    /* 等待用户按下回车 */
    while (ctx.uart_rx_char != '\r' && ctx.uart_rx_char != '\n') {
        osDelay(10);
    }
    
    /* 发送欢迎消息和提示符 */
    send_string(CLI_WELCOME_MESSAGE);
    send_prompt();
    
    ctx.initialized = true;
}

void Putty_DeInit(void) {
    if (!ctx.initialized) return;
    
    /* 释放自定义命令内存 */
    for (uint8_t i = 0; i < ctx.custom_cmd_count; i++) {
        if (ctx.custom_cmds[i] != NULL) {
            BSP_Free(ctx.custom_cmds[i]);
            ctx.custom_cmds[i] = NULL;
        }
    }
    
    /* 删除互斥锁 */
    if (ctx.mutex != NULL) {
        vSemaphoreDelete(ctx.mutex);
        ctx.mutex = NULL;
    }
    
    ctx.initialized = false;
}

Putty_State_t Putty_GetState(void) {
    return ctx.state;
}

Putty_Error_t Putty_RegisterDevice(const char *name, void *data, Putty_PrintCallback_t print_cb) {
    if (name == NULL || data == NULL) {
        return PUTTY_ERR_NULL_PTR;
    }
    
    if (ctx.device_count >= PUTTY_MAX_DEVICES) {
        return PUTTY_ERR_FULL;
    }
    
    /* 检查重名 */
    for (uint8_t i = 0; i < ctx.device_count; i++) {
        if (strcmp(ctx.devices[i].name, name) == 0) {
            return PUTTY_ERR_INVALID_ARG;  /* 设备名已存在 */
        }
    }
    
    /* 线程安全写入 */
    if (ctx.mutex != NULL) {
        xSemaphoreTake(ctx.mutex, portMAX_DELAY);
    }
    
    strncpy(ctx.devices[ctx.device_count].name, name, PUTTY_DEVICE_NAME_LEN - 1);
    ctx.devices[ctx.device_count].name[PUTTY_DEVICE_NAME_LEN - 1] = '\0';
    ctx.devices[ctx.device_count].data = data;
    ctx.devices[ctx.device_count].print_cb = print_cb;
    ctx.device_count++;
    
    if (ctx.mutex != NULL) {
        xSemaphoreGive(ctx.mutex);
    }
    
    return PUTTY_OK;
}

Putty_Error_t Putty_UnregisterDevice(const char *name) {
    if (name == NULL) {
        return PUTTY_ERR_NULL_PTR;
    }
    
    if (ctx.mutex != NULL) {
        xSemaphoreTake(ctx.mutex, portMAX_DELAY);
    }
    
    for (uint8_t i = 0; i < ctx.device_count; i++) {
        if (strcmp(ctx.devices[i].name, name) == 0) {
            /* 移动后续设备 */
            for (uint8_t j = i; j < ctx.device_count - 1; j++) {
                ctx.devices[j] = ctx.devices[j + 1];
            }
            ctx.device_count--;
            
            if (ctx.mutex != NULL) {
                xSemaphoreGive(ctx.mutex);
            }
            return PUTTY_OK;
        }
    }
    
    if (ctx.mutex != NULL) {
        xSemaphoreGive(ctx.mutex);
    }
    return PUTTY_ERR_NOT_FOUND;
}

Putty_Error_t Putty_RegisterCommand(const char *command, const char *help_text,
                                       Putty_CommandCallback_t callback, int8_t param_count) {
    if (command == NULL || help_text == NULL || callback == NULL) {
        return PUTTY_ERR_NULL_PTR;
    }
    
    if (ctx.custom_cmd_count >= PUTTY_MAX_CUSTOM_COMMANDS) {
        return PUTTY_ERR_FULL;
    }
    
    /* 动态分配命令结构体 */
    CLI_Command_Definition_t *cmd_def = BSP_Malloc(sizeof(CLI_Command_Definition_t));
    if (cmd_def == NULL) {
        return PUTTY_ERR_ALLOC;
    }
    
    /* 初始化命令定义 */
    *(const char **)&cmd_def->pcCommand = command;
    *(const char **)&cmd_def->pcHelpString = help_text;
    *(pdCOMMAND_LINE_CALLBACK *)&cmd_def->pxCommandInterpreter = (pdCOMMAND_LINE_CALLBACK)callback;
    cmd_def->cExpectedNumberOfParameters = param_count;
    
    /* 注册到 FreeRTOS CLI */
    FreeRTOS_CLIRegisterCommand(cmd_def);
    
    ctx.custom_cmds[ctx.custom_cmd_count] = cmd_def;
    ctx.custom_cmd_count++;
    
    return PUTTY_OK;
}

uint8_t Putty_GetDeviceCount(void) {
    return ctx.device_count;
}

const Putty_Device_t *Putty_FindDevice(const char *name) {
    if (name == NULL) return NULL;
    
    for (uint8_t i = 0; i < ctx.device_count; i++) {
        if (strcmp(ctx.devices[i].name, name) == 0) {
            return &ctx.devices[i];
        }
    }
    return NULL;
}

int Putty_Printf(const char *fmt, ...) {
    if (fmt == NULL || !ctx.initialized) return -1;
    
    char buffer[PUTTY_OUTPUT_BUFFER_SIZE];
    va_list args;
    va_start(args, fmt);
    int len = format_float_va(buffer, sizeof(buffer), fmt, args);
    va_end(args);
    
    if (len > 0) {
        send_string(buffer);
    }
    return len;
}

/**
 * @brief 内部函数：格式化浮点数到缓冲区（va_list 版本）
 */
static int format_float_va(char *buf, size_t size, const char *fmt, va_list args) {
    if (buf == NULL || size == 0 || fmt == NULL) return 0;
    
    char *buf_ptr = buf;
    size_t buf_remain = size - 1;
    
    const char *p = fmt;
    while (*p && buf_remain > 0) {
        if (*p != '%') {
            *buf_ptr++ = *p++;
            buf_remain--;
            continue;
        }
        
        p++;  /* 跳过 '%' */
        
        /* 处理 %% */
        if (*p == '%') {
            *buf_ptr++ = '%';
            buf_remain--;
            p++;
            continue;
        }
        
        /* 解析精度 %.Nf */
        int precision = 2;  /* 默认精度 */
        if (*p == '.') {
            p++;
            precision = 0;
            while (*p >= '0' && *p <= '9') {
                precision = precision * 10 + (*p - '0');
                p++;
            }
            if (precision > 6) precision = 6;
        }
        
        int written = 0;
        switch (*p) {
            case 'f': {  /* 浮点数 */
                double val = va_arg(args, double);
                written = Putty_FormatFloat(buf_ptr, buf_remain, (float)val, precision);
                break;
            }
            case 'd':
            case 'i': {
                int val = va_arg(args, int);
                written = snprintf(buf_ptr, buf_remain, "%d", val);
                break;
            }
            case 'u': {
                unsigned int val = va_arg(args, unsigned int);
                written = snprintf(buf_ptr, buf_remain, "%u", val);
                break;
            }
            case 'x': {
                unsigned int val = va_arg(args, unsigned int);
                written = snprintf(buf_ptr, buf_remain, "%x", val);
                break;
            }
            case 'X': {
                unsigned int val = va_arg(args, unsigned int);
                written = snprintf(buf_ptr, buf_remain, "%X", val);
                break;
            }
            case 's': {
                const char *str = va_arg(args, const char *);
                if (str == NULL) str = "(null)";
                written = snprintf(buf_ptr, buf_remain, "%s", str);
                break;
            }
            case 'c': {
                int ch = va_arg(args, int);
                *buf_ptr = (char)ch;
                written = 1;
                break;
            }
            case 'l': {
                p++;
                if (*p == 'd' || *p == 'i') {
                    long val = va_arg(args, long);
                    written = snprintf(buf_ptr, buf_remain, "%ld", val);
                } else if (*p == 'u') {
                    unsigned long val = va_arg(args, unsigned long);
                    written = snprintf(buf_ptr, buf_remain, "%lu", val);
                } else if (*p == 'x' || *p == 'X') {
                    unsigned long val = va_arg(args, unsigned long);
                    written = snprintf(buf_ptr, buf_remain, *p == 'x' ? "%lx" : "%lX", val);
                } else {
                    p--;
                }
                break;
            }
            default: {
                *buf_ptr++ = '%';
                buf_remain--;
                if (buf_remain > 0) {
                    *buf_ptr++ = *p;
                    buf_remain--;
                }
                written = 0;
                break;
            }
        }
        
        if (written > 0) {
            buf_ptr += written;
            buf_remain -= (size_t)written;
        }
        p++;
    }
    
    *buf_ptr = '\0';
    return (int)(buf_ptr - buf);
}

int Putty_Snprintf(char *buf, size_t size, const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    int len = format_float_va(buf, size, fmt, args);
    va_end(args);
    return len;
}

int Putty_FormatFloat(char *buf, size_t size, float val, int precision) {
    if (buf == NULL || size == 0) return 0;
    
    int offset = 0;
    
    /* 处理负数 */
    if (val < 0) {
        if (offset < (int)size - 1) buf[offset++] = '-';
        val = -val;
    }
    
    /* 限制精度范围 */
    if (precision < 0) precision = 0;
    if (precision > 6) precision = 6;
    
    /* 计算乘数 */
    int multiplier = 1;
    for (int i = 0; i < precision; i++) multiplier *= 10;
    
    int int_part = (int)val;
    int frac_part = (int)((val - int_part) * multiplier + 0.5f);
    
    /* 处理进位 */
    if (frac_part >= multiplier) {
        int_part++;
        frac_part -= multiplier;
    }
    
    /* 格式化输出 */
    int written;
    if (precision > 0) {
        written = snprintf(buf + offset, size - offset, "%d.%0*d", int_part, precision, frac_part);
    } else {
        written = snprintf(buf + offset, size - offset, "%d", int_part);
    }
    return (written > 0) ? (offset + written) : offset;
}

void Putty_Run(void) {
    if (!ctx.initialized) return;
    
    /* htop 模式 */
    if (ctx.state == PUTTY_STATE_HTOP) {
        handle_htop_mode();
        return;
    }
    
    /* 处理命令 */
    if (ctx.cmd_ready) {
        ctx.state = PUTTY_STATE_PROCESSING;
        
        /* 检查是否是 htop 命令 */
        if (strcmp((char *)ctx.cmd_buffer, "htop") == 0) {
            ctx.state = PUTTY_STATE_HTOP;
            ctx.htop_exit = false;
        } else {
            /* 处理其他命令 */
            BaseType_t more;
            do {
                ctx.output_buffer[0] = '\0';
                more = FreeRTOS_CLIProcessCommand((char *)ctx.cmd_buffer,
                                                   ctx.output_buffer,
                                                   sizeof(ctx.output_buffer));
                
                if (ctx.output_buffer[0] != '\0') {
                    send_string(ctx.output_buffer);
                }
            } while (more != pdFALSE);
            
            send_prompt();
            ctx.state = PUTTY_STATE_IDLE;
        }
        
        ctx.cmd_index = 0;
        ctx.cmd_ready = false;
    }
    
    osDelay(10);
}
