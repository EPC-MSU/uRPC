/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Main includes here.
 */
#include "MDR32F9Qx_config.h"
#include "systick.h"

/*
 * Other includes here.
 */
#include "MDR32F9Qx_interrupt.h"
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

static uint32_t MillisecondCounter;
static void (*AddressOfCallbackFunc)(void);

static void InterruptHandler(void);

INIT_STATE_VAR(SysTick);

/*
 * Initialize counter (SysTick).
 */
void SysTick_Init(void)
{
  INIT_START(SysTick);

  MillisecondCounter = 0;
  AddressOfCallbackFunc = NULL;

  /*
   * Setup interrupt handle.
   */
  IntRegister(SysTick_IRQn, InterruptHandler);

  /*
   * Start counter init.
   */
  SysTick_Config(CLOCKS_PER_SEC);

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
  if (SysTick->CTRL & SysTick_CTRL_COUNTFLAG_Msk)
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
  assert_param(!(SCB->ICSR & SCB_ICSR_PENDSTSET_Msk));
}

/*
 * Returns the count of ticks from system init.
 */
__ATTRIBUTES clock_t clock(void)
{
  FUNC_START(SysTick);

  __DISABLE_IRQ;

  uint32_t MillisecondCache = MillisecondCounter;
  uint32_t SysTickCache = SysTick->VAL;

  /*
   * We increment millisecond timer here (before calculate TickValue)
   * because we need have accurate TickValue
   * else TickValue can have error on one period.
   */
  if (SysTick->CTRL & SysTick_CTRL_COUNTFLAG_Msk)
  {
    MillisecondCounter++;

    /*
     * The overflow occurs! Update cache values.
     */
    MillisecondCache = MillisecondCounter;
    SysTickCache = SysTick->VAL;
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

  if (SysTick->CTRL & SysTick_CTRL_COUNTFLAG_Msk)
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
