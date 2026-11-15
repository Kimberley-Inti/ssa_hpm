# Cache event attribution

The Cache ABI2 profile counts completed outbound D-cache TileLink-A request
messages: `DCache.io.cpu.perf.acquire := edge.done(tl_out_a)` asserts on the final
accepted A beat of a request message. Rocket's existing EventSet path programs
selector0x202 and mhpmcounter3. The register and subtraction width are 40 bits.
This is request-message traffic, including qualifying PTW/uncached traffic
through this port; D-channel refill completion is a different event.

Attribution uses event increments inside the sampling interval. A delayed message
can cross a call/return boundary. Parents include descendants; source events
remain live in kernel/private code, and software removes actual S..R pause deltas.
After resume, misses caused by shared-cache pollution belong to the resumed task's
active interval. Firmware fixes one event profile for a Linux image.

[Five final RTL cases](../evidence/final-validation/regression-cache/summary.json) check
source/global/context relationships, wrong selector/context negative controls,
wrap and register transparency. The production and full-performance Linux images
export Cache metadata and real records; the direct
[two-task companion](../evidence/final-validation/linux-switch-proof/summary.json) verifies
nonzero Cache pause subtraction for both tasks. The dedicated controlled-workset
[Linux capture bundle](../evidence/cache-attribution/summary.json) is preserved separately.
Use [the protocol](EXPORT.md) to distinguish Cache and DTLB records.
