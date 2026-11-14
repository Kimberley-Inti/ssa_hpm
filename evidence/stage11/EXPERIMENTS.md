# Evidence interpretation

- `performance-final/`: formal new bare-model run, native0,150work samples,
  30calibration and6initialization samples, five repetitions per workload/mode.
- `lowlevel-summary.json`:40distinct cases (6Spike references,34Rocket RTL),
  plus the separate WB diagnostic. Negative-control native42 is expected;
  it is not relabeled as native0. Permission probes were expanded from5to7;
  their five repeated base cases are not double counted.
- `wb-memory-excerpt.txt`: unchanged SSA/native-status lines from the new actual
  WB run, excluding large per-cycle disassembly. Original and excerpt hashes
  are recorded. The published excerpt itself was rechecked successfully.
- `review-*.json`, `host-*.json`: host replay/mutations or synthetic boundary
  tests. Historical Linux replay is not a second hardware execution.
- `performance-interleaving-before.json`: intentionally failing host
  reproduction; its repaired counterpart is `host-performance-checker.json`.
- `diagnostic-status-explanation.json`: the completed pilot PID query returns1;
  this is not a retrieved native exit code. The30-row pilot had a DONE marker
  but no saved native exit receipt and is only a budget trial.
- Initial `/tmp/ssa-hpm-stage11/linux-unified/`, `linux-performance-run/`, and
  `linux-performance-final/` trials were superseded for the contract repair or
  matched-profile experiment design. Their candidate-superseded receipts retain
  reasons. SIGTERM can return native0, so they are never accepted results.
- Current Linux directories are `linux-unified-final` (default cost probes off)
  and `linux-performance-complete` (six modes including matched manual/automatic
  Cache+classification). Final acceptance requires their own end, native and
  checker receipts. They were still running at this source checkpoint.

The initial public apply/build and final-public clean apply precede test-only
suite refreshes. Hardware tree/ROM are unchanged and verified. Linux trees are
separately fetched/patched/built in production and measurement configurations;
`linux-final-source-equality.json` is the final tree proof. Earlier
`linux-source-equality.json` describes the pre-contract experiment, not the final
candidate. The source SHA map and explicitly referenced final receipts govern.

No images, upstream trees, generated RTL, binaries or PDFs are published.
Full local verbose logs remain in /tmp; their hashes and project trace excerpts
make the scope of the committed evidence explicit.
