#ifndef _SYSTICK_H
#define _SYSTICK_H

void SysTick_Init(void);
void SysTick_SetCallback(void (*pfnHandler)(void));
uint32_t SysTick_Time(void);

#endif  // _SYSTICK_H
