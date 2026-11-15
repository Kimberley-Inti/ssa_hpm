# Bounded prototype final delivery checklist

Scope is ACCEPTANCE.md: one hart, trusted kernel/firmware, audited non-privileged
single-thread LIFO targets and the tested musl continuation adaptation.
Native/semantic requirements and 12-step host evidence replay passed; audit/publication receipts
are in evidence/stage11/summary.json and the release/integration receipt.

## Required functionality and final review

- C01–C10/D01–D03 are accepted only with their documented adaptations and limits.
  Ordinary selected static and musl dynamic targets require no SSA calls.
- ABI1/2, selectors, 64/40-bit counters, wrap, private CSR/pool permissions,
  ownership, pause/rebase, exec, stop, exit and release were reviewed and checked.
- R01/R02 declare/check whole classification sidecars. Transport completion,
  abandoned calls and classifier coverage remain distinct; legacy is undeclared.
- R04 fixes progress interleaving. R05 closes a diagnostic coverage gap with a
  separate real two-record companion and exact perPID/counter proof validation.
  Initial host failures and their repaired checks remain in the evidence.
- Public source fetch/patch application,111file hashes/ROM, actual new Scala/RTL/
  Verilator build and three separately built public-source Linux payloads pass.
  Dependency/musl caches and toolchains were reused and identified.
- Fresh directed cases40(6Spike references/34RTL), WB oracle9, production Linux
  51automatic/26manual plus10ELF/5automatic/3manual negatives pass.
- Formal bare150work/30calibration and Linux150work/30calibration measurements,
 20composite performance checks and 20direct companion checks pass. Companion
  negative suite5cases passes. All four native captures exit 0; all three Linux
  payloads power down normally. Original failed host runners are not rewritten0.
- Final host-only replay and complete-history/file audit must pass before merge;
  their actual receipts govern this gate. Ordered patches and rights notices are
  retained; images, upstream trees, backups, credentials and original design PDFs are excluded; the authored English report is a checked publication artifact.

## Performance evaluation completed

Independent target boundaries, warmup1/repeats5, exact workloads/results,
raw samples and min/median/max cover off/base/DTLB/Cache/classification in bare
mode, and off/base/Cache/classification/matched manual-auto Cache+class in Linux.
DTLB Linux remains historical; automatic DTLB is untested.

Initialization, regular work, depth0/depth2 switching, successful/failed exec
and export/console costs are separately described. Non-atomic emulated time reads
and timer outliers are explained without removing samples. Call-heavy overhead
is substantial(42.58× bare base/off); no low-overhead claim or numeric performance
SLO is invented. Model elapsed time is not target speed. Nominal state/pool/ROM
sizes are recorded; no matched unextended model, synthesis area, fmax or power
measurement was performed.

## Current adaptation limits, not hidden completed capabilities

- Single hart, at most2monitored pools,36 MiB each; no perf sharing/migration.
- At most12retained pause diagnostics/session; source-reviewed overflow stops
  with partial state. More-than 12-pause stress was not newly hardware-tested.
- Full-tree domain is at most256frames; deeper folding has no sticky count after
  unwind. Export completion does not prove arbitrary inputs respected that bound.
- Classifier: integer retired load/store1/2/4/8B, virtualPC/address,2banks,
 63rows/16FIFO histories; eviction rewarms and dropped coverage is explicit.
- Tested dynamic case is musl, including an abandoned loader continuation;
  arbitrary non-LIFO/tail-call runtimes, custom signal unwinds, shared-mm/vfork,
  multithreading and privileged exec are not accepted. Rejection and scope differ.
- Auto DTLB/other untested profile combinations retain unaccepted status.

## Optional follow-up or requirements if the product scope expands

There is no remaining functionality task inside the declared tested prototype
once the recorded packaging gates pass. Production/generalization work would
need a new scope: bounded diagnostic streaming for long sessions, a call fast
path/overhead optimization, configurable memory pools, multi-hart/task migration,
non-local unwinding, full-capacity long stress, wider memory instruction coverage,
more events, general symbolization and non-console export. Reliable synthesis or
a matched no-extension implementation is needed for hardware-cost conclusions.

After final acceptance, the user authorized dependency-order merge commits of
only this repository's stage PRs, main tree equality verification and a new private
release. Preserve original commits, stage branches and v0.1.0. Integration.md
specifies the checks; actual GitHub read-back supplies the main SHA/tag/release.
