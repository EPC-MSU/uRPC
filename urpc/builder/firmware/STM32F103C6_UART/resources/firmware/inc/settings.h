#ifndef _SETTINGS_H
#define _SETTINGS_H

#include <stdbool.h>    // For bool, true, false
#include <stddef.h>     // For size_t, NULL
#include <stdint.h>     // For uint32_t, int16_t and etc.

/*
 * Other includes here.
 */
#include "stm32_assert.h"

#define INIT_STATE_VAR(m) \
static volatile enum \
{ \
  INIT_NEWBORN  = 0, \
  INIT_IN_PROG  = 1, \
  INIT_DONE     = 2 \
 \
} m ## _Engaged = INIT_NEWBORN

#define INIT_START(m) \
assert_param(m ## _Engaged != INIT_IN_PROG); \
 \
if (m ## _Engaged) \
  return; \
 \
m ## _Engaged = INIT_IN_PROG

#define INIT_END(m) \
m ## _Engaged = INIT_DONE

#define FUNC_START(m) \
assert_param(m ## _Engaged == INIT_DONE)

#define _PACKET_LENGTH      256               // Must be as large as any single protocol response (Command, Data, CRC)
#define _COMMAND_LENGTH     sizeof(uint32_t)  // Command name size in bytes (must be 4)
#define _CRC_LENGTH         sizeof(uint16_t)  // CRC size in bytes (must be 2)

#define _PROTOCOL_DELAY     2000      // Delay before buffer cleaning in milliseconds
#define _CPU_FREQUENCY      72000000  // Frequency of CPU
#define _PRIORITY_GROUP     4

#endif  // _SETTINGS_H
