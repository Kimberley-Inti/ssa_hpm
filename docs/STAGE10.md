# Stage10: controlled transparent Linux launch

Status: accepted within the controlled single-hart/single-thread/non-privilege-
gaining ELF scope below. The original native run completed0, normal powerdown,
50automatic gates and26manual regression gates. Ten independent ELF capacity
gates, four automatic host mutations and the manual owner-swap negative pass.
C05 is closed only for this tested launch policy, not arbitrary Linux runtimes.
Final evidence: [summary](../evidence/stage10/summary.json).

## Baseline and behavior

Maintenance24fa1cde07a7af6de77c136789867ce730c60f91 (stage9; PR8 verified Open/Draft,
base stage8), Chipyard6abb37ea5316bb2cad9b8280b2485cf631d482c8,
Rocketbb5b1c26a8dae5d5afee716a1636b55a1bfe1ed2,
Linuxe341319bc75a2c2c1443d4b8654c9270f922aaf8,
OpenSBI43f02ffb329d9c86b2ff2138dc450b2060778ffe. All current work is on
stage10-transparent-launch; original branches/untracked work/backups are retained.

The design PDF's loader/SCBaseReg proposal (physical p8, p11–13) is adapted to
kernel-owned physical pools rather than moving arbitrary user stacks. The new
trusted prctl ARM_EXEC policy is a concrete controlled-loader adaptation, not a
claim of the original document having specified Linux lifecycle details.

[Policy](../integration/ssa/linux/transparent/POLICY.md) defines authority,
inheritance, success/failure boundaries, unsupported forms, resource failure,
profiles, dynamic loader visibility and counting. The trusted fixture init
selects fixed targets, arms with CAP_SYS_ADMIN+no_new_privs, then drops uid/gid.
Ordinary targets never call SSA START/STOP/EXPORT. Fork clears the child's policy;
selected same-PID exec starts a fresh session only after ELF readiness. ENOENT
returns preserve old frames. Exit/signal export once before pool release.

## Actual build and independent scope

Linux/OpenSBI were fetched at the pinned public bases and all ordered patches
applied in a new workspace. The reconstructed kernel tree equals the developer
kernel. New kernel/rootfs/firmware image builds completed; toolchain/Linux-binutils
caches and source-byte-verified musl1.2.5 loader build were reused. Musl itself was
actually built during this stage's dependency preparation, with its standard
RV64 Linux ABI and unmodified source. No loader binary/source tree is published.

Public Chipyard/Rocket fetch+patch+ROM/exact-file manifest checks passed. Fresh
ordinary/user regression ELFs were then rebuilt from that installed suite:
all runtime PT_LOAD bytes, entry and function symbols match the simulated ones.
Four full ELF hashes differ only random GCC temporary STT_FILE object names in
non-loaded string tables; those differences are recorded, not called bit-identical.

Rocket Scala, ROM and model are unchanged. The stage9 read-only progress harness
and model SHA256 d266da6457c89af8ec4f3daea0c8574ed048764fc15e25b54de3a1a23c458d62
are reused. No new RTL generation or second model build is claimed. The first
preparation boot was intentionally stopped before user acceptance after preflight
found missing /classnext for the appended old regression. The rootfs was rebuilt
with both /classnext and /plain-next. A second preparation boot revealed the large standard loader gzip inflate dominated RTL startup. It was preserved and superseded by the same ELF contents in an uncompressed initramfs, which --transparent now selects. This is a packaging/runtime optimization, not a monitoring fix or passing run. SIGTERM's
native0 is not an acceptance result; preparation-stop.json records this explicitly.

## Reproduce

After the standard public installation (REPRODUCE.md), choose new directories:

```sh
source ssa/env.sh
python3 ssa/linux/build-a.py --transparent --work /tmp/ssa-auto-linux --jobs 6
python3 ssa/linux/transparent/run.py --work /tmp/ssa-auto-linux --simulator sims/verilator/simulator-chipyard-SSAHPMEventRocketConfig --out-dir /tmp/ssa-auto-results
python3 ssa/linux/transparent/check-results.py --results /tmp/ssa-auto-results --work /tmp/ssa-auto-linux
```

--transparent builds the Cache-profile kernel/firmware, the ordinary static and
PT_INTERP/DSO targets, and the old manual classification lifecycle regression in
one image. Default base/DTLB/Cache/manual entries remain available. A verified
musl source+loader cache can optionally be passed with --musl-cache; this is reuse,
not a new libc build. The runner records actual native status/hash/runtime and
grades the complete automatic part and old manual regression separately. A log
prefix or a PASS substring is never the passing condition.

## Limits and final delivery work

Single hart, single thread, no privilege-gaining target, fixed2pools, existing
LIFO notification ABI, no generic unwind. Dynamic loader/app/DSO share the session
and raw addresses; loader continuation frames may be abandoned at exit. Data
transport completeness is separate from complete activations and classifier
coverage. The actual64-record fixture exported all4base chunks and marked the
63-row sidecar's dropped observation explicitly. Full-capacity UART stress,
performance overhead benchmarks and universal ELF symbolization remain separate.
The final implementation/review/performance/optional checklist is
[FINAL_CHECKLIST.md](FINAL_CHECKLIST.md).

Ordinary ELF sanity was additionally executed in QEMU user mode (static, musl
PT_INTERP/DSO and capacity programs, all0). This only diagnoses target binaries;
it is explicitly not Rocket/kernel policy/SSA evidence. The actual accepted
Linux image uses uncompressed initramfs to bound software inflate cost; old gzip
preparation and the missing-dependency preparation are preserved and not passed.

## Actual automatic acceptance

The actual native run reached AUTO_SUITE_END at76.3Mcycles:10owned sessions,
195base records.48automatic semantic gates plus actual native0 and powerdown
make50final gates. Earlier component checkpoints remain explicitly labelled as
live prefixes; automatic-final.json records the completed run.

- Static6records exactly match ordinary ELF callees/parents and known class vectors.
- Same-PID exec exports old closed records plus abandoned frame, then clean new
 image/session. ENOENT preserves history; fork child is unselected, CLONE_THREAD
 is rejected, SIGTERM15 exports an abandoned frame and releases the pool.
- Identical unselected ELF creates no session, setid is rejected, a third task
 reports pool_exhausted/-16 while two independent holders retain their histories.
- Timer cause, runnable state, involuntary switching, two open frames/RID2 and
 reciprocal S/R chronology prove automatic A→B→A including an unmonitored handoff.
 Both histories and all modular pause deltas match, and both call trees close.
- The actual musl interpreter/app/DSO returns0.105records/7chunks are complete;
 entry/app/interp metadata, application ELF and live DSO anchor match records.
 One loader continuationRID10 remains abandoned as specified.104closed records
 preserve inclusive cycle/instret/time relationships; activation completeness
 is false while transport is complete. This is not universal loader unwinding.
- Capacity64base records/4chunks match all target ELF callees and parents.63sidecar
 rows contain64classified accesses (2parent warmups+62leaf warmups),1dropped access
 and48FIFOevictions. Status9 means valid epoch+eviction, not invalid stack. The
 dropped field/total>63 explicitly makes classification coverage incomplete.
 Ten independent ELF-linked gates pass; the262143-ID maximum remains host/older
 low-level guard coverage rather than a full-size Linux UART run.

All tests are ordinary no-SSA target ELFs; trusted init alone arms the policy.
The tested automatic image covers flags0/4/6 and fixed Cache ABI2. Existing DTLB
manual/profile evidence is reused; a new automatic-DTLB native run is not claimed.

## Final native and regression evidence

The original runner/native PIDs68984/68986 were monitored through natural exit;
no replacement simulation was started on resumption. At the interrupted96.9M
checkpoint5/7manual exports meant the final pair was still printing. At99.2M the
capture had6/7 and was outputting task32/session17 snapshots. It subsequently
reached7/7, SSA_CLASSIFICATION_SUITE_END and `reboot: Power down` at~102.3Mcycles.
Native and both checker exits are0. Runtime27484.93host seconds is simulator wall
time, not an application performance measurement.

| Actual coverage | Result / evidence |
| --- | --- |
| Automatic ordinary static/exec/fork/signal/selection/resources/timer/dynamic/capacity | 50/50gates,10sessions/195records; automatic-final.json |
| Original explicit lifecycle/classification/process fixture in the SAME boot | 26/26gates,7sessions/20records; manual-final.json |
| Full transport and release | 17sessions/215records, all END checksums and releases valid |
| Intentional incomplete activations | sessions2/4/9/12 each export one abandoned frame; not fabricated returns |
| Bounded classification | 16sidecars/109rows; only capacity session10 lacks full semantic coverage (63rows/1drop) |
| Independent ELF capacity oracle | 10/10: all64addresses/parents/nonzero HPM, inclusive parent, exact warmups/input/FIFO/drop |
| Actual negative controls | identical ELF without policy; unprivileged ARM; setid/thread rejection; third pool exhausted |
| Host-only automatic mutations | missing auto hook, wrong target identity, repaired-checksum wrong category owner, missing END all rejected |
| Host-only original manual mutation | repaired-checksum A/B category swap remains valid transport but fails attribution |
| New host protocol/reference tests | 14rule examples,21sidecar cases,48export cases |
| Unchanged low-level coverage | 34historical cases (6Spike reference/28RTL) status/hash and6golden records14452/7226 rechecked; not new runs |

The model/boot/log SHA256 and actual native command/status are in
linux-execution.json. linux-rocket-linux-transparent.txt is the unchanged raw
capture, including read-only host progress diagnostics. manual-regression.txt is
its explicitly normalized suffix, not another native run. Only known diagnostic
lines are removed by the existing normalizer; raw capture remains canonical.

Public baselines, patch application, kernel tree and final98file manifest were
verified. Fresh independently installed user programs have equal PT_LOAD/entry/
symbols; the previously documented STT_FILE differences do not change runtime
code. Independent installed automatic/manual/capacity/negative checkers produce
exactly equal JSON on this SAME capture (independent-final-check.json). This is
source reconstruction/build plus same-log independent checking, not a second
full Linux simulation, cold-machine install, Scala or C++ model build.

## Source delivery and cheap committed-log replay

Linux8b865bfe4c40332446227e2fbf6b442ab0bc651a;
Chipyard suitef05e1a0dfa274f5505c80445cdc0d0205af54d86. The final source followup only adds a portable completed-run postcheck entry; the frozen kernel/user image and model are unchanged.
Rocket/OpenSBI remain the baseline heads above. Linux patch0008 follows0007;
no new Rocket/Chipyard Scala/OpenSBI implementation patch is required. Project
fixtures/build/check scripts are installed once as standalone integration/ssa.
Full original author/date/message mappings are in source-commits.json and HISTORY.

From the maintenance checkout, these recheck committed evidence without a model:

```sh
python3 integration/ssa/linux/transparent/grade.py evidence/stage10/linux-rocket-linux-transparent.txt --exit-code 0 --users evidence/stage10/ordinary-elf-build.json --out /tmp/ssa-auto-recheck.json
python3 integration/ssa/linux/grade-classification.py evidence/stage10/manual-regression.txt --exit-code 0 --out /tmp/ssa-manual-recheck.json
python3 integration/ssa/linux/transparent/negative.py --native-log evidence/stage10/linux-rocket-linux-transparent.txt --execution evidence/stage10/linux-execution.json --users evidence/stage10/ordinary-elf-build.json --out /tmp/ssa-auto-negative.json
python3 integration/ssa/linux/test_classification_native.py --native-log evidence/stage10/manual-regression.txt --execution evidence/stage10/manual-suffix-execution.json --out /tmp/ssa-manual-negative.json
```

For a new boot use the earlier build/run commands in new directories. The capacity
ELF check additionally takes `--work /tmp/ssa-auto-linux` and needs its frozen
plain-capacity binary plus transparent-users.json. Base/DTLB/Cache explicit
entries retain their earlier meanings; the automatic image actually exercised
flags0/4/6 with fixed Cache ABI2. Automatic DTLB, flags2-only, generic signal
handlers/nonlocal transfer, vfork/shared-mm and arbitrary dynamic runtimes are
not newly accepted by extrapolation. Trusted target selection is an audited
allowlist, not static detection of every unsupported binary control-flow pattern.

`check-results.py` requires the original native and both checker exits0 and exact
log identity, then runs all50/26/10 checks and automatic/manual negatives. It
writes `results/postcheck/` and never starts a simulator. The final source
followup was actually executed on the completed run from both development and
public installed suites; see postcheck-entry.json/independent-postcheck-entry.json.
The frozen newc archive's nine ELF SHA256 values (and identical root4755 plain
copy) were also verified inside Linux Image and the actual boot ELF; see
elf-image-identity.json. No target ELF was modified to enable monitoring.
