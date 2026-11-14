# Stage6: one real DTLB event attributed to software contexts

Actual RTL and independent Rocket/Verilator Linux acceptance passed. Native exit0, normal power-down; 70 event gates,37 lifecycle gates and176 process checks passed, including all173 historical process gates.

## Event and contract

The original design page12 lists Cache/TLB events for later extension and reserves
counter slots; it does not specify a request-owner protocol. This stage selects
one existing Rocket event, not a synthetic miss signal: DCache
`io.cpu.perf.tlbMiss := io.ptw.req.fire()`, forwarded to Rocket's EventSet2 bit4.
This counts data translation requests accepted by the PTW, including ones served
by the PTW's translation cache. It is not a count of unique pages, retired loads,
page faults, cache refills, or full memory page-table walks. Retried/replayed or
subsequently faulted/squashed accesses may cause accepted requests too.

The selector is `(1<<4)<<8 | 2 = 0x1002`, mhpmevent3 CSR0x323. The standard Rocket
counter is40 bits (CSR.hpmWidth), machine CSR0xb03 and delegated view0xc03. In the
new single-hart SSAHPMEventRocketConfig exactly one programmable counter exists;
the original RocketConfig and original104-word ABI1 ROM are retained. Firmware
sets selector4098, initializes the counter once, clears inhibit bit3, enables
S-mode access via mcounteren and denies U-mode access via scounteren. Enable bits
control access, not increments; the reference PDF page5 explicitly distinguishes
these from mcountinhibit. No perf/SBI PMU multiplexing is implemented.

Attribution is the interval between each frame's fourth-counter snapshots, with
inclusive parent counts. Rocket's existing RegNext introduces one cycle from
accepted request to HPM increment, verified in the source trace. It is the actual
increment relative to the CSR sample boundary that determines attribution, not
the context that originally initiated the translation. A delayed increment can
cross call/return or scheduling boundaries. No per-request context tag or
speculation cancellation is added. The blocking dependent-load/fence test checks
the observed return boundary; it does not establish universal draining for every
possible speculative or replayed request.

The event has no privilege/trap/notification filter. Kernel/trap events within a
frame's window count even though kernel calls do not create application records.
The trusted ROM uses physical M-privilege data accesses, which do not initiate
translation in this profile; delayed requests accepted while ROM runs would
still follow interval attribution. There is no monitor-overhead subtraction.
Pausing adds the fourth counter's actual R-S to every open fourth snapshot,
excluding all events within that sampled interval. Pre-S/post-R and physical
handoff/restore costs outside it remain charged by the stage4 policy.

ABI2 is explicit START flag bit1; bit0 still selects the legacy negative control.
Flags0/1 use ABI1, flags2/3 use ABI2. Frame offset32 and record offset40 are used;
all original offsets,64-byte frames,128-byte records and36MiB pool layout remain.
The fourth values/record accumulation are zero-extended40-bit modulo2^40, whereas
the three original counters retain64-bit semantics. An individual sampling
interval must contain fewer than2^40 events. HPM3 is not reset on task switches,
START, STOP, exec or exit. The new profile and tags are described in ABI.md.

New event state follows the task's owned descriptor. Resume restores the correct
ROM mode and pool after rebasing. STOP/pause/committed exec/exit clear mode bit1
and selection. New allocations initialize record offset40 and new pushes write
the fourth snapshot. Old open exec frames are abandoned, not fabricated as
returns. New images explicitly enable fresh sessions; pre-commit ENOENT preserves
the old session, tree and all four snapshots. Multithreaded/setuid/post-commit
failed exec, migration, nonlocal unwinding and full-capacity export remain out
of scope. Only this one TLB event is implemented, not generic access classes or
all Cache/TLB events.

## RTL evidence already passed

Five actual RTL executions are under evidence/stage6/rtl-events:

- normal:257 accepted requests,257 HPM increments, one-cycle source/increment
  correspondence; global2→2→129→257. Same common under two parents records0 and255. The cold path runs twice, reusing the same record; the two nonzero activation deltas are127 and128.
- wrong selector0: real PTW requests remain present while HPM/records stay0;
  the positive oracle fails and the program exits42 as expected.
- swapped contexts: high/low workloads are exchanged between parent paths;
  the positive mapping oracle fails and the program exits42 as expected.
- wrap: counter starts at2^40-8, global pre-call2^40-6 and final249; the closed
  cold record is255. This tests real hardware width and modular subtraction.

The 4KiB test mapping uses128 data pages, with the first page warmed before enable.
ABI2 all-register canaries, x5 calls/returns and ordinary JALR jumps also passed.

One DTLB set,32 base-page ways in4-page sectors and4 superpage entries are retained
from RocketConfig. The two common records share the same callee but have different
parent IDs. The return interval exactly matches its global HPM delta in these
runs. No accepted request was observed during private ROM execution in this test;
that is an observation, not an event-source filter.

The optional `+ssa_event_trace=1` needs `+verbose` because Chipyard gates Chisel
printf with its standard verbose switch. Full instruction logs remain in the
local result directory, with their SHA-256 in summary.json. The published .txt
excerpts retain every source/increment pulse and every event/global/record/test
line; no pulses are sampled or synthesized. Large unrelated instruction traces
are excluded from the standalone history. The normal Linux run does not enable
verbose or source tracing.

All24 existing low-level tests were actually rerun (6 Spike references,18 RTL),
not reused: nested/trap/interrupt/overflow/ABI/capacity/two-pool/privilege probes.
The original context benchmark still has6 records and common instret14452/7226.
Spike has no SSA event extension and is not used as a DTLB event oracle.

## Reproduce

First use REPRODUCE.md to fetch the public Chipyard/Rocket baselines, apply all
current patches and install the standalone suite. Linux applies compat0001,
task0002, exec0003, then event0004. OpenSBI applies platform0001 and profile0002;
the latter preserves both profile and U-mode-permission source commits. Local
source commit fetches are never required. Compiler/dependency caches are reused;
Linux/OpenSBI source and kernel/firmware image were independently rebuilt.

```sh
source ssa/env.sh
make -C sims/verilator CONFIG=SSAHPMEventRocketConfig -j6 \
  OPT_FAST=-O3 OPT_SLOW=-O3 LINK='/usr/bin/g++ -B/usr/bin/'
make -C ssa all events -j4
python3 ssa/verify_events.py \
  --simulator "$PWD/sims/verilator/simulator-chipyard-SSAHPMEventRocketConfig" \
  --out-dir /tmp/ssa-event-rtl
python3 ssa/linux/build-progress.py --workspace "$PWD" \
  --config SSAHPMEventRocketConfig --out /tmp/ssa-event-model
python3 ssa/linux/build-a.py --event --work /tmp/ssa-event-linux --jobs 6
python3 ssa/linux/run-exec.py --event --work /tmp/ssa-event-linux \
  --simulator /tmp/ssa-event-model/simulator-progress \
  --out-dir /tmp/ssa-event-linux-results --timeout 43200
```

Use fresh result/build directories: the scripts refuse to overwrite executions
or source checkouts. The host progress harness reads PC/CSR state only and verifies
the generated model archive hash is unchanged. Fast generated C++ is compiled
with -O3; no simulation semantics or cycle/event source is replaced by a model.

The one Linux image chains the original stage5 exec cases, an ABI2 context test,
two real preemption cases (corrected/legacy, B512 pages), ABI2 successful/failed
exec and replacement exit, then the original stage4 fixture. grade-events.py
checks new event records/identities and delegates the original actual boot prefix
and actual regression suffix to the unchanged stage5/stage4 checkers. Removed
segments are separately graded as the event suite; no invented records or samples
are inserted. The new user HPM3 read probe must receive SIGILL. Expected results
are first-image completed/abandoned records, a fresh replacement session and one
normal failed-exec session, all independently owned and exported once.

Cache/TLB contents are not partitioned between processes. A's own translations
caused by context-switch flushes or evictions on resume remain A's interval events;
only increments inside the sampled pause interval are removed. This is monitoring
state/accounting isolation, not microarchitectural cache partitioning.

An independent public Chipyard/Rocket reconstruction regenerated RTL and rebuilt
SSAHPMEventRocketConfig, then passed all five new RTL tests. This is an actual
independent model build/execution, not merely log regrading. The version-checked
dependency modules/toolchain and caches were reused; see independent-model-build.json.

### Native scheduling defect found before acceptance

The initial Linux run reached the context export but then looped in `ssa_hpm_switch`. The actual PC trace and disassembly located the resume loop: `d[3]` still held only three temporary deltas while ABI2 iterated four counters. The fourth write corrupted adjacent stack state. It is now `d[4]`; a new-directory clean patch application reproduces the corrected kernel tree. The stopped run is failure evidence, not accepted Linux results. The corrected independent kernel and firmware were rebuilt and the full Linux suite restarted using the unchanged verified Rocket model.

## Actual Linux results

The freshly built independent Linux/OpenSBI image ran 19238.93 host seconds. All70 new event gates,37 unchanged stage5 lifecycle gates and176 stage4 checks (all173 historical gates plus three samples for an additional real scheduling event) passed. This was one real Rocket RTL Linux execution, not a Spike event model. Kernel/firmware source trees match local commits exactly. See evidence/stage6/linux/execution.json for the actual command, exit status and immutable model/image/log hashes.

| Test | Role | PID | Session | Pool | Fourth count in common |
| --- | --- | --- | --- | --- | --- |
| 8 | 0 | 17 | 4 | 0x88000000 | 2 |
| 9 | 2 | 18 | 5 | 0x88000000 | 1069 |
| 9 | 1 | 19 | 6 | 0x8c000000 | 7 |
| 10 | 2 | 20 | 7 | 0x88000000 | 1077 |
| 10 | 1 | 21 | 8 | 0x8c000000 | 1130 |
| 5 | 0 | 22 | 9 | 0x88000000 | 64 |
| 6 | 0 | 22 | 10 | 0x88000000 | 128 |
| 7 | 0 | 23 | 11 | 0x88000000 | 128 |

Fourth-counter pause proofs (all values modulo2^40):

| Test | Role | Original | Rebased | Excluded | Recorded | Raw |
| --- | --- | --- | --- | --- | --- | --- |
| 9 | 2 | 5002 | 5010 | 8 | 1069 | 1077 |
| 9 | 1 | 5010 | 6133 | 1123 | 7 | 1130 |
| 10 | 2 | 6917 | 6917 | 8 | 1077 | 1077 |
| 10 | 1 | 6925 | 6925 | 1123 | 1130 | 1130 |

Both pairs have actual IRQ5 A→B→(unmonitored task)→A evidence, B open-frame sleep/resume and reciprocal cycle sample chronology. The corrected fourth snapshot equals original plus sum(R-S); the legacy snapshot stays unchanged and fails that positive identity. B page faults/kernel work and export inside A's pause are included in the excluded interval; resume translations/handoff costs outside it remain charged. U-mode HPM3 read was rejected with SIGILL. The context test reused four records for warm/cold/warm paths. Extended exec exported the old closed child and abandoned parent once, replaced the image under the same PID, then enabled a fresh session and exited; ENOENT kept the original open frame/session until normal return.

The current original-regression differences are:

| Counter | Corrected long-short | Legacy long-short | Additional excluded interval |
| --- | --- | --- | --- |
| cycle | 9824 | 197399 | 219299 |
| instret | 4238 | 200919 | 210529 |
| time | 99 | 1974 | 2192 |

These are new-image results, not a requirement to reproduce historical4205/211029 or20/207962. All unchanged sampled accounting identities, parent/child checks, negative-control relations and actual shutdown gates passed. Independent installed-checker regrading is recorded separately and does not represent a second Linux execution.

## Final source delivery and independent verification

| Component | Source commit |
| --- | --- |
| chipyard | `d954827faca21a1534ac89db748896f0c319c559` |
| rocket | `469bfac7de26bfbb03298787ad030898c6de24c9` |
| linux | `49943b80f864a41e4ac13108a77f921e013d3570` |
| opensbi | `34520a712309790d3e9a005194b763467b980fdb` |

A final new workspace `/tmp/ssa-hpm-stage6-final-apply` fetched the public Chipyard/Rocket baselines, applied every current patch and matched the complete expected file manifest and both ROM banks. The corrected kernel patch also applied in a separate directory and matched the development tree. The prior independent model rebuild and its five test executions are reused because Rocket source did not change after them. The corrected independent kernel and firmware were incrementally rebuilt using the existing pinned compiler/build caches. No second Linux execution is claimed: the independently installed checker regraded the same completed raw log and reproduced70/37/176 passes. See final-public-apply.json, resume-array-fix.json, linux-image-build.json and independent-linux-regrade/.

The process checker adds three assertions automatically for one extra real scheduling event in legacy test3 (counter0/1/2). Its176 gates contain every historical173 gate; no old gate was removed. Each completed native result has exit0 and `reboot: Power down`.
