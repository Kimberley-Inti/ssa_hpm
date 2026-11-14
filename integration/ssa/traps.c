#include <stdint.h>
#include <stddef.h>
#ifndef TRAP_KIND
#define TRAP_KIND 0
#endif
#ifndef NESTING
#define NESTING 3
#endif
#define BASE 0x88000000UL
#define META ((volatile uint64_t *)(BASE-64))
#define DICT ((volatile uint32_t *)(BASE-1065024))
#define MTIME (*(volatile uint64_t *)0x200bff8UL)
#define MTIMECMP (*(volatile uint64_t *)0x2004000UL)
typedef struct {uint64_t callee,parent,cycle,instret,time,reserved[6],next,reserved7,pad[3];} Record;
#define RECORDS ((volatile Record *)(BASE-37748736))
extern void ssa_test_trap_entry(void);
extern volatile uint64_t tohost,fromhost;
static volatile uint64_t level,seen,max_level,bad,helpers,after_depth,after_next,trap_epc,observed_depth,observed_next;
static uint64_t status(void) {
#ifdef CHECK_STATUS
    uint64_t x; asm volatile("csrr %0,0xcc0":"=r"(x)); return x;
#else
    return level;
#endif
}
static void check_handler(void) {
#ifndef REFERENCE
    if(META[0]!=2 || META[1]!=3 || META[2]!=0) bad|=1;
#endif
#ifdef CHECK_STATUS
    uint64_t s=status();
    uint64_t expected=(s&256)?(level?level-1:0):level;
    if((s&255)!=expected || (s&~511UL)) bad|=2;
    if(level>=256 && !(s&256)) bad|=4;
#endif
}
__attribute__((noinline)) static void handler_leaf(void) {check_handler();++helpers;}
__attribute__((noinline)) static void handler_parent(void) {handler_leaf();handler_leaf();}
uintptr_t ssa_test_trap_dispatch(uint64_t cause,uintptr_t epc) {
    ++level; ++seen; if(level>max_level) max_level=level;
    if(seen==1) {observed_depth=META[0];observed_next=META[1];}
    check_handler();
    if(cause==(1UL<<63|7)) {MTIMECMP=~0UL;trap_epc=epc;}
    else if(cause==11 || (TRAP_KIND==4 && cause==2)) epc+=4;
    else {bad|=8;epc+=4;}
    handler_parent();
#if TRAP_KIND == 1 || TRAP_KIND == 3
    if(level<NESTING) asm volatile("ecall" ::: "memory");
#endif
    check_handler();
    --level;
    return epc;
}
__attribute__((noinline)) static void app_leaf(void) {
#if TRAP_KIND == 2
    while(!seen) asm volatile("nop");
#elif TRAP_KIND == 4
    asm volatile("csrw 0xcc0,zero" ::: "memory");
#else
    asm volatile("ecall" ::: "memory");
#endif
    after_depth=META[0];after_next=META[1];
}
__attribute__((noinline)) static void app_parent(void) {
#if TRAP_KIND == 2
    MTIMECMP=MTIME+2;
    asm volatile("csrs mie,%0; csrsi mstatus,8" :: "r"(128UL):"memory");
#endif
    app_leaf();
    // A second call after return must reuse the exact same parent/child ids.
#if TRAP_KIND != 3
    app_leaf();
#endif
    asm volatile("csrci mstatus,8; csrw mie,zero" ::: "memory");
}
static void print(const char *s) {
    size_t n=0;while(s[n])++n;
    volatile uint64_t cmd[8] __attribute__((aligned(64)))={64,1,(uintptr_t)s,n};
    asm volatile("fence rw,rw" ::: "memory");tohost=(uintptr_t)cmd;
    while(!fromhost){}fromhost=0;asm volatile("fence rw,rw" ::: "memory");
}
static void number(uint64_t x) {
    char s[19];s[0]='0';s[1]='x';
    for(int i=0;i<16;++i) s[i+2]="0123456789abcdef"[(x>>(60-4*i))&15];
    s[18]=0;print(s);
}
static void evidence(void) {
    // Fixed-width values in a single HTIF line: first application depth/next,
    // trap entries, maximum hardware nesting, final hardware status.
    char line[128];
    const char *prefix="SSA TRAP EVIDENCE";
    unsigned n=0;
    while(prefix[n]) {line[n]=prefix[n];++n;}
    uint64_t values[]={observed_depth,observed_next,seen,max_level,status()};
    for(unsigned j=0;j<5;++j) {
        line[n++]=' ';
        for(unsigned i=0;i<16;++i) line[n++]="0123456789abcdef"[(values[j]>>(60-4*i))&15];
    }
    line[n++]='\n';line[n]=0;print(line);
}
int main(void) {
    asm volatile("csrw mtvec,%0" :: "r"(ssa_test_trap_entry):"memory");
    MTIMECMP=~0UL;
    level=seen=max_level=bad=helpers=after_depth=after_next=trap_epc=observed_depth=observed_next=0;
    META[0]=0;META[1]=1;META[2]=0;META[3]=0;
    uintptr_t pcs[]={(uintptr_t)app_parent,(uintptr_t)app_leaf,(uintptr_t)ssa_test_trap_dispatch,
                     (uintptr_t)handler_parent,(uintptr_t)handler_leaf};
    for(unsigned f=0;f<5;++f) for(unsigned p=0;p<600;++p) DICT[((pcs[f]>>1)^p)&262143]=0;
#ifndef REFERENCE
    asm volatile("csrw 0x800,%0" :: "r"(BASE):"memory");
#endif
    app_parent();
#ifndef REFERENCE
    asm volatile("csrw 0x800,zero" ::: "memory");
#endif
#if TRAP_KIND == 1 || TRAP_KIND == 3
    const uint64_t expected_level=NESTING;
#else
    const uint64_t expected_level=1;
#endif
#if TRAP_KIND == 2 || TRAP_KIND == 3
    const uint64_t expected_seen=expected_level;
#else
    const uint64_t expected_seen=expected_level*2;
#endif
    if(seen!=expected_seen || level || max_level!=expected_level || helpers!=2*seen) return 30;
    if(bad) {
        print("SSA FAIL: handler changed application context; bad=");number(bad);
        print(" first_depth=");number(observed_depth);print(" first_next=");number(observed_next);print("\n");
        return 31;
    }
#ifndef REFERENCE
#if TRAP_KIND == 3
    if(META[0]!=2 || META[1]!=3 || after_depth!=2 || after_next!=3 ||
       RECORDS[1].instret || RECORDS[2].instret || RECORDS[1].cycle || RECORDS[2].cycle) return 32;
#else
    if(META[0] || META[1]!=3 || after_depth!=2 || after_next!=3) return 33;
    if(RECORDS[1].callee!=(uintptr_t)app_parent || RECORDS[1].parent ||
       RECORDS[2].callee!=(uintptr_t)app_leaf || RECORDS[2].parent!=1 ||
       !RECORDS[1].instret || !RECORDS[2].instret || RECORDS[1].instret<=RECORDS[2].instret) return 34;
#endif
#endif
#ifdef CHECK_STATUS
#if TRAP_KIND == 3
    if(status()!=256) return 35;
#else
    if(status()!=0) return 36;
#endif
#endif
    evidence();
#if TRAP_KIND == 2
    if(trap_epc>=0x10000000 && trap_epc<0x10001000) return 37;
#ifdef REFERENCE
    print("SSA PASS: Spike timer IRQ delivery and architectural return\n");
#else
    print("SSA PASS: timer interrupt, handler isolation, parent resume, context reuse\n");
#endif
#elif TRAP_KIND == 3
    print("SSA PASS: trap depth overflow latches fail-closed, no counter/context fabrication\n");
#elif TRAP_KIND == 1
#ifdef REFERENCE
    print("SSA PASS: Spike nested trap instructions and epc/register restoration\n");
#else
    print("SSA PASS: nested exceptions, handler isolation, balanced resume, context reuse\n");
#endif
#elif TRAP_KIND == 4
    print("SSA PASS: read-only trap status CSR rejects writes and balances return\n");
#else
    print("SSA PASS: synchronous exceptions, handler isolation, parent resume, context reuse\n");
#endif
    return 0;
}
