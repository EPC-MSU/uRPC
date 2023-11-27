#ifndef CONFIG_H
#define CONFIG_H

#include <stdbool.h>    // For bool, true, false
#include <stdint.h>     // For uint32_t, int16_t and etc.

#define MANUFACTURER      "${protocol.manufacturer}"
#define PRODUCT_NAME      "${protocol.product_name}"

#define USB_VID           ${protocol.vid}
#define USB_PID           ${protocol.pid}
#define SERIAL_NUMBER     0x12345678        // place correct serial number

/* You can add new configuration defines for your project in this file */

#endif // CONFIG_H
