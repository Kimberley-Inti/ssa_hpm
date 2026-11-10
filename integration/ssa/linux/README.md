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

## Linux monitoring prototype (stage4, acceptance pending execution)

`python3 ssa/linux/build-a.py --process --work /tmp/ssa-linux-process-rebuild`
reconstructs the pinned Linux source and kernel task-pool patch in a new directory.
It uses the same static OpenSBI platform, local Linux linker and minimal initramfs
as boot A. The process profile selects CONFIG_SSA_HPM and HZ=1000.

After A passes, run the immutable process image with the rebuilt Rocket model:

```
python3 ssa/linux/run-process.py \
  --image /tmp/ssa-linux-process-rebuild/boot-a.elf \
  --hex /tmp/ssa-linux-process-rebuild/boot-a.hex \
  --simulator "$PWD/sims/verilator/simulator-chipyard-RocketConfig" \
  --out-dir /tmp/ssa-linux-process-results
```

The userspace program uses the Linux fork/pipe/nanosleep/wait/scheduler APIs.
Children drop to uid1000 before enabling monitoring. PID1 stays unmonitored.
A finite fixed instruction loop gives the timer-woken FIFO B a chance to preempt
A with two open frames. FIFO scheduling is only the test fixture's deterministic
wake-up mechanism; user counting and pool ownership are per Linux task.
The grader requires actual timer/scheduler evidence and exported frame accounting,
not merely the userspace PASS strings. The REFERENCE compile option omits SSA
and security checks and is only an ABI/scheduler diagnostic suitable for Spike.

Supervisor CSR0x5c0 bit0 selects user-only call notifications. It does not filter
hardware counters. SCBaseReg0x800 remains the physical exclusive upper pool bound
and is now denied in U-mode. Trusted ROM memory operations use effective M-mode
translation/PMP semantics; other user memory accesses retain normal Sv39/PMP.
Default CSR0x5c0=0 retains the stage3 trap-depth notification policy.

The kernel owns two fixed physical regions outside the 32MiB Linux RAM allocator.
It maps only metadata/dictionary/stack and a bounded record export window, never
passes their addresses to userspace, initializes on enable, clears selection on
switch, and releases ownership after do_exit export. Fork starts unmonitored.
The test does not exec after enable. Export is complete only with no open/spilled
frames or allocator errors and within the 32-record export limit. Abrupt exits
with open frames produce incomplete exports; nonlocal unwinding is unsupported.

Every switched-out open frame is rebased by R-S for cycle/instret/time. This
excludes the sampling interval, including B and any unmonitored task in it.
Own kernel, IRQ, monitor and resume costs outside that interval remain included;
counts are inclusive of child calls. The time samples and ROM use the real CLINT
mtime source. The legacy debug flag deliberately omits rebasing for a same-path
negative control; it affects only the caller's pool. Logs are emitted after
sampling is stopped, preventing console export costs from contaminating records.
The short/long comparisons permit cache/timer/boundary costs rather than assuming
identical absolute cycle/time values. Linux `dmesg_restrict` and signal/access
probes verify that an unprivileged task cannot read exported kernel logs, select
another pool through the API, read SCBaseReg or directly load the pool address.

Multicore/migration, exec integration, general unwind, production resource quotas,
full-capacity export, Cache/TLB events and adversarial policy hardening remain out
of scope. This is a single-hart research interface, not a production kernel ABI.
