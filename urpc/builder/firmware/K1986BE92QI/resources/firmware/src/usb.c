/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Main includes here.
 */
#include "MDR32F9Qx_config.h"
#include "usb.h"

/*
 * Other includes here.
 */
#include "MDR32F9Qx_interrupt.h"
#include "MDR32F9Qx_usb_handlers.h"
#include "MDR32F9Qx_rst_clk.h"
#include "callback.h"     // For buffer cleaning after timeout
#include "flowparser.h"   // Upper level interface
#include "iobuffer.h"

static io_buffer_t RxBuffer;
static io_buffer_t TxBuffer;

/*
 * This buffers hold incoming
 * and outcoming flows.
 */
static uint8_t USBRxBuffer[_PACKET_LENGTH];
static uint8_t USBTxBuffer[_PACKET_LENGTH];

#ifdef USB_VCOM_SYNC
static uint32_t PendingDataLength = 0;
#endif  // USB_VCOM_SYNC

#ifdef USB_CDC_LINE_CODING_SUPPORTED
static USB_CDC_LineCoding_TypeDef LineCoding =
{
  .dwDTERate = 115200,
  .bCharFormat = 0,
  .bParityType = 0,
  .bDataBits = 8
};
#endif  // USB_CDC_LINE_CODING_SUPPORTED

static void Setup_USB(void);
static void RxBufferCleaner(void);

INIT_STATE_VAR(USB);

/*
 * Initialize USB.
 */
void USB_Init(void)
{
  INIT_START(USB);

  IOBuffer_Init(&RxBuffer);
  IOBuffer_Init(&TxBuffer);

  Callback_Init();

  Callback_SetHandler(USB_CLEANING_INDEX, RxBufferCleaner);

  /*
   * CDC layer initialization.
   */
  USB_CDC_Init(USBRxBuffer, 1, SET);

  Setup_USB();

#ifdef USB_INT_HANDLE_REQUIRED
  IntRegister(USB_IRQn, USB_IRQHandler);  // Register interrupt on USB
  NVIC_EnableIRQ(USB_IRQn);   // Enable interrupt on USB
#endif  // USB_INT_HANDLE_REQUIRED

  USB_DEVICE_HANDLE_RESET;

  INIT_END(USB);
}

/*
 * USB Device layer setup and powering on.
 */
static void Setup_USB(void)
{
  RST_CLK_PCLKcmd(RST_CLK_PCLK_USB, ENABLE);  // Enables the CPU_CLK clock on USB

  USB_Clock_TypeDef USB_Clock_InitStruct;
  USB_DeviceBUSParam_TypeDef USB_DeviceBUSParam;

  USB_Clock_InitStruct.USB_USBC1_Source = USB_C1HSEdiv2;
  USB_Clock_InitStruct.USB_PLLUSBMUL = USB_PLLUSBMUL12;

  USB_DeviceBUSParam.MODE = USB_SC_SCFSP_Full;
  USB_DeviceBUSParam.SPEED = USB_SC_SCFSR_12Mb;
  USB_DeviceBUSParam.PULL = USB_HSCR_DP_PULLUP_Set;

  USB_DeviceInit(&USB_Clock_InitStruct, &USB_DeviceBUSParam);

  USB_SetSIM(USB_SIM_SET_MASK);   // Enable all USB interrupts

  USB_DevicePowerOn();
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

#ifdef USB_CDC_LINE_CODING_SUPPORTED
USB_Result USB_CDC_GetLineCoding(uint16_t wINDEX, USB_CDC_LineCoding_TypeDef *DATA)
{
  assert_param(DATA);

  if (wINDEX != 0)
  {
    return USB_ERR_INV_REQ;
  }

  *DATA = LineCoding;   // Just store received settings

  return USB_SUCCESS;
}

USB_Result USB_CDC_SetLineCoding(uint16_t wINDEX, const USB_CDC_LineCoding_TypeDef *DATA)
{
  assert_param(DATA);

  if (wINDEX != 0)
  {
    return USB_ERR_INV_REQ;
  }

  LineCoding = *DATA;   // Just send back settings stored earlier

  return USB_SUCCESS;
}
#endif  // USB_CDC_LINE_CODING_SUPPORTED

USB_Result USB_CDC_RecieveData(uint8_t *Buffer, uint32_t Length)
{
  USB_Result result = USB_SUCCESS;

  IOBuffer_PutBuf(&RxBuffer, Buffer, Length);

  Callback_SetDelay(USB_CLEANING_INDEX, _PROTOCOL_DELAY);

  if (FlowParser_Process(&RxBuffer, &TxBuffer))
  {
    Length = IOBuffer_Size(&TxBuffer);
    IOBuffer_GetBuf(&TxBuffer, USBTxBuffer, Length);

    result = USB_CDC_SendData(USBTxBuffer, Length);
  }

#ifdef USB_VCOM_SYNC
  if (result != USB_SUCCESS)
  {
    /*
     * If data cannot be sent now,
     * it will await nearest possibility.
     * See USB_CDC_DataSent()
     */
    PendingDataLength = Length;
  }

  return result;
#else
  return USB_SUCCESS;
#endif  // USB_VCOM_SYNC
}

#ifdef USB_VCOM_SYNC
USB_Result USB_CDC_DataSent(void)
{
  USB_Result result;

  if (PendingDataLength)
  {
    result = USB_CDC_SendData(USBTxBuffer, PendingDataLength);

    PendingDataLength = 0;

    USB_CDC_ReceiveStart();
  }

  assert_param(result == USB_SUCCESS);

  return result;
}
#endif  // USB_VCOM_SYNC
