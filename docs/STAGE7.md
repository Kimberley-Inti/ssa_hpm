# Stage7: complete frozen monitoring results

Status: accepted on actual single-hart Rocket/Verilator Linux. One independent
public-source kernel/OpenSBI image completed normally (native exit0/power-down).
25 export,70 event,37 exec and179 process checks passed, plus36 synthetic host
checks and4 real-prefix/host-mutation checks. Full evidence: [summary](../evidence/stage7/summary.json).

Scope and final-project decisions are in [ACCEPTANCE.md](ACCEPTANCE.md). The new
format, counter semantics, synchronization and compatibility are in
[EXPORT.md](EXPORT.md). This stage implements core export/offline analysis TODOs
from design p13–14; it does not invent data-classification or multicore semantics.

The old exporter iterated only32 records, declared larger sessions incomplete,
and mapped only an8KiB proof window. It also printed the entire export with IRQs
masked. Hardware still allocates up to262143 usable128B records. The new path
freezes selection/state briefly, then maps/copies at most2KiB of records per chunk
and emits serial rows with IRQs enabled. The pool remains busy and the stopped
descriptor cannot resume. A final marker distinguishes transfer completion from
open/spilled/exhausted/invalid monitor state. The host verifies counts, contiguous
IDs/chunks,64-bit word checksums, counter metadata, parent/callee keys, open-frame
multiplicities and release-before-reuse.

STOP now preserves its actual cutoff; op5 exports the current STOPPED descriptor
once. Exit/committed exec export automatically if op5 did not, then release.
Open frames are abandoned, never fabricated as returns; the tested ENOENT path
retains the original live session. No privileged pool addresses/other PIDs can
be passed to op5. Both ABI1/ABI2 and all four previously accepted counters retain
their meanings and memory offsets. The chosen DTLB profile and pause accounting
are unchanged. Extra mapping/printing may change current sampled values; old
absolute Linux differences are history, while the same identities and negative
controls are the current regression criteria.

## Reproduce

Install current public patches/standalone suite using REPRODUCE.md. Use new work
and output paths (scripts refuse source/execution overwrites):

```sh
source ssa/env.sh
# Reuse a stage6 model only after checking its hash/source/config. Otherwise:
make -C sims/verilator CONFIG=SSAHPMEventRocketConfig -j6 \
  OPT_FAST=-O3 OPT_SLOW=-O3 LINK='/usr/bin/g++ -B/usr/bin/'
python3 ssa/linux/build-progress.py --workspace "$PWD" \
  --config SSAHPMEventRocketConfig --out /tmp/ssa-export-model
python3 ssa/linux/build-a.py --export --work /tmp/ssa-export-linux --jobs 6
python3 ssa/linux/run-exec.py --export --work /tmp/ssa-export-linux \
  --simulator /tmp/ssa-export-model/simulator-progress \
  --out-dir /tmp/ssa-export-results --timeout 172800
python3 ssa/linux/export_results.py /tmp/ssa-export-results/rocket-linux-events.txt \
  --out /tmp/ssa-export-results/monitoring.json --tree-limit 64
python3 ssa/linux/test_export_results.py --out /tmp/ssa-export-host.json
```

Current actual command reuses `/tmp/ssa-hpm-stage6/progress/simulator-progress`,
SHA256 `5d0ad7923007c12b67f18c613550d2476d7ef501d21849e90e8b9b7233450b52`,
and builds `/tmp/ssa-hpm-stage7/independent-linux` from public pinned Linux/SBI
bases plus all patches. Model source/config and Rocket commit469bfac7 are unchanged.
Compiler/tool dependencies are reused; kernel and firmware are freshly built.
The separate new-directory clean stage7 patch application also matches the
Linux development tree exactly; see evidence/stage7/source-match.json.

## Acceptance and coverage

- Actual Linux target:41 allocated records (one parent/40 distinct leaves, first
  repeated),41 sequential IDs and3 chunks; exact ELF-address/parent matching.
- Two-record ABI1 STOP/EXPORT and repeated-export rejection; zero-record clean
  terminal; two-record ABI2 exit with an open parent correctly incomplete.
- All pools retained through terminal export and released before subsequent
  START; same-PID old/new exec epochs remain separate and exported once.
- Full affected stage6 event gates, stage5 exec gates and stage4 process gates in
  the same actual boot. Prior low-level RTL/Spike results are reused, not rerun
  or substituted for Linux evidence. No RTL source changed.
- Host-only36 gates cover ABI1/2 small and chunk-boundary counts, maximum-capacity
  arithmetic and malformed/missing/duplicate/truncated streams. No massive
  full-capacity serial execution or kernel mapping-failure injection is claimed.

Source/full-SHA mapping: evidence/stage7/source-commits.json and HISTORY.md.
The native run must have actual exit0, normal power-down, a complete versioned
stream and all new/affected checkers passing before this stage is accepted.

## Historical in-flight checkpoints

The following checkpoints preserve the evidence available during the single long
run. Their pending/false global summaries are superseded by the final acceptance
below; no native rerun was used.

### Native41-record checkpoint

The first real session completed with41 records,3 chunks (16/16/9), IDs1..41,
all40 leaves parent1 and exactELF callee addresses. Repeated leaf ID2 instret46
versus23 in other leaves proves record reuse. Header/end status0, complete1;
END word checksum871b3b3ee92eb291. The pool release marker was captured.
The parser accepted all chunk/end hashes, and host mutations of this real prefix
(missing chunk, duplicate chunk, missing END) were all rejected. This is a passed
checkpoint, not yet the entire Linux/regression acceptance. The initial missing
END was from live incomplete input. Exit143 belonged only to the intentionally
restarted old monitor (session16333); native PID301709 remained running.
Evidence: evidence/stage7/first41/ and monitor-restart.json.

### Four-case native checkpoint

The new fixture completed all four real children and emitted its suite END.
23 export-specific gates passed:41/2/0 records, explicit STOP/export/repeat and
busy behavior, one abandoned parent with a closed child, exactELF identities,
all record/chunk hashes and release-before-reuse. Parsed sessions1/2/3 are
semantically complete; session4 has status1(open), records_complete1 and
complete=false. Every pool was released. The frozen-prefix checkpoint deliberately
uses exit-code-1: overall power-down and old-suite regression are pending, not
failed hardware cases or final acceptance. Its25-gate precheck has exactly those
two pending gates; see evidence/stage7/export-fixture/.

The chained original lifecycle payload lives at /lifecycle. Historical graders
use the logical init role, so grade-export remaps that role to the actual
/lifecycle ELF only for delegated old checks; new /init remains the export
fixture. Exact archived-stage6 /init hash/symbol equality was verified. A historical
log check reproduced two wrong-role tree failures before mapping and all70/37/176
passes after mapping. This is an oracle correction, not another Linux execution.

### Host runtime budget

The current VM run exceeded7h before the full chained suite completed. New
--export runs default to172800 host seconds (48h); an explicit --timeout overrides
it. Legacy modes retain21600. This changes only host supervision, not target
cycles or counters. The running image/model are immutable and were not restarted.
The already-running command initially requested43200; a narrowly scoped host
supervisor is armed to preserve it only if that limit is approached: stop only
the verified waiting Python runner, allow the native child to continue, then
resume the runner after child exit to reap the actual kernel exit status. A
separate real subprocess.run host check verified that sequence; any actual action
is recorded in timeout-protection.json, never presented as a native failure or
a second simulation. At this checkpoint no extension action has occurred.

### Actual lifecycle checkpoint

The same native boot completed original success/ENOENT/replacement-exit cases.
35 lifecycle-specific gates pass; only final shutdown and later stage4 regression
remain pending in its37-gate summary. PID18 old/new sessions5/6 have image2/3,
closed leaf3318/6618, old abandoned parent and new closed tree; both terminal
checksums and pool releases parsed correctly. Failed exec session7 preserves
its old tree and returns normally. These are new native results, not the earlier
archived-log role-map oracle check. See evidence/stage7/lifecycle-checkpoint/.

## Final native acceptance

The same simulation finished after51379.89 host seconds. Native exit0 was recorded
both in execution.json and in the kernel zombie wait status before resuming its
waiting Python runner. The runner then reaped0 and all delegated graders returned0.
Normal `reboot: Power down`, four `SSA LINUX DUAL USER PASS` markers and the final
process-fixture PASS are present. No model restart or second Linux execution.
The host supervisor acted at42039.43s: STOP only the waiting runner, let the native
child run, capture raw kernel wait0, CONT runner. This avoided its original12h
host timeout; future documented commands use48h. Actual actions are preserved in
[timeout-protection.json](../evidence/stage7/timeout-protection.json).

| Actual check layer | Passed | Evidence |
| --- | ---: | --- |
| Stage7 export / terminal checks |25/25|linux/summary.json|
| Stage6 event and dependencies |70/70|linux/regression/summary.json|
| Stage5 exec and dependencies |37/37|linux/regression/baseline/summary.json|
| Stage4 process and sampling |179/179|linux/regression/baseline/regression/summary.json|
| Host capacity/protocol faults |36/36|final-host-tests.json|
| Real41-record prefix plus host mutations |4/4|final-host-tests.json|

The179 process checks retain all176 stage6 checks (including all173 original
stage4 checks). The three extra assertions validate a fourth actual sample event
in the last legacy A; no historical gate was removed. Counts across layers are
separate gates, not separate simulation counts.

The complete version1 stream contains24 sessions,87 records and25 chunks. Every
session transferred its declared record count and released its own pool. Semantic
incomplete sessions4/5/13 deliberately mark an abandoned parent (fixture and old
ABI1/ABI2 exec); valid transport does not turn an unfinished call into a return.
The first41-record session has chunks16/16/9 and END871b3b3ee92eb291; allIDs,
parent/callee relationships, repeated-context reuse and all checksums passed.
Explicit STOP/op5, duplicate-export rejection, held-pool busy rejection and empty
session checks passed. Old/new same-PID exec epochs were separately exported once,
release preceded pool reuse, and failedENOENT retained the old session.

Actual DTLB common contexts count2(warm) versus127(cold). Corrected A resumes from
depth2 and records6=1131(raw)-1125(paused); legacy A deliberately records1133(raw),
retaining its1125 paused events. Original three-counter corrected long-short deltas
are cycle620,instret-40,time6; legacy deltas202135/202484/2022. Open-frame sample
identities passed for every counter; pre-S/post-R costs remain included. Absolute
values are this run's observations, not substituted historical expectations.

The independent public reconstruction's installed graders replayed the SAME
completed raw log and produced identical record JSON and all check booleans;
[report](../evidence/stage7/independent-final-check.json). This is an independent
entry-point check, not a second Linux run. Its7 rebuilt userspace ELFs match the
running image; the fresh public Linux/OpenSBI build matches the source trees.
Unchanged Rocket model, low-level RTL and Spike evidence were verified/reused;
there was no new RTL generation, model build or Spike run in this stage.

Raw log: [rocket-linux-events.txt](../evidence/stage7/linux/rocket-linux-events.txt),
SHA256 `17f30d2231bb10d9bf584fedb550c3c416c23e5a1f6d7e132fb1b7f0951aaa68`.
Image/model hashes and actual argv are in linux/execution.json. All artifact
hashes are in artifact-hashes.json; in-flight checkpoint summaries remain labeled.

To check the committed evidence without launching another simulation:

```sh
python3 integration/ssa/linux/grade-export.py \
  evidence/stage7/linux/rocket-linux-events.txt --exit-code 0 \
  --users evidence/stage7/linux/user-elfs.json --out-dir /tmp/ssa-export-recheck
python3 integration/ssa/linux/test_export_results.py \
  --native-log evidence/stage7/linux/rocket-linux-events.txt \
  --out /tmp/ssa-export-host-recheck.json
```

Actual target coverage is41 records, not262143; maximum arithmetic and malformed
streams are host-only tests. No guest filesystem service, native mapping-fault
injection, cancellation/retry, multicore or arbitrary unwind is claimed. The
current single-hart profile's core acceptance is complete. Remaining original
extended objectives and optional work are distinguished in ACCEPTANCE.md.
