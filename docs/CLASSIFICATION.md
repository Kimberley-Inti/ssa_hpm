# Memory classification rule 1 — stage9 design supplement (not yet accepted)

Design PDF physical page12 §3.1(2) names scalar/stream/random, but defines no
algorithm. The following is an explicit project choice, not a quotation from it.

Observe once at Rocket `wb_valid` (valid, no replay, no exception), integer
M_XRD/M_XWR only, widths1/2/4/8B. Address is virtual effective address from
`wb_reg_wdata`; PC is retired instruction PC. This is an architectural scalar
memory instruction observation, not data-response completion, Cache transaction,
or a classification of all bus requests. Exclude FP/vector/AMO/LRSC/PTW, cancelled
instructions, private ROM, and kernel instructions under Linux U-only policy.
Delayed load data responses must not count again. Cache/TLB effects may change
latency but not this address rule. Faulting access is not a retired observation.

Key: (session epoch, HPERecord ID, PC, load/store, width). Sixteen fully associative
history entries per session, FIFO/round-robin replacement; history capacity is
not the record capacity. Each key retains last virtual address and previous byte
delta modulo2^64. First two observations are warmup. Subsequent equal zero deltas
are scalar-repeat; equal nonzero signed deltas, magnitude<=4096 and divisible by
access width, are stream-fixed-stride. Otherwise output irregular/unrecognized;
this is NOT proof of statistical randomness. Every access gets one category.
Examples (W warmup, S scalar, T stream, I irregular):

| addresses | outputs |
| --- | --- |
| 0,0,0,0 | W,W,S,S |
| 0,8,16,24 | W,W,T,T |
| 32,24,16,8 | W,W,T,T |
| 0,32,8,80,0 | W,W,I,I,I |
| 0,0,0,8,16,24 | W,W,S,I,T,T |

Distinct PCs/op/width/parent-contexts have separate history; interleaved addresses
at the same key may become irregular. Repeated calls to the same context retain
history. On eviction the next observation warms up; publish eviction count and
history discontinuity. A mode switch is classified per access, not a dominant
label for the whole session.

Proposed bounded hardware: two session banks, matching the two trusted physical
Linux pools; each has16 histories, a256-depth record-ID stack mirror, and64
counter rows (RID1..63 usable). Five64-bit exclusive counters per row: input,
warmup,scalar,stream,irregular. RID overflow, stack spill/mismatch and counter
wrap are observable incomplete states, never silent attribution to the parent.
Root RID0 accesses are outside framed attribution and reported separately.
Parent inclusive counts can be derived by summing descendants; hardware records
are exclusive, unlike the existing inclusive cycle/time/instret/HPM intervals.

A trusted S-mode session selector restores history and record stack across
switches; disabled selection observes nothing. Successful exec/exit freezes and
exports before slot reset/reuse. Failed precommit ENOENT preserves history.
New image explicitly enables a fresh epoch. Classification is source-filtered;
it does not use the HPM pause-subtraction protocol. Existing ABI1/2 counters,
DTLB/Cache profiles and their sampling semantics remain unchanged.

Acceptance requires independent reference-vs-real-retired-trace comparison,
context/eviction/replay/fault boundaries and negative mutations, followed by
actual Rocket/Verilator Linux switching, exec, stop and complete export.
Until these pass D02 remains unaccepted. Resource size and exact CSR/export
layout will be fixed against the implementation and measured elaboration.

## CSR and transport layout (implementation)

S/M-mode only:0x5c1 is64-bit selected epoch (zero disables);0x5c3 is6-bit
query RID or reset-bank index. Write1 to0x5c2 resets bank0/1 selected by0x5c3,
binding the current nonzero physical SCBaseReg and epoch. Reset clears64 counter
rows in64cycles; poll0x5c2 bit1 until clear, then select RID0 for status. Reset is
trusted-only and may occur only after the previous bank's export/release.
0x5c4..0x5cb return eight64-bit fields. RID1..63: total,warmup,scalar,stream,
irregular,session-inputs,session-evictions,session-dropped. RID0: status,depth,
spill,unframed,currentRID,inputs,evictions,dropped. Status bits:0epoch present,
1reset busy,2context mirror mismatch,3history evicted,4counter overflow,5spill
currently active. Unframed application observations are reported separately from
unsupported framed observations (dropped). No observer input enters a bank when
selection is zero, epoch unknown or physical base mismatches.

The private ROM is unchanged. At its normal exit, shadow t3 supplies final depth;
shadow t5 supplies RID on successful push. A per-bank256×18-bit mirror restores
the previous RID on pop. Invalid transitions fail closed for classification.
This introduces no extra application/ROM instructions and retains old ABI1/2.

Linux START flags bit2 opts into classification (flags0..3 unchanged). The kernel
uses the already owned physical slot index and monotonically increasing session
as the only reset authority. Scheduler resume selects the saved epoch; switch
out/STOP clear epoch selection. Frozen exports retain bank ownership; short
IRQ-masked CSR reads copy one row before printing with IRQs enabled. Exec commit,
exit and explicit EXPORT append SSA_MBEGIN/MRECORD/MEND to the existing complete
v1 context stream; terminal per-session word checksum uses the existing FNV word
recurrence over id,total,warmup,scalar,stream,irregular. Missing/duplicate rows,
unknown rule/scope/width, incorrect sums, cross-session linkage and truncation
are rejected by classification_results.py. Core stream/record hashes remain
unchanged. Old v1 readers ignore the extension; classification-aware readers
must validate both. An open activation retains observed exclusive classification
counts and is marked by the existing frame/open metadata; it is not claimed to
have normally returned. Existing HPM closed-activation counts are not fabricated.

Logical state (not placed area): counter memory40960bits, mirror stack9216bits,
history6880bits, epoch/base/control/statistics870bits =57926bits, plus70 CSR bits.
Two associative16-way comparisons and asynchronous row reads are combinational;
reset takes64cycles outside monitored user execution. At most one retired scalar
access is observed each cycle. The64-row sidecar is an explicit capacity limit,
separate from262143 base context records; records beyond63 remain in the full
base export but classification marks dropped/unsupported coverage. History
eviction resets evidence, not accumulated counters. No counters are silently
merged into a different context to hide capacity exhaustion.
