/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Main includes here.
 */
#include "niietcm4.h"
#include "tty.h"

/*
 * Other includes here.
 */
#include "niietcm4_gpio.h"
#include "niietcm4_irq.h"
#include "niietcm4_rcc.h"
#include "flowparser.h"
#include "iobuffer.h"

// FreeRTOS files
#include "FreeRTOS.h"
#include "timers.h"

#include <stdio.h>  // For printf(...)

//#define USE_HACK

#ifdef USE_HACK
  #define HACK_PORT         NT_GPIOE
  #define HACK_RX_PIN       GPIO_Pin_0
  #define HACK_RX_ALTFUNC   GPIO_AltFunc_3
#endif  // USE_HACK

#define TTY_PORT        NT_GPIOF
#define TTY_RX_PIN      GPIO_Pin_13
#define TTY_RX_ALTFUNC  GPIO_AltFunc_1
#define TTY_TX_PIN      GPIO_Pin_12
#define TTY_TX_ALTFUNC  GPIO_AltFunc_1

#define TTY_PERIPHRST   RCC_PeriphRst_UART3
#define TTY_UART_IRQ    UART3_IRQn
#define TTY_UART        NT_UART3

static io_buffer_t RxBuffer;
static io_buffer_t TxBuffer;


TimerHandle_t CleanRxBufferTimerHandle;
static void USBCleanRxBufferCallback(TimerHandle_t xTimer);

static void TTY_IntHandler(void);
static inline void DataTransmitting(void);

static bool Engaged = false;

void TTY_Init(void)
{
  /*
   * Protection against double initialization.
   */
  if (Engaged)
  {
    return;
  }

  Engaged = true;

  IOBuffer_Init(&RxBuffer);
  IOBuffer_Init(&TxBuffer);

  CleanRxBufferTimerHandle = xTimerCreate("Clean Rx buffer timer",
                                          pdMS_TO_TICKS(_PROTOCOL_DELAY),
                                          pdFALSE,
                                          ( void * ) 0,
                                          USBCleanRxBufferCallback);


  if (CleanRxBufferTimerHandle == NULL)
  {
    #ifdef DEBUG
    printf ("The timer was not created.\n");
    while (1); // Infinite loop
    #endif
  }

  if (xTimerStart(CleanRxBufferTimerHandle, 0) != pdPASS)
  {
    #ifdef DEBUG
    printf ("The timer was not started.\n");
    while (1); // Infinite loop
    #endif
  }

  RCC_PeriphRstCmd(TTY_PERIPHRST, DISABLE);

  #ifdef USE_HACK
  /*
   * Hack the priorities of alternative function. See documentation page 77.
   */
  GPIO_AltFuncConfig(HACK_PORT, HACK_RX_PIN, HACK_RX_ALTFUNC);
  #endif  // USE_HACK

  GPIO_Init_TypeDef GPIO_InitStructure;

  /*
   * The initial data for Rx.
   */
  GPIO_InitStructure.GPIO_Pin   = TTY_RX_PIN;
  GPIO_InitStructure.GPIO_Dir   = GPIO_Dir_In;
  GPIO_InitStructure.GPIO_Out   = GPIO_Out_Dis;
  GPIO_InitStructure.GPIO_Mode  = GPIO_Mode_AltFunc;
  GPIO_InitStructure.GPIO_AltFunc   = TTY_RX_ALTFUNC;
  GPIO_InitStructure.GPIO_OutMode   = GPIO_OutMode_PP;
  GPIO_InitStructure.GPIO_PullUp    = GPIO_PullUp_Dis;

  GPIO_Init(TTY_PORT, &GPIO_InitStructure);

  /*
   * The initial data for Tx.
   */
  GPIO_InitStructure.GPIO_Pin   = TTY_TX_PIN;
  GPIO_InitStructure.GPIO_Dir   = GPIO_Dir_Out;
  GPIO_InitStructure.GPIO_Out   = GPIO_Out_En;
  GPIO_InitStructure.GPIO_Mode  = GPIO_Mode_AltFunc;
  GPIO_InitStructure.GPIO_AltFunc   = TTY_TX_ALTFUNC;
  GPIO_InitStructure.GPIO_OutMode   = GPIO_OutMode_PP;
  GPIO_InitStructure.GPIO_PullUp    = GPIO_PullUp_Dis;

  GPIO_Init(TTY_PORT, &GPIO_InitStructure);

  /*
   * Disable the reset state and enable clock.
   */
  RCC_PeriphRstCmd(TTY_PERIPHRST, ENABLE);
  RCC_UARTClkCmd(TTY_UART, ENABLE);

  UART_ITCmd(TTY_UART, UART_ITSource_RxFIFOLevel | UART_ITSource_TxFIFOLevel | UART_ITSource_RecieveTimeout, ENABLE);
  IRQ_HandlerInit(TTY_UART_IRQ, TTY_IntHandler);
  NVIC_EnableIRQ(TTY_UART_IRQ);

  /*
   * Use default settings for first init.
   */
  TTY_SettingsChange(UART_StopBit_1, UART_ParityBit_Disable, 115200);
}

void TTY_SettingsChange(UART_StopBit_TypeDef    StopBit,
                        UART_ParityBit_TypeDef  ParityBit,
                        uint32_t                BaudRate)
{
  assert_param(Engaged);

  UART_Cmd(TTY_UART, DISABLE);

  UART_Init_TypeDef UART_InitStructure;

  /*
   * The initial data for UART.
   */
  UART_InitStructure.UART_StopBit     = StopBit;
  UART_InitStructure.UART_ParityBit   = ParityBit;
  UART_InitStructure.UART_DataWidth   = UART_DataWidth_8;
  UART_InitStructure.UART_ClkFreq     = _CPU_FREQUENCY;
  UART_InitStructure.UART_BaudRate    = BaudRate;
  UART_InitStructure.UART_FIFOLevelRx   = UART_FIFOLevel_3_4;
  UART_InitStructure.UART_FIFOLevelTx   = UART_FIFOLevel_1_4;
  UART_InitStructure.UART_FIFOEn  = ENABLE;
  UART_InitStructure.UART_RxEn    = ENABLE;
  UART_InitStructure.UART_TxEn    = ENABLE;

  UART_Init(TTY_UART, &UART_InitStructure);

  UART_Cmd(TTY_UART, ENABLE);
}

static void TTY_IntHandler(void)
{
  if (UART_ITMaskedStatus(TTY_UART, UART_ITSource_RxFIFOLevel | UART_ITSource_RecieveTimeout))  // We received some data
  {
    /*
     * Pending bits are cleared automatically by reading one
     * byte from FIFO and when FIFO is becoming empty.
     */

    while (!UART_FlagStatus(TTY_UART, UART_Flag_RxFIFOEmpty))   // Until receive FIFO is not empty
    {
      uint8_t Byte = TTY_UART->DR;  // Read data from the receive FIFO

      /*
       * Checking the UART errors.
       */
      if (!(TTY_UART->RSR_ECR & (UART_RSR_ECR_FE_Msk | UART_RSR_ECR_PE_Msk | UART_RSR_ECR_BE_Msk | UART_RSR_ECR_OE_Msk)))
      {
        IOBuffer_PutC(&RxBuffer, Byte);  // Put data into buffer
      }
    }

    if (xTimerReset(CleanRxBufferTimerHandle, 0) != pdPASS)
    {
      #ifdef DEBUG
      printf ("The timer was not started.\n");
      while (1); // Infinite loop
      #endif
    }

    /*
     * Process received data and check whether there was a response continuosly.
     * There may be two or more commands in one transmission. We must handle
     * it anyways.
     */
    while (FlowParser_Process(&RxBuffer, &TxBuffer))
    {
      DataTransmitting();  // While there is a response, put data from TxBuffer to Tx FIFO until Tx empty or FIFO full
    }
  }

  if (UART_ITMaskedStatus(TTY_UART, UART_ITSource_TxFIFOLevel))   // The transmit buffer is not filled
  {
    UART_ITStatusClear(TTY_UART, UART_ITSource_TxFIFOLevel);  // Clear interrupt source

    DataTransmitting();   // Put data from TxBuffer to Tx FIFO until Tx empty or FIFO full
  }
}

/*
 * This callback function is an input buffer cleaner.
 * Every new byte moves the callback away.
 * No new bytes results in input buffer cleaning.
 * It is required for devices left in non synchronized state.
 * There is no way to synchronize such device during.
 * device discovery unless its input buffer is clean.
 */

static void USBCleanRxBufferCallback(TimerHandle_t xTimer)
{
  IOBuffer_ReInit(&RxBuffer);
}

static inline void DataTransmitting(void)
{
  uint8_t Byte;

  /*
   * While Tx FIFO is not full and there is still data to be sent.
   */
  while (!UART_FlagStatus(TTY_UART, UART_Flag_TxFIFOFull) && IOBuffer_Size(&TxBuffer))
  {
    IOBuffer_GetC(&TxBuffer, &Byte);

    TTY_UART->DR = Byte;
  }
}
