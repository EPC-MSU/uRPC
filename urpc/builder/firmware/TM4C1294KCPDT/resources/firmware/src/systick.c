/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Main includes here.
 */
#include "systick.h"

/*
 * Other includes here.
 */
#include "inc/hw_nvic.h"
#include "inc/hw_types.h"
#include "driverlib/debug.h"      // For ASSERT(...)
#include "driverlib/sysctl.h"     // For SysClockXxx()
#include "driverlib/systick.h"    // For SysTick
#include "atomicrun.h"
#define _AEABI_PORTABILITY_LEVEL 1
#undef __AEABI_PORTABLE
#include "time.h"
#ifndef __AEABI_PORTABLE
  #error "time.h not AEABI compatible"
#endif

/*
 * Number of ticks per second.
 */
#define TIMES_PER_SECOND  1000

const int32_t __aeabi_CLOCKS_PER_SEC = _CPU_FREQUENCY / TIMES_PER_SECOND;

static uint32_t MillisecondCounter          = 0;
static void (*AddressOfCallbackFunc)(void)  = NULL;

static void InterruptHandler(void);

INIT_STATE_VAR(SysTick);

/*
 * Initialize counter (SysTick).
 */
void SysTick_Init(void)
{
  INIT_START(SysTick);

  SysTickPeriodSet(CLOCKS_PER_SEC);   // No need subtract 1. See the function implementation in the driverlib
  HWREG(NVIC_ST_CURRENT) = 0;

  SysTickIntRegister(InterruptHandler);

  /*
   * Start counter init.
   */
  HWREG(NVIC_ST_CTRL) = NVIC_ST_CTRL_CLK_SRC | NVIC_ST_CTRL_INTEN | NVIC_ST_CTRL_ENABLE;

  INIT_END(SysTick);
}

/*
 * Register external callback function.
 */
void SysTick_SetCallback(void (*pfnHandler)(void))
{
  FUNC_START(SysTick);

  AddressOfCallbackFunc = pfnHandler;
}

/*
 * Interrupt handler.
 */
static void InterruptHandler(void)
{
  __DISABLE_IRQ;

  /*
   * We need check this register because increment occur in
   * several places (see function SysTick_GetTickValue()).
   */
  if (HWREG(NVIC_ST_CTRL) & NVIC_ST_CTRL_COUNT)
  {
    MillisecondCounter++;
  }

  __ENABLE_IRQ;

  /*
   * External callback function.
   */
  if (AddressOfCallbackFunc != NULL)
    AddressOfCallbackFunc();

  /*
   * Check that the processor has enough time
   * for execute all interrupts.
   */
  ASSERT(!(HWREG(NVIC_INT_CTRL) & NVIC_INT_CTRL_PENDSTSET));
}

/*
 * Returns the count of ticks from system init.
 */
__ATTRIBUTES clock_t clock(void)
{
  FUNC_START(SysTick);

  __DISABLE_IRQ;

  uint32_t MillisecondCache = MillisecondCounter;
  uint32_t SysTickCache = SysTickValueGet();

  /*
   * We increment millisecond timer here (before calculate TickValue)
   * because we need have accurate TickValue
   * else TickValue can have error on one period.
   */
  if (HWREG(NVIC_ST_CTRL) & NVIC_ST_CTRL_COUNT)
  {
    MillisecondCounter++;

    /*
     * The overflow occurs! Update cache values.
     */
    MillisecondCache = MillisecondCounter;
    SysTickCache = SysTickValueGet();
  }

  __ENABLE_IRQ;

  return MillisecondCache * CLOCKS_PER_SEC + (CLOCKS_PER_SEC - 1 - SysTickCache);
}

/*
 * Get time in milliseconds.
 */
uint32_t SysTick_Time(void)
{
  FUNC_START(SysTick);

  __DISABLE_IRQ;

  uint32_t MillisecondCache = MillisecondCounter;

  if (HWREG(NVIC_ST_CTRL) & NVIC_ST_CTRL_COUNT)
  {
    MillisecondCounter++;

    /*
     * The overflow occurs! Update cache values.
     */
    MillisecondCache = MillisecondCounter;
  }

  __ENABLE_IRQ;

  return MillisecondCache;
}
