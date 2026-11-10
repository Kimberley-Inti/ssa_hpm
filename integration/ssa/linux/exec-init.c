/* SPDX-License-Identifier: MIT */
typedef unsigned long u64;
static __attribute__((always_inline)) inline long sc(long n,long x,long y,long z,long q,long v,long w){register long a0 asm("a0")=x,a1 asm("a1")=y,a2 asm("a2")=z,a3 asm("a3")=q,a4 asm("a4")=v,a5 asm("a5")=w,a7 asm("a7")=n;asm volatile("ecall":"+r"(a0):"r"(a1),"r"(a2),"r"(a3),"r"(a4),"r"(a5),"r"(a7):"memory");return a0;}
#define C(n,x,y,z) sc(n,(long)(x),(long)(y),(long)(z),0,0,0)
static void out(const char *s){long n=0;while(s[n])n++;C(64,1,s,n);}
static __attribute__((always_inline)) inline void die(long n){C(93,n,0,0);for(;;);}
static __attribute__((always_inline)) inline void need(int ok){if(!ok){out("SSA EXEC FAIL\n");die(90);}}
static __attribute__((always_inline)) inline long api(long op,long test){
#ifdef REFERENCE
 return op==2?2:op==4?1:0;
#else
 return sc(167,0x535341,op,0,0,test,0);
#endif
}
static __attribute__((always_inline)) inline void work(unsigned long n){asm volatile(".option push\n.option norvc\n1:\n.rept 64\nnop\n.endr\naddi %0,%0,-1\nbnez %0,1b\n.option pop":"+r"(n)::"memory");}
#ifndef NEXT_IMAGE
static __attribute__((noinline,noclone)) void old_leaf(void){work(50);}
static __attribute__((noinline,noclone)) void old_parent(long success){
 old_leaf();
 need(api(4,0)==1);
 char *args[]={success?"/next":"/absent",0};char *env[]={0};
 long rc=sc(221,(long)args[0],(long)args,(long)env,0,0,0);
 if(success){out("SSA EXEC RETURNED SUCCESS PATH FAIL\n");die(91);}
 need(rc==-2);need(api(4,0)==1);old_leaf();asm volatile("":::"memory");
}
static void child(long success){
 int prio=0;need(C(119,0,0,&prio)==0);need(C(146,1000,0,0)==0);
 need(api(1,success?5:7)==0);old_parent(success);
 need(api(2,0)==2);die(0);
}
void _start(void){
 need(C(172,0,0,0)==1);int prio=2;need(C(119,0,1,&prio)==0);
 out("SSA EXEC FIXTURE START\n");
 for(long success=1;success>=0;success--){
  long pid=sc(220,17,0,0,0,0,0);need(pid>=0);if(!pid)child(success);
  int status=0;need(C(260,pid,&status,0)==pid);need(status==0);need(api(3,0)==0);
  out(success?"SSA EXEC SUCCESS CHILD PASS\n":"SSA EXEC ENOENT CHILD PASS\n");
 }
 out("SSA EXEC FIXTURE PASS\n");out("SSA EXEC REGRESSION BEGIN\n");
 char *args[]={"/regress",0};char *env[]={0};sc(221,(long)args[0],(long)args,(long)env,0,0,0);
 out("SSA EXEC REGRESSION EXEC FAIL\n");die(92);
}
#else
static __attribute__((noinline,noclone)) void common(void){work(100);}
static __attribute__((noinline,noclone)) void parent(void){common();asm volatile("":::"memory");}
void _start(void){
 out("SSA EXEC IMAGE B ENTER\n");need(C(174,0,0,0)==1000);need(api(3,0)==0);
 need(api(1,6)==0);parent();need(api(2,0)==2);
 out("SSA EXEC IMAGE B PASS\n");die(0);
}
#endif
