# Result export validation

A frozen session exports every allocated HPERecord using16-record chunks and a
2 KiB copy buffer. The pool remains owned through terminal output and release.
Session/image/PID, parent/callee identities, counters and widths, sequence numbers,
record totals, checksums, abandoned frames and classifier coverage travel with
the result. The [wire specification](EXPORT.md) and Python parsers define the format.

Actual Rocket/Linux acceptance includes 41 records in3chunks, two-record and zero-record
sessions, explicit stop, open-frame export, exec separation and release ordering.
The production capture additionally exports64 records in4chunks and a dynamic
105-record session in7chunks. Its64-record fixture has 63classifier rows and an
observable dropped access; base transport completion and classification coverage
are separate states.

[Production results](../evidence/stage11/linux-unified-final/summary.json),
[ELF-linked capacity checks](../evidence/stage11/linux-unified-final/postcheck/capacity.json)
and [export protocol checks](../evidence/stage11/host-export-final.json) retain
original observations and host-only malformed-stream tests. Those tests reject
missing/duplicate chunks, truncation, invalid ranges/checksums and missing declared
classification sidecars. Full262143-record UART stress remains an optional long run;
capacity arithmetic and bounded-copy behavior have targeted host checks.
