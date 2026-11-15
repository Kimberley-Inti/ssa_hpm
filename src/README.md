# Core implementation source browser

These files are generated verbatim from fixed public baselines after applying the accepted project patches. [Accepted component identities](../evidence/final-validation/source-commits.json), component-relative paths and upstream copyright/license notices are preserved. This small selection makes the implementation directly readable; it is not a standalone replacement for the complete upstream trees.

| Component | Core files | Role in the actual build |
|---|---|---|
| Rocket calling contexts | [RocketCore.scala](rocket-chip/src/main/scala/rocket/RocketCore.scala) | Call/return detection, private register bank and injected ROM execution; compiled by Chipyard's Rocket generator |
| Counter/privilege interface | [CSR.scala](rocket-chip/src/main/scala/rocket/CSR.scala), [IDecode.scala](rocket-chip/src/main/scala/rocket/IDecode.scala) | Monitoring state, CSR interfaces and instruction decode |
| Retirement classifier | [SSAMemoryClassifier.scala](rocket-chip/src/main/scala/rocket/SSAMemoryClassifier.scala) | Rule1 per-session/per-context retired integer-access classification |
| Private microcode | [microcode.S](rocket-chip/src/main/resources/ssa/microcode.S), [ROM generator](rocket-chip/scripts/gen-ssa-rom.py) | Canonical helper assembly; generation/checking of constants embedded in RocketCore |
| Linux monitoring | [ssa_hpm.c](linux/kernel/ssa_hpm.c), [ssa_hpm.h](linux/include/linux/ssa_hpm.h) | Pool/session ownership, pause/rebase, exec/exit, launch policy, profile state and chunked export |
| OpenSBI platform | [platform.c](opensbi/platform/ssa_rocket/platform.c), [config.mk](opensbi/platform/ssa_rocket/config.mk), [objects.mk](opensbi/platform/ssa_rocket/objects.mk) | Fixed single-hart timer/interrupt/console platform and native HPM event selection |

Linux scheduler, fork, exec, ELF-ready and syscall hooks are supplied by the [Linux patch series](../integration/ssa/linux/). Their complete upstream files are reconstructed during the build, rather than duplicated here for a few hook lines. Chipyard configuration/build changes remain in [Chipyard patches](../patches/chipyard/). Tests, reference models, runners and parsers remain under [integration/ssa](../integration/ssa/).

## Generate and verify

```sh
python3 scripts/source_browser.py generate --work /tmp/ssa-browser-reconstruction
python3 scripts/source_browser.py check --work /tmp/ssa-browser-reconstruction
```

The external work directory is created from the pinned public repositories. Sparse partial checkouts limit downloaded file contents; the full reconstructed Git tree must match the accepted tree for every component. The generator applies all component patches, copies only the explicit file list and writes [manifest.json](manifest.json). The checker compares every byte, patch hash, component tree and inventory entry. A new work directory gives an independent reconstruction; an existing directory is accepted only after exact-tree validation. It never reads implementation files from the original VM development worktrees.

The browser is generated output: change the patch-authoritative implementation, then regenerate it. Full RTL/Linux reproduction continues through [REPRODUCE.md](../REPRODUCE.md) and `scripts/final.py reproduce`, which use the original patch mechanism. `src/` is not added to the simulation build's include path. No model or workload semantics are changed by this presentation layout.

## Licensing

Rocket files retain their original headers and [Berkeley](rocket-chip/LICENSE.Berkeley)/[SiFive](rocket-chip/LICENSE.SiFive) notices. Linux monitoring files are GPL-2.0-only; [COPYING](linux/COPYING), [GPL-2.0](linux/LICENSES/preferred/GPL-2.0) and the referenced [syscall note](linux/LICENSES/exceptions/Linux-syscall-note) are included. The OpenSBI platform preserves its BSD-2-Clause notice and [COPYING.BSD](opensbi/COPYING.BSD). See [THIRD_PARTY.md](../THIRD_PARTY.md) for the complete project source/rights policy.
