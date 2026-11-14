# Final candidate review

Scope: one hart, trusted kernel/firmware, audited single-thread non-privileged
LIFO programs and the explicitly described musl loader continuation adaptation.
The original PDFs remain local. Requirements and physical page references are
in ACCEPTANCE.md; rule1 classification and physical pools are project choices,
not definitions claimed to have appeared in the original design.

| Review area | Source and checks | Finding / disposition |
|---|---|---|
| Context hierarchy and ROM | RocketCore, canonical microcode; exact ROM generation, nested/context/reuse/collision/capacity/register tests | Existing implementation retained; fresh RTL regression passed |
| Counter ABI and profiles | CSR.scala, events.c, ABI.md, kernel samples; ABI1/2, selector negatives, 40-bit event wrap and register transparency | 64-bit cycle/instret/time; 40-bit ABI2 event. Cache completed D-cache A transactions and DTLB accepted PTW requests remain distinct. No request-owner precision claim |
| Privilege and retirement | user CSR read/write/pool probes, supervisor policy; independent pre-clock WB/replay/exception oracle | All seven permission probes and WB oracle passed on the newly built model; kernel/ROM accesses excluded from user classifier |
| Ownership/lifecycle | kernel/ssa_hpm.c, fork/ELF hooks; frozen export owns descriptor and pool through terminal/release | Single-hart IRQ exclusion protects selector and pool allocation. Export can reschedule with STOPPED descriptor. exec commits retire the old pool before new setup; failed precommit exec retains it |
| Launch policy | privileged ARM_EXEC, no_new_privs, ordinary ELF fixture | Explicitly selected audited paths; fork clears policy; threads/setid rejected; full pools fail open with status. Arbitrary ELF non-LIFO behavior is not automatically detected |
| Export integrity | XBEGIN..XEND + MBEGIN..MEND, combined parser | R01: whole missing sidecar caused semantic-checker KeyError. R02: producer did not declare optional sidecar presence. Fixed by explicit declaration and early semantic validation; legacy captures remain labeled undeclared |
| Partial semantics | open frame IDs, XS_OPEN, sidecar depth/status/dropped/evictions, dynamic loader continuation | Transport completion, unfinished calls and classification coverage are separate. Open HPM activations are abandoned, not fabricated normal returns; 63-row overflow is observable |
| Diagnostic bound | MAX_EVENTS=12 in current kernel | R03: previously underdocumented. A session supports at most12 retained pause-event diagnostics; a further pause stops monitoring with bad-state/partial export. This is not an unbounded production scheduler. Boundary enforcement is source-reviewed, not newly hardware stress-tested |
| Reproduction and rights | public baselines, ordered patches, expected file hashes, license notices and independent history audit | Separate patches and project-only fixtures; no full upstream trees, images, backups, design PDFs or credentials published |
| Performance and hardware cost | independent target samples and optional kernel probes; declaration counts | Enabled/disabled execution on the same extended model. No matched unextended model, synthesis area, energy or silicon timing claim |

No expansion to multi-hart, shared-mm/vfork, arbitrary signal handlers/non-local
unwind, vector/FP/AMO classification or automatic DTLB is accepted. The classifier
is bounded to two banks, 63 context rows, 16 FIFO histories per bank and256 shadow
frames. Eviction restarts warmup; irregular means no recognized supported pattern.

Review findings do not themselves certify the remaining Linux/performance runs.
Their final receipts and gate status are recorded in STAGE11 and the final
validation summary only after actual completion.

R04: host progress lines can interrupt a target performance row. A synthetic
middle-of-hex-field reproduction failed before normalization and passes after
using the same progress/CSR-line removal as the existing Linux export parser.
This repairs host acquisition interpretation; it does not change target code.
The final performance oracle also rejects missing/duplicate samples, checksum
mismatch, missing calibration/setup and absent terminal markers.

The depth256 boundary deliberately folds deeper calls into the deepest retained
context, as the existing258-call RTL test demonstrates. After full unwind there
is no sticky count of folded activations. Export completeness is about all
allocated records, not proof that an arbitrary input respected the supported
call-depth domain. Full-tree claims require audited inputs within256frames;
no generic unbounded call-tree coverage is inferred from a complete transport.
