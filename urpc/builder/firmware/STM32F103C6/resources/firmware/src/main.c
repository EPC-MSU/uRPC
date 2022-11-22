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
#include "usb.h"
#include "stm32_assert.h"
#include "stm32f1xx_ll_rcc.h"
#include "stm32f1xx_ll_utils.h"
#include "stm32f1xx_ll_irq.h"  
#include "startup.h"

// FreeRTOS files
#include "FreeRTOS.h"
#include "task.h"

static void CPUClockSet(void);

/****    External function prototypes    ****/ 
extern void xPortSysTickHandler(void); 
extern void PendSV_Handler(void); 
extern void SVC_Handler(void); 

__noreturn int32_t main(void)
{

  CPUClockSet();  // Set to 72 MHz

  #ifdef DEBUG
  LL_RCC_ClocksTypeDef RCC_ClocksStructure;

  LL_RCC_GetSystemClocksFreq(&RCC_ClocksStructure);

  assert_param(RCC_ClocksStructure.HCLK_Frequency == _CPU_FREQUENCY);
  #endif  // DEBUG

  USB_Init();


  NVIC_SetPriorityGrouping(_PRIORITY_GROUP);  // All 3 bits for pre-emption priority, 0 bit for subpriority

  NVIC_SetPriority(SysTick_IRQn,          NVIC_EncodePriority(_PRIORITY_GROUP, 4, 0));
  NVIC_SetPriority(DMA1_Channel4_IRQn,    NVIC_EncodePriority(_PRIORITY_GROUP, 6, 0));
  NVIC_SetPriority(DMA1_Channel5_IRQn,    NVIC_EncodePriority(_PRIORITY_GROUP, 6, 0));
  NVIC_SetPriority(USART1_IRQn,           NVIC_EncodePriority(_PRIORITY_GROUP, 6, 0));
  NVIC_SetPriority(USB_LP_CAN1_RX0_IRQn,  NVIC_EncodePriority(_PRIORITY_GROUP, 6, 0));
  
  /* Assign interrupt handlers */
  /* General */
  LL_IRQ_Init(HardFault_IRQn, FaultISR);

  /* Free RTOS */
  LL_IRQ_Init(SysTick_IRQn, xPortSysTickHandler);
  LL_IRQ_Init(PendSV_IRQn, PendSV_Handler);
  LL_IRQ_Init(SVCall_IRQn, SVC_Handler);

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
  while (LL_RCC_HSE_IsReady() == RESET)
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

  LL_RCC_SetUSBClockSource(LL_RCC_USB_CLKSOURCE_PLL_DIV_1_5);
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
