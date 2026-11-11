# Stage7: complete frozen monitoring results

Status: implementation,36 host tests and independent public Linux/OpenSBI image
build passed. Actual Rocket/Verilator Linux export and affected regression are
running; final acceptance is not yet claimed.

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
  --out-dir /tmp/ssa-export-results --timeout 43200
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

## Native41-record checkpoint

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
