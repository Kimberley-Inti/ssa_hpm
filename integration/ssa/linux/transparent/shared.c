/* SPDX-License-Identifier: MIT */
static __attribute__((noinline,noclone)) long shared_inner(long x){asm volatile("":::"memory");return x+7;}
long shared_entry(long x){long y=shared_inner(x);asm volatile("":::"memory");return y+1;}
unsigned long shared_anchor(void){return (unsigned long)shared_inner;}
