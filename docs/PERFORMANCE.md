# Performance evaluation of the single-hart research prototype

Status: bare, Linux workload/phase and separate direct snapshot-proof checks passed. Final packaging/integration gates are recorded in stage11/summary.json.

## Measurement conditions

All comparisons use the same newly built extended SSAHPMEventRocketConfig. Off means context monitoring disabled; extension hardware and standard global counters still exist. No matched unextended design, synthesis area, power or physical frequency measurement is claimed. Generated L1D and L1I are 16 KiB each,64sets and 64B lines. The software device tree declares a1 MHz CLINT timebase; raw cycle/instret/time readings are primary.

Each body has one unmeasured warmup and five measured repetitions, with identical results. Data is initialized per workload/mode and read-only during measurement. Samples surround the CALL and completed RETURN, outside console output; disassembly verifies order. Empty samples are retained but not blindly subtracted. Output between repetitions can affect cache/DRAM phase. Reported ranges describe this deterministic model/run, not a silicon confidence interval.

Bare modes execute in M-mode. DTLB mode measures the ABI2 snapshot path on physical-address loads, not PTW latency. Actual translated DTLB source/attribution is separately covered by fresh RTL regressions; automatic-DTLB Linux remains untested. Linux uses a fixed Cache firmware selector. The measurement ELF contains manual paths and is not the proof of SSA-free targets; the separate ordinary-ELF regression supplies that proof.

## Accepted bare workload data

Native exit 0;150 work rows,30 calibration rows and 6 setup rows; all workload checksums agree. Wall time6532.51s describes experiment duration only. Raw data and exact min/median/max for all three counters are in `evidence/stage11/performance-final/summary.json`.

Cycle medians:

| Workload | Off | Base | DTLB | Cache | Classification | Cache+classification |
|---|---:|---:|---:|---:|---:|---:|
| compute | 1697 | 2025 | 2080 | 2092 | 2028 | 2087 |
| calls128 | 1088 | 46328 | 53038 | 53036 | 46328 | 53036 |
| depth 16 | 282 | 6620 | 7547 | 7544 | 6593 | 7545 |
| stream32 KiB | 52224 | 52641 | 52767 | 52683 | 52649 | 52866 |
| irregular32 KiB | 103375 | 103784 | 103951 | 103664 | 103768 | 103874 |

Retired-instruction medians (classification has the same values as its corresponding base/event mode):

| Workload | Off | Base | ABI2 event |
|---|---:|---:|---:|
| compute | 532 | 612 | 625 |
| calls128 | 1048 | 11752 | 13429 |
| depth 16 | 207 | 1705 | 1939 |
| stream32 KiB | 40992 | 41079 | 41092 |
| irregular32 KiB | 45088 | 45175 | 45188 |

Base mode cycle ranges are compute2025–2059, calls46325–46395, depth 6585–6666, stream52516–53054 and irregular103426–104331. Off ranges are 1693–1724,1074–1097,242–289,52048–52582 and 103007–103995 respectively. CLINT time is quantized, including zero-tick empty intervals; use the raw time ranges rather than inferring sub-tick precision.

## Why call-heavy overhead is large

128leaf calls cost46328/1088=42.58× the off cycle median (4158% extra); ABI2 costs about 48.75×. Depth 16 costs 23.48× in base mode. This is a substantial runtime cost, not evidence of a low-overhead design. The ROM serializes injected instructions and accesses dictionary, frame and record memory at each call/return. Independent instret measurements expose this work directly.

The instruction deltas reconcile exactly with the control path: one existing root activation adds 80 retired instructions, a non-root adds 83, ABI2 adds 13 per activation, and an extra collision-chain hop adds 7. Thus calls add 80+128×83=10704, matching 11752−1048. ABI2 adds 93+128×96=12381, matching 13429−1048. After recursive contexts are created, root lookup has one extra hop:87+17×83=1498, matching 1705−207; ABI2 gives100+17×96=1732, matching 1939−207.

The actual symbols are leaf0x80000050, deep0x8000005a and bench_work0x8000007a. With the implemented XOR hash, deep under parent 16 and the root bench_work collide: `(0x5a>>1)^16 == (0x7a>>1)^0 ==0x3d`. This explains the 7-instruction increase for subsequent stream/irregular root lookups; it is expected chain traversal, not hidden program work or console inclusion.

Long memory loops amortize the one activation: base cycle medians rise about 0.80% for the 32 KiB stream and 0.40% for the irregular permutation. The data set exceeds L1D capacity; this is not a fully hot-cache benchmark. Small differences between base and classification fall within phase/cache variation and do not establish a speedup or free hardware. In this model classification runs alongside retirement without extra software instructions; its physical timing/area cost remains unknown.

## Setup and lifecycle boundaries

Bare setup clears1 MiB of dictionary even in the off control, then prepares metadata/selectors. It costs 1636972–1638419 cycles and 786491–786537 instructions across the six single setup observations. Off setup is experimental cache-state preparation, not a necessary cost for an unmonitored application. These are not Linux allocator measurements. Empty bare samples span12–28 cycles; raw workload deltas are preserved.

The Linux matrix includes both manual and automatic Cache+classification to avoid attributing profile differences to policy. Work results use the same ELF/body, one warmup and five repeats. Each mode is a separately launched process; stack layout, interrupt and cache history can affect small inter-mode differences. The main controlled bare comparison has fixed physical addresses.

Kernel cost probes measure dictionary/metadata/selector reset before BEGIN formatting, not kzalloc; user START also includes syscall and diagnostics. Automatic user INIT is already-enabled entry calibration, while kernel probes measure actual setup. NNP/ARM setup is separately bracketed. Pause/resume reads are deferred until frozen export, with no scheduler-path printk.

Freeze and record-copy are subsets of export. Export includes formatting, HTIF/SBI-console transfer and bookkeeping, excluding subsequent cost diagnostics and release. It is not a UART baud-rate or pure-wire result. Exec-entry→ELF-ready/failure windows exclude their own diagnostic print but include normal old-session export/new-session setup; user failed-exec samples include probe diagnostics. Application work intervals contain no output.

Probe overhead is not silently removed. Compiler sizeof measurements show a default descriptor3768B/event128B versus instrumented4368B/event176B. This can affect allocation/cache behavior. Lifecycle figures are descriptive observations of the instrumented build, not exact unprobed production costs. Default unified Linux regression compiles the probes out.

## Non-atomic Linux sampling and interrupt outliers

The three reads in a stamp are ordered cycle, instret, then time; they are not
an atomic counter snapshot. Bare time reads CLINT MMIO directly. Linux executes
`rdtime`; this Rocket CSR map implements cycle/instret but not time, so OpenSBI
handles the illegal-CSR instruction and reads the platform timer. Consequently,
the independent Linux cycle/instret window includes the first stamp's time-read
emulation and excludes the second stamp's time-read emulation. The time window
has its own slightly shifted read points. These are observable measurement
costs, not application or SSA instructions, and are kept in every mode rather
than silently subtracted.

All Linux empty samples without a timer interrupt retire422 instructions, versus
7in the bare empty sample; non-interrupted Linux off compute/call/depth and minimum-stream observations retire414more
instructions than the corresponding bare work. Compiler sequences differ by
one instruction between empty/body cases. This cross-check and the disassembled
`rdtime`/OpenSBI path explain the substantial small-ROI sampling baseline.
A few Linux repeats have an additional4025 retired instructions: for example,
classification compute1026→5051 and off stream41406→45431. Periodic timer traps
are present in the capture; these discrete steps are consistent with their
handling, rather than changed workload results. We do not remove such samples
or infer a classification slowdown/speedup from interrupt-shifted medians.
The fixed-address bare matrix is the cleaner call/memory comparison; Linux
numbers describe the instrumented OS and its real interrupt environment.

## Resource footprint, separate from measured area

Two 36 MiB physical pools reserve72 MiB outside Linux allocation. Each has 262144record slots (ID0reserved),128B slots,1 MiB dictionary and 256×64B frames. Classifier declarations total57926state bits (about 7.07 KiB): two banks,63usable rows/bank,16history entries/bank and 256shadow frames/bank. Declared memory includes unused rows; synthesis may optimize them.

The private register bank has 32logical shadow registers; declared RF memory grows31→64 slots at 64 bits, a nominal2112-bit difference including an unused zero-address slot. ABI1/2 constant ROMs contain104/118words,888B combined. These counts exclude other CSR/pipeline/control logic and are not technology-mapped cell area. No synthesis or matched no-extension fmax result is available.



## Completed Linux workload and lifecycle measurements

The full performance native exited0, powered down normally, and supplied150 work rows,30empty rows, six INIT/six failed-exec/four STOP/four EXPORT/three ARM observations. Work results match across modes and all300bare/Linux work rows also match independent closed-form arithmetic (`performance-result-oracle.json`). There are eight released sessions and 102context records. This capture supplies workload and phase costs; direct rebase proof is a separately identified companion, for the reason below.

Cycle medians (five repetitions each; raw min/median/max for cycle, instret and time are in `linux-performance-final/work-summary.json`):

| Workload | Off | Base | Cache | Classification | Manual Cache+class | Auto Cache+class |
|---|---:|---:|---:|---:|---:|---:|
| compute | 2379 | 2728 | 2820 | 2695 | 2841 | 2767 |
| calls128 | 1970 | 47082 | 54000 | 47257 | 60547 | 60287 |
| depth 16 | 1099 | 7464 | 8761 | 7605 | 8783 | 8595 |
| stream32 KiB | 62209 | 62108 | 55206 | 62541 | 62004 | 62750 |
| irregular32 KiB | 112655 | 113099 | 113138 | 112270 | 112778 | 112580 |

Instruction medians in the same order:

| Workload | Off | Base | Cache | Classification | Manual Cache+class | Auto Cache+class |
|---|---:|---:|---:|---:|---:|---:|
| compute | 946 | 1026 | 1039 | 1026 | 1039 | 1039 |
| calls128 | 1462 | 12166 | 13843 | 12166 | 17868 | 17868 |
| depth 16 | 621 | 2112 | 2346 | 2112 | 2346 | 2346 |
| stream32 KiB | 45431 | 45511 | 41499 | 45511 | 45524 | 45524 |
| irregular32 KiB | 49527 | 49607 | 49620 | 49607 | 49620 | 49620 |

Kernel phase observations from the full performance image (n is descriptive; setup/exec are not five identical workload repeats):

| Phase | n | Cycle min–median–max | Instret median | Time ticks median |
|---|---:|---:|---:|---:|
| dictionary_init | 8 | 795611–797432.0–806300 | 139962.0 | 7978.0 |
| exec_failed | 5 | 12409–12612–16057 | 3238 | 129 |
| exec_ready | 4 | 1303345–1322337.0–7885625 | 464352.5 | 13221.0 |
| export | 8 | 1511496–4040236.0–6186274 | 3170651.5 | 40403.0 |
| freeze | 8 | 902–1286.5–2793 | 711.5 | 12.5 |
| pause | 5 | 1733–2007–2114 | 920 | 18 |
| record_copy | 8 | 5555–13469.5–20119 | 3711.0 | 139.0 |
| resume | 5 | 1494–1864–2518 | 1013 | 19 |

For depth 2 specifically, pause has n2,1733–1809.5–1886 cycles and 990 instructions; resume has n2,2261–2389.5–2518 cycles and 1228 instructions. Depth 0 pause/resume medians are2021/1748cycles and920/1013instructions (n3 each). This is a small, directly observed decomposition, not an extrapolation to arbitrary depths or scheduling rates. Kernel cost stamps also use ordered, emulated time reads; their probe cost is included.

Manual user START observations are 929211 cycles (base),1011850(Cache),931610(classification),1011463(Cache+class). These include diagnostics; the extra EVENT_BEGIN line helps explain why user START differs more than the dictionary-only kernel probe. Auto user INIT1037 cycles is entry calibration, not actual initialization; the kernel dictionary_init observations measure that work. ARM costs 67326–77405 cycles in three observations, including no_new_privs setup.

Manual user EXPORT costs 3158214–6468770 cycles for19 records, including syscall, protocol, HTIF/SBI-console transfer and the subsequent cost-diagnostic prints. Kernel export costs exclude their own diagnostic prints and release; record_copy/freeze are subsets and must not be added again. The 1.51M–6.19M kernel export range also includes smaller1/3-record sessions and different sidecars. There is no fixed per-record or pure-wire latency claim. The large7.89M successful exec observation includes old19-record export and new setup; three initial auto exec observations are about 1.30M–1.33M. User failed-exec costs include its diagnostic output; the unmonitored off case does not enable that probe.

Matched manual/auto Cache+classification have the same observed instruction minima (1039/13843/2346/41499/49620 across five workloads). Their cycle medians differ by roughly−2.6%to+1.2%, within observed IRQ/cache phase variation. No causal speedup or zero-overhead policy claim follows. Linux off/base call medians1970/47082 show substantial call cost; the larger off sampling baseline and IRQ shifts explain why this ratio differs from the cleaner bare result.

### Direct accounting evidence gap and companion

The first full-run checker returned1 only for missing snapshot proof: existing kernel diagnostics print SSA_ACCOUNT when next==3(two records), whereas the full A/B fixture also calls bench_work and allocates three records. Native shutdown,150 work samples, actual timer/open2 chronology, all eight exports and phase costs passed. The original failed summary and raw capture are retained. This is an evidence-coverage issue, not a demonstrated rebase failure.

A conditional switch-only companion keeps exactly outer/inner records and inlines the same stream/irregular memory loops, using the identical kernel/SBI trees, matched measurement configuration and exact RTL executable. It does not repeat the 150 work experiments. Default full-target loadable bytes were actually recompiled and remain identical after this conditional test addition (`performance-default-equality.json`). Final acceptance requires the companion native exit, powerdown, eight snapshot-account rows, independently summed S/R intervals and semantic mutations. Primary and companion coverage remain separately recorded; no snapshot rows are invented for the original capture.

All 150Linux instruction samples reconcile with bare body work,414sampling instructions, root80/non-root83(or ABI2root93/non-root96), plus0/1/2steps of 4025 instructions. The histogram is 87zero-step,57one-step and 6two-step observations; see linux-instruction-accounting.json for actual counts and every row. The Linux addresses avoid the bare extra7-instruction collision hop. Irregular-loop minima already include one timer-sized step, so they must not be called interrupt-free. These discrete residues support the timer explanation; a full per-instruction IRQ attribution trace was not collected.

The companion completed naturally with native0 and normal powerdown:20checks pass,2sessions/4records, eight exact PID/counter snapshot rows. A excludes4463467cycles/3429517instructions/44635time ticks/12115Cache events; B excludes132475/117572/1325/147. Original/final frame differences equal independent S/R sums. The raw column is a reconstructed counterfactual, not another uncorrected execution. Five host mutation cases validate the accepted log and reject wrong delta/offset, missing rows and duplicate counter coverage. Native elapsed values use the runner monotonic clock inside the VM; they are experiment duration, not target performance. No performance SLO was imposed or a low-overhead result inferred.
