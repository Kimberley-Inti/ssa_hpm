.option norelax
.section .text.init
.globl _start
.type _start,@function
_start:
 mv a0,sp
 tail plain_main
.size _start,.-_start
