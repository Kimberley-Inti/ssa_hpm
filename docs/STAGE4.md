# Stage4 Linux process isolation — work in progress

Baseline: stage3 418692f75b3895cbb084e26276ba7267b9f8efee. This branch does not
move main, tags or previous PRs. Acceptance A/B/C are separate; booting Spike
never satisfies the Rocket/Verilator Linux gate.

## Bootstrap implementation and first reproducible fault

The existing bare-metal GCC 15.1.0 can compile the kernel and no-libc user ELF,
but its linker has no shared-DSO support. The bootstrap locally extracts the
SHA-pinned Ubuntu Linux-target binutils 2.38 package for Linux's vDSO. No sudo,
global toolchain replacement or FireMarshal source workaround is required.
OpenSBI uses explicit GNU C11; GCC15's C23 default otherwise conflicts with
OpenSBI 0.8's bool typedef. The pinned Linux fork also requires moving its SP
register declaration outside CONFIG_FRAME_POINTER for the minimal config.

The first real Rocket boot reached Linux Sv39 relocation, then parked after:
scause=15, sepc=e000001080, stval=6000806450, satp.mode=8, satp.ppn=8021a.
An SSA ROM-PC mux had widened the normal 40-bit encoded virtual PC to 64 bits
with zero extension. AUIPC in the high-half kernel consequently produced a
noncanonical pointer. Patch0010 preserves the architectural VA width at both
PC muxes. The identical minimal supervisor ELF exits 42 on the old RTL and
zero on Spike and fixed RTL. The fix is needed even with monitoring disabled.

The static ssa_rocket OpenSBI platform reuses upstream HTIF/CLINT/PLIC helpers,
with hardware addresses matching RocketConfig. It avoids costly generic DTB
platform discovery during RTL simulation. The embedded DTB assigns Linux only
32 MiB of the hardware's 256 MiB DRAM; unused peripherals are omitted. mtime is
the actual CLINT 1 MHz source. An initramfs PID1 verifies getpid()==1, writes a
unique marker and requests a real Linux reboot/power-down. No libc or full
rootfs distribution is needed for this bootstrap.

## Reproduction

Apply all ten Rocket patches and the existing two Chipyard patches with the
normal scripts/apply.py entry. Then follow integration/ssa/linux/README.md.
The pinned-source build entry is ssa/linux/build-a.py after installation.
It fetches Linux and OpenSBI, applies their two small patches, extracts the
Linux linker, builds kernel/initramfs/firmware and emits ELF plus correct
flat +loadmem hex. Kernel and firmware local development SHAs are mapped in
HISTORY.md; their public baselines plus patches suffice for reconstruction.

Core/source bootstrap revisions:
- Rocket: 41d297689890296699d4a45699bf7e5791d33b96.
- Chipyard: cad6278c2a079e8ffa3b371158bb6f41aca64ffb.
- Linux compatibility: 3b79ddfa2fb70707ace85385d6722925fffc8eea.
- OpenSBI platform: b778927a507e4ebcc43a8ecb8d495562ef48efb3.

Independent public fetch/patch installation passed. Independent kernel and
firmware builds passed and matched development source tree hashes. Fixed RTL
was rebuilt successfully and passed all 16 stage2 regressions plus all three
stage3 process checks, including the expected-exit42 legacy negative. The
original six records and common instret14452/7226 remain unchanged.

## Gate status

A: actual Rocket Linux execution is running; no pass claimed until PID1 marker,
power-down and exit zero. The host-only progress harness links unchanged RTL
model objects and prints read-only PC/CSR fields; raw console and diagnostic
chatter must be kept distinct. Separate Spike diagnostics reached PID1 and
power-down but are not A evidence. A smaller config is also being evaluated
to reduce sysfs/input initialization time.

B: kernel-managed monitoring/exit export has not been executed.
C: real Linux preemptive two-process isolation has not been executed.

The completed M-mode tests remain low-level regression evidence only. Linux
U-mode pool protection, private ROM physical access, scheduler hooks and real
process counter attribution still require their own implementation/validation.

## Linux integration implementation prepared

Patch0011 protects the legacy SCBaseReg selector from U-mode, introduces the
supervisor-only opt-in user-call notification policy (CSR0x5c0 bit0), and makes
trusted ROM data requests use effective M privilege. Keeping TLB passthrough
false is essential: the PTW passthrough path forces S-mode PMP checks and broke
the original M-mode tests. The final effective-privilege implementation passes
all 16 stage2 checks, three stage3 checks, and five U/S/Sv39 probes. See
`evidence/stage4/regression-final.json`. Gold counts remain14452/7226.

The Linux patch allocates two task-owned fixed physical pools outside Linux RAM,
clears child ownership on fork, pauses/resumes open frames in the actual scheduler,
and exports bounded records in do_exit before releasing ownership. U-mode receives
no pool-address argument or pool mapping. The fixture drops children to uid1000;
PID1 remains unmonitored and controls deterministic timer wakeups with FIFO
priorities. A is SCHED_OTHER; a nanosleep-woken FIFO B preempts it. Four trials
combine short/long B with corrected/legacy accounting, with the same code address
for common in both processes. The strict grader requires involuntary timer
A-to-B-to-A with depth2/rid2, owner-specific records and all counter equations.

Reference validation found and fixed a fixture syscall-number bug: RISC-V syslog
is116. The corrected signal/security/scheduler reference passed on Spike without
an SSA extension. It does not validate the new kernel driver or the RTL policy.
The kernel and OpenSBI public-source independent reconstructions/builds passed;
the initial monitoring trees match the development source hashes exactly.
Unused legacy PTYs were disabled in the final profile to avoid creating512
unneeded device objects. A prior full boot timed out at7200s; this is retained as
a failed attempt, not a passing Linux result. The existing slim attempt remains
in execution; B/C run only after the real A gate passes.

The final PTY-free A image is also under actual Rocket execution, with separate
immutable image/log names; it validates the final reproduction profile. The old
slow simulation is preserved. B/C will be launched once, only after a real A
success. Build terminal exit statuses were read back: final RTL/model, development
kernel/firmware, independent kernel/firmware and corrected initramfs all exited0.
See build-final.json for source-tree matches, input/image hashes and log hashes.

## Explicit design adaptations

The design PDF pp12-13 was checked as rendered pages because text extraction
omits Chinese glyphs. Its proposed36MiB region is based on the application's
virtual SP before main. Stage4 retains the accepted physical pool layout and
SCBaseReg exclusive-upper-bound ABI, managed by the trusted single-hart kernel
instead of changing the loader/user stack. It monitors only the explicitly
enabled interval in forked children; no exec occurs after enable. Kernel-owned
physical pools and trusted ROM requests avoid granting a user a kernel/global
mapping or an address-selection interface. This is a bounded Linux adaptation,
not completion of the PDF's general virtual-stack/loader proposal.

The PDF leaves export/offline analysis as TODO. This prototype exports closed,
bounded records during do_exit to a captured host serial log, persisted to disk
by the actual simulator command and decoded into JSON. It does not implement a
general in-guest filesystem export service. Exports with open/spilled frames,
errors or too many records are marked incomplete rather than silently accepted.

## A actual acceptance completed

The existing slim Rocket run completed successfully: PID1 marker, Linux power-down,
no panic, exit0,5627.49s. See evidence/stage4/A-summary.json and raw/normalized
console logs. It used fixed-PC Rocket41d2976 and the pinned independent kernel/
firmware. Its configuration retains legacy PTYs; the final faster no-PTY profile
is also running separately. The first full configuration timed out, so its result
is not a pass. B/C has now launched once using independent PTY-free rebuilt
Linux0d6ec76 source and Rocket1c7841345. No Linux monitoring pass is yet claimed.
