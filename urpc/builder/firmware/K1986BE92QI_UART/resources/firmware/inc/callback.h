#ifndef _CALLBACK_H
#define _CALLBACK_H

#define CALLBACK_NUMBER             2
#define CALLBACK_MAX_DELAY          0x7FFFFFFFUL  // Half of 32-bits range
#define CALLBACK_CANCEL_PADDING     0x10L  // Time to substract from current time to guaranty that callback will not be run, issues #63336 and #61465

typedef enum
{
  USB_CLEANING_INDEX            = 0,
  UART_CLEANING_INDEX           = 1,

  CALLBACK_NUMBER_INDEX   // End of enum must be always

} callback_index_t;

void Callback_Init(void);
void Callback_SetHandler(callback_index_t CallbackNum, void (*pfnHandler)(void));
void Callback_SetDelay(callback_index_t CallbackNum, uint32_t Delay);
uint32_t Callback_GetDelay(callback_index_t CallbackNum);
void Callback_CancelDelay(callback_index_t CallbackNum);

#endif  // _CALLBACK_H
