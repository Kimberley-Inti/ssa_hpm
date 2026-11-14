.option norelax
.text
.globl class_common, class_access
.type class_common,@function
class_common:
  beqz a1, 2f
1: ld t0, 0(a0)
class_access:
  ld t1, 0(t0)
  addi a0,a0,8
  addi a1,a1,-1
  bnez a1,1b
2: ret
.size class_common,.-class_common
.globl class_faulting, class_fault_access
.type class_faulting,@function
class_faulting:
 li t0,0
.option push
.option norvc
class_fault_access:
 ld t1,0(t0)
.option pop
 ret
.size class_faulting,.-class_faulting
.globl class_interleave,class_interleave_scalar,class_interleave_stream
.type class_interleave,@function
class_interleave:
 li t2,8
1:
class_interleave_scalar:
 ld t0,0(a0)
class_interleave_stream:
 ld t1,0(a1)
 addi a1,a1,8
 addi t2,t2,-1
 bnez t2,1b
 ret
.size class_interleave,.-class_interleave
.globl class_stores
.type class_stores,@function
class_stores:
 li t2,8
1:
 sb zero,0(a0)
 sh zero,0(a0)
 sw zero,0(a0)
 sd zero,0(a0)
 addi a0,a0,8
 addi t2,t2,-1
 bnez t2,1b
 ret
.size class_stores,.-class_stores
