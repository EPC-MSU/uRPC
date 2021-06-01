/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Main includes here.
 */
#include "MDR32F9Qx_config.h"
#include "tty.h"

/*
 * Other includes here.
 */
#include "MDR32F9Qx_port.h"
#include "MDR32F9Qx_interrupt.h"
#include "MDR32F9Qx_rst_clk.h"
#include "callback.h"
#include "flowparser.h"
#include "iobuffer.h"

#define TTY_PORT        MDR_PORTD
#define TTY_PORT_CLK    RST_CLK_PCLK_PORTD
#define TTY_RX_PIN      PORT_Pin_0
#define TTY_RX_ALTFUNC  PORT_FUNC_ALTER
#define TTY_TX_PIN      PORT_Pin_1
#define TTY_TX_ALTFUNC  PORT_FUNC_ALTER

#define TTY_UART      MDR_UART2
#define TTY_UART_CLK  RST_CLK_PCLK_UART2
#define TTY_UART_IRQ  UART2_IRQn

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

  RST_CLK_PCLKcmd(TTY_PORT_CLK, ENABLE);
  RST_CLK_PCLKcmd(TTY_UART_CLK, ENABLE);

  PORT_InitTypeDef PORT_InitStructure;

  /*
   * The initial data for Rx.
   */
  PORT_InitStructure.PORT_Pin   = TTY_RX_PIN;
  PORT_InitStructure.PORT_OE    = PORT_OE_IN;
  PORT_InitStructure.PORT_PULL_UP     = PORT_PULL_UP_OFF;
  PORT_InitStructure.PORT_PULL_DOWN   = PORT_PULL_DOWN_OFF;
  PORT_InitStructure.PORT_PD_SHM      = PORT_PD_SHM_OFF;
  PORT_InitStructure.PORT_PD      = PORT_PD_DRIVER;
  PORT_InitStructure.PORT_GFEN    = PORT_GFEN_OFF;
  PORT_InitStructure.PORT_FUNC    = TTY_RX_ALTFUNC;
  PORT_InitStructure.PORT_SPEED   = PORT_SPEED_MAXFAST;
  PORT_InitStructure.PORT_MODE    = PORT_MODE_DIGITAL;

  PORT_Init(TTY_PORT, &PORT_InitStructure);

  /*
   * The initial data for Tx.
   */
  PORT_InitStructure.PORT_Pin   = TTY_TX_PIN;
  PORT_InitStructure.PORT_OE    = PORT_OE_OUT;
  PORT_InitStructure.PORT_FUNC  = TTY_TX_ALTFUNC;

  PORT_Init(TTY_PORT, &PORT_InitStructure);

  /*
   * Set the HCLK division factor = 1.
   */
  UART_BRGInit(TTY_UART, UART_HCLKdiv16);

  UART_ITConfig(TTY_UART, UART_IT_RX | UART_IT_TX | UART_IT_RT, ENABLE);
  IntRegister(TTY_UART_IRQ, TTY_IntHandler);
  NVIC_EnableIRQ(TTY_UART_IRQ);

  /*
   * Use default settings for first init.
   */
  TTY_SettingsChange(UART_StopBits1, UART_Parity_No, 115200);
}

void TTY_SettingsChange(uint16_t StopBit, uint16_t ParityBit, uint32_t BaudRate)
{
  assert_param(Engaged);

  UART_Cmd(TTY_UART, DISABLE);

  UART_InitTypeDef UART_InitStructure;

  /*
   * The initial data for UART.
   */
  UART_InitStructure.UART_BaudRate    = BaudRate;
  UART_InitStructure.UART_WordLength  = UART_WordLength8b;
  UART_InitStructure.UART_StopBits    = StopBit;
  UART_InitStructure.UART_Parity      = ParityBit;
  UART_InitStructure.UART_FIFOMode    = UART_FIFO_ON;
  UART_InitStructure.UART_HardwareFlowControl   = UART_HardwareFlowControl_RXE | UART_HardwareFlowControl_TXE;

  UART_Init(TTY_UART, &UART_InitStructure);

  UART_DMAConfig(TTY_UART, UART_IT_FIFO_LVL_12words, UART_IT_FIFO_LVL_4words);

  UART_Cmd(TTY_UART, ENABLE);
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
      if (!(TTY_UART->RSR_ECR & (UART_RSR_ECR_FE | UART_RSR_ECR_PE | UART_RSR_ECR_BE | UART_RSR_ECR_OE)))
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
