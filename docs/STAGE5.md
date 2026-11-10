# Stage5: single-hart Linux exec lifecycle

Runtime acceptance is pending completion of the actual Rocket/Verilator run.
Implementation and reference execution alone do not establish SSA correctness.

## Semantics and boundaries

A successful exec ends the old monitoring session immediately after exec_mmap
has committed the new address space in flush_old_exec. Earlier failures leave
that session intact. This hook is after the point where the old image can return;
a later exec failure can terminate the task, and is not the failed-return path
tested here. Linux's self_exec_id increments later in setup_new_exec, so the new
image's explicitly enabled session has the next image epoch and a distinct
monotonic session ID, even though its PID and physical pool slot are reused.

The kernel samples cutoff counters, clears selection, freezes the old session,
exports its bounded records, marks every remaining frame abandoned, detaches the
descriptor after releasing its slot, then frees the descriptor, all under the IRQ mask. No synthetic return is
inserted. Counts already accumulated by completed activations remain valid;
unfinished activations contribute no partial counts. A record may contain earlier
completed activations as well as a presently open frame; the record's `open`
field identifies the latter. Such a session is incomplete, not a normal closed
call tree. SSA_OPEN carries frame/record identity and the final entry snapshots;
SSA_EXEC_END distinguishes successful image retirement from SSA_EXIT. No old
session is exported again when the replacement image later exits.

The new image starts unmonitored. It explicitly enables a fresh zeroed dictionary
and metadata, next_id1, depth0 and fresh software offsets. Record allocation
initializes counts. The fixed kernel mapping is retained; pool reuse does not
reuse session identity. New image STOP and do_exit export use the stage4 path.
The test checks the old selector is zero before new enable, actual ELF symbol
addresses, distinct session/image identities and exactly one export per session.

For a deterministic failed exec, /absent returns ENOENT before exec_mmap. The same
old descriptor, pool, epoch and open frame survive. The process queries its frame
before/after the syscall, executes its closed child again, returns normally and
exports once at exit. This does not cover failures after image commitment,
multithreaded exec/de_thread, setuid exec, exec from signal handlers or full-capacity
exports. A normal fork clears the descriptor as in stage4; this fixture enables
only after fork. The design PDF leaves the export/lifecycle detail unspecified;
these minimal rules retain the existing trusted-pool architecture.

Counter policy is unchanged: cycle/instret and CLINT time include child calls and
monitor/kernel costs within the charged interval. Scheduler pause/resume excludes
each sampled R-S from all open frames. Pre-S outgoing and post-R incoming handoff
costs remain charged. Cutoff samples are diagnostics, not new aggregate totals;
there is no partial addition for an abandoned activation. New counting starts
only after the replacement image's explicit START. Kernel export and exec work
with selector0 produce no new records. No claim of U-mode-only hardware counts
or exact overhead subtraction is made.

## Reproduction

Use REPRODUCE.md for public Chipyard/Rocket reconstruction and toolchain setup.
The new kernel patch is applied after the public Linux baseline, compatibility
patch0001 and stage4 patch0002. No local development commit must be fetched.

```sh
cd /path/to/reconstructed-chipyard
source ssa/env.sh
python3 ssa/linux/build-a.py --exec --work /tmp/ssa-exec-rebuild --jobs 6
python3 ssa/linux/run-exec.py --work /tmp/ssa-exec-rebuild \
  --simulator /path/to/verified/simulator-progress \
  --out-dir /tmp/ssa-exec-results --timeout 21600
```

The build emits /init (old image), /next (replacement) and /regress (unchanged
stage4 fixture). One real boot executes success, ENOENT and all four short/long
stage4 scheduling trials. The runner refuses to overwrite existing results and
records exact model/image/log hashes, real process exit code and duration.
The checker grades the exec sessions, then calls the unchanged stage4 checker
on the actual boot prefix and regression suffix, retaining all173 requirements.
The reference-only build uses --exec --reference; Spike has no SSA extension,
so its pass only establishes user ABI/exec/signal fixture behavior.

Regrade an existing completed execution without starting another simulator:

```sh
python3 ssa/linux/grade-exec.py /tmp/ssa-exec-results/rocket-linux-exec.txt \
  --exit-code 0 --users /tmp/ssa-exec-results/user-elfs.json \
  --out-dir /tmp/ssa-exec-regraded
```

The exit code must be taken from execution.json, never assumed from markers.
Runtime evidence will record the actual native results separately from this
log-only recheck. No Linux image, full upstream source, original PDF, credential
or backup bundle is included in this repository.

The leaf instruction oracle uses the fixed fixture, not a general monitor-cost
subtraction: 66 instructions per iteration and a fixed non-loop contribution18
yield3318 for50 iterations,6618 for100, and6636 for two50-iteration activations.
Stage4 common(0,100) had five extra non-loop user instructions (role check,
argument moves and stack adjustment), so its6623 is not this leaf's absolute oracle.
Old/new leaf virtual addresses are identical. Exact counts distinguish reset
from carry-over; any unexpected interrupt within a short leaf must be investigated,
not silently accepted by widening the oracle.

| Diagnostic label | Image/session | Observable result |
| --- | --- | --- |
| test5 | A before successful exec | depth1, closed leaf retained, parent abandoned; SSA_EXEC_END once |
| test6 | B after successful exec, same PID | new session/next image epoch, clean enable, closed nested tree and SSA_EXIT once |
| test7 | A with failed /absent exec | two depth1 queries in the same session; two completed leaf activations, then closed exit |
| test0..4 | unchanged stage4 fixture | single exit/security and corrected/legacy short-long preemption pairs |
