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
| 1 START | flags0 normal or1 legacy negative; role0..2/test0..7 diagnostic labels | 0, or negative errno |
| 2 STOP | other arguments0 | number of allocated records; rejects open/spilled frames |
| 3 STATUS | other arguments0 | 0 only if current task has no descriptor and selector0; diagnostic for the unmonitored parent/new image |
| 4 QUERY | other arguments0 | current RUNNING task's open depth; logs identity/depth/next_id without accepting a pointer |

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

Only metadata/dictionary/stack and a bounded record window are mapped into the
kernel. They are not mapped into user processes. Kernel export is complete only
with closed frames, zero spill/allocation error and at most32 allocated records.
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


## Exec sessions (stage5)

Every START has a unique increasing session ID and captures Linux self_exec_id.
The latter changes on successful image replacement; PID alone is not an export
identity. The post-exec_mmap hook in flush_old_exec runs after the old address
space cannot return, before the new image enters userspace. It samples cutoff
counters, clears the selector and freezes the descriptor, emits SSA_SESSION and
bounded SSA_EXPORT/SSA_RECORD data, then SSA_OPEN for any abandoned frames and
SSA_EXEC_END. It detaches the descriptor, releases the slot and frees it. Export
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
Counter rebasing and stage4 S/R boundaries are unchanged; cutoff values are
diagnostics, not partial open-frame totals. Multithreaded/setuid exec, signal
handler exec and complete-capacity export remain unverified.
