#ifndef _TTY_H
#define _TTY_H

/*
 * Other includes here.
 */
#include "niietcm4_uart.h"

void TTY_Init(void);
void TTY_SettingsChange(UART_StopBit_TypeDef    StopBit,
                        UART_ParityBit_TypeDef  ParityBit,
                        uint32_t                BaudRate);

#endif  // _TTY_H
