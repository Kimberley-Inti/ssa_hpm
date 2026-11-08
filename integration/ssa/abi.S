.option norvc
.text
.globl abi_probe
.globl alt_leaf
abi_probe:
    addi sp, sp, -16
    sd ra, 0(sp)
    li a0, 10
    li a1, 11
    li a2, 12
    li a3, 13
    li a4, 14
    li a5, 15
    li a6, 16
    li a7, 17
    li t2, 7
    li t3, 28
    li t4, 29
    li t5, 30
    li t6, 31
#ifdef LATE
    li a6, 0
    li t1, -1
    li t0, 0x100000001
    divu a6, t1, t0         # completion may cross entry into the shadow bank
#endif
    jal t0, alt_leaf          # alternate x5 link register
    li t1, 10
    bne a0, t1, bad
    li t1, 11
    bne a1, t1, bad
    li t1, 12
    bne a2, t1, bad
    li t1, 13
    bne a3, t1, bad
    li t1, 14
    bne a4, t1, bad
    li t1, 15
    bne a5, t1, bad
#ifdef LATE
    li t1, 0xffffffff
#else
    li t1, 16
#endif
    bne a6, t1, bad
    li t1, 17
    bne a7, t1, bad
    li t1, 7
    bne t2, t1, bad
    li t1, 28
    bne t3, t1, bad
    li t1, 29
    bne t4, t1, bad
    li t1, 30
    bne t5, t1, bad
    li t1, 31
    bne t6, t1, bad
    li a0, 0
    j done
bad:
    li a0, 21
done:
    ld ra, 0(sp)
    addi sp, sp, 16
    ret
alt_leaf:
    la t1, ordinary_jump
    jr t1                    # computed jump is NOT a return
ordinary_jump:
#ifndef REFERENCE
    li t1, 0x87ffffc0
    ld t1, 0(t1)
    addi t1, t1, -2
    beqz t1, depth_ok
    li a0, -1
depth_ok:
#endif
    jalr zero, 0(t0)          # return via x5
