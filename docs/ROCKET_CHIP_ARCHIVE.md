# Rocket Chip development archive

The primary project entry is [SSA-HPM](https://github.com/Kimberley-Inti/ssa_hpm).
[Kimberley-Inti/rocket-chip](https://github.com/Kimberley-Inti/rocket-chip) is its original development fork of chipsalliance/rocket-chip. Retaining it preserves original commit identities, a draft code-review thread, and historical research links.

## Verified inventory and recommendation

The audit compared all seven fork branches with 402 fetched upstream branches and tags. The fork has no tags. Ten commits are absent from every fetched upstream reference. All ten exist in the local development repository and have matching format-patches here; stable patch IDs were checked. This establishes recoverability without treating the fork as redundant.

| Original commit | Work | Preserved patch |
| --- | --- | --- |
| `9c6d44169365b1423f5aa8282def76b20e6c04fb` | Update HPM logic in RocketCore | [0001-9c6d44169.patch](../patches/rocket-chip/0001-9c6d44169.patch) |
| `1543ea5445423aefae78c52b37c2521abea42fdc` | ssa_trap_mode connection logic | [0002-1543ea544.patch](../patches/rocket-chip/0002-1543ea544.patch) |
| `1f200edb0eb0832a72d04d8d4f36b912e0e447dd` | modified code sequence | [0003-1f200edb0.patch](../patches/rocket-chip/0003-1f200edb0.patch) |
| `d047a854895f008c586487e017f5346c4427c1af` | forced exit | [0004-d047a8548.patch](../patches/rocket-chip/0004-d047a8548.patch) |
| `07a9c3fa809332daa19f8ca99e2573cd0ecaced1` | normal exit | [0005-07a9c3fa8.patch](../patches/rocket-chip/0005-07a9c3fa8.patch) |
| `23f5a64f6144cd3ffc7b25d490b48f5d019ee718` | normal exit | [0006-23f5a64f6.patch](../patches/rocket-chip/0006-23f5a64f6.patch) |
| `539c3b10fee35fe0a2890083dd17c06688a704f8` | Preserve inherited uncommitted SSA-HPM implementation | [0007-539c3b10f.patch](../patches/rocket-chip/0007-539c3b10f.patch) |
| `986407bc6df8d2a67572250f1df9eb2c0edeacf9` | Fix SSA-HPM microcode retirement, context dictionary and counter attribution | [0008-986407bc6.patch](../patches/rocket-chip/0008-986407bc6.patch) |
| `3f4ab938660454b101c67f6929bfebae5be1a138` | Suspend SSA application contexts across nested architectural traps | [0009-trap-context-isolation.patch](../patches/rocket-chip/0009-trap-context-isolation.patch) |
| `41d297689890296699d4a45699bf7e5791d33b96` | Preserve compressed virtual PC width across SSA ROM muxes for Sv39 | [0010-sv39-pc-width.patch](../patches/rocket-chip/0010-sv39-pc-width.patch) |

The open [Draft PR #1](https://github.com/Kimberley-Inti/rocket-chip/pull/1) depends on `ssa-hpm-completion-20261108` and `SSA-HPM`. These archival branches keep their original names. Local feature-branch aliases were renamed; the exact mapping is in [HISTORY_MAP.json](HISTORY_MAP.json). Public reproduction fetches the official Rocket baseline and applies the delivered patches, so it does not require the fork. Historical PRs and original development references do require it.

**Recommendation: retain the fork as a development archive.** SSA-HPM is the principal research repository.
