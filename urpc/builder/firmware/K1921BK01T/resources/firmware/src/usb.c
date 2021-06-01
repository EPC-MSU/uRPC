/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Main includes here.
 */
#include "usb.h"

/*
 * Other includes here.
 */
#include "niietcm4_irq.h"
#include "niietcm4_rcc.h"
#include "usb_dev.h"
#include "usb_otg_irq.h"
#include "usb_cdc_vcp.h"
#include "flowparser.h"   // Upper level interface
#include "iobuffer.h"

// FreeRTOS files
#include "FreeRTOS.h"
#include "timers.h"

#include <stdio.h>  // For printf(...)

TimerHandle_t CleanRxBufferTimerHandle;
static void USBCleanRxBufferCallback(TimerHandle_t xTimer);

static io_buffer_t RxBuffer;
static io_buffer_t TxBuffer;

//static void RxBufferCleaner(void);
static inline void DataTransmitting(void);

INIT_STATE_VAR(USB);

/*
 * Initialize USB.
 */
void USB_Init(void)
{
  INIT_START(USB);
  
   // Initialize and start timer for Rx buffer cleaning
  CleanRxBufferTimerHandle = xTimerCreate("Clean Rx buffer timer",
                                        pdMS_TO_TICKS(_PROTOCOL_DELAY),
                                        pdFALSE,
                                        ( void * ) 0,
                                        USBCleanRxBufferCallback);

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
  
  IOBuffer_Init(&RxBuffer);
  IOBuffer_Init(&TxBuffer);
  USBDev_SetManufacturer("MANUFACTURER");  // Place manufacturer here
  USBDev_SetProduct("PRODUCT");  // Place product name here
  USBDev_SetSerial(0x12345678);  // Place serial number here

  /*
   * Disable the reset state and enable clock.
   */
  RCC_PeriphRstCmd(RCC_PeriphRst_USB, ENABLE);
  RCC_USBClkConfig(RCC_USBClk_XI_OSC, RCC_USBFreq_12MHz, ENABLE);

  NT_USBOTG->OTG_IRQ_EN = 0x03FF;   // All Interupts are activeted
  IRQ_HandlerInit(USBOTG_IRQn, usbotg_irq_handler);
  NVIC_EnableIRQ(USBOTG_IRQn);

  INIT_END(USB);
}

uint32_t VCP_CDC_DataTransmitted(void)
{
  DataTransmitting();   // Put data from TxBuffer to Tx USB buffer until Tx empty or FIFO full

  return 0;
}

uint32_t VCP_CDC_DataReceived(void)
{
  while (!VCP_IsRxBufEmpty())   // Until receive USB buffer is not empty
  {
    uint8_t Byte = VCP_GetChar();   // Read data from the receive USB buffer

    IOBuffer_PutC(&RxBuffer, Byte);   // Put data into buffer
  }
  
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
  {
    DataTransmitting();   // While there is a response, put data from TxBuffer to Tx FIFO until Tx empty or FIFO full
  }

  return 0;
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
   * While Tx USB buffer is not full and there is still data to be sent.
   */
  while (!VCP_IsTxBufFull() && IOBuffer_Size(&TxBuffer))
  {
    IOBuffer_GetC(&TxBuffer, &Byte);

    VCP_PutChar(Byte);
  }
}
