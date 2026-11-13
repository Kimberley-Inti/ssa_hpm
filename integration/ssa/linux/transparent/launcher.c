/* SPDX-License-Identifier: MIT — trusted launcher only; target binaries are separate. */
#include "syscall.h"
#define MAGIC 0x535341
INL void policy(U flags,U role,U test){need(sc(167,38,1,0,0,0,0)==0);need(sc(167,MAGIC,6,flags,role,test,0)==0);}
INL void priority(long policy,long prio){int p=prio;need(C(119,0,policy,&p)==0);}
INL long spawn(const char*path,const char*mode,int selected,U flags,U role,U test,int reject){
 long p=sc(220,17,0,0,0,0,0);need(p>=0);
 if(!p){
  priority(role==1?0:1,role==1?0:1);
  if(selected)policy(flags,role,test);
  need(C(144,1000,0,0)==0);need(C(146,1000,0,0)==0);
  if(selected && test==1){need(sc(167,MAGIC,6,flags,role,test,0)==-1);out("LAUNCH_UNPRIV_ARM_DENIED\n");}
  char *v[]={(char*)path,(char*)mode,0};char *e[]={0};long error=sc(221,(long)path,(long)v,(long)e,0,0,0);
  if(reject){need(error==-1);out("LAUNCH_SETID_REJECT_OK\n");die(0);}
  out("LAUNCH_EXEC_FAIL\n");die(94);
 }
 out("LAUNCH_PID\n");hex(p);return p;
}
INL void waitp(long p,int expected){int s=0;need(C(260,p,&s,0)==p);need(s==expected);}
INL void pipes(int fd[2]){need(C(59,fd,0,0)==0);}
void _start(void){
 need(C(172,0,0,0)==1);priority(1,2);out("AUTO_SUITE_START\n");
 long p=spawn("/plain","static",1,6,0,1,0);waitp(p,0);out("AUTO_STATIC_DONE\n");
 p=spawn("/plain","exec",1,6,0,2,0);waitp(p,0);out("AUTO_EXEC_DONE\n");
 p=spawn("/plain","fail",1,6,0,3,0);waitp(p,15);out("AUTO_FAIL_FORK_SIGNAL_DONE\n");
 p=spawn("/plain","static",0,0,0,6,0);waitp(p,0);out("AUTO_DISABLED_DONE\n");
 p=spawn("/setid","static",1,6,0,7,1);waitp(p,0);out("AUTO_SETID_DONE\n");
 int fd[2],ready[2];pipes(fd);pipes(ready);need(fd[0]==3 && fd[1]==4 && ready[0]==5 && ready[1]==6);
 long h1=spawn("/plain","hold",1,6,0,9,0);char t;need(C(63,5,&t,1)==1);
 long h2=spawn("/plain","hold",1,6,0,9,0);need(C(63,5,&t,1)==1);
 p=spawn("/plain","static",1,6,0,10,0);waitp(p,0);need(C(64,4,"xx",2)==2);waitp(h1,0);waitp(h2,0);
 for(int i=3;i<7;i++)C(57,i,0,0);out("AUTO_EXHAUST_DONE\n");
 pipes(fd);need(fd[0]==3 && fd[1]==4);
 long b=spawn("/plain","B",1,6,2,11,0),a=spawn("/plain","A",1,6,1,11,0);
 waitp(b,0);waitp(a,0);C(57,3,0,0);C(57,4,0,0);out("AUTO_DUAL_DONE\n");
 p=spawn("/plain-dynamic","dynamic",1,0,0,12,0);waitp(p,0);out("AUTO_DYNAMIC_DONE\n");
 p=spawn("/plain-capacity","capacity",1,4,0,13,0);waitp(p,0);out("AUTO_CAPACITY_DONE\n");
 out("AUTO_SUITE_END\n");char *v[]={"/class-regress",0};char *e[]={0};sc(221,(long)v[0],(long)v,(long)e,0,0,0);die(96);
}
