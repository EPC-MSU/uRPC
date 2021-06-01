/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Main includes here.
 */
#include "stm32f10x_conf.h"

/*
 * Other includes here.
 */
#ifdef DEBUG
#include <stdio.h>  // For printf(...)
#endif  // DEBUG
#include "stm32f10x_flash.h"
#include "stm32f10x_rcc.h"
#include "tty.h"

static void CPUClockSet(void);

__noreturn int32_t main(void)
{
  CPUClockSet();  // Set to 72 MHz

  TTY_Init();

  NVIC_SetPriorityGrouping(_PRIORITY_GROUP);  // All 3 bits for pre-emption priority, 0 bit for subpriority

  NVIC_SetPriority(SysTick_IRQn,  NVIC_EncodePriority(_PRIORITY_GROUP, 4, 0));
  NVIC_SetPriority(USART1_IRQn,   NVIC_EncodePriority(_PRIORITY_GROUP, 6, 0));

  while (1)
  {
    // Capture
  }
}

/*
 * Set CPU frequency to 72 MHz.
 * The frequency of the quartz resonator 8 MHz.
 * We multiply this value 9 times.
 */
static void CPUClockSet(void)
{
  RCC_HSEConfig(RCC_HSE_ON);  // Enable HSE

  /*
   * Wait till HSE is ready and if Time out is reached exit.
   */
#ifdef DEBUG
  ErrorStatus HSEStatus = RCC_WaitForHSEStartUp();
  assert_param(HSEStatus == SUCCESS);
#else
  RCC_WaitForHSEStartUp();
#endif  // DEBUG

  FLASH_PrefetchBufferCmd(FLASH_PrefetchBuffer_Enable);   // Enable Prefetch Buffer
  FLASH_SetLatency(FLASH_Latency_2);  // Flash 2 wait state

  RCC_HCLKConfig(RCC_SYSCLK_Div1);  // HCLK = SYSCLK
  RCC_PCLK1Config(RCC_HCLK_Div2);   // PCLK1 = HCLK / 2
  RCC_PCLK2Config(RCC_HCLK_Div1);   // PCLK2 = HCLK

  /*
   * PLL configuration: PLLCLK = HSE * 9 = 72 MHz.
   */
  RCC_PLLConfig(RCC_PLLSource_HSE_Div1, RCC_PLLMul_9);
  RCC_PLLCmd(ENABLE);   // Enable PLL

  FlagStatus PLLStatus;

  /*
   * Wait till PLL is ready.
   */
  do
  {
    PLLStatus = RCC_GetFlagStatus(RCC_FLAG_PLLRDY);

  } while (PLLStatus == RESET);

  RCC_SYSCLKConfig(RCC_SYSCLKSource_PLLCLK);  // Select PLL as system clock source

  uint32_t Source;

  do
  {
    Source = RCC->CFGR & RCC_CFGR_SWS;  // Get SYSCLK source

  } while (Source != RCC_CFGR_SWS_PLL);
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
