# Linux process accounting

The RV64 kernel integration attaches one monitoring descriptor to an eligible
single-thread task. Two reserved physical pools are owned until frozen export
and release. Scheduler hooks sample/disable on switch-out and rebase/select on
switch-in; an unmonitored next task keeps selection0. Classification histories
stay in their corresponding hardware bank.

Actual Rocket/Verilator Linux tests wake higher-priority B by timer while A is
runnable inside two open frames. Saved trap cause, involuntary-switch count,
frame depth/RID, peer IDs and S/R chronology establish A→B→A. A resumes and
returns normally. Different pools and session IDs isolate same-address calls.
Cache events caused by A's own post-resume accesses remain charged to A.

The direct companion's excluded values are:

| Task | cycle | instret | time ticks | Cache events |
|---|---:|---:|---:|---:|
| A(pid15) |4463467|3429517|44635|12115|
| B(pid14) |132475|117572|1325|147|

These equal actual final-minus-original frame snapshots and independent pause
sums modulo each width. The emitted raw column is a reconstructed counterfactual;
its subtraction identity is auxiliary to the direct snapshot proof.
The complete performance fixture creates three records and uses a separately
identified two-record companion because the inherited diagnostic guard emits
SSA_ACCOUNT only for exactly two records.

[Direct raw capture](../evidence/final-validation/linux-switch-proof/rocket-linux-performance.txt),
[20-check summary](../evidence/final-validation/linux-switch-proof/summary.json) and
[snapshot accounting](../evidence/final-validation/linux-switch-proof/switch-accounting.json)
record native0 and normal powerdown. [Unified validation](VALIDATION.md) identifies
other captures and host-only replay. Current diagnostics retain12pauses/session;
source-reviewed overflow stops monitoring with incomplete status.
