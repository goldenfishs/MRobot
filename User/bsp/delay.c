#include "bsp_delay.h"

#include "cmsis_os.h"
#include "main.h"

/* Private define ----------------------------------------------------------- */
/* Private macro ------------------------------------------------------------ */
/* Private typedef ---------------------------------------------------------- */
/* Private variables -------------------------------------------------------- */
static uint8_t fac_us = 0;
static uint32_t fac_ms = 0;
/* Private function  -------------------------------------------------------- */
static void delay_ticks(uint32_t ticks)
{
    uint32_t told = SysTick->VAL;
    uint32_t tnow = 0;
    uint32_t tcnt = 0;
    uint32_t reload = SysTick->LOAD;
    while (1)
    {
        tnow = SysTick->VAL;
        if (tnow != told)
        {
            if (tnow < told)
            {
                tcnt += told - tnow;
            }
            else
            {
                tcnt += reload - tnow + told;
            }
            told = tnow;
            if (tcnt >= ticks)
            {
                break;
            }
        }
    }
}
/* Exported functions ------------------------------------------------------- */

/**
 * @brief 毫秒延时函数
 * @param ms
 * @return
 */
int8_t BSP_Delay(uint32_t ms)
{
    uint32_t tick_period = 1000u / osKernelGetTickFreq();
    uint32_t ticks = ms / tick_period;

    switch (osKernelGetState())
    {
    case osKernelError:
    case osKernelReserved:
    case osKernelLocked:
    case osKernelSuspended:
        return BSP_ERR;

    case osKernelRunning:
        osDelay(ticks ? ticks : 1);
        break;

    case osKernelInactive:
    case osKernelReady:
        HAL_Delay(ms);
        break;
    }
    return BSP_OK;
}

/**
 * @brief 延时初始化
 * @param  
 * @return 
 */
int8_t BSP_Delay_Init(void)
{
    if (SystemCoreClock == 0)
    {
        return BSP_ERR;
    }
    fac_us = SystemCoreClock / 1000000;
    fac_ms = SystemCoreClock / 1000;
    return BSP_OK;
}

/**
 * @brief 微秒延时，注意：此函数会阻塞当前线程，直到延时结束，并且会被中断打断
 * @param us 
 * @return 
 */
int8_t BSP_Delay_us(uint32_t us)
{
    if (fac_us == 0)
    {
        return BSP_ERR;
    }
    uint32_t ticks = us * fac_us;
    delay_ticks(ticks);
    return BSP_OK;
}

/**
 * @brief 毫秒延时，注意：此函数会阻塞当前线程，直到延时结束，并且会被中断打断
 * @param ms 
 * @return 
 */
int8_t BSP_Delay_ms(uint32_t ms)
{
    if (fac_ms == 0)
    {
        return BSP_ERR;
    }
    uint32_t ticks = ms * fac_ms;
    delay_ticks(ticks);
    return BSP_OK;
}
