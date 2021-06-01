/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Main includes here.
 */
#include "startup.h"

/*
 * Other includes here.
 */
#include "inc/hw_types.h"
#include "inc/hw_nvic.h"
#include "inc/hw_memmap.h"
#include "driverlib/gpio.h"
#include "driverlib/sysctl.h"
#include <stdio.h>

#define RAM_START   0x20000000
#define RAM_SIZE    SysCtlSRAMSizeGet()

#define STACK_SIZE  1024

extern int32_t main(void);

static void InitDataAndBSS(void);
static inline void MemoryManagementFaultSignal(void);

extern void xPortPendSVHandler(void);
extern void xPortSysTickHandler(void);
extern void vPortSVCHandler(void);

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

#if defined (__ICCARM__)
#define __vectors   __root const uVectorEntry __vector_table[] @ ".intvec"
#define __stack     { .ulPtr = (uint32_t)Stack + sizeof(Stack) }

//*****************************************************************************
//
// A union that describes the entries of the vector table.  The union is needed
// since the first entry is the stack pointer and the remainder are function
// pointers.
//
//*****************************************************************************
typedef union
{
  void (*pfnHandler)(void);
  unsigned long ulPtr;
}
uVectorEntry;
//*****************************************************************************
//
// Enable the IAR extensions for this source file.
//
//*****************************************************************************
#pragma language=extended
#endif
#ifdef __GNUC__
#define __vectors \
  __attribute__ ((section(".isr_vector"))) \
  void (* const __cs3_interrupt_vector_cortex_m[])(void)

__attribute__((section(".stackarea"))) static unsigned long Stack[STACK_SIZE];
#define __stack (void (*)(void))((unsigned long)Stack + sizeof(Stack))

#endif

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
  __asm("mov r1,#0x00");
  __asm("ldr sp,[r1]");

  //
  // Run data and bss initialization (global variables initial values)
  //
  InitDataAndBSS();

  //
  // Call the application's entry point.
  //
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
  __stack,                            // The initial stack pointer
  ResetISR,                           // The reset handler
  NmiSR,                              // The NMI handler
  FaultISR,                           // The hard fault handler
  IntDefaultHandler,                  // The MPU fault handler
  IntDefaultHandler,                  // The bus fault handler
  IntDefaultHandler,                  // The usage fault handler
  0,                                  // Reserved
  0,                                  // Reserved
  0,                                  // Reserved
  0,                                  // Reserved
  vPortSVCHandler,                    // SVCall handler
  IntDefaultHandler,                  // Debug monitor handler
  0,                                  // Reserved
  xPortPendSVHandler,                 // The PendSV handler
  xPortSysTickHandler,                // The SysTick handler
  IntDefaultHandler,                  // GPIO Port A
  IntDefaultHandler,                  // GPIO Port B
  IntDefaultHandler,                  // GPIO Port C
  IntDefaultHandler,                  // GPIO Port D
  IntDefaultHandler,                  // GPIO Port E
  IntDefaultHandler,                  // UART0 Rx and Tx
  IntDefaultHandler,                  // UART1 Rx and Tx
  IntDefaultHandler,                  // SSI0 Rx and Tx
  IntDefaultHandler,                  // I2C0 Master and Slave
  IntDefaultHandler,                  // PWM Fault
  IntDefaultHandler,                  // PWM Generator 0
  IntDefaultHandler,                  // PWM Generator 1
  IntDefaultHandler,                  // PWM Generator 2
  IntDefaultHandler,                  // Quadrature Encoder 0
  IntDefaultHandler,                  // ADC Sequence 0
  IntDefaultHandler,                  // ADC Sequence 1
  IntDefaultHandler,                  // ADC Sequence 2
  IntDefaultHandler,                  // ADC Sequence 3
  IntDefaultHandler,                  // Watchdog timer
  IntDefaultHandler,                  // Timer 0 subtimer A
  IntDefaultHandler,                  // Timer 0 subtimer B
  IntDefaultHandler,                  // Timer 1 subtimer A
  IntDefaultHandler,                  // Timer 1 subtimer B
  IntDefaultHandler,                  // Timer 2 subtimer A
  IntDefaultHandler,                  // Timer 2 subtimer B
  IntDefaultHandler,                  // Analog Comparator 0
  IntDefaultHandler,                  // Analog Comparator 1
  IntDefaultHandler,                  // Analog Comparator 2
  IntDefaultHandler,                  // System Control (PLL, OSC, BO)
  IntDefaultHandler,                  // FLASH Control
  IntDefaultHandler,                  // GPIO Port F
  IntDefaultHandler,                  // GPIO Port G
  IntDefaultHandler,                  // GPIO Port H
  IntDefaultHandler,                  // UART2 Rx and Tx
  IntDefaultHandler,                  // SSI1 Rx and Tx
  IntDefaultHandler,                  // Timer 3 subtimer A
  IntDefaultHandler,                  // Timer 3 subtimer B
  IntDefaultHandler,                  // I2C1 Master and Slave
  IntDefaultHandler,                  // CAN0
  IntDefaultHandler,                  // CAN1
  IntDefaultHandler,                  // Ethernet
  IntDefaultHandler,                  // Hibernate
  IntDefaultHandler,                  // USB0
  IntDefaultHandler,                  // PWM Generator 3
  IntDefaultHandler,                  // uDMA Software Transfer
  IntDefaultHandler,                  // uDMA Error
  IntDefaultHandler,                  // ADC1 Sequence 0
  IntDefaultHandler,                  // ADC1 Sequence 1
  IntDefaultHandler,                  // ADC1 Sequence 2
  IntDefaultHandler,                  // ADC1 Sequence 3
  IntDefaultHandler,                  // External Bus Interface 0
  IntDefaultHandler,                  // GPIO Port J
  IntDefaultHandler,                  // GPIO Port K
  IntDefaultHandler,                  // GPIO Port L
  IntDefaultHandler,                  // SSI2 Rx and Tx
  IntDefaultHandler,                  // SSI3 Rx and Tx
  IntDefaultHandler,                  // UART3 Rx and Tx
  IntDefaultHandler,                  // UART4 Rx and Tx
  IntDefaultHandler,                  // UART5 Rx and Tx
  IntDefaultHandler,                  // UART6 Rx and Tx
  IntDefaultHandler,                  // UART7 Rx and Tx
  IntDefaultHandler,                  // I2C2 Master and Slave
  IntDefaultHandler,                  // I2C3 Master and Slave
  IntDefaultHandler,                  // Timer 4 subtimer A
  IntDefaultHandler,                  // Timer 4 subtimer B
  IntDefaultHandler,                  // Timer 5 subtimer A
  IntDefaultHandler,                  // Timer 5 subtimer B
  IntDefaultHandler,                  // FPU
  0,                                  // Reserved
  0,                                  // Reserved
  IntDefaultHandler,                  // I2C4 Master and Slave
  IntDefaultHandler,                  // I2C5 Master and Slave
  IntDefaultHandler,                  // GPIO Port M
  IntDefaultHandler,                  // GPIO Port N
  0,                                  // Reserved
  IntDefaultHandler,                  // Tamper
  IntDefaultHandler,                  // GPIO Port P (Summary or P0)
  IntDefaultHandler,                  // GPIO Port P1
  IntDefaultHandler,                  // GPIO Port P2
  IntDefaultHandler,                  // GPIO Port P3
  IntDefaultHandler,                  // GPIO Port P4
  IntDefaultHandler,                  // GPIO Port P5
  IntDefaultHandler,                  // GPIO Port P6
  IntDefaultHandler,                  // GPIO Port P7
  IntDefaultHandler,                  // GPIO Port Q (Summary or Q0)
  IntDefaultHandler,                  // GPIO Port Q1
  IntDefaultHandler,                  // GPIO Port Q2
  IntDefaultHandler,                  // GPIO Port Q3
  IntDefaultHandler,                  // GPIO Port Q4
  IntDefaultHandler,                  // GPIO Port Q5
  IntDefaultHandler,                  // GPIO Port Q6
  IntDefaultHandler,                  // GPIO Port Q7
  IntDefaultHandler,                  // GPIO Port R
  IntDefaultHandler,                  // GPIO Port S
  IntDefaultHandler,                  // SHA/MD5 0
  IntDefaultHandler,                  // AES 0
  IntDefaultHandler,                  // DES3DES 0
  IntDefaultHandler,                  // LCD Controller 0
  IntDefaultHandler,                  // Timer 6 subtimer A
  IntDefaultHandler,                  // Timer 6 subtimer B
  IntDefaultHandler,                  // Timer 7 subtimer A
  IntDefaultHandler,                  // Timer 7 subtimer B
  IntDefaultHandler,                  // I2C6 Master and Slave
  IntDefaultHandler,                  // I2C7 Master and Slave
  IntDefaultHandler,                  // HIM Scan Matrix Keyboard 0
  IntDefaultHandler,                  // One Wire 0
  IntDefaultHandler,                  // HIM PS/2 0
  IntDefaultHandler,                  // HIM LED Sequencer 0
  IntDefaultHandler,                  // HIM Consumer IR 0
  IntDefaultHandler,                  // I2C8 Master and Slave
  IntDefaultHandler,                  // I2C9 Master and Slave
  IntDefaultHandler                   // GPIO Port T
};

//*****************************************************************************
//
// This is the code that gets called when the processor receives a NMI.  This
// simply enters an infinite loop, preserving the system state for examination
// by a debugger.
//
//*****************************************************************************
void NmiSR(void)
{
  //
  // Enter an infinite loop.
  //
  while (1)
  {
  }
}

static inline void MemoryManagementFaultSignal ( void )
{
  SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOF);
  GPIOPinTypeGPIOOutput(GPIO_PORTF_BASE, GPIO_PIN_3); // set LED_pin as output
  GPIOPadConfigSet(GPIO_PORTF_BASE, GPIO_PIN_3, GPIO_STRENGTH_8MA, GPIO_PIN_TYPE_STD);



  while (true)
  {
    for (unsigned int i = 0; i < 2; i++)
    {
      GPIOPinWrite(GPIO_PORTF_BASE, GPIO_PIN_3, 0xff);
      SysCtlDelay(2000000);
      GPIOPinWrite(GPIO_PORTF_BASE, GPIO_PIN_3, 0x00);
      SysCtlDelay(2000000);
    }
    SysCtlDelay(8000000);
  }
}

//*****************************************************************************
//
// This is the code that gets called when the processor receives a fault
// interrupt.  This simply enters an infinite loop, preserving the system state
// for examination by a debugger.
//
//*****************************************************************************
void FaultISR(void)
{
  static unsigned char fMPUFault = false;

  SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOF);
  GPIOPinTypeGPIOOutput(GPIO_PORTF_BASE, GPIO_PIN_3); // set LED_pin as output
  GPIOPadConfigSet(GPIO_PORTF_BASE, GPIO_PIN_3, GPIO_STRENGTH_8MA, GPIO_PIN_TYPE_STD);
  GPIOPinWrite(GPIO_PORTF_BASE, GPIO_PIN_3, 0xff);

  // Check for MPU fault and set the corresponding flag.
  if ((HWREG(NVIC_FAULT_STAT) & 0x00000010))
  {
    fMPUFault = true;
  }


  #ifdef DEBUG
  // Memory Management Faults
  if ((HWREG(NVIC_FAULT_STAT) & 0x00000001))
  {
    printf ("Instruction Access Violation\n");// IERR
    printf ("at address %x \n", (unsigned int) HWREG(NVIC_MM_ADDR));
    fMPUFault = true;
  }
  if ((HWREG(NVIC_FAULT_STAT) & 0x00000002))
  {
    printf ("Data Access Violation\n"); // DERR
    fMPUFault = true;
  }
  if ((HWREG(NVIC_FAULT_STAT) & 0x00000008))
  {
    printf ("Unstack Access Violation\n"); // MUSTKE
    fMPUFault = true;
  }
  if ((HWREG(NVIC_FAULT_STAT) & 0x00000010))
  {
    printf ("Stack Access Violation\n"); // MSTKE
    fMPUFault = true;
  }

  // Bus Faults
  if ((HWREG(NVIC_FAULT_STAT) & 0x00000100))
  {
    printf ("Instruction Bus Error\n");  // IBUS
  }
  if ((HWREG(NVIC_FAULT_STAT) & 0x00000200))
  {
    printf ("Precise Data Bus Error\n"); // PRECISE
    printf ("at address %x \n", (unsigned int) HWREG(NVIC_FAULT_ADDR));
  }
  if ((HWREG(NVIC_FAULT_STAT) & 0x00000400))
  {
    printf ("Imprecise Data Bus Error\n");  // IMPRE
  }
  if ((HWREG(NVIC_FAULT_STAT) & 0x00000800))
  {
    printf ("Unstack Bus Fault\n");  // BUSTKE
  }
  if ((HWREG(NVIC_FAULT_STAT) & 0x00001000))
  {
    printf ("Stack Bus Fault\n");  // BSTKE
  }

  // Usage Faults
  if ((HWREG(NVIC_FAULT_STAT) & 0x00010000))
  {
    printf ("Undefined Instruction Usage Fault\n");  // UNDEF
  }
  if ((HWREG(NVIC_FAULT_STAT) & 0x00020000))
  {
    printf ("Invalid State Usage Fault\n");  // INVSTAT
  }
  if ((HWREG(NVIC_FAULT_STAT) & 0x00040000))
  {
    printf ("Invalid PC Load Usage Fault\n");  // INVPC
  }
  if ((HWREG(NVIC_FAULT_STAT) & 0x00080000))
  {
    printf ("No Coprocessor Usage Fault\n");  // NOCP
  }
  if ((HWREG(NVIC_FAULT_STAT) & 0x01000000))
  {
    printf ("Unaligned Access Usage Fault\n");  // UNALIGN
  }
  if ((HWREG(NVIC_FAULT_STAT) & 0x02000000))
  {
    printf ("Divide-by-Zero Usage Fault\n");  // DIV0
  }

  // Hard Faults
  if (HWREG(NVIC_HFAULT_STAT) & 0x00000002)
  {
    printf ("A bus fault occurred on a vector table read.\n");
  }
  if (HWREG(NVIC_HFAULT_STAT) & 0x40000000)
  {
    printf ("Forced Hard Fault\n");
  }
  #endif

  //  If the MPU fault is handled it starts to flash by LED
  if (fMPUFault )
  {
    MemoryManagementFaultSignal();
  }

  while (1); // Infinite loop
}

//*****************************************************************************
//
// This is the code that gets called when the processor receives an unexpected
// interrupt.  This simply enters an infinite loop, preserving the system state
// for examination by a debugger.
//
//*****************************************************************************
void IntDefaultHandler(void)
{
  #ifdef DEBUG
  printf ("Default handler has been triggered.\n");
  #endif
  while (1); // Infinite loop
}
