# Reproduction and evidence verification

## Public source baselines

| Component | Upstream | Pinned baseline |
|---|---|---|
| Chipyard |https://github.com/ucb-bar/chipyard.git|`2d03d10837fc1a7569d10ae2c91c8132c7fee77d`|
| Rocket Chip |https://github.com/chipsalliance/rocket-chip.git|`44b0b8249279d25bd75ea693b725d9ff1b96e2ab`|
| Constellation dependency |https://github.com/ucb-bar/constellation.git|`dce9eb03b44ad442a552242546f1672bdc15fce3`|
| Linux |https://github.com/firesim/linux.git|`5f5fd87b36e21ed59b759b69eebfa1c74955cb37`(5.7-rc3)|
| OpenSBI |https://github.com/riscv/opensbi.git|`a98258d0b537a295f517bbc8d813007336731fa9`(0.8)|

The installers fetch the public baselines, apply three Chipyard and fourteen
Rocket patches in filename order, then install standalone `integration/ssa`
fixtures. Linux/firmware builders select their ordered profile-specific patches.
`patches/history` is archival and is not applied. The Rocket tree and exact
installed-file hashes must match `provenance.json`; reconstructed commit IDs can
differ through committer metadata. No fetch of a VM-local development commit is
required. The distributed Chipyard gitlink deliberately retains the fetchable
public Rocket baseline while the nested checkout receives its patches.
Avoid submodule operations that restore that patched checkout to the base.

The original local Chipyard baseline c2391670 referenced local Rocket23f5a64f;
this public-baseline reconstruction removes that external-reproduction dependency.
The [reference map](docs/HISTORY_MAP.json) translates former branch/document names.
Raw evidence directories and mail-patch headers retain their original identifiers.

## Quick host-only verification

Run from this repository with Python3. Choose a new/empty output directory:

```sh
python3 scripts/final.py check-evidence --out /tmp/ssa-evidence-check
```

This verifies published evidence hashes, native receipts/terminal markers and
parses the saved captures. It reruns automatic/manual semantic checks, export and
sidecar tests, reference tests, performance/result arithmetic, direct accounting
mutations and the WB oracle. It builds or executes no hardware model or target ELF.
The ELF-linked capacity receipt is hash-verified; rebuilding those excluded
binaries is part of the full path. The accepted raw evidence remains unchanged
from v0.2.0; current presentation/report commits update documentation separately.

## Complete build and execution

Prerequisites are Git, Python3, RISC-V GCC/binutils, Spike, Java/sbt, Verilator and
matching Chipyard dependencies. The accepted host used Ubuntu22.04, GCC15.1.0,
Verilator4.226, Spike1.1.1-dev, Java17 and Python3.12.12. Exact observations are in
[evidence](evidence/final-validation/tools.json). Linux bootstrap extracts a pinned Ubuntu
binutils package project-locally; it does not require replacing the system linker.

```sh
python3 scripts/final.py reproduce /tmp/ssa-rebuild \
  --reuse-dependencies /path/to/matching-chipyard --jobs 6
```

An optional `--musl-cache /path/to/musl-1.2.5` is accepted after source verification;
otherwise the fixed source archive is fetched and built. The musl version/SHA is
recorded in [source notices](THIRD_PARTY.md). Actual validation reused pinned
system/tool/dependency/musl caches, freshly fetched the main public source bases,
and compiled a new model and three Linux payloads. Full Linux runs take hours
on the recorded VM. The wrapper uses new directories and preserves completed
receipts; inspect these before repeating an interrupted job.

The complete entry runs the two-record accounting companion before the full
performance image. The full image allocates three records in its A/B fixture;
the inherited kernel diagnostic emits snapshot proof only for exactly two. The
final checker explicitly joins the full work/phase capture with its separate
companion. This does not invent account rows in the original capture.

## Individual reconstruction and dependency preparation

```sh
python3 scripts/apply.py /tmp/ssa-chipyard --report /tmp/ssa-apply.json
python3 scripts/link_existing_dependencies.py /tmp/ssa-chipyard /path/to/chipyard-cache \
  --report /tmp/ssa-dependencies.json
```

The cache linker checks pinned Git revisions and tracked cleanliness, links only
matching dependencies into the new workspace, and leaves the original source
worktree intact. For a new host, `scripts/init_build_dependencies.py` offers a
network bootstrap for the recorded Rocket dependencies. System package/network
availability for a fully uncached machine was not independently retested. Choose
one dependency preparation path; do not initialize network submodules over links.

```sh
cd /tmp/ssa-chipyard
source ssa/env.sh
python3 ssa/gen_rom.py --check
make -C sims/verilator CONFIG=SSAHPMEventRocketConfig -j6 \
  OPT_FAST=-O3 OPT_SLOW=-O3 LINK='/usr/bin/g++ -B/usr/bin/'
make -C ssa -j6 all events cache-events classification linux-probes
python3 ssa/verify.py --simulator sims/verilator/simulator-chipyard-SSAHPMEventRocketConfig --out-dir /tmp/ssa-base
python3 ssa/verify_events.py --simulator sims/verilator/simulator-chipyard-SSAHPMEventRocketConfig --out-dir /tmp/ssa-dtlb
python3 ssa/verify_cache.py --simulator sims/verilator/simulator-chipyard-SSAHPMEventRocketConfig --out-dir /tmp/ssa-cache
python3 ssa/classification/run.py --simulator sims/verilator/simulator-chipyard-SSAHPMEventRocketConfig --out-dir /tmp/ssa-classification
```

`verify.py` does not implicitly build RTL. SimDRAM's `+loadmem` expects the
project-generated reversed-byte hexadecimal image, not an ELF file. The installed
`elf_to_hex.py` and build targets supply both files. Native negative controls can
have an expected nonzero status; the checker compares actual status and semantic
relationships rather than treating every nonzero code alike.

## Linux production and direct accounting

The standard simulator or a read-only progress executable linked to its unchanged
model archive can run these payloads:

```sh
python3 ssa/linux/build-progress.py --workspace "$PWD" \
  --config SSAHPMEventRocketConfig --out /tmp/ssa-progress
python3 ssa/linux/build-a.py --work /tmp/ssa-linux --transparent
python3 ssa/linux/transparent/run.py --work /tmp/ssa-linux \
  --simulator /tmp/ssa-progress/simulator-progress --out-dir /tmp/ssa-linux-results
python3 ssa/linux/transparent/check-results.py \
  --results /tmp/ssa-linux-results --work /tmp/ssa-linux
```

For the small direct snapshot proof alone:

```sh
python3 ssa/linux/build-a.py --work /tmp/ssa-accounting-build --performance-switch
python3 ssa/performance/linux-run.py --work /tmp/ssa-accounting-build \
  --simulator /tmp/ssa-progress/simulator-progress \
  --out /tmp/ssa-accounting-results --switch-only
python3 ssa/performance/linux-check.py --out /tmp/ssa-full-performance-results \
  --accounting-witness /tmp/ssa-accounting-results
```

The final line rechecks an already completed full performance capture, rather than
starting another simulation. Full performance image selection is `--performance`;
its runner accepts the same `--accounting-witness` argument. `--event`, `--cache`,
`--classification`, `--export`, `--exec` and `--process` retain their individual
fixture entries. Automatic DTLB is outside the validated combination matrix.

Actual commands, source/model/image hashes, native codes, normal shutdown and
checker coverage are indexed in [Validation](docs/VALIDATION.md) and the
[accepted summary](evidence/final-validation/summary.json). [Performance](docs/PERFORMANCE.md)
defines sampling/probe/IRQ/console boundaries. [Report sources](report/README.md)
provide an independent document-build entry; they do not trigger long simulations.

## Source-browser consistency

The generated [source browser](src/README.md) is separate from build inputs.
Reconstruct and compare its accepted component trees with:

```sh
python3 scripts/source_browser.py check --work /tmp/ssa-browser-independent
```

A fresh external directory fetches fixed public baselines and applies the component
patches. The complete build still uses the commands above. Historical raw log
paths map through [EVIDENCE_PATHS.json](docs/EVIDENCE_PATHS.json); their bytes and
hashes are preserved.
