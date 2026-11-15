# Maintenance and release provenance

The accepted implementation is preserved by v0.2.0 at
2adbfa5de81f341bd575e8498b370c5a12a02785. Its candidate was
9c1fdfb0e147c27f7aca58f306e91f532c3fb609; the integrated complete tree is identical.
Ten project PRs were merged in dependency order with merge commits. Original
commits and both release tags remain reachable. The
[release](https://github.com/Kimberley-Inti/ssa_hpm/releases/tag/v0.2.0) attaches
integration, history-audit and GitHub read-back receipts.

Current functional branch aliases retain those exact historical head commits;
[HISTORY_MAP.json](HISTORY_MAP.json) records the old/new names and document paths.
Closed PR URLs and release tags are stable. Original branch labels in raw receipts
and commit messages identify their historical execution and are intentionally
retained. Original documentation can be opened at the v0.2.0 tag with its old path.

The public-presentation follow-up edits README/navigation/report and project
metadata. It does not change the validated Rocket/Linux implementation. It is
reviewed as a separate commit on public-presentation and integrated into main
without squashing or retagging v0.2.0. Current full reproduction fetches public
Chipyard/Rocket/Linux/OpenSBI baselines and applies ordered patches; it relies on
recorded source trees and manifests rather than locally generated commit IDs.

Historical one-time publication/integration scripts are retired at their current
entry points. Their exact original implementations remain in v0.2.0 history.
Use the reproduction and evidence-verification entry points for current checks.
The development Rocket fork remains a separate original-history archive; see
[its assessment](ROCKET_CHIP_ARCHIVE.md). Remote repository deletion requires a
separate explicit decision and is not part of presentation cleanup.
