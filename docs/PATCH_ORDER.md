# Explicit patch series

[patch-series.json](../integration/ssa/patch-series.json) is the canonical ordered configuration. Arrays define application order independently of filenames. Each entry supplies its SHA-256 and a selection condition. Installers, the Linux image builder and the source-browser reconstructor read this same shipped file.

`always` applies to every image. Other conditions preserve the existing process, exec, event, export, classification and transparent-launch flags and are disabled for a reference image. Build flag implications are unchanged. The final accepted profile applies every active entry. The three historical Chipyard test patches are listed separately as archive-only and are not part of production reconstruction.

## Chipyard

Baseline: `2d03d10837fc1a7569d10ae2c91c8132c7fee77d`. Accepted patched tree: `ba41f91861f379a2ff75953ffb6d712305975f62`.

1. [constellation-dependency.patch](../patches/chipyard/constellation-dependency.patch) — `always`.
1. [fesvr-verilator-build.patch](../patches/chipyard/fesvr-verilator-build.patch) — `always`.
1. [dtlb-hpm-config.patch](../patches/chipyard/dtlb-hpm-config.patch) — `always`.

## Rocket Chip

Baseline: `44b0b8249279d25bd75ea693b725d9ff1b96e2ab`. Accepted patched tree: `0c41414a848beded9c96acc413a3d85eec00ef9b`.

1. [hpm-context-tracking.patch](../patches/rocket-chip/hpm-context-tracking.patch) — `always`.
1. [trap-mode-routing.patch](../patches/rocket-chip/trap-mode-routing.patch) — `always`.
1. [trap-signal-placement.patch](../patches/rocket-chip/trap-signal-placement.patch) — `always`.
1. [forced-monitor-exit.patch](../patches/rocket-chip/forced-monitor-exit.patch) — `always`.
1. [normal-monitor-exit.patch](../patches/rocket-chip/normal-monitor-exit.patch) — `always`.
1. [monitor-exit-finalization.patch](../patches/rocket-chip/monitor-exit-finalization.patch) — `always`.
1. [inherited-context-implementation.patch](../patches/rocket-chip/inherited-context-implementation.patch) — `always`.
1. [context-retirement-attribution.patch](../patches/rocket-chip/context-retirement-attribution.patch) — `always`.
1. [trap-context-isolation.patch](../patches/rocket-chip/trap-context-isolation.patch) — `always`.
1. [sv39-pc-width.patch](../patches/rocket-chip/sv39-pc-width.patch) — `always`.
1. [linux-user-pool-privileges.patch](../patches/rocket-chip/linux-user-pool-privileges.patch) — `always`.
1. [dtlb-request-attribution.patch](../patches/rocket-chip/dtlb-request-attribution.patch) — `always`.
1. [cache-event-trace.patch](../patches/rocket-chip/cache-event-trace.patch) — `always`.
1. [memory-classification.patch](../patches/rocket-chip/memory-classification.patch) — `always`.

## Linux

Baseline: `5f5fd87b36e21ed59b759b69eebfa1c74955cb37`. Accepted patched tree: `c937114e57032e8f896bc853d1d63ff16e9bf8a7`.

1. [stack-pointer-declaration.patch](../integration/ssa/linux/stack-pointer-declaration.patch) — `always`.
1. [linux-task-pools.patch](../integration/ssa/linux/linux-task-pools.patch) — `process`.
1. [linux-exec-lifecycle.patch](../integration/ssa/linux/linux-exec-lifecycle.patch) — `exec`.
1. [linux-dtlb-event.patch](../integration/ssa/linux/linux-dtlb-event.patch) — `event`.
1. [linux-result-export.patch](../integration/ssa/linux/linux-result-export.patch) — `export`.
1. [linux-cache-profile.patch](../integration/ssa/linux/linux-cache-profile.patch) — `export`.
1. [linux-memory-classification.patch](../integration/ssa/linux/linux-memory-classification.patch) — `classification`.
1. [linux-transparent-launch.patch](../integration/ssa/linux/linux-transparent-launch.patch) — `transparent`.
1. [linux-cost-probes.patch](../integration/ssa/linux/linux-cost-probes.patch) — `transparent`.
1. [linux-classification-contract.patch](../integration/ssa/linux/linux-classification-contract.patch) — `classification`.

## OpenSBI

Baseline: `a98258d0b537a295f517bbc8d813007336731fa9`. Accepted patched tree: `c8e81125ce6b92976ccfff630c49a61d9d887e91`.

1. [opensbi-rocket-platform.patch](../integration/ssa/linux/opensbi-rocket-platform.patch) — `always`.
1. [opensbi-dtlb-profile.patch](../integration/ssa/linux/opensbi-dtlb-profile.patch) — `event`.
1. [opensbi-cache-profile.patch](../integration/ssa/linux/opensbi-cache-profile.patch) — `event`.

The Chipyard tree identity is measured after its three patches, before installing the standalone suite. Installed test/tooling files have a separate expected-file inventory in provenance.json; adding the series file updates that inventory without changing the hardware configuration. Rocket, Linux and OpenSBI identities are their full accepted component trees.

[PATCH_NAMES.json](PATCH_NAMES.json) records all 33 original/new names and byte-identical hashes. Original patch headers and raw logs retain their historical subjects and paths. See [HISTORY.md](../HISTORY.md) for source authors and dates.

```sh
python3 scripts/check_patch_series.py
python3 scripts/apply.py /tmp/ssa-patched-workspace --report /tmp/ssa-apply.json
python3 scripts/source_browser.py check --work /tmp/ssa-component-check
```

The selection checker compares all 128 combinations of the seven Linux feature/reference flags with the original builder and verifies the unchanged build pipeline outside patch application. Actual fresh public-baseline reconstruction establishes the final source-tree equality.
