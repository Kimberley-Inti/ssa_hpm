/* SPDX-License-Identifier: MIT */
#include <stdint.h>
static volatile uint64_t data[4096],sink;
__attribute__((noinline)) static uint64_t leaf(uint64_t x){asm volatile(""::"r"(x):"memory");return x*3+1;}
__attribute__((noinline)) static uint64_t deep(uint64_t n,uint64_t x){if(n)x=deep(n-1,x+1);return x+1;}
__attribute__((noinline)) static uint64_t bench_work(uint64_t kind){uint64_t x=1;if(kind==0){for(unsigned i=0;i<128;i++)x=x*1664525+1013904223;}else if(kind==1){for(unsigned i=0;i<128;i++)x=leaf(x);}else if(kind==2)x=deep(16,x);else{unsigned j=0;for(unsigned i=0;i<4096;i++){j=kind==3?i:((j*109+37)&4095);x+=data[j];}}return x;}
