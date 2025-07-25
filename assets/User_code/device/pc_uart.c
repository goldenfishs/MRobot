/* Includes ----------------------------------------------------------------- */
#include "pc_uart.h"

#include <string.h>

#include "bsp\uart.h"
#include "device.h"

#define UART_HANDLE BSP_UART_GetHandle(BSP_UART_PC)

#define AI_LEN_RX_BUFF (sizeof(UART_RxData_t))

static bool rx_flag = false;

static uint8_t rxbuf[AI_LEN_RX_BUFF];

static void UART_RxCpltCallback(void) { rx_flag = true; }

int UART_Init(UART_t *huart)
{
    UNUSED(huart);
    //注册回调函数
    HAL_UART_RegisterCallback(UART_HANDLE, BSP_UART_RX_CPLT_CB, UART_RxCpltCallback);
    return DEVICE_OK
}

int UART_StartReceive(UART_t *huart)
{
    UNUSED(huart);
    HAL_UART_Receive_DMA(UART_HANDLE, rxbuf, AI_LEN_RX_BUFF);
    return DEVICE_OK;
}

bool UART_IsReceiveComplete(void)
{
    return rx_flag;
}

int8_t UART_ParseData(UART_t *huart)
{

    memcpy(&huart->rx_data, rxbuf, sizeof(UART_RxData_t));
}

void UART_PackTx(UART_t *huart, UART_TxData_t *tx_data)
{
    memcpy(tx_data, huart->tx_data, sizeof(UART_TxData_t));
}

int8_t UART_StartSend(UART_t *huart)
{
    if (HAL_UART_Transmit_DMA(UART_HANDLE, huart->tx_data, sizeof(UART_TxData_t)) == HAL_OK)
    {
        return DEVICE_OK
    }
    return DEVICE_ERR;
}