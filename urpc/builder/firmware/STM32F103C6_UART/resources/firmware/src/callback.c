/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Main includes here.
 */
#include "callback.h"

/*
 * Other includes here.
 */
#include "atomicrun.h"
#include "macro.h"  // For increase()
#include "systick.h"

typedef struct
{
  volatile uint32_t PlannedShot;
  volatile uint32_t Calltime;
  void (*volatile Func)(void);

} callback_t;

/*
 * Queue.
 */
static callback_t Callbacks[CALLBACK_NUMBER];

/*
 * For latter definition.
 */
static inline void Cancel(const callback_index_t CallbackNum);
static inline void Call(const callback_index_t CallbackNum);
static void Invoke(void);

INIT_STATE_VAR(Callback);

void Callback_Init(void)
{
  INIT_START(Callback);

#if defined (__ICCARM__)
  static_assert(CALLBACK_NUMBER == CALLBACK_NUMBER_INDEX, "Error in the number of callbacks");
#else
  assert_param(CALLBACK_NUMBER == CALLBACK_NUMBER_INDEX);
#endif  // __ICCARM__

  /*
   * Init SysTick module.
   */
  SysTick_Init();

  for (uint32_t Index = 0; Index < CALLBACK_NUMBER; Index++)
  {
    Callbacks[Index].Func = NULL;

    Cancel((callback_index_t)Index);
  }

  SysTick_SetCallback(Invoke);

  INIT_END(Callback);
}

void Callback_SetHandler(callback_index_t CallbackNum, void (*pfnHandler)(void))
{
  FUNC_START(Callback);

  Callbacks[CallbackNum].Func = pfnHandler;
}

void Callback_SetDelay(callback_index_t CallbackNum, uint32_t Delay)
{
  FUNC_START(Callback);
  assert_param(Delay <= CALLBACK_MAX_DELAY);

  Callbacks[CallbackNum].PlannedShot = 0xFF;

  if (Delay == 0)
  {
    Cancel(CallbackNum);  // Because it was already execute

    Call(CallbackNum);
  }
  else
  {
    /*
     * In rare occasions more priority SysTick interrupt can invoke
     * while SetDelay is still processing. Need additional checking after set.
     */
    do
    {
      Callbacks[CallbackNum].Calltime = SysTick_Time() + Delay;

    } while (Callbacks[CallbackNum].Calltime < SysTick_Time() + Delay &&
             Callbacks[CallbackNum].PlannedShot);
  }
}

uint32_t Callback_GetDelay(callback_index_t CallbackNum)
{
  FUNC_START(Callback);

  return Callbacks[CallbackNum].Calltime - SysTick_Time();
}

void Callback_CancelDelay(callback_index_t CallbackNum)
{
  FUNC_START(Callback);

  Cancel(CallbackNum);
}

static void Invoke(void)
{
  static uint32_t counter = 0;
  uint32_t Time = SysTick_Time();

  for (uint32_t Index = 0; Index < CALLBACK_NUMBER; Index++)
  {
    if (Callbacks[Index].Calltime == Time)
      Call((callback_index_t)Index);
  }

  /*
   * This code fix a undefined behavior when the milliseconds counter overflows.
   */
  if ((Callbacks[counter].Calltime - Time) > CALLBACK_MAX_DELAY)
  {
    /*
     * Draw callback time closer to current time
     * so it will never be left 2^32 milliseconds behind.
     */
    Callbacks[counter].Calltime = Time;
  }

  counter = increase(counter, 0, CALLBACK_NUMBER - 1);
}

static inline void Cancel(const callback_index_t CallbackNum)
{
  uint32_t TimeCache = SysTick_Time();

  __DISABLE_IRQ;

  Callbacks[CallbackNum].PlannedShot = 0x00;

  /*
   * In rare occasions time can change += 1 while Invoke still
   * process callbacks with old time, so the callback will be triggered
   * Also during initialization there may be even worse discrepancy
   * because interupts are disabled, but SysTick runs, that were observed
   * to reach 4 ms in another project. Thus a relatively big value
   * CALLBACK_CANCEL_PADDING must be used to guaranty disabling of callback.
   * Related to the issue #63336 and ximc-issue #61465.
   */
  Callbacks[CallbackNum].Calltime = TimeCache - CALLBACK_CANCEL_PADDING;

  __ENABLE_IRQ;
}

static inline void Call(const callback_index_t CallbackNum)
{
  FUNC_START(Callback);
  assert_param(Callbacks[CallbackNum].Func != NULL);

  Callbacks[CallbackNum].PlannedShot = 0x00;

  (*Callbacks[CallbackNum].Func)();
}
