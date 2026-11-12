/* SPDX-License-Identifier: MIT */
#define SSA_EVENT_SUITE
#define _start unused_stage4_entry
#include "process-init.c"
#undef _start
static __attribute__((noinline,noclone)) void event_common(u64 n){touch_pages(n);}
static __attribute__((noinline,noclone)) void event_warm(void){event_common(1);asm volatile("":::"memory");}
static __attribute__((noinline,noclone)) void event_cold(void){event_common(128);asm volatile("":::"memory");}
static void context_child(void){
 priority(0,0);require(C(146,1000,0,0)==0);touch_pages(512);
 require(api(1,2,0,8)==0);event_warm();event_cold();event_warm();require(api(2,0,0,0)==4);require(api(5,0,0,0)==0);require(api(5,0,0,0)==-114);die(0);
}
static void counter_security_child(void){
 struct {void (*handler)(int);u64 flags,mask;} sa={sig_exit,0,0};
 require(C(146,1000,0,0)==0);require(sc(134,4,(long)&sa,0,8,0,0)==0);
 u64 x;asm volatile("csrr %0,0xc03":"=r"(x));(void)x;die(94);
}
void _start(void){
 require(C(172,0,0,0)==1);priority(1,2);out("SSA_HPM_EVENT_SUITE_START\n");
 long q=fork_child();require(q>=0);if(!q)counter_security_child();wait_child(q,104);out("SSA HPM COUNTER PERMISSION PASS\n");
 long c=fork_child();require(c>=0);if(!c)context_child();wait_child(c,0);require(api(3,0,0,0)==0);out("SSA HPM CONTEXT PASS\n");
 for(long test=9;test<=10;test++){
  int fd[2];require(C(59,fd,0,0)==0);
  long b=fork_child();require(b>=0);if(!b)job(2,3000,test,test==10,fd);
  long a=fork_child();require(a>=0);if(!a)job(1,4000,test,test==10,fd);
  wait_child(b,0);require(api(3,0,0,0)==0);wait_child(a,0);require(api(3,0,0,0)==0);
  C(57,fd[0],0,0);C(57,fd[1],0,0);out("SSA HPM SWITCH PASS\n");
 }
 out("SSA_HPM_EVENT_EXEC_BEGIN\n");char *args[]={"/eventexec",0};char *env[]={0};sc(221,(long)args[0],(long)args,(long)env,0,0,0);die(93);
}
