#ifndef _ALGORITHM_H
#define _ALGORITHM_H

#define ALGORITHM_CRC16_SEED  0xFFFFU
#define ALGORITHM_CRC8_SEED   0xFFU

#if defined(__cplusplus)
extern "C"
{
#endif

void Algorithm_Init(void);
uint32_t Algorithm_Random(void);
//uint8_t Algorithm_CRC8(const void *Block, size_t Length, uint8_t Seed);
uint16_t Algorithm_CRC16(const void *Block, size_t Length, uint16_t Seed);

#if defined(__cplusplus)
};
#endif

#endif  // _ALGORITHM_H
