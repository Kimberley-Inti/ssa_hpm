# DTLB event attribution

The DTLB ABI2 profile uses Rocket's `io.dmem.perf.tlbMiss` EventSet input,
connected by DCache to `io.ptw.req.fire()`. It counts accepted PTW requests at the
DTLB interface. Selector0x1002 programs the existing mhpmevent3 path; the hardware
counter and snapshot arithmetic are 40-bit modular values. Basic counters remain 64-bit.

An increment belongs to the context sampling interval in which it is observed.
The source is not filtered by application privilege; paused intervals are
subtracted by the same per-frame S/R protocol. PTW/handler activity near sampling
boundaries follows that declared interval rule. Parent records remain inclusive.
The Linux DTLB image fixes the selector in firmware and exports the counter's
name, width and profile identity.

The final new RTL matrix checks real event production/global increments/context
association, selector and context negative controls, wrap and register transparency.
[DTLB results](../evidence/final-validation/regression-events/summary.json) identify actual
executions. [Dedicated Linux evidence](../evidence/dtlb-attribution/summary.json) retains
its accepted source/image/capture provenance; it is historical evidence, not a
new automatic-DTLB run. [Validation](VALIDATION.md) states that combination boundary.
