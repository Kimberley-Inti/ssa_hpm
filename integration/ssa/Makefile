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

trap.riscv: start.S trap_entry.S traps.c test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DTRAP_TEST start.S trap_entry.S traps.c -o $@
trap-status.riscv: start.S trap_entry.S traps.c test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DTRAP_TEST -DCHECK_STATUS start.S trap_entry.S traps.c -o $@
trap-nested.riscv: start.S trap_entry.S traps.c test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DTRAP_TEST -DCHECK_STATUS -DTRAP_KIND=1 start.S trap_entry.S traps.c -o $@
trap-irq.riscv: start.S trap_entry.S traps.c test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DTRAP_TEST -DCHECK_STATUS -DTRAP_KIND=2 start.S trap_entry.S traps.c -o $@
trap-overflow.riscv: start.S trap_entry.S traps.c test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DTRAP_TEST -DCHECK_STATUS -DTRAP_KIND=3 -DNESTING=256 start.S trap_entry.S traps.c -o $@
trap-reference.riscv: start.S trap_entry.S traps.c test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DTRAP_TEST -DREFERENCE -DTRAP_KIND=1 start.S trap_entry.S traps.c -o $@
trap-irq-reference.riscv: start.S trap_entry.S traps.c test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DTRAP_TEST -DREFERENCE -DTRAP_KIND=2 start.S trap_entry.S traps.c -o $@

trap-readonly.riscv: start.S trap_entry.S traps.c test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DTRAP_TEST -DCHECK_STATUS -DTRAP_KIND=4 start.S trap_entry.S traps.c -o $@
.PHONY: traps
traps: trap.hex trap-status.hex trap-nested.hex trap-irq.hex trap-overflow.hex trap-readonly.hex trap-reference.riscv trap-irq-reference.riscv
all: traps

process.riscv: start.S process_entry.S processes.c process.h test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DTRAP_TEST start.S process_entry.S processes.c -o $@
process-legacy.riscv: start.S process_entry.S processes.c process.h test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DTRAP_TEST -DLEGACY_SWITCH start.S process_entry.S processes.c -o $@
process-reference.riscv: start.S process_entry.S processes.c process.h test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DTRAP_TEST -DREFERENCE start.S process_entry.S processes.c -o $@
all: process.hex process-legacy.hex process-reference.riscv

linux/sv39.riscv: linux/sv39.S test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) linux/sv39.S -o $@
all: linux/sv39.hex

linux/user-csr.riscv: linux/user-probe.S test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DPROBE_CSR $< -o $@
linux/user-write.riscv: linux/user-probe.S test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DPROBE_CSR -DPROBE_WRITE $< -o $@
linux/user-pool.riscv: linux/user-probe.S test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) $< -o $@
linux/supervisor-policy.riscv: linux/user-probe.S test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DPROBE_SUPERVISOR $< -o $@
.PHONY: linux-probes
linux-probes: linux/sv39.hex linux/user-csr.hex linux/user-write.hex linux/user-pool.hex linux/supervisor-policy.hex

event.riscv: event_start.S events.c test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) event_start.S events.c -o $@
event-selector-negative.riscv: event_start.S events.c test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DWRONG_SELECTOR event_start.S events.c -o $@
event-context-negative.riscv: event_start.S events.c test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DSWAP_CONTEXT event_start.S events.c -o $@
event-wrap.riscv: event_start.S events.c test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DCOUNTER_WRAP event_start.S events.c -o $@
.PHONY: events
events: event.hex event-selector-negative.hex event-context-negative.hex event-wrap.hex

event-abi.riscv: start.S test.c abi.S test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DABI -DEVENT_ABI start.S test.c abi.S -o $@
events: event-abi.hex

cache.riscv: event_start.S events.c test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DCACHE_EVENT event_start.S events.c -o $@
cache-selector-negative.riscv: event_start.S events.c test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DCACHE_EVENT -DWRONG_SELECTOR event_start.S events.c -o $@
cache-context-negative.riscv: event_start.S events.c test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DCACHE_EVENT -DSWAP_CONTEXT event_start.S events.c -o $@
cache-wrap.riscv: event_start.S events.c test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DCACHE_EVENT -DCOUNTER_WRAP event_start.S events.c -o $@
.PHONY: cache-events
cache-events: cache.hex cache-selector-negative.hex cache-context-negative.hex cache-wrap.hex

cache-abi.riscv: start.S test.c abi.S test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DABI -DEVENT_ABI -DCACHE_EVENT start.S test.c abi.S -o $@
cache-events: cache-abi.hex

classification.riscv: event_start.S classification/bare.c classification/workload.S test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) event_start.S classification/bare.c classification/workload.S -o $@
.PHONY: classification
classification: classification.hex

classification-fault.riscv: classification/trap-start.S classification/bare.c classification/workload.S test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DCLASS_FAULT classification/trap-start.S classification/bare.c classification/workload.S -o $@
classification: classification-fault.hex

classification-capacity.riscv: event_start.S classification/bare.c classification/workload.S classification/capacity.S test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DCLASS_CAPACITY event_start.S classification/bare.c classification/workload.S classification/capacity.S -o $@
classification: classification-capacity.hex

classification-patterns.riscv: event_start.S classification/bare.c classification/workload.S test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DCLASS_PATTERNS event_start.S classification/bare.c classification/workload.S -o $@
classification: classification-patterns.hex

linux/user-class-read.riscv: linux/user-probe.S test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DPROBE_CSR -DCLASS_CSR $< -o $@
linux/user-class-write.riscv: linux/user-probe.S test.ld
	$(CC) $(CFLAGS) $(LDFLAGS) -DPROBE_CSR -DCLASS_CSR -DPROBE_WRITE $< -o $@
classification: linux/user-class-read.hex linux/user-class-write.hex

linux-probes: linux/user-class-read.hex linux/user-class-write.hex
