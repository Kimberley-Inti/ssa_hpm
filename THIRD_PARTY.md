# Sources, copyright and licensing

This repository distributes project patches, selected patched core source files, original fixtures, documentation and validation evidence. It does not import upstream Git ancestry or complete upstream source trees. Patch context and removed lines retain their original copyright and license conditions. Original patch authors, dates and commit messages are preserved in [HISTORY.md](HISTORY.md).

| Material | Source and applicable license |
| --- | --- |
| Rocket Chip Scala and patch context | chipsalliance/rocket-chip, baseline `44b0b8249279d25bd75ea693b725d9ff1b96e2ab`; Berkeley and SiFive file notices, retained in `LICENSES/` |
| Chipyard build/configuration context | ucb-bar/chipyard, baseline `2d03d10837fc1a7569d10ae2c91c8132c7fee77d`; BSD-3-Clause and applicable SiFive notices |
| Constellation dependency | Only its URL and fixed revision are recorded; source is fetched independently |
| Linux patches | firesim/linux `5f5fd87b36e21ed59b759b69eebfa1c74955cb37` (5.7-rc3), GPL-2.0; original file notices apply |
| OpenSBI platform patches | riscv/opensbi `a98258d0b537a295f517bbc8d813007336731fa9` (0.8), BSD-2-Clause; utility files retain their own notices |
| Project fixtures and tools | Applicable per-file SPDX identifiers and original notices; provenance is recorded in the manifests and history |
| Evidence | Original text/JSON outputs and artifact hashes, without the corresponding large compiled images |
| English report | Written for this project by Liu Qinruo; template style sources retain the notices described in [report/README.md](report/README.md) |

No single additional license is imposed on all project-original materials by this publication. Public visibility permits inspection under the hosting platform's terms; redistribution and modification rights follow the applicable file licenses and copyright holders' grants. Existing MIT, GPL and upstream notices remain intact. Publication does not replace them.

The Linux builder fetches pinned source and a pinned Ubuntu Linux-target binutils package. Toolchain binaries, package archives and built images are not redistributed. For the dynamic fixtures it builds unmodified musl 1.2.5 from https://musl.libc.org/releases/musl-1.2.5.tar.gz (SHA-256 `a9a118bbe84d8764da0ea0d28b3ab3fae8477fc7e4085d90102b8596fc7c75e4`). musl uses the MIT license with individual upstream notices retained. Its source tree and binaries are fetched/built locally rather than included here.

The original acceptance checkout ignored `ssa/env.sh`; this reproduction helper was explicitly added during packaging. Canonical microcode remains in the Rocket patches rather than a second independently maintained copy. Cost probes preserve Linux GPL-2.0-only notices; workload fixtures retain their marked project licenses.

Excluded materials include the two original design PDFs, the supplied report template's prior prose, student information, screenshots and slides, backup bundles, complete upstream trees, generated RTL, firmware/kernel images, credentials and account configuration. Historical commit author identities are retained as development provenance. The English report reuses only the template's independently sourced ACL style and bibliography style; its prose, diagrams, tables and data are project-specific.

The generated core files under [src/](src/README.md) retain their original file headers and component-relative paths. Component license texts accompany the selected sources. Their fixed public baselines, patch hashes and accepted tree identities are recorded in `src/manifest.json`; the full upstream trees and Git ancestry remain external build inputs.
