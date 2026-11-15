# Validation evidence

## Final candidate

[Validation](VALIDATION.md) defines the accepted source combination and distinguishes actual native execution from saved-log replay. The [final summary](../evidence/final-validation/summary.json) indexes 40 directed cases, production Linux checks and performance experiments. Its [artifact manifest](../evidence/final-validation/artifact-manifest.json) hashes the retained evidence files.

- Native console logs and execution receipts retain exit codes, model/image hashes and shutdown markers.
- Earlier failed native and host checks remain available alongside corrected results; semantic mutations remain negative controls.
- [Performance](PERFORMANCE.md) explains independent target boundaries, repetitions, ranges and instruction accounting. Raw performance rows remain unchanged.
- Historical feature evidence is retained where it establishes behavior or a negative comparison. Directories use functional names. [EVIDENCE_PATHS.json](EVIDENCE_PATHS.json) records the original names; raw logs retain their original internal paths and bytes. Historical test/schema identifiers remain compatibility keys, not current directory names.
- `evidence/publication/dependencies.json` remains an input to the pinned dependency initializer. The other retained files in that directory describe actual source application, builds, RTL/Spike runs, source identities and report compilation.

Use `python3 scripts/final.py check-evidence --out /tmp/ssa-check` to replay the final oracles, `python3 scripts/check_repository.py` for links and inventories, and `python3 scripts/audit.py --all` for reachable-history inspection. Choose a new evidence output directory. Full reconstruction commands are in [REPRODUCE.md](../REPRODUCE.md).
