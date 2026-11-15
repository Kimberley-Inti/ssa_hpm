# Trap isolation

Application calls and privileged trap handlers have different context roles.
Hardware trap-depth/overflow state suppresses application-call notifications
inside handlers and restores them at architectural returns. Private ROM execution
finishes coherently with interrupt handling. The Linux policy selects user-mode
calling-context notifications, while global counters continue advancing.

This separates context-tree construction from counter filtering: kernel/trap work
inside an active sampling interval can contribute to inclusive HPM deltas.
Scheduling removes only the sampled pause interval. Private CSR and physical-pool
access probes verify that ordinary user code cannot select arbitrary monitoring
memory. Counter-enable CSRs govern read permission rather than event generation.

The final matrix executes trap, nested-handler, IRQ, read-only/status, overflow
and register-transparency cases, plus seven privilege/translation probes.
[Low-level results](../evidence/stage11/lowlevel-summary.json) and
[trap captures](../evidence/stage11/regression-base/summary.json) give commands,
actual exit statuses and expected failures. These cases test architectural trap
return; software non-local unwinding is a separate extension.
