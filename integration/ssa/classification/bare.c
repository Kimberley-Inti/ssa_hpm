#include <stdint.h>
#define BASE 0x88000000UL
extern volatile uint64_t tohost,fromhost;
extern void class_common(uint64_t **,uint64_t);
static uint64_t data[4096];
static uint64_t *scalar[8],*stream[8],*randoms[8],*modes[6];
static const unsigned ix[]={0,32,8,80,0,9,71,4};
__attribute__((noinline)) void scalar_parent(void){class_common(scalar,8);asm volatile("":::"memory");}
__attribute__((noinline)) void stream_parent(void){class_common(stream,8);asm volatile("":::"memory");}
__attribute__((noinline)) void irregular_parent(void){class_common(randoms,8);asm volatile("":::"memory");}
static void line(const char *s){unsigned n=0;while(s[n])n++;volatile uint64_t cmd[8] __attribute__((aligned(64)))={64,1,(uintptr_t)s,n};asm volatile("fence rw,rw":::"memory");tohost=(uintptr_t)cmd;while(!fromhost){}fromhost=0;}
static char *num(char *p,uint64_t x){for(int i=60;i>=0;i-=4)*p++="0123456789abcdef"[(x>>i)&15];return p;}
#define RD(c) ({uint64_t x;asm volatile("csrr %0," #c:"=r"(x));x;})
#define WR(c,x) asm volatile("csrw " #c ",%0"::"r"((uint64_t)(x)):"memory")
extern void class_faulting(void);
extern void class_interleave(uint64_t *,uint64_t *);
extern void class_stores(uint64_t *);
__attribute__((noinline)) void mode_parent(void){class_common(modes,6);asm volatile("":::"memory");}
extern void class_capacity(uint64_t *);
extern volatile uint64_t class_faults;
int main(void){
 for(unsigned i=0;i<8;i++){scalar[i]=data;stream[i]=data+i;randoms[i]=data+ix[i];}
 for(unsigned i=0;i<6;i++)modes[i]=data+(i<3?0:i-2);
 volatile uint64_t *m=(void *)(BASE-64);m[1]=1;
 WR(0x800,BASE);WR(0x5c1,1);WR(0x5c3,0);WR(0x5c2,1);
 while(RD(0x5c2)&2){}
 scalar_parent();stream_parent();irregular_parent();scalar_parent();
#ifdef CLASS_FAULT
 class_faulting();
#endif
#ifdef CLASS_PATTERNS
 mode_parent();class_interleave(data,data);class_stores(data);
#endif
#ifdef CLASS_CAPACITY
 class_capacity(data);
#endif
 WR(0x800,0);
 uint64_t total=m[1]-1;
 for(uint64_t r=0;r<=total && r<64;r++){
  WR(0x5c3,r);uint64_t values[]={RD(0x5c4),RD(0x5c5),RD(0x5c6),RD(0x5c7),RD(0x5c8),RD(0x5c9),RD(0x5ca),RD(0x5cb)};
  char s[230],*p=s;const char *tag="SSA_CLASS_ROW ";while(*tag)*p++=*tag++;p=num(p,r);
  for(unsigned i=0;i<8;i++){*p++=' ';p=num(p,values[i]);}*p++='\n';*p=0;line(s);
 }
#ifdef CLASS_FAULT
 line("SSA_CLASS_FAULT_EXPECTED\n");
#endif
#ifdef CLASS_CAPACITY
 line("SSA_CLASS_CAPACITY_EXPECTED\n");
#endif
#ifdef CLASS_PATTERNS
 line("SSA_CLASS_PATTERNS_EXPECTED\n");
#endif
 line("SSA_CLASS_DONE\n");
#ifdef CLASS_PATTERNS
 return !(total==10 && m[0]==0);
#elif defined(CLASS_CAPACITY)
 WR(0x5c3,0);
 return !(total==72 && m[0]==0 && RD(0x5cb)>0 && RD(0x5ca)>0 && (RD(0x5c4)&4)==0);
#elif defined(CLASS_FAULT)
 return !(total==7 && m[0]==0 && class_faults==1);
#else
 return !(total==6 && m[0]==0);
#endif
}
