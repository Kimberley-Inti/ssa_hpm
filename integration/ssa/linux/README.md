# Linux on the existing single-hart RocketConfig

This entry builds Linux 5.7-rc3 from the FireMarshal-pinned commit and OpenSBI
0.8 from its pinned commit. No target libc or root filesystem distribution is
required for the minimal PID 1 program: init.c uses actual Linux system calls.
The initramfs contains /init and the /dev/console device node.

Prerequisites: existing RISC-V GCC 15.1.0, native GCC/make, Git, Python 3, dtc,
flex, bison, bc, gzip, cpio and dpkg-deb. The installer extracts a SHA-256-pinned
Ubuntu Linux-target binutils package locally; no sudo or system linker change.
The bare-metal linker cannot build Linux's shared vDSO. OpenSBI explicitly uses
GNU C11 because its older bool typedef conflicts with GCC 15's default C23.

```bash
source ssa/env.sh
# Use a new directory outside the repositories.
python3 ssa/linux/build-a.py --work /tmp/my-ssa-linux-a --jobs 8
make -C sims/verilator CONFIG=RocketConfig -j8 LINK='/usr/bin/g++ -B/usr/bin/'
python3 ssa/linux/verify-a.py \
  --image /tmp/my-ssa-linux-a/boot-a.elf \
  --hex /tmp/my-ssa-linux-a/boot-a.hex \
  --simulator sims/verilator/simulator-chipyard-RocketConfig \
  --out-dir /tmp/my-ssa-linux-a/results
```

The Rocket source must include the stage4 Sv39 PC-width fix. The identical
sv39.S binary exits 42 on stage3 RTL and zero after the fix (and on Spike):

```bash
make -C ssa linux/sv39.hex
spike ssa/linux/sv39.riscv
sims/verilator/simulator-chipyard-RocketConfig +permissive \
  +loadmem=ssa/linux/sv39.hex +max-cycles=2000000 \
  +permissive-off ssa/linux/sv39.riscv
```

The software DTB describes the existing CLINT/PLIC, hart 0 and real 1 MHz mtime
clock. It limits Linux's managed RAM to 32 MiB and omits unused devices. Physical
RTL DRAM stays 256 MiB. HTIF is the console/reset interface. The fixed
ssa_rocket OpenSBI platform uses upstream HTIF/CLINT/PLIC helpers and avoids
repeated generic platform DTB discovery. The DTB is embedded in cached firmware
RAM using the existing FW_PAYLOAD_FDT_PATH option, then passed to Linux.

A passes only with the user PID-1 success marker, kernel power-down and an exit
status of zero from the actual Rocket/Verilator command. A Spike boot is a
separate image/ISA diagnostic and cannot satisfy A. The expected marker alone
never identifies the simulator; the command and simulator hash are recorded.
Full Linux/HPM acceptance remains tracked separately in the stage4 report.

For long-run diagnostics, build-progress.py links a separate host harness
against the existing generated RTL model and prints read-only PC/CSR state.
It does not regenerate RTL or replace the original simulator:

```bash
python3 ssa/linux/build-progress.py --workspace "$PWD" --out /tmp/my-ssa-progress
# Pass /tmp/my-ssa-progress/simulator-progress to verify-a.py if needed.
```

Artifacts (sources, images, deb packages, compiled objects) remain in the work
or temporary build directory. They must not be committed to ssa_hpm.
