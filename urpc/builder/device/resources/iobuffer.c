/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Main includes here.
 */
#include "iobuffer.h"

/*
 * Other includes here.
 */
#include "macro.h"

#if defined(__cplusplus)
extern "C"
{
#endif

void IOBuffer_Init(io_buffer_t *b)
{
  IOBuffer_ReInit(b);

  for (uint16_t i = 0; i < IOBUFMSK; i++)
  {
    b->data[i] = 0;
  }
}

bool IOBuffer_PutC(io_buffer_t *b, const uint8_t c)
{
  if (b->length >= IOBUFMSK)
  {
    if (b->allow_overwrite)
    {
      __DISABLE_IRQ;
      b->gp = increase(b->gp, 0, IOBUFMSK - 1);
      b->data[b->pp] = c;
      b->pp = increase(b->pp, 0, IOBUFMSK - 1);
      __ENABLE_IRQ;

      return true;
    }
    else
    {
      return false;
    }
  }
  else
  {
    __DISABLE_IRQ;
    b->data[b->pp] = c;
    b->pp = increase(b->pp, 0, IOBUFMSK - 1);
    b->length++;
    __ENABLE_IRQ;

    return true;
  }
}

bool IOBuffer_PutBuf(io_buffer_t *b, const uint8_t *cbuf, size_t n)
{
  uint16_t i = 0;
  uint16_t tmp = n;

  if (n == 0)
    return true;

  if (((b->length + n) > IOBUFMSK) && (b->allow_overwrite == false))
    return false;

  while (n--)
    if (IOBuffer_PutC(b, *(cbuf++)))
      i++;

  if (i != tmp)
    return false;
  else
    return true;
}

bool IOBuffer_GetC(io_buffer_t *b, uint8_t *c)
{
  if (b->length == 0)
    return false;
  else
  {
    *c = b->data[b->gp];
    b->gp = increase(b->gp, 0, IOBUFMSK - 1);
    b->length--;

    return true;
  }
}

bool IOBuffer_PeekC(io_buffer_t *b, uint8_t *c)
{
  if(b->length == 0)
    return false;
  else
  {
    *c = b->data[b->gp];

    return true;
  }
}

bool IOBuffer_GetBuf(io_buffer_t *b, uint8_t *cbuf, size_t n)
{
  uint16_t i = 0;
  uint16_t tmp = n;

  if (n == 0)
    return true;

  if (b->length < n)
    return false;

  while (n--)
    if (IOBuffer_GetC(b, cbuf++))
      i++;

  if (i != tmp)
    return false;
  else
    return true;
}

#if defined(__cplusplus)
};
#endif
