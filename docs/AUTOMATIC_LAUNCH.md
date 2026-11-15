# Controlled automatic launch

A trusted launcher arms an exec policy with CAP_SYS_ADMIN and no_new_privs,
selecting an audited single-thread non-privileged ELF before dropping uid/gid.
The kernel establishes a clean session at successful ELF readiness. The target
source and binary use ordinary calls and syscalls without SSA start/stop/export.
Fork clears the policy/descriptor; successful exec follows the armed replacement
policy, and pre-commit failed exec keeps the existing image/session.

Scheduler hooks pause/rebase open frames. Exit or default signal termination
exports/releases automatically. Explicit setid/thread rejection and visible
pool_exhausted status define the selected-resource boundary; unselected programs
remain unmonitored. Two busy physical pools can cause a third selected program
to continue with a reported monitoring-enable failure.

The static and musl PT_INTERP/DSO fixtures are real Rocket/Verilator Linux runs.
Dynamic loader and application calls enter the same session; an audited musl
continuation leaves one loader activation explicitly abandoned. The final
production suite passes51automatic checks plus26manual compatibility checks,
with independent10ELF-capacity checks,5automatic semantic negatives and 3manual
classification negatives. It records17sessions/215records, native0/powerdown.

[Policy contract](../integration/ssa/linux/transparent/POLICY.md),
[ordinary ELF identities](../evidence/stage11/linux-users.json),
[production results](../evidence/stage11/linux-unified-final/summary.json) and
[validation](VALIDATION.md) cover the actual supported combinations. Automatic
DTLB and arbitrary language runtimes are future combinations.
