#ifndef _IOBUFFER_H
#define _IOBUFFER_H

/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Other includes here.
 */
#include "atomicrun.h"

#define IOBUFMSK (_PACKET_LENGTH + 1)

#pragma pack(push, 1)
/*
 * Flag allow_overwrite determine behavior on the buffer overflow.
 * If it is true when a put pointer reach a get pointer
 * and new data is put in the buffer then
 * the get pointer will be increased
 */
typedef struct
{
  uint16_t  length;
  uint16_t  pp;   // Put pointer
  uint16_t  gp;   // Get pointer
  uint8_t   data[IOBUFMSK];
  bool      allow_overwrite;

} io_buffer_t;
#pragma pack(pop)

#ifdef __cplusplus
extern "C"
{
#endif

void IOBuffer_Init(io_buffer_t *b);  // Empty buffer and fill it with zeroes

bool IOBuffer_PutC(io_buffer_t *b, const uint8_t c);
bool IOBuffer_PutBuf(io_buffer_t *b, const uint8_t *cbuf, size_t n);

bool IOBuffer_PeekC(io_buffer_t *b, uint8_t *c);

bool IOBuffer_GetC(io_buffer_t *b, uint8_t *c);
bool IOBuffer_GetBuf(io_buffer_t *b, uint8_t *cbuf, size_t n);

static inline void IOBuffer_ReInit(io_buffer_t *b)
{
  __DISABLE_IRQ;
  b->pp = 0;
  b->gp = 0;
  b->length = 0;
  b->allow_overwrite = false;
  __ENABLE_IRQ;
}

static inline uint16_t IOBuffer_Size(const io_buffer_t *b)
{
  return b->length;
}

static inline void IOBuffer_AllowOverwrite(io_buffer_t *b, bool allow)
{
  b->allow_overwrite = allow;
}

#ifdef __cplusplus
}
#endif

#endif  // _IOBUFFER_H
