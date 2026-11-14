#ifdef CACHE_EVENT
#define ABI_HPM_SELECTOR 0x202UL
#else
#define ABI_HPM_SELECTOR 0x1002UL
#endif
#include <stdint.h>
#include <stddef.h>
#define BASE 0x88000000UL
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
#ifdef REFERENCE
extern void sc_event(uint64_t, uint64_t, uint64_t);
static void event(int call, uintptr_t target) { sc_event(BASE,call,target); }
#define ENTER(f) event(1,(uintptr_t)(f))
#define LEAVE() event(0,0)
#else
#define ENTER(f) ((void)0)
#define LEAVE() ((void)0)
#endif
volatile uint64_t result, depth_a, depth_b;
__attribute__((noinline)) void common(void) { ENTER(common); for(volatile int i=0;i<512;++i) asm volatile("nop"); result+=7; LEAVE(); }
__attribute__((noinline)) void parent_a(void) {
    ENTER(parent_a); common(); depth_a=META[0]; common(); LEAVE();
}
__attribute__((noinline)) void parent_b(void) {
    ENTER(parent_b); common(); depth_b=META[0]; LEAVE();
}
__attribute__((noinline,section(".collision_a"))) void collision_a(void) {
    ENTER(collision_a); result+=1; LEAVE();
}
__attribute__((noinline,section(".collision_b"))) void collision_b(void) {
    ENTER(collision_b); result+=2; LEAVE();
}
static void enable(void) {
#ifdef EVENT_ABI
    asm volatile("csrw 0x323,%0;csrw 0xb03,zero;csrw 0x5c0,%1"::"r"(ABI_HPM_SELECTOR),"r"(2UL):"memory");
#endif
#ifndef REFERENCE
    asm volatile("csrw 0x800,%0" :: "r"(BASE) : "memory");
#endif
}
static void disable(void) {
#ifndef REFERENCE
    asm volatile("csrw 0x800,zero" ::: "memory");
#endif
}
static uint64_t find(uint64_t parent, uintptr_t pc) {
    for(uint64_t i=1;i<META[1];++i)
        if(RECORDS[i].callee==pc && RECORDS[i].parent==parent) return i;
    return 0;
}
static void init(void) {
    META[0]=0; META[1]=1; META[2]=0; META[3]=0;
    // Only buckets reachable in this bounded test; no assumption about DRAM
    // initial values. Production loaders must zero the entire dictionary.
    uintptr_t funcs[]={(uintptr_t)common,(uintptr_t)parent_a,(uintptr_t)parent_b,
                      (uintptr_t)collision_a,(uintptr_t)collision_b};
    for(int f=0;f<5;++f) for(int p=0;p<16;++p)
        DICT[((funcs[f]>>1)^p)&262143]=0;
    result=0;
    asm volatile("fence rw,rw" ::: "memory");
}
static int check(void) {
    if(result!=46 || META[0]!=0 || META[2]!=0 || META[3]!=0) return 1;
    if(META[1]!=7 || depth_a!=1 || depth_b!=1) return 2;
    uint64_t a=find(0,(uintptr_t)parent_a), b=find(0,(uintptr_t)parent_b);
    uint64_t ca=find(a,(uintptr_t)common), cb=find(b,(uintptr_t)common);
    uint64_t x=find(0,(uintptr_t)collision_a), y=find(0,(uintptr_t)collision_b);
    if(!a||!b||!ca||!cb||ca==cb||!x||!y||x==y) return 3;
    if(RECORDS[ca].insts<=RECORDS[cb].insts) return 4;
    if(RECORDS[a].insts<=RECORDS[ca].insts || RECORDS[b].insts<=RECORDS[cb].insts) return 5;
    if(!RECORDS[ca].time || !RECORDS[cb].time) return 8;
    if(DICT[((uintptr_t)collision_a>>1)&262143]!=y || RECORDS[y].next!=x) return 6;
    for(uint64_t i=1;i<7;++i)
        if(!RECORDS[i].cycles || !RECORDS[i].insts) return 7;
    return 0;
}
#ifdef ABI
extern int abi_probe(void);
extern void alt_leaf(void);
int main(void) {
    init();
    for(int p=0;p<4;++p) {
        DICT[(((uintptr_t)abi_probe>>1)^p)&262143]=0;
        DICT[(((uintptr_t)alt_leaf>>1)^p)&262143]=0;
    }
    enable(); int status=abi_probe(); disable();
    if(status) return status;
#ifndef REFERENCE
    if(META[0]!=0 || META[1]!=3 || RECORDS[1].callee!=(uintptr_t)abi_probe ||
       RECORDS[2].callee!=(uintptr_t)alt_leaf || RECORDS[2].parent!=1) return 22;
#endif
    print("SSA PASS: shadow registers, x5 call/return, ordinary JALR jump\n");
    return 0;
}
#elif defined(BOUNDARY)
__attribute__((noinline)) void recursive(int n) {
    ENTER(recursive);
    if(n) recursive(n-1);
    ++result;
    LEAVE();
}
int main(void) {
    init();
    for(int p=0;p<257;++p) DICT[(((uintptr_t)recursive>>1)^p)&262143]=0;
    enable(); recursive(257); disable();
    if(result!=258 || META[0]!=0 || META[1]!=257 || META[2]!=0 || META[3]!=0) return 11;
    for(int i=1;i<=256;++i) {
        if(RECORDS[i].callee!=(uintptr_t)recursive || RECORDS[i].parent!=(uint64_t)i-1 ||
           !RECORDS[i].cycles || !RECORDS[i].insts) return 12;
    }
    print("SSA PASS: 258 calls, 256 frames, overflow folds into top, full unwind\n");
    META[1]=262144;
    DICT[((uintptr_t)collision_a>>1)&262143]=0;
    enable(); collision_a(); disable();
    if(META[0]!=0 || META[1]!=262144 || META[2]!=0 || META[3]!=1 ||
       DICT[((uintptr_t)collision_a>>1)&262143]!=0) return 13;
    print("SSA PASS: record exhaustion bounded, error recorded, parent restored\n");
    return 0;
}
#else
int main(void) {
    init();
    enable();
    parent_a(); parent_a(); parent_b(); parent_b();
    collision_a(); collision_b();
    asm volatile("jal ra, collision_a" ::: "ra", "t0", "t1", "t2", "t3", "t4", "t5", "t6",
                 "a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7", "memory");
    disable();
    int status=check();
    print("SSA records (id callee parent cycle instret time next):\n");
    for(uint64_t i=1;i<META[1] && i<16;++i) {
        number(i); print(" "); number(RECORDS[i].callee); print(" ");
        number(RECORDS[i].parent); print(" "); number(RECORDS[i].cycles); print(" ");
        number(RECORDS[i].insts); print(" "); number(RECORDS[i].time); print(" ");
        number(RECORDS[i].next); print("\n");
    }
    print("SSA result="); number(result); print(" status="); number(status); print("\n");
    if(!status) print("SSA PASS: nested, parents, reuse, restore, collision, counters\n");
    return status;
}

#endif
