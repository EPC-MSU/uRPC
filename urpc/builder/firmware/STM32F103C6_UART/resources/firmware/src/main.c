/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Main includes here.
 */
#include "stm32f1xx.h"

/*
 * Other includes here.
 */
#ifdef DEBUG
#include <stdio.h>  // For printf(...)
#endif  // DEBUG
#include "tty.h"
#include "stm32_assert.h"
#include "stm32f1xx_ll_rcc.h"
#include "stm32f1xx_ll_utils.h"

// FreeRTOS files
#include "FreeRTOS.h"
#include "task.h"

static void CPUClockSet(void);

__noreturn int32_t main(void)
{
  CPUClockSet();  // Set to 72 MHz

#ifdef DEBUG
  LL_RCC_ClocksTypeDef RCC_ClocksStructure;

  LL_RCC_GetSystemClocksFreq(&RCC_ClocksStructure);

  assert_param(RCC_ClocksStructure.HCLK_Frequency == _CPU_FREQUENCY);
#endif  // DEBUG

  TTY_Init();

  NVIC_SetPriorityGrouping(_PRIORITY_GROUP);  // All 3 bits for pre-emption priority, 0 bit for subpriority

  NVIC_SetPriority(SysTick_IRQn,          NVIC_EncodePriority(_PRIORITY_GROUP, 4, 0));
  NVIC_SetPriority(DMA1_Channel4_IRQn,    NVIC_EncodePriority(_PRIORITY_GROUP, 6, 0));
  NVIC_SetPriority(DMA1_Channel5_IRQn,    NVIC_EncodePriority(_PRIORITY_GROUP, 6, 0));
  NVIC_SetPriority(USART1_IRQn,           NVIC_EncodePriority(_PRIORITY_GROUP, 6, 0));
  NVIC_SetPriority(USB_LP_CAN1_RX0_IRQn,  NVIC_EncodePriority(_PRIORITY_GROUP, 6, 0));

  vTaskStartScheduler();   

  while (1)
  {
    // Capture
  }
}

/*
 * Sets System clock frequency to 72 MHz and configure
 * HCLK, PCLK1 and PCLK2 prescalers.
 *
 * The frequency of the quartz resonator 8 MHz. We multiply this value 9 times.
 */
static void CPUClockSet(void)
{
  /*
   * Enable the External High Speed oscillator (HSE).
   */
  LL_RCC_HSE_Enable();

  /*
   * Wait till HSE is ready.
   */
  while(LL_RCC_HSE_IsReady() == RESET)
  {
    // Capture
  }

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
  UTILS_PLLInitStructure.PLLMul = LL_RCC_PLL_MUL_9;
  UTILS_PLLInitStructure.Prediv = LL_RCC_PREDIV_DIV_1;

  UTILS_ClkInitStructure.AHBCLKDivider  = LL_RCC_SYSCLK_DIV_1;
  UTILS_ClkInitStructure.APB1CLKDivider = LL_RCC_APB1_DIV_2;
  UTILS_ClkInitStructure.APB2CLKDivider = LL_RCC_APB2_DIV_1;

  LL_PLL_ConfigSystemClock_HSE(8000000, LL_UTILS_HSEBYPASS_OFF, &UTILS_PLLInitStructure, &UTILS_ClkInitStructure);
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