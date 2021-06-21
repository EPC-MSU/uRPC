#ifndef _TTY_H
#define _TTY_H

/*
 * Other includes here.
 */
#include "stm32f1xx_ll_usart.h"

void TTY_Init(void);
void TTY_SettingsChange(uint32_t StopBit, uint32_t ParityBit, uint32_t BaudRate);

#endif  // _TTY_H
