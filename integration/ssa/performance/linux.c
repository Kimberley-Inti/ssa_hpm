/* SPDX-License-Identifier: MIT. Measurement target; explicitly uses manual ABI. */
#include "../linux/transparent/syscall.h"
#include "workload.h"
#define MAGIC 0x535341
#define RD(c) ({uint64_t x;asm volatile("csrr %0," #c:"=r"(x));x;})
typedef struct {U c,i,t;} Stamp;
INL Stamp stamp(void){asm volatile("fence rw,rw":::"memory");Stamp s={RD(0xc00),RD(0xc02),RD(0xc01)};return s;}
INL char*num(char*p,U x){*p++=' ';for(int i=60;i>=0;i-=4)*p++="0123456789abcdef"[(x>>i)&15];return p;}
INL void emit(const char*tag,U mode,U kind,U rep,Stamp a,Stamp b,U x){char s[256],*p=s;while(*tag)*p++=*tag++;U v[]={mode,kind,rep,a.c,b.c,a.i,b.i,a.t,b.t,x};for(unsigned j=0;j<10;j++)p=num(p,v[j]);*p++='\n';*p=0;out(s);}
INL long api(U op,U flags){return sc(167,MAGIC,op,flags,0,op==1?14:0,0);}
INL void priority(int policy,int n){need(C(119,0,policy,&n)==0);}
INL void waitp(long p){int x;need(C(260,p,&x,0)==p && x==0);}
INL long spawn_target(const char*arg,int autom){
 long p=sc(220,17,0,0,0,0,0);need(p>=0);
 if(!p){priority(arg[0]=='A'?0:1,arg[0]=='A'?0:1);if(autom){Stamp a=stamp();need(sc(167,38,1,0,0,0,0)==0);need(sc(167,MAGIC,6,6,arg[0]=='A'?1:arg[0]=='B'?2:0,14,0)==0);Stamp b=stamp();emit("SSA_PERF_PHASE_ARM",5,arg[0]=='A'?1:arg[0]=='B'?2:0,0,a,b,C(172,0,0,0));}need(C(144,1000,0,0)==0);need(C(146,1000,0,0)==0);char*v[]={"/perf-target",(char*)arg,0};char*e[]={0};sc(221,(long)v[0],(long)v,(long)e,0,0,0);die(91);}
 return p;
}
INL void finish(void){C(142,0xfee1dead,672274793,0x4321fedc);for(;;)C(124,0,0,0);}
__attribute__((noinline)) static void dual_inner(int role){
 if(role==2){long ts[2]={0,1000000};need(C(101,ts,0,0)==0);}else work(4000);
 sink=bench_work(role==1?3:4);asm volatile("":::"memory");
}
__attribute__((noinline)) static void dual_outer(int role){dual_inner(role);asm volatile("":::"memory");}
void plain_main(U*sp){
 const char *arg=sp[0]>1?(const char*)sp[2]:"init";
 if(C(172,0,0,0)==1){
  priority(1,2);out("SSA_PERF_LINUX_START\n");
  waitp(spawn_target("0",0));waitp(spawn_target("1",0));waitp(spawn_target("3",0));waitp(spawn_target("4",0));waitp(spawn_target("6",0));waitp(spawn_target("5",1));
  int fd[2];need(C(59,fd,0,0)==0);need(fd[0]==3 && fd[1]==4);
  long b=spawn_target("B",1),a=spawn_target("A",1);waitp(b);waitp(a);C(57,3,0,0);C(57,4,0,0);
  out("SSA_PERF_LINUX_DONE\n");finish();
 }
 if(eq(arg,"A") || eq(arg,"B")){
  int role=arg[0]=='A'?1:2;char token='x';
  for(unsigned j=0;j<4096;j++)data[j]=j*17+3;
  if(role==2)need(C(63,3,&token,1)==1);else need(C(64,4,&token,1)==1);
  dual_outer(role);die(0);
 }
 if(eq(arg,"next")){
  sink=bench_work(0);out("SSA_PERF_EXEC_NEXT\n");die(0);
 }
 U mode=arg[0]-'0';need(mode==0||mode==1||mode==3||mode==4||mode==5||mode==6);
 Stamp init0=stamp(),init1;
 if(mode && mode!=5)need(api(1,mode==1?0:mode==3?2:mode==6?6:4)==0);
 init1=stamp();emit("SSA_PERF_PHASE_INIT",mode,0,0,init0,init1,0);
 for(U rep=0;rep<5;rep++){Stamp a=stamp(),b=stamp();emit("SSA_PERF_CAL",mode,0,rep,a,b,0);}
 for(U kind=0;kind<5;kind++){
  for(U j=0;j<4096;j++)data[j]=j*17+3;
  sink=bench_work(kind);
  for(U rep=0;rep<5;rep++){
   Stamp a=stamp();U x=bench_work(kind);Stamp b=stamp();sink=x;
   emit("SSA_PERF",mode,kind,rep,a,b,x);
  }
 }
 // Failed exec returns to the original image; end-to-end user boundary.
 Stamp a=stamp();char*v[]={"/missing-performance-image",0};char*e[]={0};long error=sc(221,(long)v[0],(long)v,(long)e,0,0,0);Stamp b=stamp();need(error==-2);
 emit("SSA_PERF_PHASE_FAIL_EXEC",mode,0,0,a,b,(U)error);
 if(mode && mode!=5){a=stamp();need(api(2,0)>=1);b=stamp();emit("SSA_PERF_PHASE_STOP",mode,0,0,a,b,0);a=stamp();need(api(5,0)==0);b=stamp();emit("SSA_PERF_PHASE_EXPORT",mode,0,0,a,b,0);}
 if(mode==5){char*n[]={"/perf-target","next",0};sc(221,(long)n[0],(long)n,(long)e,0,0,0);die(92);}
 die(0);
}
