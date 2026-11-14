# Stage9: retired memory access classification

Status: accepted for the bounded rule1 single-hart profile. The original real
Linux run completed native0, checker0, normal powerdown and26/26gates after
9687.36seconds. All7sessions/20context records were completely exported and
released. D02 is closed within the scope below; see
[evidence/stage9/summary.json](../evidence/stage9/summary.json).

Base: stage8 maintenance cdcf64fd5a9e2321b43fd68070b3ee45d12b42de,
Chipyard897f5d3043aeab785ef4700bc0c4b6f45c25cbc9,
Rocketbccfc47a4aecbef59aa4d4c73f15159b78ab123c,
Linux275125fabacde9e83f4bff6863bf25012537e0ed,
OpenSBI43f02ffb329d9c86b2ff2138dc450b2060778ffe. PR7 was verified Open/Draft,
base stage7, head stage8 at the stated SHA. Existing work and untracked files
remain preserved; all new source work is on stage9-memory-classification.

## Rule and implementation

[Classification rule1](CLASSIFICATION.md) supplements design PDF physical p12
§3.1(2). It observes actual WB-retired integer loads/stores at virtual effective
addresses, partitioned by session/context/PC/op/width. Two accesses warm a key;
equal zero deltas indicate scalar-repeat; equal bounded nonzero aligned deltas
indicate fixed-stride stream; other accesses are irregular/unrecognized, not
statistically proven random. This is a per-access label, not a whole-function
majority label. Pointer-table loads and target-data loads are both observations.

Two owned epoch banks preserve FIFO16-entry histories and256-level RID mirrors
across scheduling; record1..63 have exclusive64-bit counts. Total logical state
is57926bits plus70CSR bits, not placed FPGA/ASIC area. Capacity limitations,
unframed observations, dropped observations, eviction and overflow are explicit.
Base context records remain full-capacity and retain inclusive HPM semantics.

The trusted kernel opts in with START bit2; it binds/reset the owned bank, clears
selection while off CPU, and restores the retained epoch before U-mode resume.
Classifier input filtering excludes kernel/traps/private-ROM and other tasks.
This differs from the unchanged free-running inclusive HPM S..R subtraction.
Shared Cache/TLB state may affect latency/preemption, but never changes the
classifier's virtual address rule. No private ROM instructions were added.

## Actual verification

- New Scala compilation, RTL generation and Verilator model build completed0.
- Four native classification fixtures completed0: scalar/stride/irregular with
  repeat calls and distinct parents; actual load access fault;72-context capacity
  and FIFO eviction; mode switch/interleaved PCs/four store widths. Per-access
  independent reference, row partitions, native exits and deliberate host
  category/context mutations are checked, not a PASS substring.
- Additional exact ELF-linked virtual address oracles pass on the same raw logs.
- A separate read-only host harness, linked to the unchanged RTL archive,
  captured82WB candidates:7replays and1exception were excluded;72observations
  recomputed independently exactly match all hardware category sums.
- Two S-CSR U-mode permission probes complete0 (architectural probes, not Linux).
- All34 existing low-level cases pass (prior29 plus5Cache):6Spike reference
  and28actual RTL, including
  native DTLB/Cache sources, negative selectors,40-bit wrap, ABI canaries,
  traps, two pools, and U/S MMU permissions. Legacy process negative exits42 as
  expected. Golden6records and common.instret14452/7226 remain unchanged.
- Host tests:14rule examples,48old export cases,21classification protocol cases.
 64-bit overflow transport handling is host-only, not2^64 hardware execution.

Public pinned Chipyard/Rocket fetch and complete patch application match the
Rocket tree and source file manifest. Independent bareELFs were rebuilt and all4
classification cases actually executed, reusing the verified new model. Linux
and OpenSBI were fetched publicly and built independently; reconstructed kernel
tree equals developer kernel. Toolchain/dependency/ccache caches were reused.
A second Scala/C++ model build is not claimed for the independent workspace.

## Reproduction entries

After the standard public installation in REPRODUCE.md:

```sh
source ssa/env.sh
make -C ssa -j4 all events cache-events linux-probes classification
make -C sims/verilator CONFIG=SSAHPMEventRocketConfig -j6 OPT_FAST=-O3 OPT_SLOW=-O3 LINK='/usr/bin/g++ -B/usr/bin/'
python3 ssa/classification/test_reference.py
python3 ssa/classification/run.py --simulator sims/verilator/simulator-chipyard-SSAHPMEventRocketConfig --out-dir /tmp/ssa-rule1-rtl
python3 ssa/linux/test_classification_results.py
python3 ssa/linux/test_export_results.py --out /tmp/ssa-export-host.json
python3 ssa/linux/build-a.py --classification --work /tmp/ssa-rule1-linux --jobs 6
python3 ssa/linux/build-progress.py --workspace "$PWD" --config SSAHPMEventRocketConfig --out /tmp/ssa-rule1-progress
python3 ssa/linux/run-classification.py --work /tmp/ssa-rule1-linux --simulator /tmp/ssa-rule1-progress/simulator-progress --out-dir /tmp/ssa-rule1-linux-results
```

Choose new output/work directories. The runner preserves native code, model,
image/userELF/log hashes, checks normal shutdown and invokes the exact lifecycle
oracle. Progress lines may interrupt UART lines; the host parser normalizes only
those known diagnostic labels, retaining the original capture unchanged.

## Completed real Linux acceptance

The original detached process was reused through normal shutdown; no Linux
simulation was restarted. It executed the independently built public-source
kernel/firmware image on the verified new Rocket model.26gates cover:

- Explicit STOP:6records/72observations, first parent leaf32/4/14/12/2, second
 16/4/0/12/0, third16/4/0/6/6 (input/warmup/scalar/stream/irregular).
- Successful exec: old4records/39observations with openRID3. Its5exclusive
 observations are retained as partial; old open HPM record remains0 and is not
 fabricated as a normal return. Same PID15 then starts clean session3/image2,
 exports2records/18observations and exits normally.
- ENOENT precommit failure: original2records/39observations, no new session or
 loss of frames. Repeated leaf vector32/4/0/12/16 proves history was retained.
- Empty explicit STOP/export:0records/0observations, terminal seed checksum.
- Real two-task scheduling: B PID18/session6/pool0x88000000 and A PID19/session7/
 pool0x8c000000 retain separate history and3-record chains. A's leaf is
 32/4/14/12/2; B's is32/4/0/24/4. Both stacks restore to0. A timer preemption
 occurs with2open frames/RID2; strict B.S<A.S<B.R<A.R chronology, all4counter
 pause deltas and an unmonitored-task handoff pass. Classification is filtered
 at source, so B cannot add accesses to A; existing HPM rebasing is unchanged.

The two irregular accesses in A's otherwise stream-like pointer-table loads are
the repeated-call address restart; B restarts both its pointer and data streams,
producing4irregular accesses. These deterministic transitions are part of rule1,
not evidence of statistical randomness. Shared Cache/TLB pollution may change
latency and HPM counts after resume; it cannot change the virtual address rule.

A separate host negative swaps the A/B leaf category vectors and repairs both
checksums. Transport remains valid; only the semantic attribution gate fails.
This is a host mutation of the original capture, not a second faulty hardware
execution. See linux-semantic-negative.json. Reproduce with:

```sh
python3 ssa/linux/test_classification_native.py --native-log /tmp/ssa-rule1-linux-results/rocket-linux-classification.txt --execution /tmp/ssa-rule1-linux-results/execution.json --out /tmp/ssa-rule1-owner-negative.json
```

Other limitations remain: no FP/vector/AMO/PTW classification, no mathematical
randomness guarantee, finite history/row/session capacity, no transparent
loader/product support, no multi-hart migration/nonlocal unwind. Existing DTLB
and Cache profiles stay recognizable; the new directed Linux classification
image selects the Cache profile. Spike is only an architectural/software
reference and does not implement this classification extension.

First live Linux checkpoint: session1 explicit STOP exports all6records and72
observations with checksum b1f4413898179ce2. Leaf vectors are32/4/14/12/2,
16/4/0/12/0 and16/4/0/6/6 (total/warmup/scalar/stream/irregular).
This was an intermediate checkpoint; the final completed evidence is linked above.

Scheduler evidence: A PID19 event2 switches to B PID18 with depth2/RID2,
TASK_RUNNING, ivcsw4 and supervisor timer cause0x8000000000000005; restored
from unmonitored task7. The hook preempt=0 is expected for this kernel's
IRQ-return schedule(false) path. Existing stage4/6 oracles use these same
state/IRQ/chronology criteria. An implementation requiring preempt=1 would
incorrectly reject this actual user preemption.
