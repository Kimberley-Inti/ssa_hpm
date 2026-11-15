# Requirements and acceptance

This matrix defines the completed research implementation. Page numbers refer
to the physical pages of the supplied14-page design brief and 13-page HPM overview.
The original PDFs remain local; source and evidence links identify the published
implementation and executable design supplements.

## Design basis

The brief describes calling contexts, SCStack, SCDict, HPERecords and three basic
counters, then lists memory patterns and Cache/TLB events as dataflow objectives.
Its loader, OS lifecycle and offline-format details are open design points.
The implementation specifies those points through trusted physical pools,
private ROM helpers, Linux-owned sessions, interval rebasing, Rule1 and chunked
export. The original SCCodeTable is a helper-code-storage concept; the prototype
implements those helpers in generated ROM instead of writable on-chip SRAM.

## Requirements, implementation and evidence

| ID | Source | Implemented behavior | Evidence / accepted domain |
|---|---|---|---|
| C01 |Design p1,p4| Hierarchical calling contexts; same callee distinguished by parent | [Calling contexts](CALLING_CONTEXTS.md);6 records and14452/7226 golden instret |
| C02 |Design p8–9| SCStack call/return management and 256-frame default | [Boundary RTL](../evidence/final-validation/regression-base/rtl-boundary.txt);258calls exercise the defined folding boundary |
| C03 |Design p9–11| Parent/callee dictionary, chained collisions, monotonic IDs with 0reserved | Context/reuse/collision/exhaustion RTL in [low-level matrix](../evidence/final-validation/lowlevel-summary.json) |
| C04 |Design p11–12; HPM p3| cycle/instret/time in128-byte records |64-bit inclusive intervals; [ABI](../integration/ssa/linux/ABI.md) and actual captures |
| C05 |Design p8,p11–13; launch-policy supplement| Ordinary selected ELF runs without per-function instrumentation or SSA lifecycle calls | [Automatic launch](AUTOMATIC_LAUNCH.md); final51automatic/26manual checks plus ELF/negative checks; static and tested musl paths |
| C06 |Design p6,p12–13; trap adaptation| Handler calls excluded from application context construction; return restores notification | [Trap isolation](TRAP_ISOLATION.md); fresh trap/IRQ/permission RTL and real Linux |
| C07 |Design p11–13 lifecycle adaptation| Per-task pools and open-frame recovery; sampled pause exclusion | [Process accounting](LINUX_PROCESS_ACCOUNTING.md); real timer-driven A→B→A and 8direct four-counter snapshot rows |
| C08 |Design p13–14 open lifecycle details| Successful exec separates old/new sessions; failed pre-commit exec preserves old state; exit exports | [Exec lifecycle](EXEC_LIFECYCLE.md); production and dedicated lifecycle captures |
| C09 |Design p13§4,p14§4.1–4.2 open offline details| Performance/context stream to host file and reconstructed JSON tree | [Export specification](EXPORT.md); versioned records, parent/callee IDs and explicit incomplete states |
| C10 |Design p10–11 capacity; full-result export requirement| All allocated records with bounded16-record processing | Actual41records/3chunks,0/2records,64/4and105/7; targeted host capacity/fault tests |
| D01 |Design p12; HPM p4–5| One existing programmable TLB event linked to contexts | [DTLB accepted PTW requests](DTLB_EVENT_ATTRIBUTION.md), selector0x1002,40-bit modular intervals |
| D02 |Design p12§3.1(2); Rule1 supplement| Scalar-repeat/fixed-stride/irregular classification of retired integer accesses | [Rule1](CLASSIFICATION.md), four RTL fixtures, independent WB/reference oracle, Linux lifecycle/ownership/coverage checks |
| D03 |Design p12 Cache/TLB objective; native-event adaptation| One real Cache event and the TLB profile | [Completed D-cache A request messages](CACHE_EVENT_ATTRIBUTION.md), selector0x202,40 bits; source/global/context RTL and Linux export |

## Final candidate evidence

The accepted implementation is v0.2.0 at2adbfa5de81f341bd575e8498b370c5a12a02785.
[Validation](VALIDATION.md) and [summary](../evidence/final-validation/summary.json) record:

- Public-baseline application,111source/ROM hashes, actual Scala/RTL/Verilator
  build, and three public-source Linux/SBI payload builds.
-6Spike reference/34Rocket RTL cases plus9WB checks. Spike supplies applicable
  reference behavior; Rocket executes the SSA implementation.
- Real Linux native0/powerdown:51automatic/26manual,10ELF-capacity,5automatic
  and 3classification semantic-negative checks;17sessions/215records released.
- Bare/Linux150work+30calibration samples each, warmup1/repeats5. All 300results
  agree with independent closed-form arithmetic.
- Separate two-record real Linux companion:2sessions/4records,8snapshot-account
  rows,20checks and 5host mutation cases. The full performance capture uses this
  explicit companion because its three-record fixture lacks the inherited
  two-record-only diagnostic. Original host failures are retained.
-12-step host-only evidence replay and complete reachable-history audits.

## Counting and completeness

ABI1 has 64-bit cycle/instret/time. ABI2 adds one 40-bit event counter at record+40.
Counters are inclusive; class rows are exclusive. Scheduling subtracts only each
counter's sampled S..R interval. Handler/restore work outside that interval and
post-resume Cache/TLB effects belong to the active task. Delayed native events
are attributed by the interval containing the increment. Counter permissions
and source-event filtering are separate mechanisms.

Export independently represents transport integrity, unfinished activations and
classification coverage. Closed records remain settled; open frames are marked
abandoned. A complete record stream can accompany an incomplete call or a
classifier capacity diagnostic. New headers declare required classifier sidecars;
older captures remain explicitly legacy_undeclared.

## Supported completion boundary and future scope

The completed domain is one hart, trusted kernel/firmware and audited
non-privileged single-thread LIFO static/tested-musl programs. Two 36 MiB pools,
12retained pause diagnostics/session,256-frame full trees and classifier
2banks/63rows/16FIFO histories are explicit limits. Diagnostics overflow stops
with partial status; its beyond12-pause path was source-reviewed rather than newly
hardware stress-tested. Deeper call folding has no sticky post-unwind count.

Automatic DTLB combinations, multiple harts/migration, shared-mm/vfork, arbitrary
non-local/runtime/handler unwinds, FP/vector/AMO classification and full-capacity
long serial stress require separate scope and tests. [Performance](PERFORMANCE.md)
records high call-heavy cost; this acceptance has a functional research scope
and no invented numerical performance threshold. Area/power/fmax and a matched
unextended hardware baseline remain future measurements. The
[completion checklist](FINAL_CHECKLIST.md) distinguishes these extensions from
completed obligations. [Historical names and paths](HISTORY_MAP.json) remain
traceable under the unchanged release tags.
