# Validation of the bounded research prototype

The native/semantic matrix and final host-only evidence replay passed. The replay
actually completed 12 steps and rechecked 300 work results without another native
execution. Results are indexed by `evidence/stage11/summary.json`.
The acceptance domain is one hart, trusted kernel/firmware, audited single-thread
non-privileged LIFO programs and the explicitly tested musl continuation case.
This is not a universal Linux or low-overhead implementation claim.

## Frozen source and actual independent construction

Baseline maintenance commit:6ef19d6e85dfe55983794342620a026005a67d20.
Final source commits are in [source-commits.json](../evidence/stage11/source-commits.json).
Chipyard d756a546e27d40100752a0ff7c73b796c77d4fde adds the accounting companion and
strict host oracles; Linux3e7c06efefeda043f100ab635b1729ce7a11afd8 adds opt-in cost
probes and classification-sidecar declarations. Rocket
bb5b1c26a8dae5d5afee716a1636b55a1bfe1ed2 and OpenSBI
43f02ffb329d9c86b2ff2138dc450b2060778ffe are unchanged.

Pinned public Chipyard/Rocket bases were fetched and patched in a new workspace;
Scala compilation, RTL generation and Verilator build actually completed exit 0.
The final public-suite refresh verifies111exact files and ROMs. Test-only additions
do not change the hardware tree. A second clean public patch application is
recorded separately; it is not falsely counted as another RTL build.

The new standard simulator SHA256 is
90f1610511889792fd9242bf5730a87a0fa3471902fb3be3deb03b929ebf15f0.
Linux uses a separately linked read-only progress executable,
eaa9f4e92c1e3708d69dec010f7133817dbb88391a3d3ce4fbd97bb1ceaf7b4f,
against the identical unchanged model archive
c2febac75c6d749ccf954738ab9c12c71c44fc8828a795889376b43531cc9ddc.
The host harness reads PC/CSR state; it does not write RTL state.

Production, full-performance and accounting-companion Linux/SBI sources were
independently fetched/patched/built. All Linux trees equal
c937114e57032e8f896bc853d1d63ff16e9bf8a7 and all SBI trees equal
c8e81125ce6b92976ccfff630c49a61d9d887e91. The two measurement configurations
match except their initramfs path. Pinned dependency/musl caches and host tools
were reused; kernel, firmware and fixtures were actually compiled. Exact commands,
config/compiler/image hashes and complete small build logs are committed.

## Actual new execution, not historical-log replay

| Execution | Result and coverage |
|---|---|
| Directed low-level matrix |40distinct cases:6Spike references and 34Rocket RTL; expected-failure controls retain native42 |
| Independent WB oracle |82candidates,72accepted accesses,7replays,1exception;9checks pass |
| Production Linux |native0, normal powerdown;51automatic/26manual checks;17sessions,215 records, all pools released |
| Production postcheck |same capture:10ELF-capacity checks,5automatic and 3manual semantic negatives pass |
| Bare performance |native0/DONE;6modes×5 workloads×5repeats=150 work,30 calibration,6 setup observations |
| Full Linux performance |native0/powerdown;150 work/30calibration, six INIT/six failed-exec/four STOP/four EXPORT/three ARM observations;8sessions/102 records released |
| Two-record Linux companion |native0/powerdown;2real auto-enabled tasks,2sessions/4 records,8direct snapshot-account rows;20checks pass |
| Final composite performance check |20checks pass; full work/phase capture and companion coverage remain explicitly separate |
| Accounting semantic mutations |5host cases: valid accepted; wrong delta/offset, missing rows and duplicated counter row rejected |

Production tests cover ordinary static ELF with no SSA calls, musl PT_INTERP/DSO,
successful/failed exec, signal exit, fork policy, setid/thread rejection, pool
exhaustion, pause/resume, classification and chunked export. Expected abandoned
exec/loader frames remain incomplete calls;64HPM records with only63classifier
rows retain observable dropped/coverage status. Transport completion is separate
from both of these conditions. Actual ELF capacity linkage is 10checks; later
host-only replay verifies its receipt, not excluded ELF binaries.

DTLB, Cache, ABI, wrap, register transparency, permission and classification RTL
checks were newly executed on the new model. Historical Linux DTLB/old-protocol
captures remain historical evidence. Automatic DTLB is not newly accepted.
Linux process accounting's173 and exec lifecycle's37 historical checks are not relabeled as fresh runs.
The new base RTL again yields6contexts and common.instret14452/7226.

## Review repairs and evidence interpretation

See [FINAL_REVIEW](FINAL_REVIEW.md). R01/R02 fix whole-missing classification
sidecars: an explicit producer declaration and early semantic checks replace the
old KeyError/undeclared optionality. ABI1/2 and counter meanings remain unchanged;
legacy captures are explicitly `legacy_undeclared`. R04 normalizes progress lines
that interrupt target performance words/tags;8measurement-protocol tests pass.
Host protocol/reference checks are independently identified, not extra simulations.

R05: the original full A/B benchmark creates3 records, while the inherited kernel
SSA_ACCOUNT diagnostic requires exactly2. Its first checker therefore returned1
for absent snapshot proof, although native/work/phase/export/timer checks passed.
The failed receipt is retained. Only the missing proof was rerun in a small
conditional2-record image; no kernel/RTL change or 150 work rerun was needed.
Actual recompilation confirms the default full payload's loadable bytes are
unchanged. A transient host NameError in newly added metadata checks was corrected
by moving definitions before use; the same completed log was rechecked, not rerun.
The duplicate-row mutation then exposed len8 alone as insufficient: the checker
now requires the exact twoPID×fourcounter key set and correct modulo S/R arithmetic.

In the companion, actual IRQ5 cuts A out with depth2/RID2 and state runnable;
S_B<S_A<R_B<R_A proves A→B→A, with an unmonitored scheduling interval also covered.
Frame2 final−original equals independently summed pause samples for all counters:

| Task | cycle excluded | instret excluded | time ticks excluded | Cache events excluded |
|---|---:|---:|---:|---:|
| B(pid14) |132475|117572|1325|147|
| A(pid15) |4463467|3429517|44635|12115|

Both tasks restore and return; their physical pools, sessions and same-address
call paths are distinct. Classification histories remain in their own banks.
Cache pollution after resume can cause additional A events; those belong to A's
active interval. `SSA_ACCOUNT.raw` is the reconstructed counterfactual
`recorded+(final-original)`, not another uncorrected execution. Direct proof uses
actual frame memory and independent S/R samples, not that constructed identity alone.
One raw tag was interrupted by host progress, so substring monitoring counted7;
canonical parsing correctly recovered all 8 rows.

## Performance and supported completion boundary

[PERFORMANCE](PERFORMANCE.md) reports raw repeated target cycle/instret/time,
min/median/max, initialization, switching, exec and console-export costs. Bare
call128off/base medians1088/46328 cycles expose42.58× overhead; memory loops
amortize it to about 0.80%/0.40% in this model. No low-overhead claim follows.
All300bare/Linux workload results match independent closed-form arithmetic.
All 150Linux instruction samples reconcile with body work, sampling, monitor ROM
and 0/1/2timer-sized4025 instruction steps. Time reads are non-atomic and emulated
in Linux; probe/IRQ costs are retained. Runner monotonic elapsed time describes
VM experiment duration, not hardware speed. No matched unextended model, synthesis
area, physical fmax or power result is claimed.

Current software retains at most12pause diagnostics/session; the source-reviewed
next-pause path stops with bad-state/partial export, not unbounded monitoring.
Depth beyond256folds into the deepest record without a sticky post-unwind count;
full-tree claims require audited inputs within256frames. Classification has
2banks/63rows/16histories, with observable warmup/eviction/drop behavior.
Multi-hart/migration, shared-mm/vfork, arbitrary handlers/non-local runtimes,
FP/vector/AMO classification and automatic DTLB combinations remain outside scope.

Reproduction and fast host-only evidence replay are in [REPRODUCE](../REPRODUCE.md).
