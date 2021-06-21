#ifndef _STARTUP_H
#define _STARTUP_H

#if defined (__GNUC__)
void ResetISR(void) __attribute__((__interrupt__));
void NmiSR(void) __attribute__((__interrupt__));
void FaultISR(void) __attribute__((__interrupt__));
#elif defined (__ICCARM__)
void ResetISR(void);
void NmiSR(void);
void FaultISR(void);
#endif

#endif  // _STARTUP_H
