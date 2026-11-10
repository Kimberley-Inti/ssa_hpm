/* U-mode protection/physical-pool probes. No Linux acceptance is inferred. */
.option norvc
.section .text.init
.globl _start
_start:
 csrw mie,zero
 csrw medeleg,zero
 la t0,trap
 csrw mtvec,t0
 la t0,root
 li t1,1024
1: sd zero,0(t0)
 addi t0,t0,8
 addi t1,t1,-1
 bnez t1,1b
 la t0,level1
 srli t1,t0,12
 slli t1,t1,10
 ori t1,t1,1
 la t2,root
 sd t1,0(t2)
#ifdef PROBE_SUPERVISOR
 li t1,0x200000cf
#else
 li t1,0x200000df
#endif
 sd t1,0(t0) /* User VA 0..2MiB maps only PA 80000000..80200000 */
 la t0,root
 srli t0,t0,12
 li t1,0x8000000000000000
 or t0,t0,t1
 csrw satp,t0
 sfence.vma
 li t0,-1
 csrw pmpaddr0,t0
 li t0,15
 csrw pmpcfg0,t0
 li t0,0x88000000
 addi t1,t0,-64
 sd zero,0(t1)
 li t2,1
 sd t2,8(t1)
 sd zero,16(t1)
 sd zero,24(t1)
 li t1,-1065024
 add t1,t0,t1
 li t2,0x2020 /* hash bucket for leaf at VA1010, parent0 */
 add t1,t1,t2
 sw zero,0(t1)
#ifdef PROBE_SUPERVISOR
 li t1,1
 csrw 0x5c0,t1
 li t1,0x800
 csrw mstatus,t1
#else
 csrw mstatus,zero
#endif
 li t1,0x1000
 csrw mepc,t1
 csrw 0x800,t0
 mret
trap:
 csrr t3,0x800
 csrw 0x800,zero
 li a0,43
 csrr t0,mstatus
 srli t0,t0,11
 andi t0,t0,3
#ifdef PROBE_SUPERVISOR
 li t1,1
 bne t0,t1,finish
#else
 bnez t0,finish
#endif
 li t0,0x88000000
 bne t0,t3,finish
 csrr t0,mcause
#ifdef PROBE_CSR
 li t1,2
 bne t0,t1,old_allowed
 csrr t0,mepc
 li t1,0x1000
 bne t0,t1,finish
 li a0,0
 j finish
old_allowed:
 li a0,42
#elif defined(PROBE_SUPERVISOR)
 li t1,9
 bne t0,t1,finish
 li t0,0x87ffffc0
 ld t1,0(t0)
 bnez t1,finish
 ld t1,8(t0)
 li t2,1
 bne t1,t2,finish
 li a0,0
#else
 li t1,8
 bne t0,t1,finish
 li t0,0x87ffffc0
 ld t1,0(t0)
 bnez t1,finish
 ld t1,8(t0)
 li t2,2
 bne t1,t2,finish
 li t0,0x85c00080
 ld t1,0(t0)
 li t2,0x1010
 bne t1,t2,finish
 ld t1,8(t0)
 bnez t1,finish
 ld t1,24(t0)
 beqz t1,finish
 li a0,0
#endif
finish:
 slli a0,a0,1
 ori a0,a0,1
 la t0,tohost
 sd a0,0(t0)
2: j 2b
.balign 4096
user_entry:
#ifdef PROBE_CSR
#ifdef PROBE_WRITE
 csrw 0x800,zero
#else
 csrr t0,0x800
#endif
 li a0,42
 ecall
#else
 jal ra,leaf
 li a0,0
 ecall
 j user_entry
leaf: /* VA1010, with norvc fixed above */
 nop
 ret
#endif
.section .tohost,"aw",@progbits
.balign 64
.globl tohost,fromhost
tohost: .dword 0
fromhost: .dword 0
.section .bss
.balign 4096
root: .skip 4096
level1: .skip 4096
