OUTPUT_ARCH(riscv)
ENTRY(_start)
SECTIONS {
 . = 0x80000000;
 .text : { *(.text.init) *(.text .text.*) }
 .rodata : { *(.rodata .rodata.*) }
 .data : { *(.data .data.*) }
 .sdata : { PROVIDE(__global_pointer$ = . + 0x800); *(.sdata .sdata.*) }
 .tohost : { *(.tohost) }
 .bss : { *(.bss .bss.*) *(COMMON) }
 . = 0x80080000;
 .collision_a : { *(.collision_a) }
 . = 0x80100000;
 .collision_b : { *(.collision_b) }
}
