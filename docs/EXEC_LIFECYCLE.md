# Exec lifecycle

A successful image replacement retires the old monitoring session at its commit
boundary. Closed records are exported; open activations are marked abandoned
rather than treated as completed returns. Selection is cleared, export retains
pool ownership through its terminal record, and release precedes reuse. Session
ID and image generation distinguish two results under the same PID.

The manual policy lets the new image explicitly start a clean session. A trusted
automatic-exec policy starts the new session when the ELF image is ready. A
repeatable pre-commit ENOENT failure returns to the old image and preserves its
pool, open frames and classification history. Normal exit and default signal
termination freeze/export the current session and release its resources.

The production Linux capture checks successful/failed exec, new-image exit,
open-frame markers, one-time export, policy inheritance and pool reuse. See
[automatic launch](AUTOMATIC_LAUNCH.md), [format](EXPORT.md),
[production summary](../evidence/final-validation/linux-unified-final/summary.json), and
[manual lifecycle summary](../evidence/final-validation/linux-unified-final/manual-summary.json).
The original dedicated lifecycle evidence remains in
[its immutable capture bundle](../evidence/exec-lifecycle/summary.json).
