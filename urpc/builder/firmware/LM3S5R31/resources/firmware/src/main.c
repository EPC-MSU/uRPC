/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

#include <string.h>
#include <stdio.h>  // Reqired for printf

#include "usb_composite.h"  // Required for USB init

#include "atomicrun.h"
#include "startup.h"

#include "inc/hw_memmap.h"
#include "inc/hw_types.h"
#include "inc/hw_ints.h"

#include "driverlib/interrupt.h"
#include "driverlib/sysctl.h"
#include "driverlib/systick.h"		// For SysTick
#include "driverlib/usb.h"	// Required to disable USB before reboot
#include "driverlib/adc.h"  // Required for change engine type logic
#include "driverlib/timer.h"
#include "driverlib/gpio.h"

// FreeRTOS files
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "croutine.h"
#include "semphr.h"
#include "timers.h"
#include "pdc.h"

io_buffer_t SlaveReadBuf[I2C_DEVICES_LIMIT - 1];
xSemaphoreHandle xMutex;

void vApplicationIdleHook(void);
static void ClearInterrupts(void);
void vBlinkRedTask(void *pvParametrs);
void vTurnOffRedTask(void *pvParametrs);

__noreturn int32_t main(void)
{
  SysCtlClockSet(SYSCTL_SYSDIV_2_5 | SYSCTL_USE_PLL | SYSCTL_OSC_MAIN | SYSCTL_XTAL_16MHZ); // Set system clock to 80 MHz

  // Initialization of hardware and software.

  __DISABLE_IRQ;  // Interrupts must be disabled by default except when we start fresh

  ClearInterrupts();  // Before enabling interrupts we must clear any pending interrupts

  //Interrupt priority Set(Engines block using priority 1 and 2 only)
  //You can using here only priorities from 3 to 7
  IntPrioritySet(FAULT_SYSTICK, 4 << 5);  // Handles all periodical maintenance
  IntPrioritySet(INT_ADC0SS2, 3 << 5);    // Handles various analog readings
  IntPrioritySet(INT_ADC1SS2, 3 << 5);    // Handles various analog readings
  IntPrioritySet(INT_TIMER1A, 3 << 5);    // Handles sync out timer
  IntPrioritySet(INT_TIMER1B, 3 << 5);    // Handles sync in timer
  IntPrioritySet(INT_GPIOA, 3 << 5);      // Handles limit switches and synch in pin
  IntPrioritySet(INT_GPIOB, 5 << 5);      //
  IntPrioritySet(INT_GPIOC, 5 << 5);      //
  IntPrioritySet(INT_GPIOD, 5 << 5);      //
  IntPrioritySet(INT_GPIOE, 5 << 5);      //
  IntPrioritySet(INT_GPIOF, 5 << 5);      //
  IntPrioritySet(INT_GPIOG, 5 << 5);      //
  IntPrioritySet(INT_GPIOH, 5 << 5);      //
  IntPrioritySet(INT_GPIOJ, 3 << 5);      // Handles limit switches
  IntPrioritySet(INT_I2C1, 5 << 5);       // FRAM memory interface must supercede USB and UART blocks but can be used carefully from higher priority interfaces
  IntPrioritySet(INT_QEI0, 6 << 5);       // Handles errors in encoder signal
  IntPrioritySet(INT_USB0, 6 << 5);       // USB control
  IntPrioritySet(INT_UART1, 6 << 5);      // UART control
  IntPrioritySet(INT_WATCHDOG, 7 << 5);   // WATCHDOG control

  __ENABLE_IRQ;

  // Check the USB Connection
  USB_InitAndCheck();

  SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOF);

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


#ifdef DEBUG
void __error__(char *pcFilename, unsigned long ulLine)
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