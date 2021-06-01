/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Main includes here.
 */

#include "niietcm4.h"
#include "startup.h"



/*
 * Other includes here.
 */
#ifdef DEBUG
  #include <stdio.h>  // For printf(...)
#endif  // DEBUG

#define STACK_SIZE  4096

extern int32_t main(void);

static inline void InitDataAndBSS(void);
static inline void SystemInit(void);

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
  {
    *_data++ = *_data_init++;
  }

  /*
   * Copy the textrw segment initializers from flash to SRAM.
   */
  n = _etextrw - _textrw;

  while (n--)
  {
    *_textrw++ = *_textrw_init++;
  }

  /*
   * Zero fill the bss segment.
   */
  n = _ebss - _bss;

  while (n--)
  {
    *_bss++ = 0x00000000;
  }
}

static inline void SystemInit(void)
{
  SCB->VTOR = 0x00;   // Reset vector table offset register

  #if (__FPU_USED == 1)
  /*
   * Set floating point coprosessor access mode.
   */
  SCB->CPACR = (0x3UL << 20UL) | (0x3UL << 22UL);   // Set CP10 and CP11 to full access
  #endif  // (__FPU_USED == 1)
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
  ResetISR,           // The reset handler
  NmiSR,              // The NMI handler
  FaultISR,           // The hard fault handler
  IntDefaultHandler,  // The MPU fault handler
  IntDefaultHandler,  // The bus fault handler
  IntDefaultHandler,  // The usage fault handler
  0,                  // Reserved
  0,                  // Reserved
  0,                  // Reserved
  0,                  // Reserved
  SVC_Handler,  // SVCall handler
  IntDefaultHandler,  // Debug monitor handler
  0,                  // Reserved
  PendSV_Handler,  // The PendSV handler
  xPortSysTickHandler,  // The SysTick handler

  /*
   * External interrupts.
   */
  IntDefaultHandler,  // IRQ0   WWDG Interrupt
  IntDefaultHandler,  // IRQ1   I2C0 Interrupt
  IntDefaultHandler,  // IRQ2   I2C1 Interrupt
  IntDefaultHandler,  // IRQ3   TIM0 Interrupt
  IntDefaultHandler,  // IRQ4   TIM1 Interrupt
  IntDefaultHandler,  // IRQ5   TIM2 Interrupt
  IntDefaultHandler,  // IRQ6   DMA_Stream0 Interrupt
  IntDefaultHandler,  // IRQ7   DMA_Stream1 Interrupt
  IntDefaultHandler,  // IRQ8   DMA_Stream2 Interrupt
  IntDefaultHandler,  // IRQ9   DMA_Stream3 Interrupt
  IntDefaultHandler,  // IRQ10  DMA_Stream4 Interrupt
  IntDefaultHandler,  // IRQ11  DMA_Stream5 Interrupt
  IntDefaultHandler,  // IRQ12  DMA_Stream6 Interrupt
  IntDefaultHandler,  // IRQ13  DMA_Stream7 Interrupt
  IntDefaultHandler,  // IRQ14  DMA_Stream8 Interrupt
  IntDefaultHandler,  // IRQ15  DMA_Stream9 Interrupt
  IntDefaultHandler,  // IRQ16  DMA_Stream10 Interrupt
  IntDefaultHandler,  // IRQ17  DMA_Stream11 Interrupt
  IntDefaultHandler,  // IRQ18  DMA_Stream12 Interrupt
  IntDefaultHandler,  // IRQ19  DMA_Stream13 Interrupt
  IntDefaultHandler,  // IRQ20  DMA_Stream14 Interrupt
  IntDefaultHandler,  // IRQ21  DMA_Stream15 Interrupt
  IntDefaultHandler,  // IRQ22  DMA_Stream16 Interrupt
  IntDefaultHandler,  // IRQ23  DMA_Stream17 Interrupt
  IntDefaultHandler,  // IRQ24  DMA_Stream18 Interrupt
  IntDefaultHandler,  // IRQ25  DMA_Stream19 Interrupt
  IntDefaultHandler,  // IRQ26  DMA_Stream20 Interrupt
  IntDefaultHandler,  // IRQ27  DMA_Stream21 Interrupt
  IntDefaultHandler,  // IRQ28  DMA_Stream22 Interrupt
  IntDefaultHandler,  // IRQ29  DMA_Stream23 Interrupt
  IntDefaultHandler,  // IRQ30  USART0_MX Interrupt
  IntDefaultHandler,  // IRQ31  USART0_RX Interrupt
  IntDefaultHandler,  // IRQ32  USART0_TX Interrupt
  IntDefaultHandler,  // IRQ33  USART0_RT Interrupt
  IntDefaultHandler,  // IRQ34  USART0_E Interrupt
  IntDefaultHandler,  // IRQ35  USART0 Interrupt
  IntDefaultHandler,  // IRQ36  USART1_MX Interrupt
  IntDefaultHandler,  // IRQ37  USART1_RX Interrupt
  IntDefaultHandler,  // IRQ38  USART1_TX Interrupt
  IntDefaultHandler,  // IRQ39  USART1_RT Interrupt
  IntDefaultHandler,  // IRQ40  USART1_E Interrupt
  IntDefaultHandler,  // IRQ41  USART1 Interrupt
  IntDefaultHandler,  // IRQ42  USART2_MX Interrupt
  IntDefaultHandler,  // IRQ43  USART2_RX Interrupt
  IntDefaultHandler,  // IRQ44  USART2_TX Interrupt
  IntDefaultHandler,  // IRQ45  USART2_RT Interrupt
  IntDefaultHandler,  // IRQ46  USART2_E Interrupt
  IntDefaultHandler,  // IRQ47  USART2 Interrupt
  IntDefaultHandler,  // IRQ48  USART3_MX Interrupt
  IntDefaultHandler,  // IRQ49  USART3_RX Interrupt
  IntDefaultHandler,  // IRQ50  USART3_TX Interrupt
  IntDefaultHandler,  // IRQ51  USART3_RT Interrupt
  IntDefaultHandler,  // IRQ52  USART3_E Interrupt
  IntDefaultHandler,  // IRQ53  USART3 Interrupt
  IntDefaultHandler,  // IRQ54  PWM0 Interrupt
  IntDefaultHandler,  // IRQ55  PWM0_HD Interrupt
  IntDefaultHandler,  // IRQ56  PWM0_TZ Interrupt
  IntDefaultHandler,  // IRQ57  PWM1 Interrupt
  IntDefaultHandler,  // IRQ58  PWM1_HD Interrupt
  IntDefaultHandler,  // IRQ59  PWM1_TZ Interrupt
  IntDefaultHandler,  // IRQ60  PWM2 Interrupt
  IntDefaultHandler,  // IRQ61  PWM2_HD Interrupt
  IntDefaultHandler,  // IRQ62  PWM2_TZ Interrupt
  IntDefaultHandler,  // IRQ63  PWM3 Interrupt
  IntDefaultHandler,  // IRQ64  PWM3_HD Interrupt
  IntDefaultHandler,  // IRQ65  PWM3_TZ Interrupt
  IntDefaultHandler,  // IRQ66  PWM4 Interrupt
  IntDefaultHandler,  // IRQ67  PWM4_HD Interrupt
  IntDefaultHandler,  // IRQ68  PWM4_TZ Interrupt
  IntDefaultHandler,  // IRQ69  PWM5 Interrupt
  IntDefaultHandler,  // IRQ70  PWM5_HD Interrupt
  IntDefaultHandler,  // IRQ71  PWM5_TZ Interrupt
  IntDefaultHandler,  // IRQ72  PWM6 Interrupt
  IntDefaultHandler,  // IRQ73  PWM6_HD Interrupt
  IntDefaultHandler,  // IRQ74  PWM6_TZ Interrupt
  IntDefaultHandler,  // IRQ75  PWM7 Interrupt
  IntDefaultHandler,  // IRQ76  PWM7_HD Interrupt
  IntDefaultHandler,  // IRQ77  PWM7_TZ Interrupt
  IntDefaultHandler,  // IRQ78  PWM8 Interrupt
  IntDefaultHandler,  // IRQ79  PWM8_HD Interrupt
  IntDefaultHandler,  // IRQ80  PWM8_TZ Interrupt
  IntDefaultHandler,  // IRQ81  ADC_SEQ0 Interrupt
  IntDefaultHandler,  // IRQ82  ADC_SEQ1 Interrupt
  IntDefaultHandler,  // IRQ83  ADC_SEQ2 Interrupt
  IntDefaultHandler,  // IRQ84  ADC_SEQ3 Interrupt
  IntDefaultHandler,  // IRQ85  ADC_SEQ4 Interrupt
  IntDefaultHandler,  // IRQ86  ADC_SEQ5 Interrupt
  IntDefaultHandler,  // IRQ87  ADC_SEQ6 Interrupt
  IntDefaultHandler,  // IRQ88  ADC_SEQ7 Interrupt
  IntDefaultHandler,  // IRQ89  ADC_CompInt Interrupt
  IntDefaultHandler,  // IRQ90  CAP0 Interrupt
  IntDefaultHandler,  // IRQ91  CAP1 Interrupt
  IntDefaultHandler,  // IRQ92  CAP2 Interrupt
  IntDefaultHandler,  // IRQ93  CAP3 Interrupt
  IntDefaultHandler,  // IRQ94  CAP4 Interrupt
  IntDefaultHandler,  // IRQ95  CAP5 Interrupt
  IntDefaultHandler,  // IRQ96  QEP0 Interrupt
  IntDefaultHandler,  // IRQ97  QEP1 Interrupt
  IntDefaultHandler,  // IRQ98  BootFlash Interrupt
  IntDefaultHandler,  // IRQ99  CMP0 Interrupt
  IntDefaultHandler,  // IRQ100 CMP1 Interrupt
  IntDefaultHandler,  // IRQ101 CMP2 Interrupt
  IntDefaultHandler,  // IRQ102 SPI0 Interrupt
  IntDefaultHandler,  // IRQ103 SPI1 Interrupt
  IntDefaultHandler,  // IRQ104 SPI2 Interrupt
  IntDefaultHandler,  // IRQ105 SPI3 Interrupt
  IntDefaultHandler,  // IRQ106 UserFlash Interrupt
  IntDefaultHandler,  // IRQ107 GPIOA Interrupt
  IntDefaultHandler,  // IRQ108 GPIOB Interrupt
  IntDefaultHandler,  // IRQ109 GPIOC Interrupt
  IntDefaultHandler,  // IRQ110 GPIOD Interrupt
  IntDefaultHandler,  // IRQ111 GPIOE Interrupt
  IntDefaultHandler,  // IRQ112 GPIOF Interrupt
  IntDefaultHandler,  // IRQ113 GPIOG Interrupt
  IntDefaultHandler,  // IRQ114 GPIOH Interrupt
  IntDefaultHandler,  // IRQ115 Ethernet Interrupt
  IntDefaultHandler,  // IRQ116 CAN0 Interrupt
  IntDefaultHandler,  // IRQ117 CAN1 Interrupt
  IntDefaultHandler,  // IRQ118 CAN2 Interrupt
  IntDefaultHandler,  // IRQ119 CAN3 Interrupt
  IntDefaultHandler,  // IRQ120 CAN4 Interrupt
  IntDefaultHandler,  // IRQ121 CAN5 Interrupt
  IntDefaultHandler,  // IRQ122 CAN6 Interrupt
  IntDefaultHandler,  // IRQ123 CAN7 Interrupt
  IntDefaultHandler,  // IRQ124 CAN8 Interrupt
  IntDefaultHandler,  // IRQ125 CAN9 Interrupt
  IntDefaultHandler,  // IRQ126 CAN10 Interrupt
  IntDefaultHandler,  // IRQ127 CAN11 Interrupt
  IntDefaultHandler,  // IRQ128 CAN12 Interrupt
  IntDefaultHandler,  // IRQ129 CAN13 Interrupt
  IntDefaultHandler,  // IRQ130 CAN14 Interrupt
  IntDefaultHandler,  // IRQ131 CAN15 Interrupt
  IntDefaultHandler,  // IRQ132 RTC Interrupt
  IntDefaultHandler,  // IRQ133 USBOTG Interrupt
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
