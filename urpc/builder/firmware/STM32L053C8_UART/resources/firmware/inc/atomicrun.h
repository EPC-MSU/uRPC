#ifndef _ATOMIC_RUN_H
#define _ATOMIC_RUN_H

/*
 * Other includes here.
 */
#include "stm32l0xx.h"

#define __ENABLE_IRQ  __enable_irq()

#define __DISABLE_IRQ \
  { \
    assert_param(!__get_PRIMASK()); \
    __disable_irq(); \
  }

#define ATOMIC_RUN(code) \
  { \
    __DISABLE_IRQ; \
    code; \
    __ENABLE_IRQ; \
  }

#endif  // _ATOMIC_RUN_H
