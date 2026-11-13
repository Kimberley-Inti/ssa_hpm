# Controlled transparent launch (stage10)

This is a single-hart, single-thread, non-privilege-gaining ELF profile, not a
global process monitor. An ordinary target need not include SSA headers, link a
monitor library, issue START/STOP/EXPORT, or instrument functions. Its normal
JAL/JALR instructions drive the existing Rocket engine. Raw callee addresses
identify machine functions; symbolization requires the exact ELF and load map.
Tail calls, nonlocal unwinding, arbitrary language runtimes and signals that
rewrite control flow do not acquire universal stack semantics from this policy.

## Authority and selection

The trusted launcher forks an unmonitored child, sets no_new_privs (irreversible),
then uses prctl(0x535341,6,flags,role,test) while CAP_SYS_ADMIN is available.
It subsequently drops gid/uid to1000 and execs the selected ordinary executable.
Arming requires no descriptor, one thread and flags0..7, role0..2, test0..14.
Operation7 with zero arguments disarms only a future policy and also requires
CAP_SYS_ADMIN/no descriptor. An unprivileged process cannot arm/disarm another
process or provide a pool address, PID selector or arbitrary kernel pointer.
The old explicit START interface remains available for compatibility; this
policy is a trusted opt-in convenience, not exclusive global admission control.

Selection is attached to the current task and follows its successful exec chain.
Fork clears both descriptor and policy in the child. The child may run normally
unmonitored; a trusted launcher can arm an independent child before dropping
privileges. No inherited open frames or classifier epoch are copied. CLONE_THREAD
is rejected with EOPNOTSUPP for an armed or currently monitored task. Shared-mm
clone/vfork, multithread exec and namespace/capability variations are outside the
accepted fixture. The policy does not globally select children or unrelated tasks.

The ELF loader checks before flush_old_exec: no_new_privs, one thread, direct ELF
(recursion_depth1), no setuid/setgid mode bits and no euid/egid change. An
unsupported selected ELF is rejected with EPERM while the old image can still
return. Recursive script loading is rejected at the ELF check. File capabilities
cannot gain privilege under no_new_privs; distinct file-capability fixtures are
not claimed. Unselected programs follow normal Linux loader behavior.

## Successful and failed exec

1. At the existing successful exec_mmap commitment, freeze old selection and
   snapshots; emit closed records and explicit abandoned open frames; finish
   checksummed chunks and release ownership. An open activation adds no invented
   partial HPM count. Exclusive classifier observations already made remain
   available as partial data. This is unchanged stage5/7 behavior.
2. Load mappings/credentials/stack and prepare start_thread. At the final ELF
   readiness hook, before any new U instruction, allocate/reset a fresh owned
   pool, dictionary, stack, snapshots and classifier epoch using the saved flags.
3. Emit SSA_AUTO_RESULT with pid/image/session, enabled/error/reason and
   entry/app/interp addresses. Same PID does not imply the same session.
4. Enter the new image. On normal exit or signal termination, freeze/export once
   before release. SSA_AUTO_END records Linux exit code/signal and monitoring
   enable failure. Remaining open frames are abandoned, never normal returns.

ENOENT pathname lookup is the exercised failed-return path. It never reaches the
commit hook, so the old session, open frames, history and selection continue.
Precommit policy rejection also preserves the old descriptor. Postcommit fatal
loader failures cannot return to the old image; no claim of rollback is made.
They do not start a new session unless the final readiness hook is reached.

## Capacity and counters

Two physical36MiB pools and two classifier epoch banks remain kernel owned.
If both pools are busy, the new executable runs unmonitored (fail-open) and
SSA_AUTO_RESULT explicitly reports enabled0/error-16/reason=pool_exhausted.
A policy remains armed, but there is no mid-image retry; the next successful exec
may try again. It cannot steal a live/exporting pool. ENOMEM/ENODEV and other
start failures likewise report enable_failed. Console evidence is privileged;
this prototype provides no general guest disk service or unprivileged error ioctl.

Flags bit0 is the old no-rebase negative control, bit1 chooses ABI2, bit2 enables
rule1 classification. Production fixtures use bit0=0. Base cycle/instret/time are
64-bit, inclusive of children and interval-local kernel/ROM overhead. The fourth
ABI2 counter is40-bit modular DTLB accepted PTW requests or native Cache completed
TL A transactions, fixed jointly by the kernel/OpenSBI build profile. Automatic
policy does not reprogram the hart selector per task. Existing base/DTLB/Cache
builders and explicit interfaces remain compatible. The directed automatic image
uses Cache; the dynamic case uses ABI1, and the capacity case ABI1+classification.
Classification is exclusive, retired integer virtual-address rule1 with source
filtering;16 FIFO history entries and63 counter rows per epoch. Capacity beyond
RID63 leaves complete base records but explicitly increments dropped and marks
classification semantic coverage incomplete. Transport completeness is separate.

Scheduling retains the old S/R protocol: pause selection, preserve all open
frames/history; rebase HPM snapshots by modular R-S, select the owned epoch before
resume. Only S..R is subtracted. Own trap/monitor/resume work outside S..R remains
included. Shared Cache/TLB pollution can cause new events after resume, charged
to that resumed interval. Source-filtered classification needs no subtraction.
The launcher does not change these accounting rules.

## Static and dynamic boundaries

Static monitoring starts before its ELF entry. For PT_INTERP ELF, entry is the
interpreter entry while app is the main ELF entry and interp its load base.
The same session therefore includes dynamic loader, application and shared-library
calls. Startup continuation frames can remain open at exit and must be marked
abandoned; transport may be complete while activation completeness is false.
No claim of loader-free application counts or universal loader unwinding is made.
The fixture uses the unmodified standard musl1.2.5 loader built from its pinned
MIT source, an actual DT_NEEDED shared library and a normal PT_INTERP executable.
Its raw live function anchor plus the recorded interpreter base distinguish DSO
and loader records; general ASLR-aware symbol maps are future tooling work.

## Fixture and evidence boundary

launcher.c alone configures SSA policy. plain.c, capacity.c/.S and shared.c use
ordinary Linux syscalls and integer loads/stores. build-users.py records SHA256,
PT_INTERP/DT_NEEDED and disassembly/symbol rejection checks for the target ELFs.
The identical plain ELF is used selected and unselected, and its fork child stays
unselected. The setid copy retains identical bytes but has04755 inode mode.
The64-context capacity fixture exceeds both the old32-record export limit and
classification63-row capacity. Host checks must verify all base chunks and the
explicit one dropped observation, not treat transport success as full coverage.
The appended class-regress/classnext executables intentionally use the old
manual ABI and are not advertised as ordinary targets.
