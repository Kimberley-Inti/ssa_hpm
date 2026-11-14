# Final candidate performance experiment protocol

All modes use the same extended single-hart SSAHPMEventRocketConfig. Target
cycle/instret/CLINT-time samples, not Verilator wall time, support conclusions.
There is no matched unextended model, synthesis area or silicon timing result.

## Workload comparison

Bare modes: monitor off; ABI1 base; ABI2 DTLB selector0x1002; ABI2 Cache
selector0x202; ABI1 classification; ABI2 Cache plus classification.
The bare workload runs in M-mode with user_only=0. Physical-address loads do not
stress PTW traffic; DTLB mode isolates the extra snapshot path. Separate fresh
translated RTL tests validate actual DTLB event production and attribution.

Linux modes: off; manual base; manual Cache; manual classification; manual
Cache plus classification; automatic Cache plus classification. The last two
share a profile so automatic policy is not confounded with adding a counter.
Firmware fixes the Linux event selector to Cache. No automatic-DTLB acceptance
is added. Off disables context monitoring, not the standard global counters or
extension hardware.

The same body/ELF executes computation,128leaf calls, depth16 recursion,32KiB
sequential loads and a deterministic irregular permutation. Read-only data is
initialized once per workload/mode; local seed starts identically on each call.
One unmeasured warmup precedes five measured repetitions. Initial single-repeat
bare trial estimated the budget; only final native receipts are formal evidence.

Independent samples fence,cycle,instret,time before CALL and after RETURN.
Compiler disassembly verifies ordering. No console output is inside the work
interval. Empty intervals calibrate stamp overhead; raw deltas are not blindly
subtracted. Between repetitions, outside-interval output can affect cache state;
all modes use the same sequence and report min/median/max. Every checksum agrees.
The32KiB data set exceeds the generated16KiB L1D; warmup is not a hot-cache claim.

## Lifecycle decomposition

Bare dictionary initialization is separately sampled. Linux dictionary_init
covers1MiB zeroing, metadata, selector and classifier reset before BEGIN output,
not kzalloc. User START brackets additionally include syscall and diagnostics.
Auto INIT user rows are already-enabled entry calibration; kernel probes measure
its actual setup. Privileged NNP/ARM setup is independently bracketed separately.

Optional SSA_COST_PROFILE probes apply only to test14 sessions. They retain
pause/resume samples until frozen export and never print in the scheduler path.
The descriptor is larger in this measurement build; allocation/switch/exec data
are instrumented-build observations, not exact unprobed production costs.
The ordinary unified Linux regression compiles these probes out.

Freeze is distinct from export. record_copy is a subset of export. Export includes
formatting, transport and bookkeeping; its own later cost diagnostics and release
are outside that interval. Do not describe the residual as pure wire time.
Kernel exec windows run from exec entry to ELF ready/failure, excluding their
own diagnostic print. Successful replacement includes old-session export;
user failed-exec brackets include diagnostic output in measured profiles.

The timer-controlled A/B case supplies real open-frame pause/resume observations
and an unmonitored idle/launcher handoff. The existing FIFO/OTHER priorities and
1ms timer are retained; the contemplated RT-bandwidth change was not implemented.
Finite pool, event-diagnostic and classifier limits remain explicit.

Raw target data, repetitions, artifacts, exit codes and normal shutdown are
required before conclusions. Probe footprint and declared hardware state are
separate from actual area, and enabled/disabled cost is separate from added
hardware cost. Preserve anomalies; optimize only for an identified defect.
