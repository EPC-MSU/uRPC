/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Main includes here.
 */
#include "stm32f1xx.h"
#include "tty.h"

/*
 * Other includes here.
 */
#include <stdio.h>
#include "stm32f1xx_ll_bus.h"
#include "stm32f1xx_ll_dma.h"
#include "stm32f1xx_ll_gpio.h"
#include "stm32f1xx_ll_irq.h"
#include "flowparser.h"
#include "iobuffer.h"
   
// FreeRTOS files
#include "FreeRTOS.h"
#include "timers.h"

#define TTY_PORT      GPIOA
#define TTY_PORT_CLK  LL_APB2_GRP1_PERIPH_GPIOA
#define TTY_RX_PIN    LL_GPIO_PIN_10
#define TTY_RX_MODE   LL_GPIO_MODE_FLOATING
#define TTY_TX_PIN    LL_GPIO_PIN_9
#define TTY_TX_MODE   LL_GPIO_MODE_ALTERNATE

#define TTY_UART      USART1
#define TTY_UART_CLK  LL_APB2_GRP1_PERIPH_USART1
#define TTY_UART_IRQ  USART1_IRQn

#define TTY_DMA       DMA1
#define TTY_DMA_CLK   LL_AHB1_GRP1_PERIPH_DMA1
#define TTY_RX_CHAN   LL_DMA_CHANNEL_5
#define TTY_RX_IRQ    DMA1_Channel5_IRQn
#define TTY_TX_CHAN   LL_DMA_CHANNEL_4
#define TTY_TX_IRQ    DMA1_Channel4_IRQn

TimerHandle_t CleanRxBufferTimerHandle;
TimerHandle_t TimeoutTimerHandle;
   
static io_buffer_t RxBuffer;
static io_buffer_t TxBuffer;

static bool TimeoutOrInterrupt;

static void TTY_UARTHandler(void);
static void TTY_DMAHandler(void);

static void RxBufferCleaner(TimerHandle_t TimeoutTimerHandle);
static void Timeout(TimerHandle_t TimeoutTimerHandle);
static void DataTransmitting(void);
static inline void SettingsChange(uint32_t StopBit, uint32_t ParityBit, uint32_t BaudRate);

INIT_STATE_VAR(TTY);

void TTY_Init(void)
{
  INIT_START(TTY);

  // Initialize and start timer for Rx buffer cleaning
  CleanRxBufferTimerHandle = xTimerCreate("Clean Rx buffer timer",
                                        pdMS_TO_TICKS(_PROTOCOL_DELAY),
                                        pdFALSE,
                                        ( void * ) 0,
                                        RxBufferCleaner);
  
  if (CleanRxBufferTimerHandle == NULL) 
  {
  #ifdef DEBUG
    printf ("The timer was not created.\n");
    while(1); // Infinite loop
  #endif
  }  
    if (xTimerStart(CleanRxBufferTimerHandle, 0) != pdPASS)
  {
  #ifdef DEBUG
    printf ("The timer was not started.\n");
    while(1); // Infinite loop
  #endif
  }
  TimeoutTimerHandle = xTimerCreate("Timeout timer",
                                        1,
                                        pdFALSE,
                                        ( void * ) 0,
                                        Timeout);
  
  if (CleanRxBufferTimerHandle == NULL) 
  {
  #ifdef DEBUG
    printf ("The timer was not created.\n");
    while(1); // Infinite loop
  #endif
  }
  
    if (xTimerStart(CleanRxBufferTimerHandle, 0) != pdPASS)
  {
  #ifdef DEBUG
    printf ("The timer was not started.\n");
    while(1); // Infinite loop
  #endif
  }
  
  LL_APB2_GRP1_EnableClock(TTY_PORT_CLK);
  LL_APB2_GRP1_EnableClock(TTY_UART_CLK);
  LL_AHB1_GRP1_EnableClock(TTY_DMA_CLK);

  LL_GPIO_InitTypeDef GPIO_InitStructure;

  /*
   * The initial data for Rx.
   */
  GPIO_InitStructure.Pin        = TTY_RX_PIN;
  GPIO_InitStructure.Mode       = TTY_RX_MODE;
  GPIO_InitStructure.Speed      = LL_GPIO_SPEED_FREQ_HIGH;
  GPIO_InitStructure.OutputType = LL_GPIO_OUTPUT_PUSHPULL;
  GPIO_InitStructure.Pull       = LL_GPIO_PULL_UP;

  LL_GPIO_Init(TTY_PORT, &GPIO_InitStructure);

  /*
   * The initial data for Tx.
   */
  GPIO_InitStructure.Pin  = TTY_TX_PIN;
  GPIO_InitStructure.Mode = TTY_TX_MODE;

  LL_GPIO_Init(TTY_PORT, &GPIO_InitStructure);

  /*
   * Use default settings for first init.
   */
  SettingsChange(LL_USART_STOPBITS_1, LL_USART_PARITY_NONE, 115200);

  LL_DMA_InitTypeDef DMA_InitStructure;

  /*
   * Configure the DMA functional parameters for reception.
   */
  DMA_InitStructure.PeriphOrM2MSrcAddress   = LL_USART_DMA_GetRegAddr(TTY_UART);
  DMA_InitStructure.MemoryOrM2MDstAddress   = (uint32_t)RxBuffer.data;
  DMA_InitStructure.Direction               = LL_DMA_DIRECTION_PERIPH_TO_MEMORY;
  DMA_InitStructure.Mode                    = LL_DMA_MODE_CIRCULAR;
  DMA_InitStructure.PeriphOrM2MSrcIncMode   = LL_DMA_PERIPH_NOINCREMENT;
  DMA_InitStructure.MemoryOrM2MDstIncMode   = LL_DMA_MEMORY_INCREMENT;
  DMA_InitStructure.PeriphOrM2MSrcDataSize  = LL_DMA_PDATAALIGN_BYTE;
  DMA_InitStructure.MemoryOrM2MDstDataSize  = LL_DMA_MDATAALIGN_BYTE;
  DMA_InitStructure.NbData                  = IOBUFMSK;
  DMA_InitStructure.Priority                = LL_DMA_PRIORITY_LOW;

  LL_DMA_Init(TTY_DMA, TTY_RX_CHAN, &DMA_InitStructure);

  LL_DMA_EnableChannel(TTY_DMA, TTY_RX_CHAN);

  /*
   * Configure the DMA functional parameters for transmission.
   */
  DMA_InitStructure.PeriphOrM2MSrcAddress = LL_USART_DMA_GetRegAddr(TTY_UART);
  DMA_InitStructure.MemoryOrM2MDstAddress = (uint32_t)TxBuffer.data;
  DMA_InitStructure.Direction             = LL_DMA_DIRECTION_MEMORY_TO_PERIPH;
  DMA_InitStructure.Mode                  = LL_DMA_MODE_NORMAL;
  DMA_InitStructure.NbData                = 0;

  LL_DMA_Init(TTY_DMA, TTY_TX_CHAN, &DMA_InitStructure);

  /*
   * Enable DMA interrupts.
   */
  LL_DMA_EnableIT_TC(TTY_DMA, TTY_TX_CHAN);
  LL_DMA_EnableIT_TC(TTY_DMA, TTY_RX_CHAN);
  LL_DMA_EnableIT_HT(TTY_DMA, TTY_RX_CHAN);

  LL_IRQ_Init(TTY_TX_IRQ, TTY_DMAHandler);
  LL_IRQ_Init(TTY_RX_IRQ, TTY_DMAHandler);

  /*
   * Interrupts in core.
   */
  NVIC_ClearPendingIRQ(TTY_TX_IRQ);
  NVIC_ClearPendingIRQ(TTY_RX_IRQ);
  NVIC_EnableIRQ(TTY_TX_IRQ);
  NVIC_EnableIRQ(TTY_RX_IRQ);

  /*
   * Enable DMA requests.
   */
  LL_USART_EnableDMAReq_TX(TTY_UART);
  LL_USART_EnableDMAReq_RX(TTY_UART);

  /*
   * Interrupts in USART.
   */
  LL_USART_EnableIT_RXNE(TTY_UART);

  LL_IRQ_Init(TTY_UART_IRQ, TTY_UARTHandler);

  /*
   * Interrupts in core.
   */
  NVIC_ClearPendingIRQ(TTY_UART_IRQ);
  NVIC_EnableIRQ(TTY_UART_IRQ);

  INIT_END(TTY);
}

void TTY_SettingsChange(uint32_t StopBit, uint32_t ParityBit, uint32_t BaudRate)
{
  FUNC_START(TTY);

  SettingsChange(StopBit, ParityBit, BaudRate);
}

static void TTY_UARTHandler(void)
{
  /*
   * Clearing interrupt source will be do by DMA.
   */
  
  if (xTimerResetFromISR(TimeoutTimerHandle, 0) != pdPASS)
    {
    #ifdef DEBUG
      printf ("The timer was not started.\n");
      while(1); // Infinite loop
    #endif
    }
  
}

static void TTY_DMAHandler(void)
{
  if (LL_DMA_IsActiveFlag_TC5(TTY_DMA) && LL_DMA_IsEnabledIT_TC(TTY_DMA, TTY_RX_CHAN))
  {
    LL_DMA_ClearFlag_TC5(TTY_DMA);  // Clear interrupt source

    TimeoutOrInterrupt = true;
  }

  if (LL_DMA_IsActiveFlag_HT5(TTY_DMA) && LL_DMA_IsEnabledIT_HT(TTY_DMA, TTY_RX_CHAN))
  {
    LL_DMA_ClearFlag_HT5(TTY_DMA);  // Clear interrupt source

    TimeoutOrInterrupt = true;
  }

  if (TimeoutOrInterrupt)
  {
    TimeoutOrInterrupt = false;   // Clear source

    uint16_t  PutPtr  = IOBUFMSK - LL_DMA_GetDataLength(TTY_DMA, TTY_RX_CHAN);
    int32_t   Delta   = (int32_t)PutPtr - RxBuffer.pp;

    RxBuffer.length += (Delta < 0) ? IOBUFMSK + Delta : Delta;
    RxBuffer.pp = PutPtr;

    if (xTimerReset(CleanRxBufferTimerHandle, 0) != pdPASS)
    {
    #ifdef DEBUG
      printf ("The timer was not started.\n");
      while(1); // Infinite loop
    #endif
    }
    /*
     * Process received data and check whether there was a response continuosly.
     * There may be two or more commands in one transmission. We must handle
     * it anyways.
     */
    while (FlowParser_Process(&RxBuffer, &TxBuffer))
      DataTransmitting();   // While there is a response, put data from TxBuffer to Tx FIFO until Tx empty or FIFO full
  }

  if (LL_DMA_IsActiveFlag_TC4(TTY_DMA) && LL_DMA_IsEnabledIT_TC(TTY_DMA, TTY_TX_CHAN))
  {
    LL_DMA_ClearFlag_TC4(TTY_DMA);  // Clear interrupt source

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
static void RxBufferCleaner(TimerHandle_t CleanRxBufferTimerHandle)
{
  IOBuffer_ReInit(&RxBuffer);
}

static void Timeout(TimerHandle_t TimeoutTimerHandle)
{
  TimeoutOrInterrupt = true;

  NVIC_SetPendingIRQ(TTY_RX_IRQ);
}

static void DataTransmitting(void)
{
  LL_DMA_DisableChannel(TTY_DMA, TTY_TX_CHAN);

  int32_t   Num     = LL_DMA_GetDataLength(TTY_DMA, TTY_TX_CHAN);
  uint16_t  Length  = TxBuffer.length;
  uint16_t  GetPtr  = TxBuffer.gp;

  Length += Num;
  GetPtr -= ((Num > GetPtr) ? Num - IOBUFMSK : Num);

  LL_DMA_SetMemoryAddress(TTY_DMA, TTY_TX_CHAN, (uint32_t)TxBuffer.data + GetPtr);

  uint16_t BeforeEnd = IOBUFMSK - GetPtr;

  if (Length < BeforeEnd)
  {
    LL_DMA_SetDataLength(TTY_DMA, TTY_TX_CHAN, Length);

    TxBuffer.length = 0;
    TxBuffer.gp     = GetPtr + Length;
  }
  else
  {
    LL_DMA_SetDataLength(TTY_DMA, TTY_TX_CHAN, BeforeEnd);

    TxBuffer.length = Length - BeforeEnd;
    TxBuffer.gp     = 0;
  }

  LL_DMA_EnableChannel(TTY_DMA, TTY_TX_CHAN);
}

static inline void SettingsChange(uint32_t StopBit, uint32_t ParityBit, uint32_t BaudRate)
{
  LL_USART_Disable(TTY_UART);

  LL_USART_InitTypeDef USART_InitStructure;

  /*
   * The initial data for UART.
   */
  USART_InitStructure.BaudRate  = BaudRate;
  USART_InitStructure.DataWidth = LL_USART_DATAWIDTH_8B;
  USART_InitStructure.StopBits  = StopBit;
  USART_InitStructure.Parity    = ParityBit;
  USART_InitStructure.TransferDirection   = LL_USART_DIRECTION_TX_RX;
  USART_InitStructure.HardwareFlowControl = LL_USART_HWCONTROL_NONE;

  LL_USART_Init(TTY_UART, &USART_InitStructure);

  LL_USART_Enable(TTY_UART);
}
