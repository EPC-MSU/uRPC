/*
USB control block. See Firmware.graphml
Interface:
SetUsbSerial(uint32_t) - set USB serial
USB_InitAndCheck() - Initialization of USB control block
SendToUsb() - Indicates to USB control that there is new data in Tx buffer
I2C rudiments;
*/
// Each file must start with this include. Containes global settings
#include "settings.h"

/*
 * Main includes here.
 */
#include "usb_composite.h"

#include "inc/hw_types.h"
#include "usblib/usblib.h"
#include "usblib/usbcdc.h"
#include "usblib/usb-ids.h"
#include "usblib/device/usbdevice.h"
#include "usblib/device/usbdcomp.h"
#include "usblib/device/usbdcdc.h"

#include "inc/hw_memmap.h"
#include "inc/hw_usb.h"
#include "inc/hw_ints.h"

#include "driverlib/usb.h"
#include "driverlib/sysctl.h"
#include "driverlib/interrupt.h"
#include "driverlib/gpio.h"

#include "flowparser.h"   // Upper level interface
#include "algorithm.h"

#include "stdio.h"

// FreeRTOS files
#include "FreeRTOS.h"
#include "timers.h"


#define DESCRIPTOR_DATA_SIZE    (COMPOSITE_DCDC_SIZE * I2C_DEVICES_LIMIT)

static unsigned char g_pucDescriptorData[DESCRIPTOR_DATA_SIZE];
static io_buffer_t RxBuf, TxBuf;

static uint8_t USBbreakReconnectEnable;
TimerHandle_t CleanRxBufferTimerHandle;

static inline void SendToUSB(void);
static void USBStart(uint8_t NumDevices);
static void USBIntHandler(void);
static void USBGetData(uint8_t COMID);
static void USBCleanRxBufferCallback(TimerHandle_t xTimer);

/*
 * CDC device callback function prototypes.
 */
static unsigned long ControlHandler(void *pvCBData, unsigned long ulEvent, unsigned long ulMsgValue, void *pvMsgData);
static unsigned long TxHandler(void *pvCBData, unsigned long ulEvent, unsigned long ulMsgValue, void *pvMsgData);
static unsigned long RxHandler(void *pvCBData, unsigned long ulEvent, unsigned long ulMsgValue, void *pvMsgData);

static const unsigned char g_pLangDescriptor[] =
{
  4,
  USB_DTYPE_STRING,
  USBShort(USB_LANG_EN_US)
};

static unsigned char g_pManufacturerString[] =
{
  2 + (16 * 2),
  USB_DTYPE_STRING,
  ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0,
  ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0
};

static unsigned char g_pProductString[] =
{
  2 + (40 * 2),
  USB_DTYPE_STRING,
  ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0,
  ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0,
  ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0,
  ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0,
  ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0, ' ', 0
};

static unsigned char g_pSerialNumberString[] =
{
  2 + (8 * 2),
  USB_DTYPE_STRING,
  '1', 0, '2', 0, '3', 0, '4', 0, '5', 0, '6', 0, '7', 0, '8', 0  // Place serial number here
};

static const unsigned char *const g_pStringDescriptors[] =
{
  g_pLangDescriptor,
  g_pManufacturerString,
  g_pProductString,
  g_pSerialNumberString
};

static unsigned char HexTable[16] =
{
  '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F'
};

void SetUsbSerial(uint32_t SN)
{
  for (uint32_t i = 2; i <= 16; i += 2)
    g_pSerialNumberString[i] =
      HexTable[(SN & (0xF << (32 - i * 2))) >> (32 - i * 2)];
}

void SetUsbManufacturer(char *MFC)
{
  for (uint32_t i = 0; i <= strlen(MFC); i += 1)
  {
    g_pManufacturerString[i * 2 + 2] = MFC[i];
  }
}

void SetUsbProduct(char *PRT)
{
  for (uint32_t i = 0; i <= strlen(PRT); i += 1)
  {
    g_pProductString[i * 2 + 2] = PRT[i];
  }
}

#define NUM_STRING_DESCRIPTORS (sizeof(g_pStringDescriptors) / sizeof(uint8_t *))

//*****************************************************************************
//
// The CDC device initialization and customization structures. In this case,
// we are using USBBuffers between the CDC device class driver and the
// application code. The function pointers and callback data values are set
// to insert a buffer in each of the data channels, transmit and receive.
//
// With the buffer in place, the CDC channel callback is set to the relevant
// channel function and the callback data is set to point to the channel
// instance data. The buffer, in turn, has its callback set to the application
// function and the callback data set to our CDC instance structure.
//
//*****************************************************************************
static tCDCSerInstance g_psCDCInstance[I2C_DEVICES_LIMIT];
static tUSBDCDCDevice g_psCDCDevice[I2C_DEVICES_LIMIT];
//*****************************************************************************
//
// Receive buffer (from the USB perspective).
//
//*****************************************************************************
static unsigned char g_pcUSBRxBuffer[_PACKET_LENGTH * I2C_DEVICES_LIMIT];
static unsigned char g_pucRxBufferWorkspace[USB_BUFFER_WORKSPACE_SIZE * I2C_DEVICES_LIMIT];
static tUSBBuffer g_psRxBuffer[I2C_DEVICES_LIMIT];

//*****************************************************************************
//
// Transmit buffer (from the USB perspective).
//
//*****************************************************************************
static unsigned char g_pcUSBTxBuffer[_PACKET_LENGTH * I2C_DEVICES_LIMIT];
static unsigned char g_pucTxBufferWorkspace[USB_BUFFER_WORKSPACE_SIZE * I2C_DEVICES_LIMIT];
static tUSBBuffer g_psTxBuffer[I2C_DEVICES_LIMIT];

//*****************************************************************************
//
// The array of devices supported by this composite device.
//
//*****************************************************************************
static tCompositeEntry g_psCompDevices[I2C_DEVICES_LIMIT];

//*****************************************************************************
//
// Allocate the Device Data for the top level composite device class.
//
//*****************************************************************************
static tCompositeInstance g_CompInstance;
static unsigned long g_pulCompWorkspace[I2C_DEVICES_LIMIT];

tUSBDCompositeDevice g_sCompDevice =
{
  USB_VID,
  USB_PID,
  250,		        // This is in 2mA increments so 500mA.
  USB_CONF_ATTR_BUS_PWR,	// Bus powered device.
  0,			        // There is no need for a default composite event handler.
  g_pStringDescriptors,	// The string table.
  NUM_STRING_DESCRIPTORS,
  I2C_DEVICES_LIMIT,
  g_psCompDevices,
  g_pulCompWorkspace,		// Workspace required by the composite device.
  &g_CompInstance
};

//This function checking the USB bus state by USBInterruptRecieved bit
//and reset USB module then no any interrupt recieved(Bus fail)
#define USB_FAIL_START_WAITING_TIME 500  //Time for first waiting before interrupt bit check(in ms) 
#define USB_FAIL_MAX_WAITING_TIME   60000//Maximum WaitingTime (in ms)
#define USB_FAIL_EXP_A              375  //Koefficients for waiting time 
#define USB_FAIL_EXP_B              2883 //calculation formula T=A*exp(B*x/11365)
#define USB_FAIL_START_TIME         5000 //The usb brake module will be active only after this time from power up controller

static void USBIntHandler(void)
{
  uint32_t IntStatusControl = USBIntStatusControl(USB0_BASE);

  /*
   * Here we can use only IntStatusControl function for Interrupt status
   * because Endpoint status in funcions USBIntStatus and
   * USBIntStatusEndPoint is read-sensitive
   */
  switch (IntStatusControl)
  {
    case USB_INTCTRL_SUSPEND:
    case USB_INTCTRL_RESUME:
      if (USBbreakReconnectEnable)
      {
        // Here you...
      }
      break;

    case USB_INTCTRL_RESET:
      // Here you can do something on USB connect
      break;

    case 0:
      // Data interrupts (From Endpoint)
      USBbreakReconnectEnable = 1;
      break;

    default:
      // Other interrupts
      break;
  }

  USB0DeviceIntHandler();
}

void USB_InitAndCheck(void)
{
  static bool Engaged = false;

  /*
   * Protection against double initialization.
   */
  if (Engaged)
  {
    return;
  }

  Engaged = true;

  IOBuffer_Init(&TxBuf);
  IOBuffer_Init(&RxBuf);

  // Initialize and start timer for Rx buffer cleaning
  CleanRxBufferTimerHandle = xTimerCreate("Clean Rx buffer timer",
                                          pdMS_TO_TICKS(_PROTOCOL_DELAY),
                                          pdFALSE,
                                          ( void * ) 0,
                                          USBCleanRxBufferCallback);

  SetUsbManufacturer(MANUFACTURER);
  SetUsbProduct(PRODUCT_NAME);
  SetUsbSerial(SERIAL_NUMBER);

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

  SysCtlPeripheralEnable(USB_MUX_GPIO_PERIPH);
  GPIOPinTypeGPIOOutput(USB_MUX_GPIO_BASE, USB_MUX_GPIO_PIN);
  GPIOPinWrite(USB_MUX_GPIO_BASE, USB_MUX_GPIO_PIN, USB_MUX_SEL_DEVICE);
  SysCtlPeripheralReset(SYSCTL_PERIPH_USB0);
  SysCtlPeripheralEnable(SYSCTL_PERIPH_USB0);
  SysCtlUSBPLLEnable();
  USBStackModeSet(0, USB_MODE_FORCE_DEVICE, 0);
  HWREGB(USB0_BASE + USB_O_IS) = 0;     // Clear Interrupt
  USBDevMode(USB0_BASE);
  USBDevConnect(USB0_BASE);
  USBIntEnableControl(USB0_BASE, USB_INTCTRL_RESET | USB_INTCTRL_SUSPEND);

  IntRegister(INT_USB0, &USBIntHandler);
  IntEnable(INT_USB0);

  USBStart(1);
}

static void USBGetData(uint8_t COMID)
{
  extern io_buffer_t SlaveReadBuf[];  // Rudiment of I2C

  while (USBBufferDataAvailable((tUSBBuffer *)&g_psRxBuffer[COMID]))
  {
    uint8_t TempBuf[_PACKET_LENGTH];  // Prepare buffer for new data
    uint8_t NumBytes = USBBufferDataAvailable((tUSBBuffer *)&g_psRxBuffer[COMID]);  // Get and store number of available bytes
    USBBufferRead((tUSBBuffer *)&g_psRxBuffer[COMID], TempBuf, NumBytes);   // Gs data in the buffer

    if (COMID == 0)   // If we work with main buffer
    {
      IOBuffer_PutBuf(&RxBuf, TempBuf, NumBytes);   // First put data into buffer
      if (xTimerReset(CleanRxBufferTimerHandle, 0) != pdPASS)
      {
        #ifdef DEBUG
        printf ("The timer was not started.\n");
        while (1); // Infinite loop
        #endif
      }

      if (FlowParser_Process(&RxBuf, &TxBuf))   // Process received data and check whether there was a response
      {
        SendToUSB();  // Got any response - send immidiately
      }
    }
    else
    {
      IOBuffer_PutBuf(&SlaveReadBuf[COMID - 1], TempBuf, NumBytes);
    }
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
  IOBuffer_ReInit(&RxBuf);
}

static unsigned long ControlHandler(void *pvCBData, unsigned long ulEvent, unsigned long ulMsgValue, void *pvMsgData)
{
  switch (ulEvent)
  {
    // We are connected to a host and communication is now possible.
    case USB_EVENT_CONNECTED:
      {
        break;
      }
    // The host has disconnected.
    case USB_EVENT_DISCONNECTED:
      {
        break;
      }
    // Return the current serial communication parameters.
    case USBD_CDC_EVENT_GET_LINE_CODING:
      {
        ((tLineCoding *)pvMsgData)->ulRate = 115200;
        ((tLineCoding *)pvMsgData)->ucDatabits = 8;
        ((tLineCoding *)pvMsgData)->ucParity = USB_CDC_PARITY_NONE;
        ((tLineCoding *)pvMsgData)->ucStop = USB_CDC_STOP_BITS_1;
        break;
      }
    // We don't expect to receive any other events.  Ignore any that show
    // up in a release build or hang in a debug build.
    default:
      {
        break;
      }
  }
  return (0);
}

static unsigned long TxHandler(void *pvCBData, unsigned long ulEvent, unsigned long ulMsgValue, void *pvMsgData)
{
  return (0);
}

static unsigned long RxHandler(void *pvCBData, unsigned long ulEvent, unsigned long ulMsgValue, void *pvMsgData)
{
  switch (ulEvent)
  {
    case USB_EVENT_RX_AVAILABLE:
      {
        USBGetData(((tUSBDCDCDevice *)pvCBData)->usMaxPowermA);
        break;
      }

    case USB_EVENT_DATA_REMAINING:
      {
        return (0);
      }

    case USB_EVENT_REQUEST_BUFFER:
      {
        return (0);
      }
    default:
      {
        break;
      }
  }
  return (0);
}

static void USBStart(unsigned char NumDevices)
{

  for (long i = 0; i < NumDevices; i++)
  {
    g_psCDCDevice[i].usVID = USB_VID;
    g_psCDCDevice[i].usPID = USB_PID;
    g_psCDCDevice[i].usMaxPowermA = i;
    g_psCDCDevice[i].ucPwrAttributes = USB_CONF_ATTR_BUS_PWR;
    g_psCDCDevice[i].pfnControlCallback = ControlHandler;
    g_psCDCDevice[i].pvControlCBData = (void *)&g_psCDCDevice[i];
    g_psCDCDevice[i].pfnRxCallback = USBBufferEventCallback;
    g_psCDCDevice[i].pvRxCBData = (void *)&g_psRxBuffer[i];
    g_psCDCDevice[i].pfnTxCallback = USBBufferEventCallback;
    g_psCDCDevice[i].pvTxCBData = (void *)&g_psTxBuffer[i];
    g_psCDCDevice[i].ppStringDescriptors = 0;
    g_psCDCDevice[i].ulNumStringDescriptors = 0;
    g_psCDCDevice[i].psPrivateCDCSerData = &g_psCDCInstance[i];

    g_psRxBuffer[i].bTransmitBuffer = false;
    g_psRxBuffer[i].pfnCallback = RxHandler;
    g_psRxBuffer[i].pvCBData = (void *)&g_psCDCDevice[i];
    g_psRxBuffer[i].pfnTransfer = USBDCDCPacketRead;
    g_psRxBuffer[i].pfnAvailable = USBDCDCRxPacketAvailable;
    g_psRxBuffer[i].pvHandle = (void *)&g_psCDCDevice[i];
    g_psRxBuffer[i].pcBuffer = &g_pcUSBRxBuffer[_PACKET_LENGTH * i];
    g_psRxBuffer[i].ulBufferSize = _PACKET_LENGTH;
    g_psRxBuffer[i].pvWorkspace = &g_pucRxBufferWorkspace[USB_BUFFER_WORKSPACE_SIZE * i];

    g_psTxBuffer[i].bTransmitBuffer = true;
    g_psTxBuffer[i].pfnCallback = TxHandler;
    g_psTxBuffer[i].pvCBData = (void *)&g_psCDCDevice[i];
    g_psTxBuffer[i].pfnTransfer = USBDCDCPacketWrite;
    g_psTxBuffer[i].pfnAvailable = USBDCDCTxPacketAvailable;
    g_psTxBuffer[i].pvHandle = (void *)&g_psCDCDevice[i];
    g_psTxBuffer[i].pcBuffer = &g_pcUSBTxBuffer[_PACKET_LENGTH * i];
    g_psTxBuffer[i].ulBufferSize = _PACKET_LENGTH;
    g_psTxBuffer[i].pvWorkspace = &g_pucTxBufferWorkspace[USB_BUFFER_WORKSPACE_SIZE * i];

    g_psCompDevices[i].psDevice = &g_sCDCSerDeviceInfo;
    g_psCompDevices[i].pvInstance = 0;
  }

  g_sCompDevice.ulNumDevices = NumDevices;
  for (long i = 0; i < NumDevices; i++)
  {
    USBBufferInit((tUSBBuffer *)&g_psTxBuffer[i]);
    USBBufferInit((tUSBBuffer *)&g_psRxBuffer[i]);
    g_sCompDevice.psDevices[i].pvInstance =
      USBDCDCCompositeInit(0, (tUSBDCDCDevice *)&g_psCDCDevice[i]);
  }
  USBDCompositeInit(0, &g_sCompDevice, DESCRIPTOR_DATA_SIZE,
                    g_pucDescriptorData);
}

static inline void SendToUSB(void)
{
  uint8_t tmpreg[_PACKET_LENGTH];
  uint8_t size;

  size = IOBuffer_Size(&TxBuf);
  IOBuffer_GetBuf(&TxBuf, tmpreg, size);

  USBBufferWrite((tUSBBuffer *)&g_psTxBuffer[0], tmpreg, size);
}
