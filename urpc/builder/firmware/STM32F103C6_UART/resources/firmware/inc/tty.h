#ifndef _TTY_H
#define _TTY_H

/*
 * Other includes here.
 */
#include "stm32f10x_usart.h"

void TTY_Init(void);
void TTY_SettingsChange(uint16_t StopBit, uint16_t ParityBit, uint32_t BaudRate);

#endif  // _TTY_H
