/* SPDX-License-Identifier: MIT
 * Freestanding Linux ABI fixture. No libc, exec after enable, or shared pool API. */
typedef unsigned long u64;
static __attribute__((always_inline)) inline long sc(long n,long x,long y,long z,long q,long v,long w){register long a0 asm("a0")=x,a1 asm("a1")=y,a2 asm("a2")=z,a3 asm("a3")=q,a4 asm("a4")=v,a5 asm("a5")=w,a7 asm("a7")=n;asm volatile("ecall":"+r"(a0):"r"(a1),"r"(a2),"r"(a3),"r"(a4),"r"(a5),"r"(a7):"memory");return a0;}
#define C(n,x,y,z) sc(n,(long)(x),(long)(y),(long)(z),0,0,0)
static void out(const char *s){long n=0;while(s[n])n++;C(64,1,s,n);}
static __attribute__((always_inline)) inline void die(long n){C(93,n,0,0);for(;;);}
static __attribute__((always_inline)) inline void require(int yes){if(!yes){out("SSA LINUX TEST FAIL\n");die(90);}}
static __attribute__((always_inline)) inline long api(long op,long flags,long role,long test){
#ifdef REFERENCE
 return op==2?2:0;
#else
 return sc(167,0x535341,op,flags,role,test,0);
#endif
}
static __attribute__((always_inline)) inline void work(unsigned long n){asm volatile(".option push\n.option norvc\n1:\n.rept 64\nnop\n.endr\naddi %0,%0,-1\nbnez %0,1b\n.option pop":"+r"(n)::"memory");}
static __attribute__((noinline,noclone)) void common(long role,long amount){
 if(role==2){long ts[2]={0,1000000};C(101,ts,0,0);}
 work(amount);
}
static __attribute__((noinline,noclone)) void parent(long role,long amount){common(role,amount);asm volatile("":::"memory");}
static long fork_child(void){return sc(220,17,0,0,0,0,0);}
static void wait_child(long pid,long expect){int status=0;require(C(260,pid,&status,0)==pid);require(status==expect*256);}
static void priority(long policy,long prio){int p=prio;require(C(119,0,policy,&p)==0);}
static void job(long role,long amount,long test,long legacy,int *pipefd){
 priority(role==2?1:0,role==2?1:0);
 require(C(146,1000,0,0)==0);require(C(174,0,0,0)==1000);
 require(api(1,legacy,role,test)==0);
 /* Only inlined syscalls execute while selected, except the two measured calls. */
 if(pipefd){char token='x';if(role==2){if(C(63,pipefd[0],&token,1)!=1)die(91);}else if(C(64,pipefd[1],&token,1)!=1)die(92);}
 parent(role,amount);
 if(api(2,0,0,0)!=2)die(93);
 die(0);
}
static void sig_exit(int sig){die(100+sig);}
static void security_child(long test){
 struct {void (*handler)(int);u64 flags,mask;} sa={sig_exit,0,0};
 require(C(146,1000,0,0)==0);
 require(sc(134,4,(long)&sa,0,8,0,0)==0);require(sc(134,11,(long)&sa,0,8,0,0)==0);
 if(test==0){u64 x;asm volatile("csrr %0,0x800":"=r"(x));die(94);}
 if(test==1){volatile u64 x=*(volatile u64 *)0x88000000UL;(void)x;die(95);}
 if(test==2){require(sc(167,0x535341,1,0x88000000UL,0,0,0)==-22);die(0);}
 if(test==3){char b[16];require(C(116,3,b,16)==-1);die(0);}
 die(96);
}
void _start(void){
 require(C(172,0,0,0)==1);priority(1,2);
 out("SSA LINUX PROCESS FIXTURE START\n");
 long p=fork_child();require(p>=0);if(!p)job(0,100,0,0,0);wait_child(p,0);
 require(api(3,0,0,0)==0);out("SSA LINUX B USER PASS\n");
#if !defined(REFERENCE) || defined(REFERENCE_SECURITY)
 for(long i=0;i<4;i++){p=fork_child();require(p>=0);if(!p)security_child(i);wait_child(p,i==0?104:i==1?111:0);}
 out("SSA LINUX SECURITY USER PASS\n");
#endif
 for(long test=1;test<=4;test++){
  int fd[2];require(C(59,fd,0,0)==0);
  long b=fork_child();require(b>=0);if(!b)job(2,test%2?20:3000,test,test>=3,fd);
  long a=fork_child();require(a>=0);if(!a)job(1,4000,test,test>=3,fd);
  wait_child(b,0);require(api(3,0,0,0)==0);wait_child(a,0);require(api(3,0,0,0)==0);
  C(57,fd[0],0,0);C(57,fd[1],0,0);out("SSA LINUX DUAL USER PASS\n");
 }
 out("SSA LINUX PROCESS FIXTURE PASS\n");
 C(142,0xfee1dead,672274793,0x4321fedc);for(;;)C(124,0,0,0);
}
