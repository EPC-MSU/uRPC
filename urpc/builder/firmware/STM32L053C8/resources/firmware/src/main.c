/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

#include "atomicrun.h"

/*
 * Other includes here.
 */
#ifdef DEBUG
  #include <stdio.h>  // For printf(...)
#endif  // DEBUG
#include "usb.h"
#include "stm32_assert.h"
#include "stm32l0xx_ll_bus.h"
#include "stm32l0xx_ll_pwr.h"
#include "stm32l0xx_ll_rcc.h"
#include "stm32l0xx_ll_utils.h"

// FreeRTOS files
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "croutine.h"
#include "semphr.h"
#include "timers.h"
#include "pdc.h"


static void CPUClockSet(void);

__noreturn int32_t main(void)
{
  CPUClockSet();  // Set to 32 MHz

  #ifdef DEBUG
  LL_RCC_ClocksTypeDef RCC_ClocksStructure;

  LL_RCC_GetSystemClocksFreq(&RCC_ClocksStructure);

  assert_param(RCC_ClocksStructure.HCLK_Frequency == _CPU_FREQUENCY);
  #endif  // DEBUG

  USB_Init();

  NVIC_SetPriority(SysTick_IRQn,              1);
  NVIC_SetPriority(DMA1_Channel4_5_6_7_IRQn,  3);
  NVIC_SetPriority(USART1_IRQn,               3);
  NVIC_SetPriority(USB_IRQn,                  3);

  vTaskStartScheduler();

  while (1)
  {
    // Capture
  }
}

/*
 * Sets System clock frequency to 32 MHz and configure
 * HCLK, PCLK1 and PCLK2 prescalers.
 */
static void CPUClockSet(void)
{
  /*
   * Enable Power Control clock.
   */
  LL_APB1_GRP1_EnableClock(LL_APB1_GRP1_PERIPH_PWR);

  /*
   * The voltage scaling allows optimizing the power consumption when the device is
   * clocked below the maximum system frequency, to update the voltage scaling value
   * regarding system frequency refer to product datasheet.
   */
  LL_PWR_SetRegulVoltageScaling(LL_PWR_REGU_VOLTAGE_SCALE1);

  /*
   * Enable the Internal High Speed oscillator (HSI).
   */
  LL_RCC_HSI_Enable();

  /*
   * Wait till HSI is ready.
   */
  while (LL_RCC_HSI_IsReady() == RESET)
  {
    // Capture
  }

  /*
   * Adjusts the Internal High Speed oscillator (HSI) calibration value.
   */
  LL_RCC_HSI_SetCalibTrimming(0x10);  // Default value is 16

  LL_UTILS_PLLInitTypeDef UTILS_PLLInitStructure;
  LL_UTILS_ClkInitTypeDef UTILS_ClkInitStructure;

  /*
   * Do that steps:
   *   - Configure the main PLL clock source, multiplication and division factors.
   *   - Enable the main PLL.
   *   - Wait till PLL is ready.
   *   - Increasing the number of flash wait states because of higher CPU frequency.
   *   - Select PLL as System Clock Source.
   */
  UTILS_PLLInitStructure.PLLMul = LL_RCC_PLL_MUL_6;
  UTILS_PLLInitStructure.PLLDiv = LL_RCC_PLL_DIV_3;

  UTILS_ClkInitStructure.AHBCLKDivider  = LL_RCC_SYSCLK_DIV_1;
  UTILS_ClkInitStructure.APB1CLKDivider = LL_RCC_APB1_DIV_1;
  UTILS_ClkInitStructure.APB2CLKDivider = LL_RCC_APB2_DIV_1;

  LL_PLL_ConfigSystemClock_HSI(&UTILS_PLLInitStructure, &UTILS_ClkInitStructure);

  LL_RCC_SetUSBClockSource(LL_RCC_USB_CLKSOURCE_PLL);
}

#ifdef DEBUG
/*
 * Reports the name of the source file and the source line number
 * where the assert_param error has occurred.
 */
void assert_failed(uint8_t *file, uint32_t line)
{
  printf("Error in %s, line %ld\n", file, line);

  while (1)
  {
    // Capture
  }
}
#endif  // DEBUG
