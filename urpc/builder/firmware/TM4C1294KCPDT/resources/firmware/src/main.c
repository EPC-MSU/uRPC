/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

#include <string.h>
#include <stdio.h>              // Reqired for printf

#include "usb_composite.h"      // Required for USB init

#include "atomicrun.h"
#include "startup.h"
#include "iobuffer.h"

#include "inc/hw_memmap.h"
#include "inc/hw_types.h"
#include "inc/hw_ints.h"

#include "driverlib/interrupt.h"
#include "driverlib/sysctl.h"
#include "driverlib/systick.h"  // For SysTick
#include "driverlib/usb.h"	// Required to disable USB before reboot
#include "driverlib/adc.h"      // Required for change engine type logic
#include "driverlib/timer.h"

// FreeRTOS files
#include "FreeRTOS.h"
#include "task.h"

io_buffer_t SlaveReadBuf[I2C_DEVICES_LIMIT - 1];

extern void xPortPendSVHandler(void);
extern void xPortSysTickHandler(void);
extern void vPortSVCHandler(void);

static void ClearInterrupts(void);
static void FixVectorTable(void);

void vApplicationIdleHook(void);
__noreturn int32_t main(void)
{
  uint32_t Freq = SysCtlClockFreqSet(SYSCTL_OSC_MAIN | SYSCTL_XTAL_25MHZ | SYSCTL_USE_PLL | SYSCTL_CFG_VCO_480, _CPU_FREQUENCY);  // Set system clock to 80 MHz

  /*
   * Initialization of hardware and software.
   */
  __DISABLE_IRQ;  // Interrupts must be disabled by default except when we start fresh

  FixVectorTable();     // Some IRQ vectors could be overwritten by bootloader. Restore them
  ClearInterrupts();    // Before enabling interrupts we must clear any pending interrupts

  //Interrupt priority Set
  //You can using here only priorities from 3 to 7
  //Make sure to set the correct priority for all the blocks used
  //Also note that communication protocols such as USB and UART should usually have lower
  //priorities than main firmware function blocks
  IntPrioritySet(FAULT_SYSTICK, 4 << 5);  // Handles all periodical maintenance
  IntPrioritySet(INT_TIMER1A, 3 << 5);    // Timer
  IntPrioritySet(INT_TIMER1B, 3 << 5);    // 
  IntPrioritySet(INT_GPIOA, 5 << 5);      // GPIO interrupts' priorities
  IntPrioritySet(INT_GPIOB, 5 << 5);      //
  IntPrioritySet(INT_GPIOC, 5 << 5);      //
  IntPrioritySet(INT_GPIOD, 5 << 5);      //
  IntPrioritySet(INT_GPIOE, 5 << 5);      //
  IntPrioritySet(INT_GPIOF, 5 << 5);      //
  IntPrioritySet(INT_GPIOG, 5 << 5);      //
  IntPrioritySet(INT_GPIOH, 5 << 5);      //
  IntPrioritySet(INT_GPIOJ, 5 << 5);      // Handles limit switches
  IntPrioritySet(INT_USB0, 6 << 5);       // USB control
  IntPrioritySet(INT_UART1, 6 << 5);      // UART control

  __ENABLE_IRQ;

  // Check the USB Connection
  USB_InitAndCheck();

  // Start FreeRTOS sheduler
  // Blocking function. We will not go to while(1) below.
  vTaskStartScheduler();

  while (1)
  {
    // Capture
  }
}

static void ClearInterrupts(void)
{
  // Disable interrupts
  SysTickDisable();
  SysTickIntDisable();

  // Disable vectors
  HWREG(0xE000E180) = 0xFFFFFFFF;
  HWREG(0xE000E184) = 0xFFFFFFFF;

  // Disable pendings
  HWREG(0xE000E280) = 0xFFFFFFFF;
  HWREG(0xE000E284) = 0xFFFFFFFF;

  // Clear SysTick pending
  HWREG(0xE000ED04) = 1 << 25;
}

static void FixVectorTable(void)
{
  IntRegister(FAULT_NMI, NmiSR);
  IntRegister(FAULT_HARD, FaultISR);

  for (uint32_t i = 4; i < 11; i++)
  {
    IntRegister(i, IntDefaultHandler);
  }

  IntRegister(FAULT_SVCALL, vPortSVCHandler);

  for (uint32_t i = 12; i < 14; i++)
  {
    IntRegister(i, IntDefaultHandler);
  }

  IntRegister(FAULT_PENDSV, xPortPendSVHandler);
  IntRegister(FAULT_SYSTICK, xPortSysTickHandler);

  for (uint32_t i = 16; i < 80; i++)
  {
    IntRegister(i, IntDefaultHandler);
  }
}

#ifdef DEBUG
void __error__(char *pcFilename, uint32_t ui32Line)
{
  while (1)
  {
    // Capture
  }
}
#endif  // DEBUG


void vApplicationIdleHook(void)
{
  /* From FreeRTOS tasks.c:
   *    NOTE: vApplicationIdleHook() MUST NOT,
   *    UNDER ANY CIRCUMSTANCES,
   *   CALL A FUNCTION THAT MIGHT BLOCK.
   *
   * Since that and according to information on https://www.freertos.org/RTOS-idle-task.html
   * FreeRTOS oficcial doc web-site endless loop was removed to prevent blocking
   * in non-preemptive multitasking.
   * FreeRTOS has preemtive scheduling by default so while(1)
   * in our older firmwares is OK. #67377
   *
   * This task can be used for the application purposes but take into
   * account that it has the lowest priority that can't be changed.
   */
}
