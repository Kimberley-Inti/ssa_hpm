# Stage8: native Cache event attribution

Status: five Cache RTL cases and all29 prior low-level cases passed on the new
model. Corrected independent Linux image is running; Linux acceptance is pending.
D03 is not closed until that passes. Base: accepted stage7,
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
