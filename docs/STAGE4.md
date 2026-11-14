# Stage4: Rocket Linux and process monitoring

Baseline: stage3 `418692f75b3895cbb084e26276ba7267b9f8efee`. This branch preserves
main, v0.1.0 and earlier PRs. PR3 remains draft against stage3-process-isolation.

## Actual acceptance status

- **A PASS**: real single-hart Rocket/Verilator Linux, user PID1 marker, power-down,
  exit0. Final PTY-free profile took3287.93s; see A-final-summary.json and console.
  An earlier slim profile also passed in5627.49s. The first full configuration
  timed out at7200s and is not a pass. No Spike output substitutes for this gate.
- **B PASS**: real Linux uid1000 child, parent/common calls, two closed records,
  successful child exit checked by PID1, export before slot release, selector0.
  Actual unprivileged CSR, physical-pool, invalid-interface and syslog denial
  probes passed. See single-process-summary.json and B-checkpoint-raw.txt.
- **C PASS**: four real Linux process-pair trials completed on Rocket/Verilator:
  two corrected short/long cases and two legacy controls showing expected cross-talk.
  All173 unified checks passed, all children completed, the kernel powered down
  and the simulator exited0 after11800.79s. See BC-summary.json and BC-console.txt.

The single-process result (PID14 in this run; child PIDs are not fixed) is:

| id | symbol/address | parent | cycle | instret | time |
| --- | --- | --- | --- | --- | --- |
| 1 | parent0x1024e | 0 | 7422 | 6722 | 74 |
| 2 | common0x10114 | 1 | 6820 | 6623 | 69 |

The pool was0x88000000, next_id3, depth0, spill0, complete1. common's fixed loop
executes6600 user instructions; the remaining23 are measured boundary/body work.
The actual user ELF and embedded initramfs ELF hashes match, and record addresses
match its symbols. A depth0 switch to/from kernel task7 occurred before the calls;
it does not belong to the later common activation. Counts are inclusive of child
calls and measured monitoring/kernel costs outside paused intervals.

## Implementation and reproducibility

Use the public baselines and ordered patches via scripts/apply.py, then follow
[integration/ssa/linux/README.md](../integration/ssa/linux/README.md).
The pinned build entry fetches Linux5.7-rc3 (firesim5f5fd87) and OpenSBI0.8
(a98258d), applies compatibility/platform/task-pool patches and builds the
kernel, no-libc Linux initramfs and firmware. Build outputs stay outside Git.
Full source revisions/tree hashes and file checksums are in provenance.json.

Bare-metal GCC15.1 compiles the kernel and user ELF. Its linker lacks shared-DSO
support, so the build locally extracts SHA-pinned Ubuntu Linux binutils2.38 for
the vDSO; no sudo or global linker replacement. OpenSBI uses GNU C11 to avoid
GCC15's C23 bool conflict; the old kernel uses ISA-spec2.2 assembler compatibility.
The kernel SP declaration patch supports the minimal unwinder configuration.
The static single-hart OpenSBI platform reuses upstream HTIF/CLINT/PLIC helpers.
The software DTB assigns32MiB to Linux while physical RTL DRAM remains256MiB;
CLINT mtime is the actual1MHz source. Unused legacy PTYs are disabled.

Independent public fetch/patch installation passed, with exact Rocket tree/file
and ROM checks. Independent Linux/OpenSBI builds passed and matched development
source trees. The final process initramfs was rebuilt to fix the fixture's
RISC-V syslog syscall number116; the exact embedded ELF was independently checked.
Development RTL was regenerated and Verilator rebuilt successfully. Dependency
and toolchain caches were reused explicitly. This does not claim a cold-machine
installation or a separate full RTL build in the reconstructed Linux directory.

## Root causes and low-level validation

The first real boot failed after Sv39 relocation: scause15,sepc=e000001080,
stval=6000806450,satp.mode8. An SSA PC mux widened the normal40-bit encoded VA to
64 bits with zero extension, corrupting high-half kernel AUIPC results. Patch0010
preserves the architectural VA width at both PC muxes. The identical minimal
supervisor ELF exits42 on old RTL and0 on fixed RTL/Spike.

Patch0011 denies U access to SCBaseReg0x800, adds supervisor opt-in user-only
notifications at CSR0x5c0 bit0, and gives trusted ROM data requests effective M
privilege. The old U selector probes exited42/43; old U pool access asserted255;
all corresponding fixed probes exit0. The first attempted TLB passthrough change
broke M-mode PMP checks. Keeping passthrough false and changing only effective
privilege fixes physical access while retaining original M-mode behavior.

All16 stage2 checks, all3 stage3 checks and5 new U/S/Sv39 probes passed. Six gold
contexts and instret14452/7226 are unchanged. See regression-final.json. Spike has
no SSA extension: the additional Linux reference fixture verifies ABI, signals,
fork/UID/pipe/scheduler/nanosleep/wait behavior, not the new driver or hardware.
The final reference/security fixture completed and powered down successfully.

## Process and counter protocol

[ABI.md](../integration/ssa/linux/ABI.md) specifies ownership, transitions and
limits. The kernel owns two fixed physical pools, clears child ownership on
fork, pauses/resumes all open frames in the actual scheduler, and exports bounded
records during do_exit before releasing a slot. Users cannot pass another PID or
pool address. Children drop to uid1000 before enable. PID1 remains unmonitored.

The real fixture uses forked processes, not M-mode tasks: A is SCHED_OTHER,
B is FIFO1 and sleeps inside common; its timer wake preempts A's open frames.
PID1 is FIFO2 and waits for actual child exits. Short/long B work and an opt-in
legacy flag isolate the effect of unre-based snapshots. Background kernel tasks
may run between the named processes; adjacency to PID1 is not assumed.

The strict checker requires A's timer/involuntary depth2/rid2 switch to B,
reciprocal B sleep/resume, and instret sample chronology B.S<A.S<B.R<A.R. It
checks record ownership/symbols, mandatory user instruction lower bounds, all
counter R-S equations, open-frame interval sums, real snapshot rebasing and
short/long counter differences for both common and the open parent record.

The hart counters are not reset. Each frame excludes its own paused S-to-R
interval, including other processes, their kernel/trap/export work and any
unmonitored tasks within it. Own kernel/IRQ/monitor/resume costs outside those
sampling boundaries remain included. User-only call notifications do not mean
U-only counters. cycle/instret are hart counters; time is the same CLINT source
seen by the ROM and firmware CSR view. Separate samples are not an atomic trio.

## Explicit design adaptations and limits

Rendered design PDF pp12-13 was checked because Chinese extraction omits glyphs.
The proposed virtual-SP36MiB loader region is adapted here to kernel-owned
physical pools while retaining the accepted microcode layout and exclusive-upper
bound ABI. Monitoring starts at an explicit interval in forked children; no exec
occurs after enable. This does not implement the general virtual-stack loader.

The PDF's export section is TODO. This prototype persists do_exit records through
the captured host serial log and JSON, not a general in-guest file-export service.
Open/spilled frames, allocation errors or more than32 records mark export
incomplete. Multicore, migration, full exec lifecycle, nonlocal unwind, production
resource policy/full-capacity export and Cache/TLB events remain deferred.

## Final measured attribution comparison

A executes the same4000-iteration user loop in every trial. B changes from20 to
3000 iterations. All addresses match the actual embedded user ELF. Nine monitored
process exports contain18 closed records in total; no pool/record mixing was
observed. Both parent and common frame corrections were checked.

| A common, long minus short | corrected | legacy control |
| --- | --- | --- |
| instret | 20 | 207962 |
| cycle | 1667 | 219262 |
| CLINT time ticks | 16 | 2193 |

Corrected A common instret is278450/278470; legacy A is1545490/1753452. B's
corrected common instret is4026/209102 (delta205076). Its mandatory user-loop
increment is196680; interval totals also include non-loop execution. Corrected
A's independently logged excluded instret grows by209744. The difference20 is
consistent with the defined interval semantics: identical user work plus variable
non-loop/kernel/handoff/monitor execution outside S-to-R. Exact equality is not
an acceptance condition. There is no instruction trace assigning those20 to a
specific kernel routine; no stronger claim is made.

The checker independently verifies each R-S sample, sums only intervals with
common open, compares actual frame snapshots, checks B.S<A.S<B.R<A.R, and
requires both parent/common short-long changes to be less than half the observed
legacy cross-talk. The legacy frames remain unchanged with rebased0; corrected
frames equal original+excluded intervals. The raw-derived relation alone is not
used as proof of isolation. Original gold6 contexts/14452/7226 remain unchanged.

CONFIG_PREEMPT_NONE is enabled. RISC-V's return-to-user reschedule path calls
schedule, so the logged preempt argument is0. Actual involuntary preemption is
established by timer IRQ5, TASK_RUNNING/state0, nivcsw advancement, depth2/rid2
and the reciprocal process/sample ordering. Background kernel PID7 may intervene;
no incorrect assumption of direct adjacency to PID1 is used.

The final checker was also run from the independently reconstructed project tree
against the same immutable original execution log and real exit code0; all173
checks passed again. Input image/model hashes match the original execution record.
This reuses the completed simulation rather than claiming a second Linux replay.
See independent-final-grade.json, final-source-reproduction.json and summary.json.

For instret the corrected raw-derived interval increment is209764; the independently
sampled extra excluded interval is209744, leaving20. A's mandatory user loop is
identical. The exact frame/sampling checks establish exclusion of execution inside
S-to-R; post-R handoff/restore and pre-S scheduling remain charged by definition.
The20 is therefore compatible with this contract, not an expected-zero assertion
or an instruction-by-instruction attribution of all Linux overhead.
