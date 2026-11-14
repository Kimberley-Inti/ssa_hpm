# Stage10: controlled transparent Linux launch

Status: all automatic scenarios completed with48semantic gates and10independent ELF-linked capacity gates passed (same original Rocket/Linux run). The appended manual regression and final native shutdown are still running. C05 final acceptance remains pending those results.

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
python3 ssa/linux/transparent/grade.py /tmp/ssa-auto-results/rocket-linux-transparent.txt --exit-code 0 --users /tmp/ssa-auto-linux/transparent-users.json --out /tmp/ssa-auto-grade.json
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
coverage. A64-record fixture must export all4base chunks while marking the
63-row sidecar's dropped observation explicitly. Full-capacity UART stress,
performance overhead benchmarks and universal ELF symbolization remain separate.
The final implementation/review/performance/optional checklist is
[FINAL_CHECKLIST.md](FINAL_CHECKLIST.md).

Ordinary ELF sanity was additionally executed in QEMU user mode (static, musl
PT_INTERP/DSO and capacity programs, all0). This only diagnoses target binaries;
it is explicitly not Rocket/kernel policy/SSA evidence. The actual accepted
Linux image uses uncompressed initramfs to bound software inflate cost; old gzip
preparation and the missing-dependency preparation are preserved and not passed.

## Completed automatic prefix

The actual native run reached AUTO_SUITE_END at76.3Mcycles:10owned sessions,
195base records.48automatic semantic gates pass; native exit/shutdown remain
separate pending gates. See automatic-checkpoint.json and component checkpoints.

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
