#!/bin/bash
set -euo pipefail
ssa_perf_dir=$(cd -- "$(dirname -- "$0")" && pwd)
ssa_perf_out=${1:?Usage: build.sh OUT [REPEATS]}
ssa_perf_repeats=${2:-5}
mkdir -p "$ssa_perf_out"
"${CROSS_COMPILE:-/opt/riscv/bin/riscv64-unknown-elf-}gcc" -march=rv64gc -mabi=lp64d -mcmodel=medany -O1 -ffreestanding -fno-builtin -fno-optimize-sibling-calls -msmall-data-limit=0 -nostdlib -nostartfiles -Wl,--no-relax -T "$ssa_perf_dir/../test.ld" -DREPEATS="$ssa_perf_repeats" "$ssa_perf_dir/../event_start.S" "$ssa_perf_dir/bench.c" -o "$ssa_perf_out/benchmark.riscv"
"${CROSS_COMPILE:-/opt/riscv/bin/riscv64-unknown-elf-}objcopy" -O binary "$ssa_perf_out/benchmark.riscv" "$ssa_perf_out/benchmark.bin"
python3 "$ssa_perf_dir/../elf_to_hex.py" "$ssa_perf_out/benchmark.bin" "$ssa_perf_out/benchmark.hex"
