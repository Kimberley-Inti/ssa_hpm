/* SPDX-License-Identifier: MIT */
#include <stdint.h>
#include <stddef.h>
#define BASE 0x88000000UL
#define RD(c) ({uint64_t x;asm volatile("csrr %0," #c:"=r"(x));x;})
#define WR(c,x) asm volatile("csrw " #c ",%0"::"r"((uint64_t)(x)):"memory")
extern volatile uint64_t tohost,fromhost;
#include "workload.h"
typedef struct {uint64_t c,i,t;} Stamp;
static __attribute__((always_inline)) inline Stamp stamp(void){asm volatile("fence rw,rw":::"memory");Stamp s={RD(0xc00),RD(0xc02),*(volatile uint64_t *)0x200bff8UL};return s;}
static void line(char*s){unsigned n=0;while(s[n])n++;volatile uint64_t cmd[8] __attribute__((aligned(64)))={64,1,(uintptr_t)s,n};asm volatile("fence rw,rw":::"memory");tohost=(uintptr_t)cmd;while(!fromhost){}fromhost=0;}
static char*num(char*p,uint64_t x){*p++=' ';for(int i=60;i>=0;i-=4)*p++="0123456789abcdef"[(x>>i)&15];return p;}
static void emit(unsigned mode,unsigned kind,unsigned rep,Stamp a,Stamp b,uint64_t x){char s[230],*p=s;char*tag=mode>=200?"SSA_PERF_CAL":mode>=100?"SSA_PERF_INIT":"SSA_PERF";mode%=100;while(*tag)*p++=*tag++;uint64_t v[]={mode,kind,rep,a.c,b.c,a.i,b.i,a.t,b.t,x};for(unsigned j=0;j<10;j++)p=num(p,v[j]);*p++='\n';*p=0;line(s);}
#ifndef REPEATS
#define REPEATS 5
#endif
int main(void){
 WR(0x306,0);WR(0x320,0);WR(0x3a0,15);WR(0x3b0,~0UL);
 uint64_t expected[5]={0};
 for(unsigned mode=0;mode<6;mode++){
  WR(0x800,0);WR(0x5c1,0);
  Stamp init0=stamp();
  volatile uint32_t*d=(void*)(BASE-1065024);for(unsigned j=0;j<262144;j++)d[j]=0;
  volatile uint64_t*m=(void*)(BASE-64);for(unsigned j=0;j<8;j++)m[j]=0;m[1]=1;
  WR(0x323,mode==2?0x1002:((mode==3||mode==5)?0x202:0));WR(0x5c0,(mode==2||mode==3||mode==5)?2:0);
  if(mode){WR(0x800,BASE);if(mode>=4){WR(0x5c1,mode);WR(0x5c3,0);WR(0x5c2,1);while(RD(0x5c2)&2){}}}
  Stamp init1=stamp();
  WR(0x800,0);WR(0x5c1,0);emit(100+mode,0,0,init0,init1,1048576);
  if(mode){WR(0x800,BASE);if(mode>=4)WR(0x5c1,mode);}
  // Every call to stamp/emit is inlined or outside enabled sampling.
  for(unsigned rep=0;rep<REPEATS;rep++){
   Stamp a=stamp(),b=stamp();WR(0x800,0);WR(0x5c1,0);emit(200+mode,0,rep,a,b,0);
   if(mode){WR(0x800,BASE);if(mode>=4)WR(0x5c1,mode);}
  }
  for(unsigned kind=0;kind<5;kind++){
   for(unsigned j=0;j<4096;j++)data[j]=j*17+3;
   sink=bench_work(kind);
   for(unsigned rep=0;rep<REPEATS;rep++){
    Stamp a=stamp();uint64_t x=bench_work(kind);Stamp b=stamp();sink=x;
    // Disable for output then restore the same epoch/history and dictionary.
    WR(0x800,0);if(mode>=4)WR(0x5c1,0);
    emit(mode,kind,rep,a,b,x);
    if(mode==0)expected[kind]=x;else if(expected[kind]!=x)return 12;
    if(mode){WR(0x800,BASE);if(mode>=4)WR(0x5c1,mode);}
   }
  }
  WR(0x800,0);WR(0x5c1,0);
 }
 line("SSA_PERF_DONE\n");return 0;
}
