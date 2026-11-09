#include <stdint.h>
#include <stddef.h>
#include "process.h"
extern void ssa_process_entry(void);
extern volatile uint64_t tohost,fromhost;
static SSAProcess proc[2];
static uint64_t stacks[2][2048] __attribute__((aligned(16)));
static uint64_t *frames[2],*main_frame;
static int current,phase,heavy;
static volatile uint64_t bad,sink;
#ifndef REFERENCE
static uint64_t a_count[2],off[2],frozen;
#endif
#ifndef REFERENCE
static uint64_t fingerprint(uintptr_t b){
 uint64_t h=0;volatile uint64_t *m=(void *)(b-64),*r=(void *)(b-37748736);
 for(unsigned n=0;n<48;n++)h=h*31+r[n];
 for(unsigned n=0;n<24;n++)h=h*31+((volatile uint64_t *)(b-192))[n];
 return h+m[0]+m[1];
}
#endif
__attribute__((noinline)) static void common(int id){
 if(id==1)for(int n=0;n<(heavy?700:7);n++)sink+=n;
 asm volatile("ecall":::"memory");
 sink+=id+1;
}
__attribute__((noinline)) static void parent(int id){common(id);}
static void task(int id){parent(id);asm volatile("ecall":::"memory");for(;;){}}
uint64_t *ssa_process_dispatch(uint64_t *f){
 uint64_t cause;asm volatile("csrr %0,mcause":"=r"(cause));
 if(cause!=11){bad|=1;f[30]+=4;return f;}
 f[30]+=4;
 if(phase==0){main_frame=f;current=0;phase=1;
#ifndef REFERENCE
 volatile uint64_t *m=(void *)(proc[0].base-64);m[0]=1;
 if(ssa_resume(&proc[0])!=-1)bad|=8192;
 m[0]=0;
#endif
 if(ssa_resume(&proc[0]))bad|=2;
 if(ssa_resume(&proc[0])!=-1)bad|=16384;
 return frames[0];}
 frames[current]=f;
 if(ssa_pause(&proc[current]))bad|=4;
 if(phase==1){
#ifndef REFERENCE
 if(ssa_exit(&proc[0])!=-1)bad|=32768;
#endif
#ifndef REFERENCE
 if(*(volatile uint64_t *)(proc[0].base-64)!=2)bad|=8;
 frozen=fingerprint(proc[0].base);
#endif
 current=1;
 }else if(phase==2){
#ifndef REFERENCE
 if(fingerprint(proc[0].base)!=frozen)bad|=16;
#endif
 current=0;
 }else if(phase==3){if(ssa_exit(&proc[0]))bad|=32;current=1;}
 else {if(ssa_exit(&proc[1]))bad|=64;phase=5;return main_frame;}
 ++phase;if(ssa_resume(&proc[current]))bad|=128;return frames[current];
}
static void print(const char *s){size_t n=0;while(s[n])n++;volatile uint64_t c[8] __attribute__((aligned(64)))={64,1,(uintptr_t)s,n};asm volatile("fence rw,rw":::"memory");tohost=(uintptr_t)c;while(!fromhost){}fromhost=0;}
static void number(uint64_t x){char s[18];for(int n=0;n<16;n++)s[n]="0123456789abcdef"[(x>>(60-4*n))&15];s[16]='\n';s[17]=0;print(s);}
int main(void){
 asm volatile("csrw mtvec,%0"::"r"(ssa_process_entry));
 for(heavy=0;heavy<2;heavy++){
 for(int id=0;id<2;id++){
 uintptr_t b=id?0x8c000000UL:0x88000000UL;
 proc[id]=(SSAProcess){.base=b,.state=SSA_NEW};
#ifndef REFERENCE
 volatile uint64_t *m=(void *)(b-64);for(int n=0;n<8;n++)m[n]=0;m[1]=1;
 /* This directed program can reach exactly these two buckets. Production
 * initialization must zero the entire dictionary before first activation. */
 volatile uint32_t *d=(void *)(b-1065024);
 d[((uintptr_t)parent>>1)&262143]=0;
 d[(((uintptr_t)common>>1)^1)&262143]=0;
#endif
 uint64_t *f=&stacks[id][2048-36];for(int n=0;n<36;n++)f[n]=0;
 asm volatile("mv %0,gp":"=r"(f[1]));asm volatile("mv %0,tp":"=r"(f[2]));
 f[8]=id;f[30]=(uintptr_t)task;f[31]=0x1800;frames[id]=f;
 }
 phase=0;asm volatile("ecall":::"memory");
 if(phase!=5 || proc[0].state!=SSA_EXITED || proc[1].state!=SSA_EXITED)bad|=256;
 if(ssa_resume(&proc[0])!=-1 || ssa_exit(&proc[0])!=-1)bad|=512;
#ifndef REFERENCE
 for(int id=0;id<2;id++){
 volatile uint64_t *m=(void *)(proc[id].base-64),*r=(void *)(proc[id].base-37748736);
 if(m[0]||m[1]!=3||m[2])bad|=1024;
 if(!r[18] || !r[19] || r[19]<r[35] || !r[34] || !proc[id].off_cycle)bad|=65536;
 print(id?"B parent cycle/instret/time, common cycle/instret/time, excluded cycle/instret/time:\n":"A parent cycle/instret/time, common cycle/instret/time, excluded cycle/instret/time:\n");
 number(r[18]);number(r[19]);number(r[20]);number(r[34]);number(r[35]);number(r[36]);
 number(proc[id].off_cycle);number(proc[id].off_instret);number(proc[id].off_time);
 if(r[16]!=(uintptr_t)parent || r[32]!=(uintptr_t)common || r[33]!=1)bad|=2048;
 }
 a_count[heavy]=((volatile uint64_t *)(proc[0].base-37748736))[35];
 off[heavy]=proc[0].off_instret;
#endif
 }
#ifndef REFERENCE
 print("A short/long instret and off-CPU instret:\n");number(a_count[0]);number(a_count[1]);number(off[0]);number(off[1]);
 if(a_count[0]!=a_count[1] || off[1]<=off[0])bad|=4096;
#endif
 if(bad){print("SSA FAIL process mask:\n");number(bad);return 42;}
 print("SSA PASS: two pools, open-frame resume, isolation, exit and off-CPU exclusion\n");return 0;
}
