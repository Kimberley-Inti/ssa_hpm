.option norelax
.section .text.init
.globl _start
_start:
    csrw mie, zero
    la gp, __global_pointer$
    la sp, stack_top
    la t0, trap
    csrw mtvec, t0
    call main
    j finish
 .balign 4
trap:
    csrr t0, mcause
    li t1,9
    beq t0,t1,finish
    mv a0,t0
    addi a0,a0,100
finish:
    slli a0, a0, 1
    ori a0, a0, 1
    la t0, tohost
    sd a0, 0(t0)
1:  j 1b
.section .tohost,"aw",@progbits
.balign 64
.globl tohost
tohost: .dword 0
.globl fromhost
fromhost: .dword 0
.section .bss
.balign 16
stack:
#ifdef TRAP_TEST
    .skip 131072
#else
    .skip 32768
#endif
stack_top:
