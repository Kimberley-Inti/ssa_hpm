/* SPDX-License-Identifier: MIT
 * Ordinary Linux program. No SSA includes, syscall selector or custom CSR.
 * The same static ELF serves selected, disabled, fork-child, holder and A/B cases.
 */
#include "syscall.h"
extern void class_common(U**,U);
static U data[128],*scalar[8],*stream[8],*irregular[8];
INL void prepare(void){const U ix[]={0,32,8,80,0,9,71,4};for(U i=0;i<8;i++){scalar[i]=data;stream[i]=data+i;irregular[i]=data+ix[i];data[ix[i]]=i+1;}}
#define FN static __attribute__((noinline,noclone))
FN void scalar_parent(void){class_common(scalar,8);asm volatile("":::"memory");}
FN void stream_parent(void){class_common(stream,8);asm volatile("":::"memory");}
FN void irregular_parent(void){class_common(irregular,8);asm volatile("":::"memory");}
FN void replace(void){class_common(irregular,8);char *v[]={"/plain-next","next",0};char *e[]={0};sc(221,(long)v[0],(long)v,(long)e,0,0,0);die(91);}
FN void fail_fork(void){
 class_common(irregular,8);char *v[]={"/missing-auto-program",0};char *e[]={0};need(sc(221,(long)v[0],(long)v,(long)e,0,0,0)==-2);
 class_common(irregular,8);
 long p=sc(220,17,0,0,0,0,0);need(p>=0);
 if(!p){stream_parent();out("PLAIN_FORK_CHILD_UNSELECTED\n");die(0);}
 int status=0;need(C(260,p,&status,0)==p && status==0);class_common(irregular,8);
 asm volatile("":::"memory");
}
FN void terminate(void){class_common(scalar,8);need(C(129,C(172,0,0,0),15,0)==0);die(92);}
FN void hold(void){
 class_common(scalar,8);char token='r';need(C(64,6,&token,1)==1);need(C(63,3,&token,1)==1);class_common(scalar,8);asm volatile("":::"memory");
}
FN void task_common(long role){
 class_common(role==1?scalar:stream,8);if(role==2){long ts[2]={0,1000000};C(101,ts,0,0);}else work(4000);
 class_common(role==1?scalar:stream,8);asm volatile("":::"memory");
}
FN void task_parent(long role){task_common(role);asm volatile("":::"memory");}
#ifdef DYNAMIC_TARGET
extern long shared_entry(long);
extern U shared_anchor(void);
FN void dynamic_parent(void){need(shared_entry(5)==13);U p=shared_anchor();out("PLAIN_DYN_ANCHOR\n");hex(p);asm volatile("":::"memory");}
#endif
__attribute__((noreturn)) void plain_main(U *stack){
 char **argv=(void*)(stack+1);const char *mode=stack[0]>1?argv[1]:"static";
 prepare();
#ifdef NEXT_TARGET
 stream_parent();out("PLAIN_NEXT_OK\n");die(0);
#endif
#ifdef DYNAMIC_TARGET
 dynamic_parent();out("PLAIN_DYNAMIC_OK\n");die(0);
#endif
 if(eq(mode,"static")){scalar_parent();stream_parent();irregular_parent();scalar_parent();out("PLAIN_STATIC_OK\n");die(0);}
 if(eq(mode,"exec")){scalar_parent();replace();}
 if(eq(mode,"fail")){
  /* A real thread would violate the selected single-thread profile. */
  need(sc(220,0x50f00,0,0,0,0,0)==-95);
  fail_fork();out("PLAIN_ENOENT_FORK_OK\n");terminate();
 }
 if(eq(mode,"hold")){hold();out("PLAIN_HOLDER_OK\n");die(0);}
 if(eq(mode,"A")||eq(mode,"B")){
  long role=eq(mode,"A")?1:2;char token='x';if(role==2)need(C(63,3,&token,1)==1);else need(C(64,4,&token,1)==1);
  task_parent(role);out(role==1?"PLAIN_A_OK\n":"PLAIN_B_OK\n");die(0);
 }
 die(93);
}
