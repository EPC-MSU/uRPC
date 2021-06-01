/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Main includes here.
 */
#include "MDR32F9Qx_config.h"

/*
 * Other includes here.
 */
#include <stdio.h>  // For printf(...)
#include "MDR32F9Qx_rst_clk.h"
#include "usb.h"

static void CPUClockSet(void);

__noreturn int32_t main(void)
{
  CPUClockSet();  // Set to 80 MHz

  USB_Init();

  NVIC_SetPriorityGrouping(_PRIORITY_GROUP);  // All 3 bits for pre-emption priority, 0 bit for subpriority

  NVIC_SetPriority(SysTick_IRQn,  NVIC_EncodePriority(_PRIORITY_GROUP, 4, 0));
  NVIC_SetPriority(USB_IRQn,      NVIC_EncodePriority(_PRIORITY_GROUP, 6, 0));
  NVIC_SetPriority(UART1_IRQn,    NVIC_EncodePriority(_PRIORITY_GROUP, 6, 0));

  while (1)
  {
    // Capture
  }
}

/*
 * Set CPU frequency to 80 MHz.
 * The frequency of the quartz resonator 8 MHz.
 * We multiply this value 10 times.
 */
static void CPUClockSet(void)
{
  RST_CLK_HSEconfig(RST_CLK_HSE_ON);  // Enable HSE

  if (RST_CLK_HSEstatus() != SUCCESS)
  {
    while (1)
    {
      // Capture
    }
  }

  /*
   * Multiplied frequency 10 times.
   */
  RST_CLK_CPU_PLLconfig(RST_CLK_CPU_PLLsrcHSEdiv1, RST_CLK_CPU_PLLmul10);   // CPU_C1_SEL = HSE
  RST_CLK_CPU_PLLcmd(ENABLE);

  if (RST_CLK_CPU_PLLstatus() != SUCCESS)
  {
    while (1)
    {
      // Capture
    }
  }

  RST_CLK_CPUclkPrescaler(RST_CLK_CPUclkDIV1);  // CPU_C3_SEL = CPU_C2_SEL
  RST_CLK_CPU_PLLuse(ENABLE);   // CPU_C2_SEL = PLL
  RST_CLK_CPUclkSelection(RST_CLK_CPUclkCPU_C3);  // HCLK_SEL = CPU_C3_SEL
}

#ifdef DEBUG
/*
 * Reports the name of the source file and the source line number
 * where the assert_param error has occurred.
 */
void assert_failed(const uint8_t *file, uint32_t line, const uint8_t* expr)
{
  printf("Error in %s, line %ld. Expression: %s is not true\n", file, line, expr);

  while (1)
  {
    // Capture
  }
}
#endif  // DEBUG
