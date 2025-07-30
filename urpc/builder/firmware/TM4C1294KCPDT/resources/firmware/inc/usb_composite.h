#ifndef _USB_COMPOSITE_H
#define _USB_COMPOSITE_H
#include "config.h"

#define I2C_DEVICES_LIMIT   4   // Can not exceed 16 because of addresses limit

/*
 * USB mux GPIO definitions.
 */
#define USB_MUX_GPIO_PERIPH     SYSCTL_PERIPH_GPIOH
#define USB_MUX_GPIO_BASE       GPIO_PORTH_BASE
#define USB_MUX_GPIO_PIN        GPIO_PIN_2
#define USB_MUX_SEL_DEVICE      USB_MUX_GPIO_PIN

void SetUsbSerial(uint32_t SN);
void SetUsbManufacturer(char *MFC);
void SetUsbProduct(char *PRT);

void USB_InitAndCheck(void);

#endif  // _USB_COMPOSITE_H
