/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Main includes here.
 */
#include "stm32f10x_conf.h"
#include "tty.h"

/*
 * Other includes here.
 */
#include "stm32f10x_gpio.h"
#include "stm32f10x_irq.h"
#include "stm32f10x_rcc.h"
#include "callback.h"
#include "flowparser.h"
#include "iobuffer.h"

#define TTY_PORT      GPIOA
#define TTY_PORT_CLK  RCC_APB2Periph_GPIOA
#define TTY_RX_PIN    GPIO_Pin_10
#define TTY_RX_MODE   GPIO_Mode_IN_FLOATING
#define TTY_TX_PIN    GPIO_Pin_9
#define TTY_TX_MODE   GPIO_Mode_AF_PP

#define TTY_UART      USART1
#define TTY_UART_CLK  RCC_APB2Periph_USART1
#define TTY_UART_IRQ  USART1_IRQn

static io_buffer_t RxBuffer;
static io_buffer_t TxBuffer;

static void TTY_IntHandler(void);
static void RxBufferCleaner(void);
static inline void DataTransmitting(void);

static bool Engaged = false;

void TTY_Init(void)
{
  /*
   * Protection against double initialization.
   */
  if (Engaged)
    return;

  Engaged = true;

  IOBuffer_Init(&RxBuffer);
  IOBuffer_Init(&TxBuffer);

  Callback_Init();

  Callback_SetHandler(UART_CLEANING_INDEX, RxBufferCleaner);

  RCC_APB2PeriphClockCmd(TTY_PORT_CLK, ENABLE);
  RCC_APB2PeriphClockCmd(RCC_APB2Periph_AFIO, ENABLE);
  RCC_APB2PeriphClockCmd(TTY_UART_CLK, ENABLE);

  GPIO_InitTypeDef GPIO_InitStructure;

  /*
   * The initial data for Rx.
   */
  GPIO_InitStructure.GPIO_Pin     = TTY_RX_PIN;
  GPIO_InitStructure.GPIO_Speed   = GPIO_Speed_50MHz;
  GPIO_InitStructure.GPIO_Mode    = TTY_RX_MODE;

  GPIO_Init(TTY_PORT, &GPIO_InitStructure);

  /*
   * The initial data for Tx.
   */
  GPIO_InitStructure.GPIO_Pin   = TTY_TX_PIN;
  GPIO_InitStructure.GPIO_Mode  = TTY_TX_MODE;

  GPIO_Init(TTY_PORT, &GPIO_InitStructure);

  /*
   * Set the HCLK division factor = 1.
   */
  UART_BRGInit(TTY_UART, UART_HCLKdiv16);

  USART_ITConfig(TTY_UART, UART_IT_RX | UART_IT_TX | UART_IT_RT, ENABLE);
  IRQ_HandlerInit(TTY_UART_IRQ, TTY_IntHandler);
  NVIC_EnableIRQ(TTY_UART_IRQ);

  /*
   * Use default settings for first init.
   */
  TTY_SettingsChange(USART_StopBits_1, USART_Parity_No, 115200);
}

void TTY_SettingsChange(uint16_t StopBit, uint16_t ParityBit, uint32_t BaudRate)
{
  assert_param(Engaged);

  USART_Cmd(TTY_UART, DISABLE);

  USART_InitTypeDef USART_InitStructure;

  /*
   * The initial data for UART.
   */
  USART_InitStructure.USART_BaudRate    = BaudRate;
  USART_InitStructure.USART_WordLength  = USART_WordLength_8b;
  USART_InitStructure.USART_StopBits    = StopBit;
  USART_InitStructure.USART_Parity      = ParityBit;
  USART_InitStructure.USART_Mode        = USART_Mode_Rx | USART_Mode_Tx;
  USART_InitStructure.USART_HardwareFlowControl   = USART_HardwareFlowControl_None;

  USART_Init(TTY_UART, &USART_InitStructure);

  UART_DMAConfig(TTY_UART, UART_IT_FIFO_LVL_12words, UART_IT_FIFO_LVL_4words);

  USART_Cmd(TTY_UART, ENABLE);
}

static void TTY_IntHandler(void)
{
  if (UART_GetITStatusMasked(TTY_UART, UART_IT_RX | UART_IT_RT))  // We received some data
  {
    /*
     * Pending bits are cleared automatically by reading one
     * byte from FIFO and when FIFO is becoming empty.
     */

    while (!UART_GetFlagStatus(TTY_UART, UART_FLAG_RXFE))   // Until receive FIFO is not empty
    {
      uint8_t Byte = TTY_UART->DR;  // Read data from the receive FIFO

      /*
       * Checking the UART errors.
       */
      if (!(TTY_UART->SR & (USART_SR_FE | USART_SR_PE | USART_SR_LBD | USART_SR_ORE)))
        IOBuffer_PutC(&RxBuffer, Byte);   // Put data into buffer
    }

    Callback_SetDelay(UART_CLEANING_INDEX, _PROTOCOL_DELAY);  // Set callback for buffer cleaning

    /*
     * Process received data and check whether there was a response continuosly.
     * There may be two or more commands in one transmission. We must handle
     * it anyways.
     */
    while (FlowParser_Process(&RxBuffer, &TxBuffer))
      DataTransmitting();   // While there is a response, put data from TxBuffer to Tx FIFO until Tx empty or FIFO full
  }

  if (UART_GetITStatusMasked(TTY_UART, UART_IT_TX))   // The transmit buffer is not filled
  {
    UART_ClearITPendingBit(TTY_UART, UART_IT_TX);   // Clear interrupt source

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
static void RxBufferCleaner(void)
{
  IOBuffer_ReInit(&RxBuffer);
}

static inline void DataTransmitting(void)
{
  uint8_t Byte;

  /*
   * While Tx FIFO is not full and there is still data to be sent.
   */
  while (!UART_GetFlagStatus(TTY_UART, UART_FLAG_TXFF) && IOBuffer_Size(&TxBuffer))
  {
    IOBuffer_GetC(&TxBuffer, &Byte);

    TTY_UART->DR = Byte;
  }
}
