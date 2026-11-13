/* SPDX-License-Identifier: MIT */
typedef unsigned long U;
#define INL static __attribute__((always_inline)) inline
INL long sc(long n,long x,long y,long z,long q,long v,long w){register long a0 asm("a0")=x,a1 asm("a1")=y,a2 asm("a2")=z,a3 asm("a3")=q,a4 asm("a4")=v,a5 asm("a5")=w,a7 asm("a7")=n;asm volatile("ecall":"+r"(a0):"r"(a1),"r"(a2),"r"(a3),"r"(a4),"r"(a5),"r"(a7):"memory");return a0;}
#define C(n,x,y,z) sc(n,(long)(x),(long)(y),(long)(z),0,0,0)
INL void out(const char*s){long n=0;while(s[n])n++;C(64,1,s,n);}
INL __attribute__((noreturn)) void die(long n){C(93,n,0,0);for(;;);}
INL void need(int x){if(!x){out("PLAIN_TEST_FAIL\n");die(90);}}
INL int eq(const char*a,const char*b){while(*a && *a==*b){a++;b++;}return *a==*b;}
INL void hex(U x){char s[19];s[0]='0';s[1]='x';for(int i=0;i<16;i++)s[i+2]="0123456789abcdef"[(x>>(60-4*i))&15];s[18]='\n';C(64,1,s,19);}
INL void work(U n){asm volatile(".option push\n.option norvc\n1:\n.rept 64\nnop\n.endr\naddi %0,%0,-1\nbnez %0,1b\n.option pop":"+r"(n)::"memory");}
