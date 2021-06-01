/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Main includes here.
 */
#include "niietcm4.h"

/*
 * Other includes here.
 */
#include "niietcm4_gpio.h"
#include "niietcm4_rcc.h"
#include "tty.h"

#ifdef DEBUG
  #include <stdio.h>  // For printf(...)

  #define LIFEBUOY_PORT   NT_GPIOF
  #define LIFEBUOY_PIN    GPIO_Pin_7

  // FreeRTOS files
  #include "FreeRTOS.h"
  #include "task.h"

  static inline void Lifebuoy(void);
#endif  // DEBUG

__noreturn int32_t main(void)
{
  #ifdef DEBUG
  Lifebuoy();   // Check F7 pin

  OperationStatus Status = RCC_PLLAutoConfig(RCC_PLLRef_XI_OSC, _CPU_FREQUENCY);

  assert_param(Status == OK);
  #else
  RCC_PLLAutoConfig(RCC_PLLRef_XI_OSC, _CPU_FREQUENCY);
  #endif  // DEBUG

  TTY_Init();

  NVIC_SetPriorityGrouping(_PRIORITY_GROUP);  // All 3 bits for pre-emption priority, 0 bit for subpriority

  NVIC_SetPriority(SysTick_IRQn,  NVIC_EncodePriority(_PRIORITY_GROUP, 4, 0));
  NVIC_SetPriority(USBOTG_IRQn,   NVIC_EncodePriority(_PRIORITY_GROUP, 6, 0));
  NVIC_SetPriority(UART3_IRQn,    NVIC_EncodePriority(_PRIORITY_GROUP, 6, 0));

  vTaskStartScheduler();


  while (1)
  {
    // Capture
  }
}

#ifdef DEBUG
/*
 * Save chip when JTAG is locked.
 */
static inline void Lifebuoy(void)
{
  GPIO_Init_TypeDef GPIO_InitStructure;

  /*
   * The initial data for port.
   */
  GPIO_InitStructure.GPIO_Pin = LIFEBUOY_PIN;
  GPIO_InitStructure.GPIO_Dir = GPIO_Dir_In;
  GPIO_InitStructure.GPIO_Out = GPIO_Out_Dis;
  GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IO;
  GPIO_InitStructure.GPIO_AltFunc = GPIO_AltFunc_1;
  GPIO_InitStructure.GPIO_OutMode = GPIO_OutMode_PP;
  GPIO_InitStructure.GPIO_PullUp = GPIO_PullUp_Dis;

  GPIO_Init(LIFEBUOY_PORT, &GPIO_InitStructure);

  assert_param(GPIO_ReadBit(LIFEBUOY_PORT, LIFEBUOY_PIN));
}

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