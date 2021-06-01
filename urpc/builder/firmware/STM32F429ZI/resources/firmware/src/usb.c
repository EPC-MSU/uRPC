/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Main includes here.
 */
#include "stm32f4xx.h"
#include "usb.h"

/*
 * Other includes here.
 */
#include "stm32f4xx_ll_bus.h"
#include "stm32f4xx_ll_gpio.h"
#include "stm32f4xx_ll_irq.h"
#include "usbd_core.h"
#include "usbd_desc.h"
#include "usbd_cdc.h"
#include "usbd_cdc_if.h"
#include "flowparser.h"   // Upper level interface
#include "iobuffer.h"
#include "usb_device.h"

// FreeRTOS files
#include "FreeRTOS.h"
#include "timers.h"

TimerHandle_t CleanRxBufferTimerHandle;
/*
 * USB Device Core handle declaration.
 */

static io_buffer_t RxBuffer;
static io_buffer_t TxBuffer;

/*
 * This buffers hold incoming
 * and outcoming flows.
 */
static uint8_t USBRxBuffer[_PACKET_LENGTH];
static uint8_t USBTxBuffer[_PACKET_LENGTH];

static void RxBufferCleaner(TimerHandle_t xTimer);
static void DataTransmitting(void);

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
                                          RxBufferCleaner);

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

  /*
   * Init Device Library, add supported class and start the library.
   */


  USBD_Init(&hUsbDeviceHS, &HS_Desc, DEVICE_HS);

  USBD_RegisterClass(&hUsbDeviceHS, &USBD_CDC);

  USBD_CDC_RegisterInterface(&hUsbDeviceHS, &USBD_Interface_fops_HS);

  USBD_Start(&hUsbDeviceHS);

  INIT_END(USB);
}

int8_t CDC_Init_HS(void)
{
  /*
   * Set application buffers.
   */
  USBD_CDC_SetTxBuffer(&hUsbDeviceHS, USBTxBuffer, _PACKET_LENGTH);
  USBD_CDC_SetRxBuffer(&hUsbDeviceHS, USBRxBuffer);

  return USBD_OK;
}

int8_t CDC_Receive_HS(uint8_t *Buf, uint32_t *Len)
{
  IOBuffer_PutBuf(&RxBuffer, Buf, *Len);  // First put data into buffer

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
    DataTransmitting();   // While there is a response, put data from TxBuffer to Tx FIFO until Tx empty or FIFO full
  }

  USBD_CDC_ReceivePacket(&hUsbDeviceHS);

  return USBD_OK;
}

/*
 * This callback function is an input buffer cleaner.
 * Every new byte moves the callback away.
 * No new bytes results in input buffer cleaning.
 * It is required for devices left in non synchronized state.
 * There is no way to synchronize such device during.
 * device discovery unless its input buffer is clean.
 */
static void RxBufferCleaner(TimerHandle_t xTimer)
{
  IOBuffer_ReInit(&RxBuffer);
}

static void DataTransmitting(void)
{
  uint16_t Size = IOBuffer_Size(&TxBuffer);

  IOBuffer_GetBuf(&TxBuffer, USBTxBuffer, Size);

  CDC_Transmit_HS(USBTxBuffer, Size);
}
