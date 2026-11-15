# Original development archives

[Kimberley-Inti/ssa_hpm](https://github.com/Kimberley-Inti/ssa_hpm) is the sole maintained project and presentation entry. It contains the implementation patches, generated source browser, tests, report and releases. The two original repositories are read-only archives; their existing visibility is retained.

| Archive | Visibility | Default branch | Original upstream-unique development commits | Review |
|---|---|---|---:|---|
| [Kimberley-Inti/SSA-HPM](https://github.com/Kimberley-Inti/SSA-HPM) | private | `main` | 15 | [closed original PR](https://github.com/Kimberley-Inti/SSA-HPM/pull/1) |
| [Kimberley-Inti/rocket-chip](https://github.com/Kimberley-Inti/rocket-chip) | public | `master` | 10 | [closed original PR](https://github.com/Kimberley-Inti/rocket-chip/pull/1) |

Counts describe the development refs before adding the archive notice, not the later README-only commits. Both original repositories had seven branches and no tags. Comparison used all fetched upstream branches and tags (413 Chipyard refs and 402 Rocket refs). Original SHAs, authors, author dates, current ref targets and complete name mappings are in [DEVELOPMENT_ARCHIVES.json](DEVELOPMENT_ARCHIVES.json). Full remote mirrors and local all-reference bundles were verified with Git object-closure and integrity checks; original history was not rewritten.

## Source coverage and original reviews

The Rocket review's implementation commits are preserved by the maintained Rocket patch series. The accepted final Rocket tree extends its original head. The Chipyard review's simulation build fixes, environment entry and calling-context fixtures are represented by the maintained build patches and standalone suite; original native logs remain under [calling-context evidence](../evidence/calling-contexts/). Its old test-layout edits, deleted prototype tests, PR-description files and repository plumbing remain recoverable in the original Git history rather than becoming current build inputs.

Both historical PRs are closed as superseded, without merging them into either archive. Their original review descriptions and records remain available, with a pointer to the maintained project. Historical PR head labels may retain a former branch name; current branch names and original head/base SHAs are recorded in the source index.

## Build and submodule independence

Current reconstruction fetches fixed public upstream baselines from ucb-bar/chipyard, chipsalliance/rocket-chip, firesim/linux and riscv/opensbi. It applies the [explicit patch series](PATCH_ORDER.md); neither archived repository is a fetch dependency. The [source browser](../src/README.md) verifies the accepted component trees without using local development worktrees.

The original Chipyard branch gitlinks refer to the original Rocket commits through the archived Linux-bootstrap revision; all those objects remain reachable in the Rocket archive. The current development worktree's later gitlink and its source commits are also preserved in the verified local bundle and maintained patch/source manifests. No submodule pointer or original development worktree was changed by archival organization.

## Naming and historical references

The archives use functional branch names. [HISTORY_MAP.json](HISTORY_MAP.json) distinguishes these remote archive names from earlier local aliases, which can point to different later commits. Local tracking refs were refreshed without replacing local default branches or accepted source heads. Original names remain in patch headers, raw logs, original source records, closed review metadata and immutable release snapshots. Those historical identifiers are evidence, not active build parameters.

Original documentation is retained below each archive's new English notice. The private Chipyard archive requires its existing GitHub access; the maintained project's public-baseline reproduction and report do not require that access.
