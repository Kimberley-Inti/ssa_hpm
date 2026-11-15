# Memory classification validation

[Rule1](CLASSIFICATION.md) supplies an executable definition for the original
brief's scalar/stream/random categories. It observes valid retired integer
1/2/4/8-byte load/store instructions using virtual PC/address. Replay, exception,
cancellation, private ROM, kernel accesses under user-only policy and other memory
instruction families are excluded at the source. One accepted access produces one
warmup/scalar/stream/irregular category for its context.

The independent Python reference consumes actual observed sequences. Four RTL
fixtures exercise fixed, stride, irregular, mixed/interleaved patterns, first
accesses, repeated/different-parent contexts, eviction/capacity and fault/replay
boundaries. The pre-clock WB oracle sees82candidates and 72accepted observations,
including7replay candidates and 1exception. Wrong category/context controls are
rejected even after transport checksums are repaired.

Linux preserves histories across open-frame task switches, resets new exec epochs,
and exports exclusive category rows with completeness diagnostics. The final
production capture checks those paths together with 63-row overflow and 48FIFO
evictions. [Retirement oracle](../evidence/stage11/wb-summary.json),
[RTL cases](../evidence/stage11/regression-classification/summary.json),
[production manual checks](../evidence/stage11/linux-unified-final/manual-summary.json)
and [original dedicated Linux evidence](../evidence/stage9/summary.json) identify
new execution versus retained historical evidence. Irregular means that the
specified local pattern was not recognized; the rule has no statistical-randomness test.
