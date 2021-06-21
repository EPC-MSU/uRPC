/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Main includes here.
 */
#include "stm32f4xx.h"

/*
 * Other includes here.
 */
#ifdef DEBUG
  #include <stdio.h>  // For printf(...) DEBUG
#endif  // DEBUG
#include "tty.h"
#include "stm32_assert.h"
#include "stm32f4xx_ll_bus.h"
#include "stm32f4xx_ll_rcc.h"
#include "stm32f4xx_ll_utils.h"
#include "stm32f4xx_ll_system.h"
#include "stm32f4xx_ll_cortex.h"
#include "stm32f4xx_ll_pwr.h"
#include "stm32f4xx_ll_irq.h"
#include "stm32f4xx_ll_tim.h"
#include "stm32f4xx_ll_gpio.h"

#include "FreeRTOS.h"
#include "task.h"

void vApplicationIdleHook(void);
static void CPUClockSet(void);

__noreturn int32_t main(void)
{
  //Clocking
  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOH);
  LL_AHB1_GRP1_EnableClock(LL_AHB1_GRP1_PERIPH_GPIOG);
  LL_APB2_GRP1_EnableClock(LL_APB2_GRP1_PERIPH_SYSCFG);
  LL_APB1_GRP1_EnableClock(LL_APB1_GRP1_PERIPH_PWR);

  CPUClockSet();  // Set to 144 MHz

  #ifdef DEBUG
  LL_RCC_ClocksTypeDef RCC_ClocksStructure;

  LL_RCC_GetSystemClocksFreq(&RCC_ClocksStructure);
  assert_param(RCC_ClocksStructure.HCLK_Frequency == _CPU_FREQUENCY);
  #endif  // DEBUG

  TTY_Init();

  NVIC_SetPriorityGrouping(_PRIORITY_GROUP);  // All 3 bits for pre-emption priority, 0 bit for subpriority
  NVIC_SetPriority(SysTick_IRQn,          NVIC_EncodePriority(_PRIORITY_GROUP, 4, 0));
  NVIC_SetPriority(DMA1_Stream1_IRQn,     NVIC_EncodePriority(_PRIORITY_GROUP, 6, 0));
  NVIC_SetPriority(DMA1_Stream3_IRQn,     NVIC_EncodePriority(_PRIORITY_GROUP, 6, 0));
  NVIC_SetPriority(USART3_IRQn,           NVIC_EncodePriority(_PRIORITY_GROUP, 6, 0));


  vTaskStartScheduler();

  while (1)
  {
    // Capture
  }
}

/*
 * Sets System clock frequency to 144 MHz and configure
 * HCLK, PCLK1 and PCLK2 prescalers.
 *
 * The frequency of the quartz resonator 8 MHz. We multiply this value 18 times.
 */
static void CPUClockSet(void)
{
  LL_FLASH_SetLatency(LL_FLASH_LATENCY_4);

  if (LL_FLASH_GetLatency() != LL_FLASH_LATENCY_4)
  {
    //Error_Handler();
  }
  LL_PWR_SetRegulVoltageScaling(LL_PWR_REGU_VOLTAGE_SCALE1);
  LL_PWR_EnableOverDriveMode();
  LL_RCC_HSE_Enable();

  /* Wait till HSE is ready */
  while (LL_RCC_HSE_IsReady() != 1)
  {

  }
  LL_RCC_PLL_ConfigDomain_SYS(LL_RCC_PLLSOURCE_HSE, LL_RCC_PLLM_DIV_8, 288, LL_RCC_PLLP_DIV_2);
  LL_RCC_PLL_ConfigDomain_48M(LL_RCC_PLLSOURCE_HSE, LL_RCC_PLLM_DIV_8, 288, LL_RCC_PLLQ_DIV_6);
  LL_RCC_PLL_Enable();

  /* Wait till PLL is ready */
  while (LL_RCC_PLL_IsReady() != 1)
  {

  }
  LL_RCC_SetAHBPrescaler(LL_RCC_SYSCLK_DIV_1);
  LL_RCC_SetAPB1Prescaler(LL_RCC_APB1_DIV_4);
  LL_RCC_SetAPB2Prescaler(LL_RCC_APB2_DIV_2);
  LL_RCC_SetSysClkSource(LL_RCC_SYS_CLKSOURCE_PLL);

  /* Wait till System clock is ready */
  while (LL_RCC_GetSysClkSource() != LL_RCC_SYS_CLKSOURCE_STATUS_PLL)
  {

  }
  LL_Init1msTick(144000000);
  LL_SYSTICK_SetClkSource(LL_SYSTICK_CLKSOURCE_HCLK);
  LL_SetSystemCoreClock(144000000);
  LL_RCC_SetTIMPrescaler(LL_RCC_TIM_PRESCALER_TWICE);
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

void vApplicationIdleHook(void)
{
  while (1);
}