CROSS_COMPILE ?= riscv64-unknown-elf-
CC = $(CROSS_COMPILE)gcc
CFLAGS = -march=rv64gc -mabi=lp64d -mcmodel=medany -O1 -g -ffreestanding -fno-builtin -fno-optimize-sibling-calls -msmall-data-limit=0 -Wall -Wextra
LDFLAGS = -nostdlib -nostartfiles -Wl,--no-relax -T test.ld
all: test.riscv reference.riscv boundary.riscv boundary-reference.riscv abi.riscv abi-reference.riscv late.riscv test.hex boundary.hex abi.hex late.hex reference.hex

test.riscv: start.S test.c test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) start.S test.c -o $@
reference.S: microcode.S
	sed -e 's/\.globl _start/.globl sc_event/' -e 's/^_start:/sc_event:/' -e 's/\.word 0x00060067/ret/' $< > $@
reference.riscv: start.S test.c reference.S test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DREFERENCE start.S test.c reference.S -o $@
.PHONY: all rom check-rom
rom:
	python3 gen_rom.py
check-rom:
	python3 gen_rom.py --check
%.bin: %.riscv
	$(CROSS_COMPILE)objcopy -O binary $< $@
%.hex: %.bin elf_to_hex.py
	python3 elf_to_hex.py $< $@
.PHONY: spike rtl
spike: reference.riscv
	spike $<
rtl: test.riscv test.hex
	cd .. && sims/verilator/simulator-chipyard-RocketConfig +permissive +loadmem=ssa/test.hex +max-cycles=3000000 +permissive-off ssa/test.riscv

boundary.riscv: start.S test.c test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DBOUNDARY start.S test.c -o $@
boundary-reference.riscv: start.S test.c reference.S test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DBOUNDARY -DREFERENCE start.S test.c reference.S -o $@

abi.riscv: start.S test.c abi.S test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DABI start.S test.c abi.S -o $@
abi-reference.riscv: start.S test.c abi.S reference.S test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DABI -DREFERENCE start.S test.c abi.S reference.S -o $@

late.riscv: start.S test.c abi.S test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DABI -DLATE start.S test.c abi.S -o $@
