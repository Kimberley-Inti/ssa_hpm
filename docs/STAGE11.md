# Stage11 final candidate review

Status: validation in progress; not yet approved for integration or release.

Baseline is stage10 `6ef19d6e85dfe55983794342620a026005a67d20`.
The scope remains the explicitly supported single-hart research prototype in
ACCEPTANCE.md. Multi-thread/shared-mm/vfork, arbitrary non-LIFO runtimes, task
migration and automatic DTLB combinations are not newly accepted here.

The independent workspace fetched the pinned public Chipyard and Rocket bases,
applied all patches, checked the exact source manifest and ROM, and actually
compiled Scala, generated RTL and built Verilator. Source/dependency caches were
reused; the final model was newly built. A Linux source checkout separately
fetched the pinned public baseline and applied the lifecycle and optional cost
probe patches. Its tree matches the development source tree.

Review finding R01: deleting a whole classification sidecar leaves a valid base
transport, but the auto-launch semantic checker previously raised KeyError.
The checker now validates its expected profile-sidecar set and row coverage
before dereferencing it, reporting a semantic rejection. A normalized capture
reproduction and the newly added whole-block negative demonstrate the fix. R02 additionally
adds an explicit XBEGIN classification/rule/rows contract; the combined parser
now rejects a wholly missing declared sidecar. New host sidecar checks total27,
including zero-row and wrong-declaration cases.
The good historical capture passes 51 checks; this is a host recheck, not a new
Linux simulation. Existing stage10 acceptance counts remain historical facts.

Fresh low-level checks on the new model passed base/trap/process, DTLB and Cache
(including expected-failure negative controls), CSR/physical-pool permissions,
four classification fixtures and the independent pre-clock WB oracle. The WB
oracle observed 82 candidates, 72 accepted accesses, seven replay candidates and
one exception, with no duplicate retirement accounting.

A fresh unified Linux run uses the newly built model and a newly built
public-source transparent/static/dynamic/manual-classification image. A separate
public-source Linux performance image enables optional `SSA_COST_PROFILE` probes;
default builds compile them out and keep the ABI. Both source trees match the
development candidate. The pinned musl source/binary cache and host tools were
reused, but target fixtures, kernel and firmware were rebuilt. Earlier startup
trials were superseded for the sidecar-declaration repair and are not acceptance.
Neither a partial UART log nor native exit0 alone is acceptance.

The performance protocol is saved before measurement. Independent target
cycle/instret/time boundaries surround the same workloads, with setup and
console output outside the application interval. Six bare modes and five Linux
modes are tested separately; DTLB Linux auto-launch remains untested. Source and
firmware hashes, repeated raw samples and variation are retained. The extended
model's enabled/disabled cost is not an unextended-hardware or area comparison.

Final status, run receipts, measured costs and integration result will be added
only after completed runs have passed their checkers. See INTEGRATION.md for the
authorized dependency-preserving merge procedure.
