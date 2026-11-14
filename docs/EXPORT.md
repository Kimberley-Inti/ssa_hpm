# Result export v1 (stage7–8)

This is a bounded kernel-to-host stream for the existing single-hart prototype,
not an upstream Linux syscall ABI, guest filesystem service or raw36MiB dump.
The semantic content is every allocated HPERecord, active counter definitions,
parent/callee identity and abandoned-frame identities. SCDict hash buckets and
unused record slots are implementation details and are not needed to rebuild a
tree. Physical slots and calling ABI are unchanged. See ACCEPTANCE.md for scope.

## Freeze, ownership and interfaces

START flags0/1 remain ABI1 three-counter normal/legacy;2/3 remain ABI2 four-counter
normal/legacy. In the default DTLB image record+40 is40-bit accepted PTW requests, selector4098. The
other three fields remain cycle,instret,time,64-bit. No new Rocket ROM, firmware,
selector or counting rule was introduced by stage7; stage8 selects an alternative
fixed native event as described below. The memory ABI and stream version are
separate version spaces: v1 can describe either ABI1 or ABI2.

prctl(0x535341,2,0,0,0) STOP still rejects open/spilled frames and freezes the
current task with no selection, returning its allocated count. New op5 EXPORT
accepts only zero arguments and the current STOPPED task. It returns0 after a
terminal stream, EBUSY while running, EALREADY after an earlier export, EINVAL
for absent descriptor/nonzero arguments, or EIO after a terminal mapping/buffer
failure. There is no PID, address, session selector or user output pointer.
A task cannot request another task's pool. Internal read_chunk additionally
checks current task/descriptor/session/busy/frozen state, record interval and
count<=16. Diagnostic test labels0..14 replace0..10; prior labels are unchanged.

STOP samples cutoff and clears SCBaseReg and ABI2 mode under a short IRQ mask.
At exec commitment or exit, an active descriptor is frozen the same way. The
hardware completes private ROM updates before the architectural kernel path;
no task can select this owned pool afterward. A STOPPED descriptor is not
resumed by scheduler hooks. Counter registers remain free-running and are not
reset by export. Records from completed activations remain immutable; no partial
counts are fabricated for unfinished ones. Pre-S/post-R costs remain charged as
before. Cutoff diagnostics reuse the STOP boundary instead of resampling at exit.

IRQs are restored before allocation/mapping or UART output. Each chunk maps and
copies at most16*128=2048 bytes, unmaps, emits bounded rows and calls cond_resched.
The temporary record buffer is2KiB; a fixed256-entry frame-ID snapshot belongs
to the descriptor. Runtime and output are linear in allocated records; no memory
buffer or mapping scales with total capacity. Existing8KiB record mapping is
retained only for the original small-record accounting proof.

The descriptor stays attached and its slot busy through the terminal stream.
Explicit EXPORT marks it exported once and retains its pool until exit/committed
exec; later release does not dump it again. Ordinary exit and committed exec
export first, then emit RELEASE and detach/free under a short IRQ mask. The new
image is unmonitored and may explicitly allocate a clean session. Pre-commit
ENOENT preserves the old live session. There is no asynchronous worker or remote
reader racing this current-task operation. A mapping/allocation failure emits a
terminal IO-incomplete result; release is permitted only after that explicit
terminal failure, not silently as a successful complete result. An interrupted
host capture lacking END is rejected and preserved as partial JSON.

## Framing and payload

Every line is tagged, session IDs bind all pieces, and each boot is one input
stream. Parallel task exports may interleave by session. Existing SSA_BEGIN is
the ownership/allocation marker, and SSA_RECORD/SSA_EVENT_RECORD payloads are
retained byte-for-byte in field meaning for the prior graders. New tags:

| Tag | Fields / checks |
| --- | --- |
| SSA_XBEGIN | version1,session,pid,image,abi,total,capacity262143,chunk16,counters,reason(stop/exit/exec),pool,next,depth,spill,errors,status,legacy,policy |
| SSA_XCOUNTER | session,index,name,width,selector; fixed indexes0cycle,1instret,2time,3 profile-specific dtlb_accepted_ptw_requests or dcache_a_transactions |
| SSA_XCHUNK | session,seq starting0,first starting1,count1..16 within total |
| SSA_RECORD | pid,id,callee hex,parent,cycle,instret,time,session,open; exactly count rows in ID order |
| SSA_EVENT_RECORD | ABI2 only, matching identity plus profile-specific dtlb/cache; exactly one after each scalar row |
| SSA_XCHUNK_END | session,seq,count,hash; detects missing/duplicate/truncated chunks |
| SSA_XFRAME | session,frame starting1,rid,status=abandoned; all retained open frames, capped at valid256-frame storage |
| SSA_XEND | session,chunks,emitted,total,hash,status,records_complete; final transport/integrity authority |
| SSA_XRELEASE | session,pid,pool,reason(exit/exec), only after END; needed before another START may reuse this slot |

The checksum is a64-bit **word checksum v1**, not cryptographic authentication.
Seed14695981039346656037; for each unsigned64-bit word,
`h=((h XOR word)*1099511628211) mod 2^64`. Per-record words, in order:
`id,parent,callee,cycle,instret,time,fourth-profile-event-or-zero,open`. Each chunk resets its seed;
the END hash runs over all emitted records without resetting at chunk boundaries.
Empty exports have no chunks and END hash equal to the seed. Counts are decimal,
callee/checksum hex. No dependence on host byte order or pointer serialization.

`total=next-1`, valid next1..262144; slot0 is reserved. Last valid ID262143.
Status bitmask:1open frames,2spill,4allocation errors/exhaustion,8monitor state
invalid,16metadata invalid,32IO/buffer/mapping failure. Header is the freeze-time
status; END may add32. `records_complete=1` means all allocated records were
transferred; semantic `complete` additionally requires status0. An open session
can therefore have complete transport and incomplete activations. Invalid next
is reported with status16 and no unbounded memory walk. Capacity exhaustion
exports all genuinely allocated records and marks allocation errors; it does
not pretend the lost context was a successful call. The preexisting SSA_EXPORT
complete field is an initial semantic check; new readers use END for IO results.

The parser enforces consecutive IDs and chunks, correct counts/checksums,
parent<id, unique(parent,callee), ABI-specific counter definitions/widths, open
frame multiplicities, lifecycle/session identities and pool reuse ordering.
It writes explicit errors/partial sessions and exits2 on malformed or truncated
input. Semantic incomplete sessions remain valid parsed results with
`complete=false`; silently missing data never becomes a valid complete result.

## Host entry and compatibility

```sh
python3 ssa/linux/export_results.py /path/to/rocket-linux-events.txt \
  --out /tmp/results.json --tree-limit 64
python3 ssa/linux/test_export_results.py --out /tmp/export-host-tests.json
```

The host JSON is the persistent offline file required by design p13–14, using
parent IDs and callee addresses rather than raw hash chains. The optional tree
summary is bounded; records are inclusive, so summing parents and children double
counts nested work. Function symbol names can be joined from the exact ELF; the
acceptance checker already matches those addresses to the fixture's ELF symbols.

Historical pre-v1 logs are still read by grade-process.py/grade-exec.py/
grade-events.py and the bare-metal analyze.py. The new parser rejects missing
versioned framing rather than inventing hashes for old captures. Existing ABI1
and ABI2 consumers retain their scalar/event rows, and their actual regressions
are rerun in stage7. Format v1 adds framing; it does not reinterpret historical
counter values or relabel DTLB accepted requests as unique misses.

## Coverage distinction

Stage7 actual Linux fixture:41 records under one parent, the first leaf called twice
with ID reuse; two-record explicit STOP/EXPORT; zero-record STOP/EXPORT; two-record
exit with one open parent; new and old exec sessions, DTLB/event preemption and
original process regressions. Current-source public Linux/OpenSBI build, reused
hash-verified stage6 model. Actual acceptance completed with native exit0 and all
checkers passing; see STAGE7.md. Stage8 rebuilt the model and separately accepted
the Cache fixture, as recorded in STAGE8.md.

Host-only checks: maximum262143-record chunk arithmetic and final bounds,
zero/1/2/15/16/17/32/33/41 records in ABI1/ABI2, invalid capacity, missing/duplicate
chunks, truncation, count/parent/session/width/hash damage, premature pool reuse,
missing event channel and explicit IO-abort framing. No claim of executing all
262143 records on Rocket or fault-injecting kernel memremap failure. Allocation
exhaustion behavior of the hardware remains covered by earlier RTL boundary
logs; parser/capacity framing coverage is separate.

The bounded target-memory claim applies to kernel chunk buffers/mappings. The
offline Python validator retains the input and reconstructed records in host RAM
(O(records)), including parent/key indexes. It is not a constant-memory host
streaming database. Target export does not depend on host-side heap capacity.

After the real41-record export has completed, replay the same captured data and
its deliberately damaged copies with:

```sh
python3 ssa/linux/test_export_results.py --native-log /path/to/rocket-linux-events.txt \
  --out /tmp/export-real-log-negatives.json
```

These are host mutations of actual native evidence, not extra hardware failures.
The original log is read only. Missing END during a live export remains pending,
while missing END in a finished capture is a genuine validation error.

## Accepted coverage

Actual single-hart Rocket/Linux exported41 records in3 chunks plus small/zero/open
sessions, then completed all affected event/exec/process suites. Across the single
boot24 sessions/87 records/25 chunks passed and all pools were released. Open
sessions4/5/13 are semantic-incomplete but transport-complete. See STAGE7.md and
evidence/stage7/summary.json for raw logs, checksums, counters and exact hashes.
The host's maximum-capacity plan and corrupt-stream tests are not native full-pool
or native I/O fault-injection coverage.

## Stage8 fixed Cache profile compatibility

A Cache image pairs kernel/firmware SSA_CACHE_PROFILE and keeps ABI2 layout/ROM.
Counter3 is `dcache_a_transactions`,40bit,selector514; event rows use`cache`.
XBEGIN explicitly says`profile=dcache_a_transactions`. Default DTLB uses its own
name/selector4098/`dtlb`; absent-profile historical ABI2 meansDTLB, ABI1 meansbase.
The reader rejects mismatched/unknown profiles, selectors, widths, duplicate event
channels and event data injected into scalar rows. It never silently labels a
Cache payload asDTLB. Checksums retain the same numeric fourth word.

The native event is completed D-cache outbound TL A transactions (cached and
uncached), occurrence intervals inclusive of children/kernel/private ROM, with
S..R exclusion for normal mode. Late increments belong to their sampling interval;
post-R resumed-task cache effects remain charged. See ABI.md and STAGE8.md for
exact source/limits. Actual Cache41 rows/3chunks plus small/empty/open andexec
passed in Linux; full source logs/results are in evidence/stage8/.
