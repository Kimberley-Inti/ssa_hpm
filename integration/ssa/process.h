#ifndef SSA_PROCESS_H
#define SSA_PROCESS_H
#include <stdint.h>
/* Single-hart privileged scheduler ABI. Call only inside a trap, with interrupts
 * masked and resident writable physical pools. Pool initialization zeros all
 * dictionary buckets and metadata, sets next_id=1. No Linux virtual ABI yet. */
typedef struct { uintptr_t base; uint64_t cycle,instret,time,off_cycle,off_instret,off_time; unsigned state; } SSAProcess;
enum {SSA_NEW,SSA_RUNNING,SSA_PAUSED,SSA_EXITED};
static inline uint64_t ssa_cycle(void){uint64_t x;asm volatile("csrr %0,mcycle":"=r"(x));return x;}
static inline uint64_t ssa_instret(void){uint64_t x;asm volatile("csrr %0,minstret":"=r"(x));return x;}
static inline uint64_t ssa_time(void){return *(volatile uint64_t *)0x200bff8UL;}
static inline void ssa_select(uintptr_t base){
#ifndef REFERENCE
 asm volatile("csrw 0x800,%0"::"r"(base):"memory");
#else
 (void)base;
#endif
}
static inline int ssa_scheduler_valid(uintptr_t expected){
#ifndef REFERENCE
 uint64_t selected,status;asm volatile("csrr %0,0x800":"=r"(selected));
 asm volatile("csrr %0,0xcc0":"=r"(status));
 return selected==expected && (status&255)!=0 && !(status&256);
#else
 (void)expected;return 1;
#endif
}
/* Hart trap depth is deliberately never saved/restored with a process. */
static inline int ssa_pause(SSAProcess *p){
 if(p->state!=SSA_RUNNING || !ssa_scheduler_valid(p->base))return -1;
 p->cycle=ssa_cycle();p->instret=ssa_instret();p->time=ssa_time();
 ssa_select(0);p->state=SSA_PAUSED;return 0;
}
static inline int ssa_resume(SSAProcess *p){
 if((p->state!=SSA_NEW && p->state!=SSA_PAUSED) || !ssa_scheduler_valid(0))return -1;
 volatile uint64_t *meta=(void *)(p->base-64);
#ifndef REFERENCE
 if(meta[0]>256 || (p->state==SSA_NEW && (meta[0]||meta[2])))return -1;
#endif
 if(p->state==SSA_PAUSED){
 uint64_t c=ssa_cycle()-p->cycle,i=ssa_instret()-p->instret,t=ssa_time()-p->time;
 p->off_cycle+=c;p->off_instret+=i;p->off_time+=t;
#if !defined(REFERENCE) && !defined(LEGACY_SWITCH)
 /* Rebase every open frame, including ancestors. Spill depth remains in pool. */
 for(uint64_t n=1;n<=meta[0];++n){volatile uint64_t *f=(void *)(p->base-64-n*64);f[1]+=c;f[2]+=i;f[3]+=t;}
#endif
 }
 (void)meta;ssa_select(p->base);p->state=SSA_RUNNING;return 0;
}
static inline int ssa_exit(SSAProcess *p){
 if(p->state!=SSA_PAUSED)return -1;
#ifndef REFERENCE
 volatile uint64_t *m=(void *)(p->base-64);if(m[0]||m[2])return -1;
#endif
 p->state=SSA_EXITED;return 0;
}
#endif
