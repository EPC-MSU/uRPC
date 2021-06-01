#ifndef _MACRO_H
#define _MACRO_H

#define swap(x,y) \
{ \
  (x)^=(y); \
  (y)^=(x); \
  (x)^=(y); \
}

#define sgn(x)    ((x)?(((x)>0)?1:-1):0)
#define abs(x)    (((x)<0)?-(x):(x))
#define max(x,y)  (((x)>(y))?(x):(y))
#define min(x,y)  (((x)<(y))?(x):(y))

#define clamp(x,low,high)   (((x)>(high))?(high):(((x)<(low))?(low):(x)))

#define increase(x,low,high)  (((x)==high)?(low):((x)+1))
#define decrease(x,low,high)  (((x)==low)?(high):((x)-1))
#define limit_up(x,lim)       ((x)=(((x)>(lim))?(lim):(x)))
#define limit_down(x,lim)     ((x)=(((x)>(lim))?(x):(lim)))

#ifndef HWREG
#define HWREG(x)    (*((volatile uint32_t *)(x)))
#endif  // HWREG

#ifndef HWREGH
#define HWREGH(x)   (*((volatile uint16_t *)(x)))
#endif  // HWREGH

#ifndef HWREGB
#define HWREGB(x)   (*((volatile uint8_t *)(x)))
#endif  // HWREGB

#endif  // _MACRO_H
