#ifndef _FLOWPARSER_H
#define _FLOWPARSER_H

/*
 * Other includes here.
 */
#include "iobuffer.h"

#if defined(__cplusplus)
extern "C"
{
#endif

uint16_t FlowParser_Process(io_buffer_t *pRxBuf, io_buffer_t *pTxBuf);

#if defined(__cplusplus)
};
#endif

#endif  // _FLOWPARSER_H
