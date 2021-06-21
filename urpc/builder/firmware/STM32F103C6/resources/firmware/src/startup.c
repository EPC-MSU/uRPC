/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Main includes here.
 */
#include "stm32f1xx.h"
#include "startup.h"

/*
 * Other includes here.
 */
#ifdef DEBUG
#include <stdio.h>  // For printf(...)
#endif  // DEBUG
#include "system_stm32f1xx.h"

#define STACK_SIZE  400

extern int32_t main(void);

static inline void InitDataAndBSS(void);

static void IntDefaultHandler(void);
extern void PendSV_Handler(void);
extern void xPortSysTickHandler(void);
extern void SVC_Handler(void);

/*
 * Reserve space for the system stack. MPU can protect
 * an aligned address at 32 bytes.
 */
#if defined (__ICCARM__)
#pragma data_alignment=32
__no_init static uint32_t Stack[STACK_SIZE] @ "CSTACK";
#elif defined (__GNUC__)
static __attribute__((section("stack")))
uint32_t Stack[STACK_SIZE] __attribute__((aligned(32)));
#else
#error "Compiler is undefined!"
#endif

static inline void InitDataAndBSS(void)
{
#ifdef __GNUC__
  register unsigned long *_data, *_edata, *_bss, *_ebss, *_data_init;

  extern unsigned long __data_start;
  extern unsigned long __data_end;
  extern unsigned long __bss_start;
  extern unsigned long __bss_end;
  extern unsigned long __data_init;

  _data = &__data_start;
  _edata = &__data_end;
  _bss = &__bss_start;
  _ebss = &__bss_end;
  _data_init = &__data_init;

#elif __ICCARM__
#pragma section = ".data"
#pragma section = ".data_init"
#pragma section = ".bss"
#pragma section = ".textrw"
#pragma section = ".textrw_init"
  uint32_t *_data         = __section_begin(".data");
  uint32_t *_edata        = __section_end(".data");
  uint32_t *_data_init    = __section_begin(".data_init");
  uint32_t *_bss          = __section_begin(".bss");
  uint32_t *_ebss         = __section_end(".bss");
  uint32_t *_textrw       = __section_begin(".textrw");
  uint32_t *_etextrw      = __section_end(".textrw");
  uint32_t *_textrw_init  = __section_begin(".textrw_init");
#endif  // __ICCARM__

  uint32_t n;

  /*
   * Copy the data segment initializers from flash to SRAM.
   */
  n = _edata - _data;

  while (n--)
    *_data++ = *_data_init++;

  /*
   * Copy the textrw segment initializers from flash to SRAM.
   */
  n = _etextrw - _textrw;

  while (n--)
    *_textrw++ = *_textrw_init++;

  /*
   * Zero fill the bss segment.
   */
  n = _ebss - _bss;

  while (n--)
    *_bss++ = 0x00000000;
}

#if defined (__ICCARM__)
#define __vectors   __root const uVectorEntry __vector_table[] @ ".intvec"
#define __stack     { .ui32Ptr = (uint32_t)Stack + sizeof(Stack) }

/*
 * A union that describes the entries of the vector table.
 * The union is needed since the first entry is the stack
 * pointer and the remainder are function pointers.
 */
typedef union
{
  void (*Handler)(void);
  uint32_t ui32Ptr;

} uVectorEntry;

#endif // __ICCARM__

/*
 * This function must be non-optimized, because the medium optimization
 * makes code that have bad behavior with SP and LR registers,
 * when there is stack in the end of memory.
 */
#ifdef __ICCARM__
#pragma optimize=none
#endif  // __ICCARM__
void ResetISR(void)
{
  __set_MSP((uint32_t)Stack + sizeof(Stack));

  /*
   * Run data and bss initialization (global variables initial values).
   */
  InitDataAndBSS();

  /*
   * Setup the microcontroller system. RST clock configuration to
   * the default reset state. Setup SystemCoreClock variable.
   */
  SystemInit();

  /*
   * Call the application's entry point
   */
  main();
}

//*****************************************************************************
//
// External declarations for the interrupt handlers used by the application.
//
//*****************************************************************************
// There could be no declarations when interrupt table is derived from bootloader

// The vector table.  Note that the proper constructs must be placed on this to
// ensure that it ends up at physical address 0x0000.0000.
//
//*****************************************************************************

__vectors =
{
  __stack,            // The initial stack pointer
  ResetISR,           // Reset Handler
  NmiSR,              // NMI Handler
  FaultISR,           // Hard Fault Handler
  IntDefaultHandler,  // MPU Fault Handler
  IntDefaultHandler,  // Bus Fault Handler
  IntDefaultHandler,  // Usage Fault Handler
  0,                  // Reserved
  0,                  // Reserved
  0,                  // Reserved
  0,                  // Reserved
  SVC_Handler,  // SVCall Handler
  IntDefaultHandler,  // Debug Monitor Handler
  0,                  // Reserved
  PendSV_Handler,  // PendSV Handler
  xPortSysTickHandler,  // SysTick Handler

  /*
   * External interrupts.
   */
  IntDefaultHandler,  // IRQ0   Window Watchdog
  IntDefaultHandler,  // IRQ1   PVD through EXTI Line detect
  IntDefaultHandler,  // IRQ2   Tamper
  IntDefaultHandler,  // IRQ3   RTC
  IntDefaultHandler,  // IRQ4   Flash
  IntDefaultHandler,  // IRQ5   RCC
  IntDefaultHandler,  // IRQ6   EXTI Line 0
  IntDefaultHandler,  // IRQ7   EXTI Line 1
  IntDefaultHandler,  // IRQ8   EXTI Line 2
  IntDefaultHandler,  // IRQ9   EXTI Line 3
  IntDefaultHandler,  // IRQ10  EXTI Line 4
  IntDefaultHandler,  // IRQ11  DMA1 Channel 1
  IntDefaultHandler,  // IRQ12  DMA1 Channel 2
  IntDefaultHandler,  // IRQ13  DMA1 Channel 3
  IntDefaultHandler,  // IRQ14  DMA1 Channel 4
  IntDefaultHandler,  // IRQ15  DMA1 Channel 5
  IntDefaultHandler,  // IRQ16  DMA1 Channel 6
  IntDefaultHandler,  // IRQ17  DMA1 Channel 7
  IntDefaultHandler,  // IRQ18  ADC1 & ADC2
  IntDefaultHandler,  // IRQ19  USB High Priority or CAN1 TX
  IntDefaultHandler,  // IRQ20  USB Low  Priority or CAN1 RX0
  IntDefaultHandler,  // IRQ21  CAN1 RX1
  IntDefaultHandler,  // IRQ22  CAN1 SCE
  IntDefaultHandler,  // IRQ23  EXTI Line 9..5
  IntDefaultHandler,  // IRQ24  TIM1 Break
  IntDefaultHandler,  // IRQ25  TIM1 Update
  IntDefaultHandler,  // IRQ26  TIM1 Trigger and Commutation
  IntDefaultHandler,  // IRQ27  TIM1 Capture Compare
  IntDefaultHandler,  // IRQ28  TIM2
  IntDefaultHandler,  // IRQ29  TIM3
  IntDefaultHandler,  // IRQ30  Reserved
  IntDefaultHandler,  // IRQ31  I2C1 Event
  IntDefaultHandler,  // IRQ32  I2C1 Error
  IntDefaultHandler,  // IRQ33  Reserved
  IntDefaultHandler,  // IRQ34  Reserved
  IntDefaultHandler,  // IRQ35  SPI1
  IntDefaultHandler,  // IRQ36  Reserved
  IntDefaultHandler,  // IRQ37  USART1
  IntDefaultHandler,  // IRQ38  USART2
  IntDefaultHandler,  // IRQ39  Reserved
  IntDefaultHandler,  // IRQ40  EXTI Line 15..10
  IntDefaultHandler,  // IRQ41  RTC Alarm through EXTI Line
  IntDefaultHandler   // IRQ42  USB Wakeup from suspend
};

/*
 * This is the code that gets called when the processor receives a NMI.  This
 * simply enters an infinite loop, preserving the system state for examination
 * by a debugger.
 */
void NmiSR(void)
{
  while (1)
  {
    // Capture
  }
}

/*
 * This is the code that gets called when the processor receives a fault
 * interrupt. This simply enters an infinite loop, preserving the system state
 * for examination by a debugger.
 */
void FaultISR(void)
{
#ifdef DEBUG
  if (SCB->CFSR & SCB_CFSR_USGFAULTSR_Msk)
  {
    printf("Usage fault");
  }
  else if (SCB->CFSR & SCB_CFSR_BUSFAULTSR_Msk)
  {
    printf("Bus fault");
  }
  else  // (SCB->CFSR & SCB_CFSR_MEMFAULTSR_Msk)
  {
    printf("Memory manage fault");
  }
#endif  // DEBUG

  while (1)
  {
    // Capture
  }
}

/*
 * This is the code that gets called when the processor receives an unexpected
 * interrupt. This simply enters an infinite loop, preserving the system state
 * for examination by a debugger.
 */
static void IntDefaultHandler(void)
{
  while (1)
  {
    // Capture
  }
}
