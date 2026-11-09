/* Supervisor high-half PC regression; runs on Spike and actual Rocket RTL. */
.option norvc
.section .text.init
.globl _start
_start:
 csrw mie,zero
 la t0,trap
 csrw mtvec,t0
 la t0,root
 li t1,512
1: sd zero,0(t0)
 addi t0,t0,8
 addi t1,t1,-1
 bnez t1,1b
 la t0,root
 li t1,0x200000cf
 li t2,3072
 add t2,t0,t2
 sd t1,0(t2) /* pgd[384]: high-half VA -> 0x80000000, 1 GiB leaf */
 srli t0,t0,12
 li t1,0x8000000000000000
 or t0,t0,t1
 csrw satp,t0
 sfence.vma
 li t0,-1
 csrw pmpaddr0,t0
 li t0,15
 csrw pmpcfg0,t0
 li t0,0x800
 csrw mstatus,t0
 li t0,0xffffffe000001000
 csrw mepc,t0
 mret
trap:
 csrr t0,mcause
 li t1,9
 beq t0,t1,finish
 li a0,43
finish:
 slli a0,a0,1
 ori a0,a0,1
 la t0,tohost
 sd a0,0(t0)
2: j 2b
.balign 4096
.globl supervisor
supervisor:
 auipc t0,0
 li t1,0xffffffe000001000
 bne t0,t1,bad
 jal ra,child
 la t0,supervisor
 bne t0,t1,bad
 li a0,0
 ecall
bad:
 li a0,42
 ecall
child:
 srai t0,ra,39
 li t2,-1
 bne t0,t2,bad
 ret
.section .tohost,"aw",@progbits
.balign 64
.globl tohost,fromhost
tohost: .dword 0
fromhost: .dword 0
.section .bss
.balign 4096
root: .skip 4096
