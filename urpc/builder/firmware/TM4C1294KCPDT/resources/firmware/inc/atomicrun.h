#ifndef _ATOMIC_RUN_H
#define _ATOMIC_RUN_H

#include "driverlib/cpu.h"
#include "driverlib/debug.h"

#define __ENABLE_IRQ  CPUcpsie()

#define __DISABLE_IRQ \
  { \
    ASSERT(!CPUprimask()); \
    CPUcpsid(); \
  }

#define ATOMIC_RUN(code) \
  { \
    __DISABLE_IRQ; \
    code; \
    __ENABLE_IRQ; \
  }

#endif  // _ATOMIC_RUN_H
