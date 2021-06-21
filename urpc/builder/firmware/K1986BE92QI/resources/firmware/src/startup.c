/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Main includes here.
 */
#include "MDR32F9Qx_config.h"
#include "startup.h"

/*
 * Other includes here.
 */
#ifdef DEBUG
#include <stdio.h>  // For printf(...)
#endif  // DEBUG
#include "system_MDR32F9Qx.h"

//#define STACK_SIZE  1024
#define STACK_SIZE  400

extern int32_t main(void);

static void InitDataAndBSS(void);
static void IntDefaultHandler(void);
extern void xPortSysTickHandler(void);
extern void PendSV_Handler(void);
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

static void InitDataAndBSS(void)
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
 * A union that describes the entries of the vector table.  The union is needed
 * since the first entry is the stack pointer and the remainder are function
 * pointers.
 */
typedef union
{
  void (*pfnHandler)(void);
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
   * Run data and bss initialization (global variables initial values)
   */
  InitDataAndBSS();

  /*
   * Setup the microcontroller system. RST clock configuration to
   * the default reset state. Setup SystemCoreClock variable.
   */
  SystemInit();

  /*
   * SystemInit always set constant firmware address 0x08000000 to the NVIC VTOR register.
   * But when bootloader is used, firmware is biased and other address should be written to SCB->VTOR.
   * So fix it. We believe .intvec is located in the beginning and use this address.
   * More details: #38552
   */
#ifdef __ICCARM__
  #pragma section = ".intvec"
  SCB->VTOR = (uint32_t)__section_begin(".intvec");
#else
  /* 
   * There is no firmware address definition implementation for your compiler
   */
  while(1);
#endif // __ICCARM__
  
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
  __stack,              // The initial stack pointer
  ResetISR,             // The reset handler
  NmiSR,                // The NMI handler
  FaultISR,             // The hard fault handler
  IntDefaultHandler,    // The MPU fault handler
  IntDefaultHandler,    // The bus fault handler
  IntDefaultHandler,    // The usage fault handler
  0,                    // Reserved
  0,                    // Reserved
  0,                    // Reserved
  0,                    // Reserved
  IntDefaultHandler,    // SVCall handler
  IntDefaultHandler,    // Debug monitor handler
  0,                    // Reserved
  IntDefaultHandler,    // The PendSV handler
  IntDefaultHandler,    // The SysTick handler

  /*
   * External interrupts
   */
  IntDefaultHandler,    // IRQ0 CAN1 Interrupt
  IntDefaultHandler,    // IRQ1 CAN1 Interrupt
  IntDefaultHandler,    // IRQ2 USB Host Interrupt
  0,                    // IRQ3 Reserved
  0,                    // IRQ4 Reserved
  IntDefaultHandler,    // IRQ5 DMA Interrupt
  IntDefaultHandler,    // IRQ6 UART1 Interrupt
  IntDefaultHandler,    // IRQ7 UART2 Interrupt
  IntDefaultHandler,    // IRQ8 SSP1 Interrupt
  0,                    // IRQ9 Reserved
  IntDefaultHandler,    // IRQ10 I2C Interrupt
  IntDefaultHandler,    // IRQ11 POWER Detecor Interrupt
  IntDefaultHandler,    // IRQ12 Window Watchdog Interrupt
  0,                    // IRQ13 Reserved
  IntDefaultHandler,    // IRQ14 TIMER1 Interrupt
  IntDefaultHandler,    // IRQ15 TIMER2 Interrupt
  IntDefaultHandler,    // IRQ16 TIMER3 Interrupt
  IntDefaultHandler,    // IRQ17 ADC Interrupt
  0,                    // IRQ18 Reserved
  IntDefaultHandler,    // IRQ19 COMPARATOR Interrupt
  IntDefaultHandler,    // IRQ20 SSP2 Interrupt
  0,                    // IRQ21 Reserved
  0,                    // IRQ22 Reserved
  0,                    // IRQ23 Reserved
  0,                    // IRQ24 Reserved
  0,                    // IRQ25 Reserved
  0,                    // IRQ26 Reserved
  IntDefaultHandler,    // IRQ27 BACKUP Interrupt
  IntDefaultHandler,    // IRQ28 EXT_INT1 Interrupt
  IntDefaultHandler,    // IRQ29 EXT_INT2 Interrupt
  IntDefaultHandler,    // IRQ30 EXT_INT3 Interrupt
  IntDefaultHandler     // IRQ31 EXT_INT4 Interrupt
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
