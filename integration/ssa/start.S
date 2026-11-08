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
    csrr a0, mcause
    addi a0, a0, 100
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
stack: .skip 32768
stack_top:
