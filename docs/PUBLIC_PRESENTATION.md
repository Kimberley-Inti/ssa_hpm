# Public presentation and archival references

The implementation release remains **v0.2.0**, integrated at
`2adbfa5de81f341bd575e8498b370c5a12a02785` from candidate
`9c1fdfb0e147c27f7aca58f306e91f532c3fb609`. Subsequent presentation commits add the
English introduction, functional navigation and project report. Implementation
patches, original author records, release tags and raw validation captures remain
unchanged.

## Functional naming

[HISTORY_MAP.json](HISTORY_MAP.json) records every old branch, new branch and
unchanged full SHA across the maintenance and four development repositories.
Ten maintenance remote branches and 62 local branch references were renamed.
Each remote target was read back and matched before proceeding. Documents are
mapped in the same file. Short compatibility pages at former document paths keep shared links usable; raw evidence directories keep their original storage
identifiers so checkers and historical checksums continue to work.

GitHub keeps old head labels on already-merged PRs. Their URLs, merge commits and
base `main` remain valid. The ten PR titles/descriptions now link their functional
aliases and current documentation. An old Git client must fetch/use the new
branch name; GitHub web redirects do not rename a local tracking branch. The
original Rocket fork PR and its two archival branch names remain intact because
they are a live development-review dependency. Source-repository local aliases
were synchronized without changing code or archival remote references.

The one-time release/integration automation is retired. Its exact original code
is retained at v0.2.0; current verification uses [REPRODUCE.md](../REPRODUCE.md),
not an old script that assumes private visibility or obsolete branch names.

## Checks performed for this presentation

- Fresh fetch of the two public reconstruction baselines, all 17 Chipyard/Rocket
  patches, all expected installed-file hashes, exact Rocket tree and ROM check.
- Twelve host-only accepted-evidence replay steps; all 300 performance workload
  results rechecked. No new hardware execution is counted for this documentation change.
- Functional Markdown links, unchanged implementation patches, source-package
  membership and preserved implementation tags.
- English report compilation, independent ZIP extraction/compilation and matching
  PDF text; page-by-page visual inspection, embedded fonts, author metadata,
  references and overflow checks.
- All reachable standalone Git commits, blobs, refs and tags inspected for excluded
  source trees, binaries, backup bundles and credential patterns. Only the authored
  PDF and inspectable LaTeX ZIP are permitted publication binaries.
- Every existing release attachment downloaded, JSON/size/hash checked and scanned.
  No Actions runs or artifacts exist. Public Git author identities and historical
  source paths remain development provenance; credentials and account configuration
  are excluded. No history rewrite was needed.

Receipts are in [evidence/publication](../evidence/publication/). Original validation
receipts remain in their fixed directories. Source worktrees and their pre-existing
untracked files were preserved. The original design PDFs and supplied template's
prior report, student fields and example assets were excluded from distribution.

## Development fork

[Archive assessment](ROCKET_CHIP_ARCHIVE.md) explains the ten upstream-unique Rocket
commits, matching preserved patches and recoverable local mirror/bundle. Retaining
the fork preserves research provenance and its open draft review. It is not pinned;
SSA-HPM is the principal presentation entry. Deletion was not performed.
