# Performance evaluation of the single-hart research prototype

Status: bare experiment accepted; Linux work/phase results still running. No final release gate has passed yet.

## Measurement conditions

All comparisons use the same newly built extended SSAHPMEventRocketConfig. Off means context monitoring disabled; extension hardware and standard global counters still exist. No matched unextended design, synthesis area, power or physical frequency measurement is claimed. Generated L1D and L1I are16KiB each,64sets and64B lines. The software device tree declares a1MHz CLINT timebase; raw cycle/instret/time readings are primary.

Each body has one unmeasured warmup and five measured repetitions, with identical results. Data is initialized per workload/mode and read-only during measurement. Samples surround the CALL and completed RETURN, outside console output; disassembly verifies order. Empty samples are retained but not blindly subtracted. Output between repetitions can affect cache/DRAM phase. Reported ranges describe this deterministic model/run, not a silicon confidence interval.

Bare modes execute in M-mode. DTLB mode measures the ABI2 snapshot path on physical-address loads, not PTW latency. Actual translated DTLB source/attribution is separately covered by fresh RTL regressions; automatic-DTLB Linux remains untested. Linux uses a fixed Cache firmware selector. The measurement ELF contains manual paths and is not the proof of SSA-free targets; the separate ordinary-ELF regression supplies that proof.

## Accepted bare workload data

Native exit0;150work rows,30calibration rows and6setup rows; all workload checksums agree. Wall time6532.51s describes experiment duration only. Raw data and exact min/median/max for all three counters are in `evidence/stage11/performance-final/summary.json`.

Cycle medians:

| Workload | Off | Base | DTLB | Cache | Classification | Cache+classification |
|---|---:|---:|---:|---:|---:|---:|
| compute | 1697 | 2025 | 2080 | 2092 | 2028 | 2087 |
| calls128 | 1088 | 46328 | 53038 | 53036 | 46328 | 53036 |
| depth16 | 282 | 6620 | 7547 | 7544 | 6593 | 7545 |
| stream32KiB | 52224 | 52641 | 52767 | 52683 | 52649 | 52866 |
| irregular32KiB | 103375 | 103784 | 103951 | 103664 | 103768 | 103874 |

Retired-instruction medians (classification has the same values as its corresponding base/event mode):

| Workload | Off | Base | ABI2 event |
|---|---:|---:|---:|
| compute | 532 | 612 | 625 |
| calls128 | 1048 | 11752 | 13429 |
| depth16 | 207 | 1705 | 1939 |
| stream32KiB | 40992 | 41079 | 41092 |
| irregular32KiB | 45088 | 45175 | 45188 |

Base mode cycle ranges are compute2025–2059, calls46325–46395, depth6585–6666, stream52516–53054 and irregular103426–104331. Off ranges are1693–1724,1074–1097,242–289,52048–52582 and103007–103995 respectively. CLINT time is quantized, including zero-tick empty intervals; use the raw time ranges rather than inferring sub-tick precision.

## Why call-heavy overhead is large

128leaf calls cost46328/1088=42.58× the off cycle median (4158% extra); ABI2 costs about48.75×. Depth16 costs23.48× in base mode. This is a substantial runtime cost, not evidence of a low-overhead design. The ROM serializes injected instructions and accesses dictionary, frame and record memory at each call/return. Independent instret measurements expose this work directly.

The instruction deltas reconcile exactly with the control path: one existing root activation adds80retired instructions, a non-root adds83, ABI2 adds13per activation, and an extra collision-chain hop adds7. Thus calls add80+128×83=10704, matching11752−1048. ABI2 adds93+128×96=12381, matching13429−1048. After recursive contexts are created, root lookup has one extra hop:87+17×83=1498, matching1705−207; ABI2 gives100+17×96=1732, matching1939−207.

The actual symbols are leaf0x80000050, deep0x8000005a and bench_work0x8000007a. With the implemented XOR hash, deep under parent16 and the root bench_work collide: `(0x5a>>1)^16 == (0x7a>>1)^0 ==0x3d`. This explains the7-instruction increase for subsequent stream/irregular root lookups; it is expected chain traversal, not hidden program work or console inclusion.

Long memory loops amortize the one activation: base cycle medians rise about0.80% for the32KiB stream and0.40% for the irregular permutation. The data set exceeds L1D capacity; this is not a fully hot-cache benchmark. Small differences between base and classification fall within phase/cache variation and do not establish a speedup or free hardware. In this model classification runs alongside retirement without extra software instructions; its physical timing/area cost remains unknown.

## Setup and lifecycle boundaries

Bare setup clears1MiB of dictionary even in the off control, then prepares metadata/selectors. It costs1636972–1638419cycles and786491–786537instructions across the six single setup observations. Off setup is experimental cache-state preparation, not a necessary cost for an unmonitored application. These are not Linux allocator measurements. Empty bare samples span12–28cycles; raw workload deltas are preserved.

The Linux matrix includes both manual and automatic Cache+classification to avoid attributing profile differences to policy. Work results use the same ELF/body, one warmup and five repeats. Each mode is a separately launched process; stack layout, interrupt and cache history can affect small inter-mode differences. The main controlled bare comparison has fixed physical addresses.

Kernel cost probes measure dictionary/metadata/selector reset before BEGIN formatting, not kzalloc; user START also includes syscall and diagnostics. Automatic user INIT is already-enabled entry calibration, while kernel probes measure actual setup. NNP/ARM setup is separately bracketed. Pause/resume reads are deferred until frozen export, with no scheduler-path printk.

Freeze and record-copy are subsets of export. Export includes formatting, HTIF/SBI-console transfer and bookkeeping, excluding subsequent cost diagnostics and release. It is not a UART baud-rate or pure-wire result. Exec-entry→ELF-ready/failure windows exclude their own diagnostic print but include normal old-session export/new-session setup; user failed-exec samples include probe diagnostics. Application work intervals contain no output.

Probe overhead is not silently removed. Compiler sizeof measurements show a default descriptor3768B/event128B versus instrumented4368B/event176B. This can affect allocation/cache behavior. Lifecycle figures are descriptive observations of the instrumented build, not exact unprobed production costs. Default unified Linux regression compiles the probes out.

## Resource footprint, separate from measured area

Two36MiB physical pools reserve72MiB outside Linux allocation. Each has262144record slots (ID0reserved),128B slots,1MiB dictionary and256×64B frames. Classifier declarations total57926state bits (about7.07KiB): two banks,63usable rows/bank,16history entries/bank and256shadow frames/bank. Declared memory includes unused rows; synthesis may optimize them.

The private register bank has32logical shadow registers; declared RF memory grows31→64slots at64bits, a nominal2112-bit difference including an unused zero-address slot. ABI1/2 constant ROMs contain104/118words,888B combined. These counts exclude other CSR/pipeline/control logic and are not technology-mapped cell area. No synthesis or matched no-extension fmax result is available.

Linux numerical data and final verdict will be appended only after native shutdown and all work/export/cost checks complete.
