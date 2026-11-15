# Single-hart Linux prototype ABI

This experimental kernel interface is not a stable upstream Linux ABI.
It is enabled by CONFIG_SSA_HPM on RV64 MMU kernels without CONFIG_SMP.
The static Rocket/OpenSBI profile supplies the physical DRAM and counter sources.

## Ownership and transitions

The task descriptor, pool, dictionary, records, open frames, counter snapshots,
accumulated excluded intervals and switch diagnostics belong to one Linux task.
Fork clears the child's descriptor. The fixtures fork before enabling. Successful
exec retires the old descriptor; failed pre-commit exec preserves it. The counters, trap state, notification policy and current
SCBaseReg selector belong to the hart. Counter registers are never overwritten
on a task switch. Trap depth is not copied into task state.

| Operation | Before | After |
| --- | --- | --- |
| START | no descriptor | zero dictionary/meta, next_id1, own pool selected, RUNNING |
| switch out | RUNNING | sample S, clear selector, preserve frames, PAUSED |
| switch to unmonitored task | selector cleared | keep selector0 |
| switch in | PAUSED | sample R, rebase every open snapshot by R-S, select own pool, RUNNING |
| STOP | RUNNING with no open/spilled frames | selector0, STOPPED, records retained |
| committed exec | owned descriptor | selector0, bounded export, mark open frames abandoned, release slot/free descriptor |
| do_exit | owned descriptor | selector0, bounded export, release slot, free descriptor |

Interrupts are masked around sampling/state changes. Pool initialization publishes
its stores before selection. This implementation is intentionally single-hart;
there is no migration, cross-hart counter epoch or concurrent pool allocator ABI.
Detected selector/depth inconsistencies in the running/resume paths or exhausted
diagnostic capacity clear selection and mark the export incomplete.

## Userspace operation

Use `prctl(0x535341, op, flags, role, test)` on the current task only.
No PID, physical address, virtual address, user mapping or record pointer is accepted.

| op | Arguments | Result |
| --- | --- | --- |
| 1 START | flags0/1 ABI1, flags2/3 ABI2 normal/legacy; role0..2/test0..14 diagnostic labels | 0, or negative errno |
| 2 STOP | other arguments0 | number of allocated records; rejects open/spilled frames |
| 3 STATUS | other arguments0 | 0 only if current task has no descriptor and selector0; diagnostic for the unmonitored parent/new image |
| 4 QUERY | other arguments0 | current RUNNING task's open depth; logs identity/depth/next_id without accepting a pointer |
| 5 EXPORT | other arguments0, current STOPPED descriptor | emit version1 stream once, return0; EBUSY running, EALREADY repeated, EINVAL absent/nonzero args, EIO terminal read failure |

There are two concurrent pool slots. START returns EBUSY for an existing descriptor
or no available slot; invalid labels/flags return EINVAL, allocation failure ENOMEM,
and missing platform initialization ENODEV. STOP retains ownership until do_exit.
It returns EIO for inconsistent state/selection and EBUSY for open/spilled frames.
The legacy flag omits snapshot rebasing only for that task; it deliberately counts
off-CPU work and is used to demonstrate the attribution bug. It grants no access
to another task or to privileged CSR policy. Production quotas/access policy,
re-enable episodes within an existing descriptor and threads are deferred.
After committed exec, the new image may explicitly START a fresh session.

## Privilege and memory

Supervisor CSR0x5c0 bit0 enables user-only call/return notifications; reset0 keeps
the original trap-depth policy for bare-metal regressions. This is notification
filtering, not privilege filtering of the hardware counters. U-mode read/write
of SCBaseReg0x800 is illegal. Trusted ROM data requests have effective M privilege
and bypass user translation; ordinary user loads/stores retain Sv39/PMP checks.
The architectural privilege does not change merely because the private ROM runs.

The selected physical value is the pool's exclusive upper bound, not an allocatable
user pointer. Slots use0x88000000 and0x8c000000, outside the32MiB managed Linux RAM.
The retained microcode ABI is:

| Object | Physical position |
| --- | --- |
| metadata | base-64: depth, next_id, spilled_depth, allocation_errors |
| stack | 256 entries of64B immediately below metadata |
| dictionary | 262144 u32 buckets immediately below stack; starts base-1065024 |
| records | 262144 entries of128B starting base-37748736; record0 reserved |

Metadata/dictionary/stack and an8KiB proof window are retained; export maps/copies
at most16 records (2KiB) per chunk through the entire262143 usable-ID capacity.
Pools are never user-mapped. Complete transport and complete activations are
separate: all allocated records can be exported with an incomplete status for
open frames, spill, allocation errors or monitor state errors.
Abrupt exit with open frames is marked incomplete; unwinding is not implemented.

## Counts and evidence

The ROM reads mcycle/minstret and physical CLINT mtime. Kernel samples use
cycle/instret and the firmware-provided time CSR view of the same CLINT source.
The profile's mtime frequency is1MHz. Each counter is sampled separately in a
fixed instruction sequence; the sequence is not an atomic three-counter sample.

Each open frame's entry snapshot is increased by that counter's R-S before resume.
This excludes the paused interval, including other tasks, their kernel/trap work,
exports and any unmonitored task running within it. The task's own kernel/IRQ,
monitoring and resume costs outside those boundaries remain included. Records
are inclusive of child calls. No constant monitor-overhead subtraction is used.

The fixture executes one parent/common activation per task. Its saved entry,
rebased entry, paused interval and final record therefore give an exact audit
relation: raw=recorded+final_entry-original_entry. Normal mode requires
final_entry-original_entry=sum(R-S); legacy mode requires unchanged entries.
Repeated activations remain covered by existing low-level regressions, not this
single-activation Linux audit identity.

Exports occur in do_exit or after exec_mmap commitment before slot release and are captured to a host disk log,
then decoded to JSON. Kernel logging is restricted to privileged readers; the
fixture checks syslog denial after dropping to uid1000. This is not a general
in-guest file export service. PASS requires actual Rocket Linux execution,
closed records, reciprocal scheduling/frame evidence and short/long comparisons;
Spike's REFERENCE fixture only diagnoses Linux ABI behavior without SSA.

The scheduler hook executes pause/resume immediately before context_switch.
S is sampled in the outgoing task's kernel path. R is sampled before the physical
switch into the incoming task, then its frame snapshots are rebased and its pool
selected. Scheduling/IRQ entry work before S is charged to the outgoing interval;
rebasing, context-switch tail and restore work after R are charged to the incoming
interval. This is the explicitly measured sampling-boundary policy. No separate
measurement claims an exact split of those kernel handoff costs.


## Exec sessions (exec lifecycle)

Every START has a unique increasing session ID and captures Linux self_exec_id.
The latter changes on successful image replacement; PID alone is not an export
identity. The post-exec_mmap hook in flush_old_exec runs after the old address
space cannot return, before the new image enters userspace. It samples cutoff
counters, clears the selector and freezes the descriptor, emits SSA_SESSION and
bounded SSA_EXPORT/SSA_RECORD data, then SSA_OPEN for any abandoned frames and
SSA_EXEC_END. result export additionally emits versioned chunk framing and explicit
release. Only freeze/release transitions mask IRQs; mapping/output run with IRQs
enabled and the descriptor remains STOPPED and owned until terminal export. Export
is once per session; later new-image exit cannot export the old descriptor.

Unfinished activations are not fabricated as normal returns and add no partial
counts. Completed activations already in a record remain; `open` counts present
frames for that record. An open export is incomplete even when its closed child
records are valid. Fresh START resets dictionary/metadata/offsets and record
allocation initializes counts, even when the same physical slot is reused.
The new image starts with no descriptor/selector and opts in explicitly.

ENOENT during pathname lookup is the covered failed-return path. It occurs before
exec_mmap and changes neither descriptor nor frame/session identity. Failures
after the commit point can kill the task and are not claimed to return safely.
Counter rebasing and Linux process accounting S/R boundaries are unchanged; cutoff values are
diagnostics, not partial open-frame totals. Multithreaded/setuid exec, signal
handler exec and full-capacity runtime stress remain unverified. result export removes
the32-record limit; actual41-record acceptance and host capacity boundaries are
reported separately.

## Optional DTLB request profile (DTLB attribution, ABI2)

Use SSAHPMEventRocketConfig (one hart, one standard HPM counter). Firmware selects
mhpmevent3=0x1002, initializes mhpmcounter3 once, clears mcountinhibit bit3, leaves
mcounteren bit3 set and clears scounteren bit3. Only the kernel reads hpmcounter3;
unprivileged reads trap. These enable bits control access, not event filtering.
The minimal kernel does not share this counter with perf or another selector.

START flags bit1 enables ABI2; bit0 retains the legacy no-rebase negative control.
Thus flags0/1 retain ABI1 and flags2/3 select ABI2 normal/legacy. Diagnostic labels
now allow0..14. Unsupported hardware rejects bit1 with ENODEV before allocation.
CSR0x5c0 bit1 selects the extended SCCodeTable, latched on each private invocation;
bit0 retains the user-notification policy. The original104-instruction ABI1 ROM
is byte-identical; ABI2 adds a fourth sample/update. Opt-in ABI2 instruction
counts include those additional monitor instructions, so scalar instruction
oracles are not transferred to ABI2 workloads. No overhead subtraction is used.

Pool sizes and all existing offsets remain unchanged. ABI2 frame offset32 holds
the fourth entry snapshot; record offset40 (previously reserved[0]) holds DTLB
request counts. Values are zero-extended40-bit, including record accumulation;
all fourth-counter subtraction, rebasing and accumulation is modulo2^40. A
sampling interval must contain fewer than2^40 events to avoid ambiguity. The
three original counters retain their64-bit semantics. ABI1 does not read/export
the reserved field. Allocation initializes the fourth record count and every
ABI2 push initializes its fourth frame snapshot, including reused physical slots.
SSA_EVENT_BEGIN carries abi2/selector4098/width40; SSA_EVENT_RECORD carries the
fourth count without changing the original SSA_RECORD format. SSA_SAMPLE and
SSA_ACCOUNT counter3 carry its pause/resume proof. SSA_EVENT_SESSION carries the
cutoff and policy after clearing bit1; SSA_EVENT_OPEN marks abandoned snapshots.

The source is io.dmem.perf.tlbMiss, wired to DCache io.ptw.req.fire(): a data-side
translation walk request accepted by the PTW. It is not a count of distinct pages,
page faults, cache refills, or retired loads. Replays/retries may cause further
accepted walks. Existing EventSet2 bit4 is selected by(1<<12)|2 =0x1002. The
registered HPM increment is one cycle after the source handshake. Intervals are
measured at the fourth counter's actual CSR snapshot points; an increment crossing
a call/return or scheduler boundary belongs to the interval containing that
increment, regardless of the initiating request's original context. This is not
request-owner attribution. Counter samples are not simultaneous with the other
three counters. The dependent-load/fence fixture tests the observed return
boundary, not a universal drain of every possible speculative request.

There is no privilege, trap or notification-mode filter on the event source.
S/U translation requests can count; a faulted/squashed access can still cause an
accepted request. The trusted ROM uses physical M-privilege data accesses and
does not itself require translation in this profile, but a delayed external walk
accepted during ROM execution would still follow interval attribution. Parent
counts include child calls and monitor/trap/kernel work inside their windows.
While paused, every open fourth snapshot is increased by its sampled R-S modulo
2^40, excluding events within that interval from other tasks and their kernel
work. Pre-S and post-R handoff/restore costs remain charged by the Linux process accounting policy.
Stopping selection does not freeze/reset the hart's global HPM counter.

Fork clears ownership as before. Pause clears selection and bit1; resume restores
the owning task's bit1 and pool after rebasing all four snapshots. STOP, committed
exec and exit clear bit1 as well as the selector. Committed exec exports the old
ABI2 session once, marks open frames abandoned without partial totals, releases
its slot and detaches it. The replacement starts unmonitored, then explicitly
STARTs a fresh session. Pre-commit ENOENT retains all four snapshots/session/tree.

## Versioned complete results (result export)

STOP now preserves its cutoff snapshot. op5 exports a STOPPED current-task session
once and retains its descriptor/pool until exec or exit; repeated op5 returns
EALREADY. Without op5, exit or committed exec automatically exports first. The
new stream version1 encloses the existing ABI1/ABI2 record rows in numbered
16-record chunks with counts and64-bit word checksums. Counter names, widths,
selector, total, session, image, status, per-record open counts and abandoned frame
IDs are explicit. SSA_XEND is authoritative for transfer completeness and
SSA_XRELEASE precedes actual pool reuse. No remote PID/address/cursor is accepted;
internal read_chunk validates current ownership and frozen bounds. See the
maintenance repository docs/EXPORT.md and docs/ACCEPTANCE.md.

Host export_results.py rejects missing/duplicate/truncated/corrupt streams, writes
explicit partial JSON on errors and can print a bounded call-tree summary. Old
pre-v1 logs use the unchanged historical graders; no synthetic hashes are added.
This does not change inclusive counting, paused interval exclusion or40-bit DTLB
occurrence-interval semantics. Allocation exhaustion is status4, not silent loss;
full-capacity execution is distinct from the host-tested capacity arithmetic.

## Fixed Cache profile (Cache attribution, ABI2)

A `build-a.py --cache` image compiles BOTH kernel and OpenSBI with
`SSA_CACHE_PROFILE`. Firmware fixes HPM3 selector0x202 (EventSet2 bit1).
Default builds continue to select0x1002/DTLB. START flags2/3 mean the configured
ABI2 fourth counter; they do not give users permission to change selectors.
The Cache profile has the SAME record/frame offsets, ROM and40-bit modular
snapshot/rebase/accumulation as DTLB; no fifth counter/state is added.

`dcache_a_transactions` counts the existing native Rocket D$ miss event:
`DCache.io.cpu.perf.acquire = edge.done(tl_out_a)` -> EventSet2 bit1 ->
registered HPM3 increment on the next cycle. It is completed outgoing TileLink A
transaction handshakes, including cached acquires and uncached requests on that
interface, NOT unique retired load misses or incoming refill beats. Accepted
speculative/replayed transactions count when they actually occur. There is no
request-owner tag or U/S/kernel/private-ROM source filter. The profile metadata
and firmware boot selector must agree; the checker rejects a mismatched image.

At calls/returns, increments belong to the actual CSR sampling interval even
if a transaction originated earlier. Parents include children, kernel/trap and
private-ROM activity inside their interval. Existing S..R subtraction excludes
other tasks and their activity in the measured paused interval; pre-S/post-R
work and A's own cache misses after B polluted the cache remain charged to A.
No cache partitioning or overhead subtraction is claimed. Every interval must
span fewer than2^40 events to avoid modular ambiguity.

Version1 XBEGIN adds `profile=base|dtlb_accepted_ptw_requests|dcache_a_transactions`.
ABI2 counter3 metadata supplies its matching name, width40 and selector4098/514.
DTLB rows retain `dtlb=...`; Cache rows use `cache=...`. Checksums use the same
numeric fourth word. Legacy v1 captures lacking profile mean ABI1/base or
ABI2/DTLB; a Cache capture always requires explicit profile and matching metadata.
The parser rejects mixed fields and selectors, preserving old ABI1/2 recognition.

## memory classification optional memory classification

START flags bit2 opts into rule1 classification, independently of bit1 ABI2 and
bit0 legacy-HPM control. Flags0..3 retain their meanings. The directed classification
Linux image uses flags6 (Cache ABI2 plus classification); existing base/DTLB/Cache
build entries remain available. Ordinary users never select an epoch, physical
pool, another task or query RID through prctl.

The S/M-only CSR interface is0x5c1 epoch (zero disables),0x5c3 six-bit index,
0x5c2 write1 reset owned bank0/1 then poll bit1 until clear.0x5c4..0x5cb expose
five exclusive64-bit classification counters plus session statistics. Index0 is
status/depth/spill/unframed/currentRID/inputs/evictions/dropped. Index1..63 is
input/warmup/scalar/stream/irregular/inputs/evictions/dropped. The trusted kernel
resets only a freshly acquired physical pool, before U-mode; reads only its
frozen bank, under short IRQ masks; keeps ownership through terminal export.

Two epoch banks retain16FIFO history entries and256RID mirror frames each.
Switch-out clears selection; resume restores epoch without discarding histories.
STOP freezes; exec commitment/exit export before release; failed ENOENT preserves
the old epoch; the replacement image explicitly STARTs a fresh zeroed epoch.
Actual observations are WB-retired integer load/store virtual addresses,1/2/4/8B.
Kernel/trap/private-ROM/other-task instructions are source-filtered. No HPM S..R
subtraction is needed for these counters; existing HPM counters remain inclusive
and keep their original pause rebasing rules.

Rule1 keys(epoch,RID,PC,op,width), first2warmup; equal zero deltas scalar-repeat,
equal nonzero aligned signed byte stride with magnitude<=4096 stream; else
irregular/unrecognized, not mathematical randomness. Counts are exclusive per
current record; parent-inclusive classification can be derived separately.
Evictions restart evidence without dropping accumulated counts. RID>=64 or
unsupported framed state cannot silently be merged into parent counts. The base
export remains full capacity; the sidecar explicitly declares63usable rows.
See the maintenance repository docs/CLASSIFICATION.md for full scope and examples.


## Controlled automatic ELF launch (automatic launch)

The existing START/STOP/EXPORT operations remain compatible. The optional trusted
policy uses two new operations on the current task:

| op | Arguments | Result |
| --- | --- | --- |
| 6 ARM_EXEC | flags0..7, role0..2, test0..14 | CAP_SYS_ADMIN + no_new_privs + one thread + no descriptor; arm successful-exec inheritance, fork clears |
| 7 DISARM_EXEC | other arguments0 | CAP_SYS_ADMIN and no descriptor; remove future policy |

A successful ELF replacement retires the old session at the existing commit
hook, then automatically STARTs at final ELF readiness before first U execution.
Failure ENOENT preserves the old descriptor. Selected setid/credential-changing,
recursive script and multithread forms are rejected before commit. Armed or
monitored CLONE_THREAD is rejected. Pool exhaustion is fail-open with an explicit
SSA_AUTO_RESULT error and no session; there is no mid-image retry. Normal exit
and signal termination export before release, with abandoned-frame markers.
Unselected processes remain unselected, and children do not inherit the policy.

Static entry and dynamic PT_INTERP entry are both covered; the latter includes
loader/application/DSO calls in one epoch with raw callee addresses and explicit
entry/app/interp metadata. Loader continuation frames may remain open. This is
not a promise of universal unwinding, arbitrary setuid/thread runtimes or a stable
upstream ABI. [Transparent policy](transparent/POLICY.md) specifies lifecycle,
authority, profile/capacity and accounting boundaries. Only the actual automatic launch
Linux evidence establishes which fixture forms have passed.

## Final-candidate export contract and optional cost probes

Version1 XBEGIN may additionally carry `classification=0|1 class_rule=0|1
class_rows=N`. New classification-enabled builds declare the sidecar before any
payload: rule1 and min(total,63) rows, including a BEGIN/END for a zero-row
session. A disabled declaration requires rule0/rows0 and no sidecar. The combined
host parser rejects a completely missing declared sidecar. Legacy captures are
accepted as `legacy_undeclared`; they cannot promise detection of an entirely
removed optional sidecar without a fixture-specific expectation. ABI1/ABI2,
record layout, profiles, counter widths and checksums are unchanged.

`SSA_COST_PROFILE` is an optional compile-time experiment, not a user ABI.
Only test14 sessions collect kernel dictionary/setup, scheduler pause/resume,
freeze, record-copy, export and exec-window counter samples. Scheduler samples
are retained until export; no scheduler-path printk is added. Exec diagnostics
are outside application workload intervals. Probe reads/bookkeeping and any
included formatting are disclosed in the performance report. Default builds
compile the probes and associated fields out.
