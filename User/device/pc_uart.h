/*
  UART通讯模板
*/

#pragma once

#ifdef __cplusplus
extern "C"
{
#endif

/* Includes ----------------------------------------------------------------- */
#include <stdbool.h>
#include <stdint.h>

    /* Exported constants ------------------------------------------------------- */
    /* Exported macro ----------------------------------------------------------- */
    /* Exported types ----------------------------------------------------------- */

    typedef struct
    {
        uint8_t head;
        uint8_t data;
        uint8_t crc;
    } UART_RxData_t;

    typedef struct
    {
        uint8_t head;
        uint8_t data;
        uint8_t crc;
    } UART_TxData_t;

    typedef struct
    {
        UART_RxData_t rx_data; // Received data buffer
        UART_TxData_t tx_data; // Transmit data buffer
    } UART_t;

    /* Exported functions prototypes -------------------------------------------- */

    int UART_Init(UART_t *huart);
    int UART_StartReceive(UART_t *huart);
    bool UART_IsReceiveComplete(void);
    int8_t UART_ParseData(UART_t *huart);
    void UART_PackTx(UART_t *huart, UART_TxData_t *tx_data);
    int8_t UART_StartSend(UART_t *huart);
#ifdef __cplusplus
}
#endif
