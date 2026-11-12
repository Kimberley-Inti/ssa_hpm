#include <stdint.h>
#include <stddef.h>
#define BASE 0x88000000UL
#ifdef CACHE_EVENT
#define EVENT_FIELD " cache="
#define EVENT_SELECTOR 0x202
#else
#define EVENT_FIELD " dtlb="
#define EVENT_SELECTOR 0x1002
#endif
#define RECORDS ((volatile Record *)(BASE - 36UL*1024*1024))
#define DICT ((volatile uint32_t *)(BASE - 1065024))
#define META ((volatile uint64_t *)(BASE - 64))
typedef struct {
    uint64_t callee, parent, cycles, insts, time;
    uint64_t reserved[6], next, reserved_seventh, padding[3];
} Record;
_Static_assert(sizeof(Record)==128, "record size");
extern volatile uint64_t tohost, fromhost;
static void write_line(const char *s) {
    size_t n=0; while(s[n]) ++n;
    volatile uint64_t cmd[8] __attribute__((aligned(64)))={64,1,(uintptr_t)s,n,0,0,0,0};
    asm volatile("fence rw,rw" ::: "memory");
    tohost=(uintptr_t)cmd;
    while(!fromhost) {}
    fromhost=0;
    asm volatile("fence rw,rw" ::: "memory");
}
// One HTIF transaction per line keeps serial RTL simulation practical.
static void print(const char *s) {
    static char line[256];
    static unsigned used;
    while(*s) {
        char c=*s++;
        line[used++]=c;
        if(c=='\n' || used==sizeof(line)-1) {
            line[used]=0;
            write_line(line);
            used=0;
        }
    }
}
static void number(uint64_t x) {
    char s[19]; s[0]='0'; s[1]='x';
    for(int i=0;i<16;++i) s[2+i]="0123456789abcdef"[(x >> (60-4*i))&15];
    s[18]=0; print(s);
}

static uint64_t pgd[512] __attribute__((aligned(4096)));
static uint64_t pmd[512] __attribute__((aligned(4096)));
static uint64_t pte[512] __attribute__((aligned(4096)));
static inline uint64_t hpm(void){uint64_t x;asm volatile("csrr %0,0xc03":"=r"(x));return x;}
__attribute__((noinline)) void event_common(uint64_t pages){
 for(uint64_t i=0;i<pages;i++){uint64_t x;asm volatile("ld %0,0(%1)":"=r"(x):"r"(0x40000000UL+i*4096):"memory");asm volatile(""::"r"(x));}
 asm volatile("fence rw,rw":::"memory");
}
__attribute__((noinline)) void warm_parent(void){
#ifdef SWAP_CONTEXT
 event_common(128);
#else
 event_common(1);
#endif
 asm volatile("":::"memory");
}
__attribute__((noinline)) void cold_parent(void){
#ifdef SWAP_CONTEXT
 event_common(1);
#else
 event_common(128);
#endif
 asm volatile("":::"memory");
}
static void supervisor(void){
 event_common(1); /* warm data before enabling */
 META[1]=1;
 asm volatile("csrw 0x5c0,%0;csrw 0x800,%1"::"r"(2UL),"r"(BASE):"memory");
 uint64_t a=hpm();warm_parent();uint64_t b=hpm();cold_parent();uint64_t mid=hpm();cold_parent();uint64_t c=hpm();
 asm volatile("csrw 0x800,zero":::"memory");
 uint64_t lo=RECORDS[2].reserved[0],hi=RECORDS[4].reserved[0];
 print("SSA_EVENT_GLOBAL before=");number(a);print(" warm=");number(b);print(" mid=");number(mid);print(" cold=");number(c);print("\n");
 for(uint64_t i=1;i<META[1];i++){
  print("SSA_EVENT_RECORD id=");number(i);print(" parent=");number(RECORDS[i].parent);print(" callee=");number(RECORDS[i].callee);print(EVENT_FIELD);number(RECORDS[i].reserved[0]);print("\n");
 }
 uint64_t mask=(1UL<<40)-1;
 int ok=META[0]==0 && META[1]==5 && lo<=6 && hi>=100 && hi<=270 && ((c-b)&mask)>=hi && ((c-b)&mask)<=hi+8 && RECORDS[1].reserved[0]>=lo && RECORDS[3].reserved[0]>=hi;
#ifdef CACHE_EVENT
 ok=META[0]==0 && META[1]==5 && hi>=128 && hi>lo+64 && ((c-b)&mask)>=hi && ((c-b)&mask)<hi+128 && RECORDS[1].reserved[0]>=lo && RECORDS[3].reserved[0]>=hi;
#endif
#ifdef COUNTER_WRAP
 ok=ok && c<a;
#endif
 print(ok?"SSA PASS: selected event source, parent contexts, interval boundary\n":"SSA NEGATIVE: wrong selector or swapped contexts detected\n");
 register unsigned long a0 asm("a0")=ok?0:42;asm volatile("ecall"::"r"(a0));__builtin_unreachable();
}
int main(void){
 pgd[2]=(0x80000000UL>>2)|0xcf;
 pgd[1]=((uintptr_t)pmd>>2)|1;
 pmd[0]=((uintptr_t)pte>>2)|1;
 for(uint64_t i=0;i<512;i++)pte[i]=((0x81000000UL+i*4096)>>2)|0xcf;
 uint64_t satp=(8UL<<60)|((uintptr_t)pgd>>12);
 asm volatile("csrw pmpaddr0,%0;csrw pmpcfg0,%1;csrw mcounteren,%2;csrw mcountinhibit,zero"::"r"(~0UL),"r"(15UL),"r"(15UL):"memory");
#ifdef WRONG_SELECTOR
 unsigned long sel=0;
#else
 unsigned long sel=EVENT_SELECTOR;
#endif
#ifdef COUNTER_WRAP
 unsigned long initial=(1UL<<40)-
#ifdef CACHE_EVENT
 128;
#else
 8;
#endif
#else
 unsigned long initial=0;
#endif
 asm volatile("csrw 0x323,%0;csrw 0xb03,%1;csrw satp,%2;sfence.vma;csrw mstatus,%3;csrw mepc,%4;mret"::"r"(sel),"r"(initial),"r"(satp),"r"(0x800UL),"r"(supervisor):"memory");__builtin_unreachable();
}
