/*
 * Each file must start with this include.
 * File containes global settings.
 */
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

#include "callback.h"     // For buffer cleaning
#include "flowparser.h"   // Upper level interface
#include "algorithm.h"

#define NUM_SERIAL_DEVICES      1
#define DESCRIPTOR_DATA_SIZE    (COMPOSITE_DCDC_SIZE * NUM_SERIAL_DEVICES)

#define UNCONST(t,a)            *((t *)(&(a)))

static unsigned char g_pucDescriptorData[DESCRIPTOR_DATA_SIZE];
static io_buffer_t RxBuf, TxBuf;

static uint8_t USBbreakReconnectEnable;

static inline void SendToUSB(void);
static void USBStart(uint8_t NumDevices);
static void USBIntHandler(void);
static void USBGetData(uint8_t COMID);
static void RxBufferCleaner(void);

/*
 * CDC device callback function prototypes.
 */
static uint32_t ControlHandler(void *pvCBData, uint32_t ulEvent, uint32_t ulMsgValue, void *pvMsgData);
static uint32_t TxHandler(void *pvCBData, uint32_t ulEvent, uint32_t ulMsgValue, void *pvMsgData);
static uint32_t RxHandler(void *pvCBData, uint32_t ulEvent, uint32_t ulMsgValue, void *pvMsgData);

static const unsigned char g_pLangDescriptor[] =
{
    4,
    USB_DTYPE_STRING,
    USBShort(USB_LANG_EN_US)
};

static const unsigned char g_pManufacturerString[] =
{
    2 + (4 * 2),
    USB_DTYPE_STRING,
    'X', 0, 'I', 0, 'M', 0,'C', 0
};

static const unsigned char g_pProductString[] =
{
    2 + (21 * 2),
    USB_DTYPE_STRING,
    'X', 0,'I', 0,'M', 0,'C', 0,' ', 0,'M', 0,'o', 0,'t', 0,'o', 0,
    'r', 0,' ', 0,'C', 0,'o', 0,'n', 0,'t', 0,'r', 0,'o', 0,'l', 0,
    'l', 0,'e', 0,'r', 0
};

static unsigned char g_pSerialNumberString[] =
{
    2 + (8 * 2),
    USB_DTYPE_STRING,
    '1', 0, '2', 0, '3', 0, '4', 0, '5', 0, '6', 0, '7', 0, '8', 0
};

static const unsigned char * const g_pStringDescriptors[] =
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
static tUSBDCDCDevice g_psCDCDevice[NUM_SERIAL_DEVICES];

//*****************************************************************************
//
// Receive buffer (from the USB perspective).
//
//*****************************************************************************
static uint8_t g_ppui8USBRxBuffer[NUM_SERIAL_DEVICES][_PACKET_LENGTH];
static tUSBBuffer g_psRxBuffer[I2C_DEVICES_LIMIT];

//*****************************************************************************
//
// Transmit buffer (from the USB perspective).
//
//*****************************************************************************
static uint8_t g_ppcUSBTxBuffer[NUM_SERIAL_DEVICES][_PACKET_LENGTH];
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
tUSBDCompositeDevice g_sCompDevice =
{
  USB_VID_TI_1CBE,
  USB_PID_COMP_SERIAL,
  250,		        // This is in 2mA increments so 500mA.
  USB_CONF_ATTR_BUS_PWR,	// Bus powered device.
  0,			        // There is no need for a default composite event handler.  						
  g_pStringDescriptors,	// The string table.
  NUM_STRING_DESCRIPTORS,
  NUM_SERIAL_DEVICES,
  g_psCompDevices
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
    USBbreakReconnectEnable=1;
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
    return;

  Engaged = true;

  IOBuffer_Init(&TxBuf);
  IOBuffer_Init(&RxBuf);

  Callback_Init();

  Callback_SetHandler(USB_CLEANING_INDEX, RxBufferCleaner);   // Callback to clean input buffer

  SysCtlPeripheralReset(SYSCTL_PERIPH_USB0);
  SysCtlDelay(0x800);

  // Enabling peripheral
  SysCtlPeripheralEnable(SYSCTL_PERIPH_USB0);

  while (!(SysCtlPeripheralReady(SYSCTL_PERIPH_USB0)))  // We wait enabling
  {
    // Nothing
  }

  SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOL);  // USB0 needs GPIO port L

  while (!(SysCtlPeripheralReady(SYSCTL_PERIPH_GPIOL))) // We wait only last enabling port
  {
    // Nothing
  }

  SysCtlUSBPLLEnable();

  GPIOPinTypeUSBAnalog(GPIO_PORTL_BASE, GPIO_PIN_6 | GPIO_PIN_7);

  USBStackModeSet(0, eUSBModeForceDevice, 0);
  
  HWREGB(USB0_BASE + USB_O_IS) = 0;     // Clear Interrupt
  USBDevMode(USB0_BASE);
  USBDevConnect(USB0_BASE);
  USBIntEnableControl(USB0_BASE, USB_INTCTRL_RESET | USB_INTCTRL_SUSPEND);

  IntRegister(INT_USB0, &USBIntHandler);
  IntEnable(INT_USB0);

  USBStart(NUM_SERIAL_DEVICES);
}

static void USBGetData(uint8_t COMID)
{
  extern io_buffer_t SlaveReadBuf[];  // Rudiment of I2C

  while(USBBufferDataAvailable((tUSBBuffer *)&g_psRxBuffer[COMID]))
  {
    uint8_t TempBuf[_PACKET_LENGTH];  // Prepare buffer for new data
    uint8_t NumBytes = USBBufferDataAvailable((tUSBBuffer *)&g_psRxBuffer[COMID]);  // Get and store number of available bytes
    USBBufferRead((tUSBBuffer *)&g_psRxBuffer[COMID], TempBuf, NumBytes);   // Gs data in the buffer

    if (COMID == 0)   // If we work with main buffer
    {
      IOBuffer_PutBuf(&RxBuf, TempBuf, NumBytes);   // First put data into buffer

      Callback_SetDelay(USB_CLEANING_INDEX, _PROTOCOL_DELAY);

      if (FlowParser_Process(&RxBuf, &TxBuf))   // Process received data and check whether there was a response
        SendToUSB();  // Got any response - send immidiately
    }
    else
      IOBuffer_PutBuf(&SlaveReadBuf[COMID - 1], TempBuf, NumBytes);
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
  IOBuffer_ReInit(&RxBuf);
}

static uint32_t ControlHandler(void *pvCBData, uint32_t ulEvent, uint32_t ulMsgValue, void *pvMsgData)
{
    switch(ulEvent)
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
	  ((tLineCoding *)pvMsgData)->ui32Rate = 115200;
	  ((tLineCoding *)pvMsgData)->ui8Databits = 8;
	  ((tLineCoding *)pvMsgData)->ui8Parity = USB_CDC_PARITY_NONE;
	  ((tLineCoding *)pvMsgData)->ui8Stop = USB_CDC_STOP_BITS_1;
          break;
        }
        // We don't expect to receive any other events.  Ignore any that show
        // up in a release build or hang in a debug build.
        default:
        {
            break;
        }
    }
    return(0);
}

static uint32_t TxHandler(void *pvCBData, uint32_t ulEvent, uint32_t ulMsgValue, void *pvMsgData)
{
  return(0);
}

static uint32_t RxHandler(void *pvCBData, uint32_t ulEvent, uint32_t ulMsgValue, void *pvMsgData)
{
    switch(ulEvent)
    {
        case USB_EVENT_RX_AVAILABLE:
        {   
            USBGetData(((tUSBDCDCDevice *)pvCBData)->ui16MaxPowermA);
            break; 
        }

        case USB_EVENT_DATA_REMAINING:
        {
            return(0);
        }

        case USB_EVENT_REQUEST_BUFFER:
        {
            return(0);
        }
        default:
        {
            break;
        }
    }
    return(0);
}

static void USBStart(unsigned char NumDevices)
{
  for (int32_t i = 0; i < NumDevices; i++)
  {
    UNCONST(uint16_t, g_psCDCDevice[i].ui16VID) = USB_VID_TI_1CBE;
    UNCONST(uint16_t, g_psCDCDevice[i].ui16PID) = USB_PID_SERIAL;
    UNCONST(uint16_t, g_psCDCDevice[i].ui16MaxPowermA) = 0;
    UNCONST(uint8_t, g_psCDCDevice[i].ui8PwrAttributes) = USB_CONF_ATTR_SELF_PWR;
    UNCONST(tUSBCallback, g_psCDCDevice[i].pfnControlCallback) = ControlHandler;
    g_psCDCDevice[i].pvControlCBData = (void *)&g_psCDCDevice[i];
    UNCONST(tUSBCallback, g_psCDCDevice[i].pfnRxCallback) = USBBufferEventCallback;
    g_psCDCDevice[i].pvRxCBData=(void *)&g_psRxBuffer[i];
    UNCONST(tUSBCallback, g_psCDCDevice[i].pfnTxCallback) = USBBufferEventCallback;
    g_psCDCDevice[i].pvTxCBData=(void *)&g_psTxBuffer[i];
    g_psCDCDevice[i].ppui8StringDescriptors=g_pStringDescriptors;
    UNCONST(uint32_t, g_psCDCDevice[i].ui32NumStringDescriptors) = NUM_STRING_DESCRIPTORS;

    g_psRxBuffer[i].bTransmitBuffer=false;                      // This is a receive buffer.
    g_psRxBuffer[i].pfnCallback=RxHandler;                      // pfnCallback
    g_psRxBuffer[i].pvCBData=(void *)&g_psCDCDevice[i];         // Callback data is our device pointer.
    g_psRxBuffer[i].pfnTransfer=USBDCDCPacketRead;              // pfnTransfer
    g_psRxBuffer[i].pfnAvailable=USBDCDCRxPacketAvailable;      // pfnAvailable
    g_psRxBuffer[i].pvHandle=(void *)&g_psCDCDevice[i];         // pvHandle
    g_psRxBuffer[i].pui8Buffer=g_ppui8USBRxBuffer[i];           // pcBuffer
    g_psRxBuffer[i].ui32BufferSize=_PACKET_LENGTH;
      
    g_psTxBuffer[i].bTransmitBuffer=true;                       // This is a transmit buffer.
    g_psTxBuffer[i].pfnCallback=TxHandler;                      // pfnCallback
    g_psTxBuffer[i].pvCBData=(void *)&g_psCDCDevice[i];         // Callback data is our device pointer.
    g_psTxBuffer[i].pfnTransfer=USBDCDCPacketWrite;             // pfnTransfer
    g_psTxBuffer[i].pfnAvailable=USBDCDCTxPacketAvailable;      // pfnAvailable
    g_psTxBuffer[i].pvHandle=(void *)&g_psCDCDevice[i];         // pvHandle
    g_psTxBuffer[i].pui8Buffer=g_ppcUSBTxBuffer[i];             // pcBuffer
    g_psTxBuffer[i].ui32BufferSize=_PACKET_LENGTH;
  }

  UNCONST(uint32_t, g_sCompDevice.ui32NumDevices) = NumDevices;

  for (int32_t i = 0; i < NumDevices; i++)
  {
    USBBufferInit((tUSBBuffer *)&g_psTxBuffer[i]);
    USBBufferInit((tUSBBuffer *)&g_psRxBuffer[i]);

    g_sCompDevice.psDevices[i].pvInstance = USBDCDCCompositeInit(0, &g_psCDCDevice[i], &g_psCompDevices[i]);
  }

  USBDCompositeInit(0, &g_sCompDevice, DESCRIPTOR_DATA_SIZE, g_pucDescriptorData);
}

static inline void SendToUSB(void)
{
  uint8_t tmpreg[_PACKET_LENGTH];
  uint8_t size;

  size = IOBuffer_Size(&TxBuf);
  IOBuffer_GetBuf(&TxBuf, tmpreg, size);

  USBBufferWrite((tUSBBuffer *)&g_psTxBuffer[0], tmpreg, size);
}
