# Calling contexts

Rocket recognizes supported calls and returns from architectural `JAL`/`JALR`
behavior. A private integer-register bank and serialized microcode update three
structures: SCStack stores open record IDs and counter snapshots; SCDict resolves
`(parent record ID, callee address)` with collision chains; HPERecords store the
parent/callee relation and accumulated intervals. Callee identity uses the full
virtual target address within a session. The SCCodeTable helper-code proposal
is realized as generated private ROMs rather than writable SRAM.

Each physical pool reserves36 MiB, including a1 MiB dictionary,25664-byte frames
and 128-byte record slots. ID0 is reserved; usable allocated IDs are 1..262143.
Repeated calls on an existing path reuse its record. Different parents produce
different records for the same callee. Returns restore the parent context.
Basic ABI1 uses64-bit cycle/instret/time; ABI2 adds a40-bit event at record+40.
Counter intervals include child calls and monitoring work between samples.

The canonical fixture produces6 records: parent_a/common and parent_b/common are
separate paths, and two deliberately colliding functions remain distinct.
common.instret is 14452 under parent_a and 7226 under parent_b. The same fixture
was rerun in the final RTL matrix. Boundary tests exercise258calls with 256saved
frames and bounded record exhaustion; full-tree support is declared within 256frames.

Source: `patches/rocket-chip/`, `integration/ssa/test.c`, the canonical ROM installed
by `scripts/apply.py`, and [the memory/interface contract](../integration/ssa/linux/ABI.md).
[Final context capture](../evidence/stage11/regression-base/rtl-context.txt)
and [low-level results](../evidence/stage11/lowlevel-summary.json) retain actual outputs.
