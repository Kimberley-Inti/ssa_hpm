/* SPDX-License-Identifier: MIT */
#define _start unused_stage4_entry
#include "process-init.c"
#undef _start
extern void class_common(u64 **,u64);
asm(".option push\n.option norelax\n.text\n.globl class_common, class_access\n.type class_common,@function\nclass_common:\nbeqz a1,2f\n1: ld t0,0(a0)\nclass_access:\nld t1,0(t0)\naddi a0,a0,8\naddi a1,a1,-1\nbnez a1,1b\n2: ret\n.size class_common,.-class_common\n.option pop");
static u64 data[4096];
static u64 *scalar[8],*stream[8],*irregular[8];
static void prepare(void){
 const unsigned ix[]={0,32,8,80,0,9,71,4};
 for(unsigned i=0;i<8;i++){scalar[i]=data;stream[i]=data+i;irregular[i]=data+ix[i];data[ix[i]]=i+1;}
}
static __attribute__((noinline,noclone)) void scalar_parent(void){class_common(scalar,8);asm volatile("":::"memory");}
static __attribute__((noinline,noclone)) void stream_parent(void){class_common(stream,8);asm volatile("":::"memory");}
static __attribute__((noinline,noclone)) void irregular_parent(void){class_common(irregular,8);asm volatile("":::"memory");}
static __attribute__((noinline,noclone)) void task_common(long role){
 class_common(role==1?scalar:stream,8);
 if(role==2){long ts[2]={0,1000000};C(101,ts,0,0);}else work(4000);
 class_common(role==1?scalar:stream,8);asm volatile("":::"memory");
}
static __attribute__((noinline,noclone)) void task_parent(long role){task_common(role);asm volatile("":::"memory");}
static void dual(long role,int *fd){
 priority(role==2?1:0,role==2?1:0);prepare();require(C(146,1000,0,0)==0);
 require(api(1,6,role,9)==0);
 char token='x';if(role==2)require(C(63,fd[0],&token,1)==1);else require(C(64,fd[1],&token,1)==1);
 task_parent(role);require(api(2,0,0,0)>=3);die(0);
}
static __attribute__((noinline,noclone)) void exec_open(int success){
 class_common(irregular,8);
 char *args[]={success?"/classnext":"/absent-class-image",0};char *env[]={0};
 long result=sc(221,(long)args[0],(long)args,(long)env,0,0,0);
 require(!success && result==-2);
 class_common(irregular,8);asm volatile("":::"memory");
}
static void simple(unsigned kind){
 prepare();require(C(146,1000,0,0)==0);require(api(1,6,0,8)==0);
 if(kind==0){scalar_parent();stream_parent();irregular_parent();scalar_parent();require(api(2,0,0,0)==6);require(api(5,0,0,0)==0);}
 if(kind==1){scalar_parent();exec_open(1);die(91);}
 if(kind==2){exec_open(0);require(api(2,0,0,0)==2);}
 if(kind==3){require(api(2,0,0,0)==0);require(api(5,0,0,0)==0);}
 die(0);
}
void _start(void){
#ifdef CLASS_NEXT
 require(api(3,0,0,0)==0);prepare();require(api(1,6,0,8)==0);stream_parent();require(api(2,0,0,0)==2);die(0);
#else
 require(C(172,0,0,0)==1);priority(1,2);out("SSA_CLASSIFICATION_SUITE_START\n");
 for(unsigned kind=0;kind<4;kind++){
  long p=fork_child();require(p>=0);if(!p)simple(kind);wait_child(p,0);
  require(api(3,0,0,0)==0);out("SSA_CLASSIFICATION_LIFECYCLE_CASE\n");
 }
 int fd[2];require(C(59,fd,0,0)==0);
 long b=fork_child();require(b>=0);if(!b)dual(2,fd);
 long a=fork_child();require(a>=0);if(!a)dual(1,fd);
 wait_child(b,0);wait_child(a,0);require(api(3,0,0,0)==0);
 out("SSA_CLASSIFICATION_SUITE_END\n");
 C(142,0xfee1dead,672274793,0x4321fedc);for(;;)C(124,0,0,0);
#endif
}
