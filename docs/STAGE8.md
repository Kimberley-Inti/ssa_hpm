# Stage8: native Cache event attribution

Status: accepted on actual Rocket/Verilator Linux. Five Cache RTL cases and all29
prior low-level cases passed on the newly generated model. The corrected Linux
image completed with native/runner exit0 and normal power-down:39 aggregate and
all-counter checks,69 Cache/event/exec gates and24 full-export gates passed.
D03's one-Cache-event gap is closed for this explicitly scoped native profile.
See [final summary](../evidence/stage8/summary.json). Base: accepted stage7,
2c63845c4bd262594f6d5ed0e4fc12773957d833; PR6 remains Draft/Open.

The native D$ miss EventSet entry has selector0x202 (set2,bit1). In the actual
blocking DCache (64sets,4ways,64B lines,16KiB,nMSHRs0), its source is
`io.cpu.perf.acquire := edge.done(tl_out_a)`. This is a completed outbound
TileLink A transaction, including cached acquisition and uncached requests;
it is not a unique retired load miss, incoming refill beat, or blocked cycle.
The native registered HPM increment follows next cycle. No new event is invented.
Original design p12 §3.1 includes Cache/TLB behavior; this native observable is
an explicit implementation adaptation of that goal, without relabeling it as
request-owner-tagged or retired-load-miss accounting.

One40-bit HPM3 counter is reused by a fixed Cache image profile. Both Linux and
OpenSBI compile with SSA_CACHE_PROFILE; default builds keep DTLB0x1002. ABI1/2
ROMs, memory offsets and modulo40 snapshot/rebase/accumulation stay unchanged.
The existing version1 stream adds explicit profile, selector and counter name;
Cache event payload is `cache`, DTLB payload remains `dtlb`. Old absent-profile
ABI2 captures mean DTLB. Mixed/unknown profiles, selectors and payloads fail.
Kernel/firmware must be paired; the actual boot selector is checked against all
exported metadata. User processes cannot choose selectors or another task's pool.

Events belong to actual sampling intervals, including delayed/replayed/speculative
transactions when accepted. Parents include child calls and interval-internal
kernel/trap/private-ROM work. S..R pauses are excluded from every open frame;
pre-S/post-R restore work and A's own cache misses after B's pollution remain
included. This is no cache partitioning, source privilege filtering, or precise
retired-instruction request attribution. Intervals must span fewer than2^40 events.

## Reproduce

Use REPRODUCE.md to fetch/apply the pinned public Chipyard/Rocket bases and install
the standalone suite. Never overwrite a running model/image/result directory.

```sh
source ssa/env.sh
make -C ssa -j4 all events cache-events linux-probes
make -C sims/verilator CONFIG=SSAHPMEventRocketConfig -j6 \
  OPT_FAST=-O3 OPT_SLOW=-O3 LINK='/usr/bin/g++ -B/usr/bin/'
python3 ssa/verify_cache.py \
  --simulator "$PWD/sims/verilator/simulator-chipyard-SSAHPMEventRocketConfig" \
  --out-dir /tmp/ssa-cache-rtl
python3 ssa/linux/build-progress.py --workspace "$PWD" \
  --config SSAHPMEventRocketConfig --out /tmp/ssa-cache-model
python3 ssa/linux/build-a.py --cache --work /tmp/ssa-cache-linux --jobs 4
python3 ssa/linux/run-exec.py --cache --work /tmp/ssa-cache-linux \
  --simulator /tmp/ssa-cache-model/simulator-progress \
  --out-dir /tmp/ssa-cache-linux-results --timeout 172800
python3 ssa/linux/export_results.py \
  /tmp/ssa-cache-linux-results/rocket-linux-events.txt \
  --out /tmp/ssa-cache-monitoring.json --tree-limit 64
python3 ssa/linux/test_export_results.py --out /tmp/ssa-cache-host.json
```

The bare-metal oracle (four source/negative/wrap cases plus one Cache-mode register
canary) traces real Cache source pulses, registered increments,
actual HPM CSR reset/reads and ELF-identified context keys. A one-line hot working
set contrasts with128 page-stride lines thrashing the same set; the cold context
is repeated. No prefetcher is introduced. Wrong-selector and swapped-context
negatives must exit42 and fail the positive relation; wrap crosses modulo40.
Raw disassembly can be large; event excerpts retain every source/CSR/guest row
unchanged and reports hash the full raw output kept outside Git.

The directed Linux boot tests8 Cache event/lifecycle sessions (context, corrected
and legacy timer pairs, successful/failed exec and replacement exit), then4
stage7 export cases (41/2/0/open). Two small/empty cases retain ABI1. This exercises
all changed metadata/export boundaries without replaying the unchanged old
three-counter Linux workload pairs. The old complete stage7 log is independently
regraded as historical evidence; it is not presented as a new Linux execution.
New model regressions cover base ABI1, DTLB ABI2, traps/permissions, register
canaries and both process protocols; Spike remains a reference, not a Cache model.

Versions/source SHA/tree mapping and precise completed coverage will be recorded
in evidence/stage8/. Public Linux/OpenSBI sources are newly fetched and built;
existing toolchain/Chipyard dependency/ccache caches may be reused. Independent
public Chipyard/Rocket patch reconstruction must match the implementation file
manifest; any reuse of the already built model must be identified explicitly.

## Workload correction before accepted Linux execution

Read-only BSS pages may alias the Linux shared zero page. Cache fixtures therefore
write each page before START to obtain distinct physical backing, then prewarm
and fence. Page allocation/initial writes are outside monitoring. The page-stride
lines conflict in the4-way L1, giving a reproducible data working set rather than
using virtual-address count as a proxy. PTW/private-ROM/kernel Cache traffic is
still included by the native event. The initial automatic launch raced this
preflight correction and was stopped at200000 harness cycles before userspace;
the simulator handled SIGTERM and returned0, but no power-down/test markers exist
and all graders rejected it. That superseded early boot is explicitly retained,
not counted as accepted Linux evidence. The corrected image has its own hashes
and run. See superseded-linux-start.json and linux-image-build.json.

Cache-mode all-register/x5 call/return canaries also pass in a dedicated ABI2
fixture; default DTLB/base/permissions/traps/process RTL regressions and six Spike
references pass on the newly generated model. An independently installed suite
repeated the four source/negative/wrap tests and the Cache canary on fresh test
images against that same verified model. This is model reuse, not a second model
build. Host parser tests now48, including payload-channel confusion detection.

## Historical in-flight Linux checkpoints

These preserve observations available during the run. Their pending/global-false
checkpoint summaries are superseded by the final accepted evidence below.

The corrected boot reached userspace. Session1 exported four complete Cache
records, exact parent/ELF keys: common under small-working-set parent counts4,
under128-page parent131; inclusive parents13/135. Both warm activations reuse
IDs1/2. Metadata saysCache/40bits/selector514; explicit STOP/export/repeat rejection
and release passed. A label such as warm names the small working set, not a claim
that every access hits: START clears a1MiB dictionary, and monitoring/cold paths
can evict prewarmed lines. The measured event includes their traffic as specified.

The corrected true timer pair completed: A has two open frames at cutout and
returns after resume; Cache10688raw-10495paused=193recorded. B common730 includes
real512-page Cache traffic and interval overhead. All four counter sample/record
identities passed on both tasks. Residual193 includes pre-S/post-R own kernel/ROM
and possible post-resume misses, not a promise of cache partitioning or a measure
of only A's retired data misses. Other suites and overall shutdown remain pending.

The Cache-mode replacement-image common performs a store sweep and a read sweep
of128 already-backed pages; old/failed exec leafs read64 pages per activation.
Initial backing faults/writes happen before START. Counts are not compared to
DTLB absolute values or to identical load-only work across images.

## Final acceptance

The corrected native execution completed in19620.89 host seconds (about5.45h),
last harness diagnostic75200000 cycles. `reboot: Power down`, all four export-case
PASS markers and the actual runner/native exit0 are present. All12 sessions /
63 records /13 chunks transferred and all pools were released. Open sessions6
(old exec) and12 (open-frame fixture) are intentionally semantic-incomplete,
transport-complete, not fabricated normal returns. No healthy run was restarted.
The earlier stopped200000-cycle preflight boot is retained separately; it was
rejected even though the simulator's signal handler returned0.

| Layer | Actual passed checks | Evidence under evidence/stage8/ |
| --- | ---: | --- |
| New Cache source/selector/context/reuse/wrap/canary RTL |5 cases|rtl-cache/ + cache-abi.json + cache-source-replay.json|
| Existing DTLB/base/trap/permission/process RTL and Spike references |29 cases (23RTL,6Spike)|rtl-dtlb/,rtl-regression/,probes/,process-regression/,spike/|
| Directed Linux Cache context/true timer/exec lifecycle |69/69|linux/event/summary.json|
| Linux full export/lifecycle fixture |24/24|linux/export/summary.json|
| Aggregate/all4 counter identities + parent restoration |39/39|linux/summary.json|
| Host capacity/profile/malformed protocol |48/48|final-host-tests.json|
| Actual Cache41 protocol and missing/duplicate/truncated mutations |4/4|final-host-tests.json|
| Fresh independent installed Cache benchmark repeat, same verified model |5 cases|independent-rtl-cache-final/|

The Linux count layers include dependency gates; they are not132 separate native
runs. There is one accepted full Cache boot. The unchanged old complete Linux
workload was not rerun: its immutable stage7 log was rechecked with current readers
and passed25/70/37/179. New Cache boots exercise the changed event, selector,
metadata, timer, exec and export paths; existing DTLB/base low-level behavior was
actually rerun on the new RTL model. Spike is an ISA/software reference only.

Key observed relationships (not universal expected absolutes):

- RTL source/CSR samples match hardware increments in both directions and every
  actual HPM CSR read matches the reset-plus-increment prefix. Global samples
  before/warm/firstcold/repeatedcold are4/16/156/288; common contexts1/261 and
  the same cold context accumulates across both calls. Startup pulses before
  selection are not conflated with selected HPM increments.
- Linux common under two parents counts4/131, inclusive parents13/135. A corrected
  timer pair restores both open frames; common193=raw10688-paused10495, B common730.
  Legacy A retains10752 including its10556 paused events; its entry was deliberately
  not rebased. Every counter's S/R and original/final/record identity passes.
  Corrected parent-only extras are B:729cycle/113instret/7time/12cache and
  A:904/113/9/17; bounded parent checks would catch applying correction only to
  the child. Residual Cache events include own pre-S/post-R kernel/ROM/interrupt
  and post-pollution work; this does not identify which request caused each miss.
- Same-PID successful exec old/new sessions6/7 have images2/3: old leaf65 and
  abandoned parent0, new leaf290 with closed parent299. The new workload is a
  store+read sweep of128 already-backed pages. FailedENOENT session8 retains its
  old tree and ends with leaf130 across two64-page read activations, parent552
  including failed-exec kernel work. All sessions export once before pool reuse.
- Actual large export session9 has41 records in16/16/9 chunks, sequential IDs and
  exact ELF/parent keys, END `e9872487db2fd6d0`. Small ABI1, empty ABI1, open ABI2
  and explicit STOP/repeat/busy tests pass. Host mutation checks select the actual
  completed41-record Cache session from the chained log, preserving protocol rows.

The independent installed final Linux checker replays the SAME completed raw log,
producing identical record JSON and check booleans (independent-final-check.json).
Its complete source manifest matches the public patch reconstruction; all7 freshly
compiled user ELFs byte-match the running image. Kernel/SBI sources were freshly
fetched/applied/built, then the corrected user/initramfs/kernel/firmware payload
was incrementally relinked from that verified cache. The independent RTL checks
reuse the new hash-verified model; no second complete model build is claimed.

Actual model SHA256:
`796d4752b2bc46aec87adf11c538c1a712071d8ce763568c8a7205d8fcdbf5ee`.
Corrected boot ELF:
`991b5ea21c581a9dcd20be0b4f2647e83e60d2d816a288c983ac9f3be6d19e9c`.
Full raw serial log:
`881e85fbe2a9600088bb81d5810d2341122ed9c04759cf1509010af1f6653c06`.
Actual argv/exit/image/model hashes are in linux/execution.json and runner-status.json.
Tools are pinned/reported in versions.json; build logs, source trees, dependency
reuse distinctions and artifact hashes are committed. RTL source/CSR event
excerpts preserve every relevant native row; full noisy disassembly logs remain
locally outside Git with their original hashes in the RTL reports.

To recheck committed evidence without launching another simulation:

```sh
python3 integration/ssa/linux/grade-cache.py \
  evidence/stage8/linux/rocket-linux-events.txt --exit-code 0 \
  --users evidence/stage8/linux/user-elfs.json --out-dir /tmp/ssa-cache-review
python3 integration/ssa/linux/test_export_results.py \
  --native-log evidence/stage8/linux/rocket-linux-events.txt \
  --out /tmp/ssa-cache-host-review.json
```

D02 scalar/stream/random classification remains next-round work and first needs
precise rules. Generic automatic Linux loader enable, multicore/migration, other
Cache/TLB events, request-owner tagging/privilege filtering, arbitrary unwind,
multithread/setuid/complexexec, maximum-capacity serial stress and native I/O-failure
injection remain outside this accepted fixed single-hart profile.
