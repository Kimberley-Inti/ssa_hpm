# Stage 2: trap-aware application context isolation

Status: development and independent public-baseline reconstruction both passed all 16 tests on `stage2-trap-isolation`.
Baseline: v0.1.0 (`0421e67203e0cfb63d96699f061ffa7d8d00fddf`).

## Design review

Local sources: the Software Semantic Aware Hardware Performance Monitoring PDF
and the RISC-V HPM PDF supplied by the maintainer. Key design pages 8–13 and HPM
counter/privilege pages were inspected as rendered images because text extraction
loses Chinese. The PDFs are not distributed.

| Area | Existing but unverified / incomplete | Missing implementation | Undefined boundary / dependency |
| --- | --- | --- | --- |
| Exceptions / IRQ | Architectural CSR trap/return machinery; IRQ masking during private microcode | No application/handler context boundary in v0.1.0 | Whether handlers belong to the application tree; nonlocal unwind ABI |
| Linux lifecycle | SCBaseReg exists; pool/loader contract documented | loader allocation, per-task save/restore, exit dump and fault integration | Process/thread ownership, dynamic linker, unmapped pool recovery |
| Multicore | CSR and monitor registers instantiate per hart | System-level pool ownership/isolation tests and synchronization | Shared vs per-thread/per-hart records; migration |
| Data classification | Scalar Rocket loads/stores and HPM events exist | No SSA classification or per-context data-event recording | Definition of scalar/stream/random, stride/window and classification policy |
| Cache/TLB | Native Rocket event sources and selectors exist | No verified association with software records, replay/in-flight ownership | Source instruction vs completion attribution; filtering handlers/private code |

The PDF scopes its first phase to cycle/time/instret. Additional data events lack
an executable classification policy. Handler calls already contaminate the
application dictionary before such events are added, making trap boundaries the
most immediate independently verifiable prerequisite.

## Chosen minimal semantics

On every architecturally taken trap, including ECALL/EBREAK and asynchronous IRQ,
pause application call/return updates. Nested traps increase a per-hart depth;
only an actual xRET decreases it. CSRFile `io.eret` is **not** a return-only
signal: it also redirects ECALL/EBREAK. Use its internal actual exception/return
decodes instead. Resume after the outermost matching return. Ignore a return at
zero depth (e.g. bootstrap privilege transition); never underflow.

Custom user read-only CSR `0xcc0`: bits 7:0 are the saturating depth, bit 8 is
sticky overflow. Other bits are zero. Depth capacity is 255. A further entry
sets overflow and permanently inhibits application notifications until reset;
this protects against silently resuming with a lost nesting level. An open
profile after overflow is incomplete and must be discarded, not presented as a
completed zero-cost measurement. This is not an OS recovery mechanism.

SCBaseReg, pool ABI, hash, frame/record sizes and ROM remain unchanged. Counter
semantics remain interval-inclusive: child calls, monitor overhead and time /
retired instructions in intervening handlers are included. Only handler-induced
context transitions are suppressed. Application-only counter filtering is not
claimed; a future event implementation must explicitly use the active-context
signal and choose its filtering policy.

## Concrete checks

- v0.1.0 baseline: original 3 Spike + 5 RTL regressions run again from copied,
  immutable binaries; all pass and preserve 6 records, common instret 14452/7226.
- Pre-fix synchronous ECALL test on the saved old simulator fails with code 31:
  first handler sees application depth=3, next_id=4 instead of depth=2, next_id=3.
- Required normal tests: synchronous trap, nested traps, real CLINT timer IRQ,
  unchanged parent/child ids on a second call after return.
- Required boundary tests: observable CSR depth; illegal write to read-only CSR;
  256 nested traps latch overflow and fail closed without fabricated counters.
- Spike has no SSA extension. Separate tests cover only nested ECALL/MRET,
  timer delivery and assembly register/EPC restoration; hardware context/status
  checks execute only on Rocket RTL.

Later work: Linux/process lifecycle, real multicore configurations, debug/NMI and
S/VS delegation evidence, nonlocal exception unwinds/longjmp, transparent recovery
from private-microcode memory faults, data classification and Cache/TLB events.


## Source commits and development evidence

- Rocket baseline `986407bc6df8d2a67572250f1df9eb2c0edeacf9` →
  `3f4ab938660454b101c67f6929bfebae5be1a138`.
- Chipyard accepted `375068b6180fa968f86f07fc4b2e1ec104f632ee` → environment
  checkpoint `339d349d35e308f2912c5db55c42c6e4adcb18ba` →
  `fa0ccc7be59a624acc1dcd80af211919be17cd56`.
- The environment checkpoint has the identical tree as publication follow-up
  `58a7acde9598b4e08d11e5b5f3da0e146e138078`; original refs are unchanged.
- `evidence/stage2/baseline/`: v0.1.0's actual 8-test rerun with the saved simulator.
- `evidence/stage2/development/`: actual regenerated RocketConfig RTL and all
  16 tests (5 Spike reference/instruction tests, 11 RTL tests), all exit 0.
- `trap-before-same-elf.txt` / `trap-after.txt`: the same trap ELF fails on the
  old saved simulator with depth=3/next=4 and succeeds on the rebuilt simulator
  with depth=2/next=3. No new status CSR is read by this distinguishing test.

The six new RTL cases observe `(depth,next_id)=(2,3)` in handlers. Nested tests
see 6 entries with maximum nesting 3. Timer IRQ sees one entry and returns out
of private ROM. Overflow sees 256 entries, maximum software nesting 256 and
final status `0x100`; open records remain uncompleted and must be discarded.
Illegal status writes take an actual illegal-instruction trap and resume.


## Independent reconstruction

`evidence/stage2/independent/` records a fresh network fetch of the two public
upstream bases, clean application of all 9 Rocket patches, and exact final tree
`535c551af33cce20384ca2f8c3560ac5e70cdca4`. The tests were built in that checkout;
339 Rocket Scala sources were compiled, fresh RTL generated and a new Verilator
executable linked there. It was not copied from development. Matching external
modules and toolchain/cache data were reused and individually checked; this is
not a completely cold online dependency installation. All 5 Spike and 11 RTL
checks passed. The first-stage 6-record result and 14452/7226 instret are unchanged.

The independent observations are in `trap-observations.json`: normal cases end
with status 0; the 256-entry case ends with status 256 (`0x100`) and uncompleted
application frames, explicitly invalidating that profile. The baseline, negative
same-ELF reproduction, development and independent evidence are stored separately.

Tool versions for this round are in `evidence/stage2/versions.txt`; Java is now
17.0.20.1 while the archived v0.1.0 report recorded an earlier Java 17 patch level.
GCC remains 15.1.0, Verilator 4.226 and Spike 1.1.1-dev with the same binary hash.
The rerun baseline and new regressions demonstrate unchanged instruction results.
