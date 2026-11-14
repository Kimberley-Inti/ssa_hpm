/* SPDX-License-Identifier: MIT */
#define _start unused_stage4_entry
#include "process-init.c"
#undef _start
#define LEAF(n) static __attribute__((noinline,noclone)) void leaf##n(void){asm volatile("nop; nop; nop; nop":::"memory");}
LEAF(00)
LEAF(01)
LEAF(02)
LEAF(03)
LEAF(04)
LEAF(05)
LEAF(06)
LEAF(07)
LEAF(08)
LEAF(09)
LEAF(10)
LEAF(11)
LEAF(12)
LEAF(13)
LEAF(14)
LEAF(15)
LEAF(16)
LEAF(17)
LEAF(18)
LEAF(19)
LEAF(20)
LEAF(21)
LEAF(22)
LEAF(23)
LEAF(24)
LEAF(25)
LEAF(26)
LEAF(27)
LEAF(28)
LEAF(29)
LEAF(30)
LEAF(31)
LEAF(32)
LEAF(33)
LEAF(34)
LEAF(35)
LEAF(36)
LEAF(37)
LEAF(38)
LEAF(39)
static void (*const leaves[])(void)={leaf00,leaf01,leaf02,leaf03,leaf04,leaf05,leaf06,leaf07,leaf08,leaf09,leaf10,leaf11,leaf12,leaf13,leaf14,leaf15,leaf16,leaf17,leaf18,leaf19,leaf20,leaf21,leaf22,leaf23,leaf24,leaf25,leaf26,leaf27,leaf28,leaf29,leaf30,leaf31,leaf32,leaf33,leaf34,leaf35,leaf36,leaf37,leaf38,leaf39};
static __attribute__((noinline,noclone)) void export_parent(void){
 for(unsigned int i=0;i<40;i++)leaves[i]();
 leaves[0]();asm volatile("":::"memory");
}
static __attribute__((noinline,noclone)) void export_small(void){leaf00();asm volatile("":::"memory");}
static __attribute__((noinline,noclone)) void export_open(void){
 leaf00();require(api(2,0,0,0)==-16);die(0);
}
static void child(long test){
 priority(0,0);require(C(146,1000,0,0)==0);
 require(api(1,(test==11 || test==14)?2:0,0,test)==0);
 require(api(5,0,0,0)==-16);require(api(5,1,0,0)==-22);
 if(test==11){export_parent();require(api(2,0,0,0)==41);die(0);}
 if(test==12)export_small();
 if(test==14)export_open();
 require(api(2,0,0,0)==(test==12?2:0));
 require(api(5,0,0,0)==0);require(api(5,0,0,0)==-114);
 require(api(1,0,0,test)==-16);die(0);
}
void _start(void){
 require(C(172,0,0,0)==1);priority(1,2);out("SSA_RESULT_EXPORT_SUITE_START\n");
 for(long test=11;test<=14;test++){
  long pid=fork_child();require(pid>=0);if(!pid)child(test);wait_child(pid,0);
  require(api(3,0,0,0)==0);out("SSA RESULT CASE PASS\n");
 }
 out("SSA_RESULT_EXPORT_SUITE_END\n");
#ifdef CACHE_END
 C(142,0xfee1dead,672274793,0x4321fedc);for(;;)C(124,0,0,0);
#endif
 char *args[]={"/lifecycle",0};char *env[]={0};
 sc(221,(long)args[0],(long)args,(long)env,0,0,0);die(93);
}
