# Process accounting

SCBaseReg selects the current physical monitoring pool. A software session owns
its dictionary, records, open frames, snapshots and classification epoch. Hart
counters and privileged notification state remain shared hardware resources.
The controlled M-mode fixtures establish the underlying switching protocol;
[real Linux scheduling](LINUX_PROCESS_ACCOUNTING.md) validates its OS integration.

At switch-out software samples S, disables selection and preserves open frames.
Before resuming it samples R and adds `(R-S) mod 2^w` to each open snapshot,
where w is 64 for cycle/instret/time and 40 for the event counter. The final return
difference excludes the paused interval. Unmonitored tasks execute with selection0.
This works without overwriting global counters or another session's records.

The final low-level matrix includes a corrected two-pool run and the legacy
uncorrected negative control. The Linux accounting companion additionally reads
actual frame snapshots and independently sums raw pause samples for each of
four distinct counters in both tasks. See [the proof](VALIDATION.md),
[ABI ownership](../integration/ssa/linux/ABI.md), and
[controlled-switch results](../evidence/final-validation/regression-process/summary.json).
