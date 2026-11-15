# Documentation

| Topic | Entry |
|---|---|
| Architecture and implementation | [Calling contexts](CALLING_CONTEXTS.md) |
| Privilege and interrupt behavior | [Trap isolation](TRAP_ISOLATION.md) |
| Pool/snapshot switching protocol | [Process accounting](PROCESS_ACCOUNTING.md) |
| Real Linux scheduling | [Linux process accounting](LINUX_PROCESS_ACCOUNTING.md) |
| Image replacement and failure | [Exec lifecycle](EXEC_LIFECYCLE.md) |
| Native PTW events | [DTLB event attribution](DTLB_EVENT_ATTRIBUTION.md) |
| Native Cache traffic | [Cache event attribution](CACHE_EVENT_ATTRIBUTION.md) |
| Address rules and implementation | [Classification specification](CLASSIFICATION.md), [validation](MEMORY_CLASSIFICATION_VALIDATION.md) |
| Kernel-to-host format | [Export specification](EXPORT.md), [validation](RESULT_EXPORT_VALIDATION.md) |
| Ordinary ELF launch policy | [Automatic launch](AUTOMATIC_LAUNCH.md) |
| Unified evidence and source versions | [Validation](VALIDATION.md) |
| Target-side measurements | [Performance](PERFORMANCE.md) |
| Requirements and completion domain | [Acceptance](ACCEPTANCE.md), [checklist](FINAL_CHECKLIST.md) |
| Review findings | [Final review](FINAL_REVIEW.md) |
| Rebuild and evidence replay | [Reproduction](../REPRODUCE.md) |
| Full English project report | [PDF](../report/SSA-HPM-report.pdf), [editable source](../report/README.md) |
| Development provenance | [History](../HISTORY.md), [reference map](HISTORY_MAP.json) |
| Original development archives | [Development archive index](DEVELOPMENT_ARCHIVES.md) |

Evidence directories use functional names. Original raw log bytes and hashes
remain unchanged; the path map preserves their historical locations.

[Evidence organization and verification](EVIDENCE.md).

[Core implementation browser](../src/README.md) · [Historical evidence path map](EVIDENCE_PATHS.json).

[Patch application order and filename map](PATCH_ORDER.md).
