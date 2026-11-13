.option norelax
.section .text.init
.globl _start
_start:
 csrw mie,zero
 la gp,__global_pointer$
 la sp,stack_top
 la t0,class_trap
 csrw mtvec,t0
 call main
 j finish
.balign 4
class_trap:
 csrr t0,mcause
 li t1,5
 bne t0,t1,bad
 la t0,class_faults
 ld t1,0(t0)
 addi t1,t1,1
 sd t1,0(t0)
 csrr t0,mepc
 addi t0,t0,4
 csrw mepc,t0
 mret
bad:
 addi a0,t0,100
finish:
 slli a0,a0,1
 ori a0,a0,1
 la t0,tohost
 sd a0,0(t0)
1: j 1b
.section .tohost,"aw",@progbits
.balign 64
.globl tohost,fromhost
tohost: .dword 0
fromhost: .dword 0
.section .bss
.globl class_faults
.balign 8
class_faults: .dword 0
.balign 16
stack: .skip 32768
stack_top:
