# Development history and source provenance

SSA-HPM is a standalone patch-and-validation repository. Original commits remain reachable in their development archives; their identities, authors and dates are recorded below. Imported commits do not inherit upstream Git ancestry. Original format-patch headers remain unchanged.

## Original development and imported commits

| Repository | Original commit | Author | Author date | Original subject | Imported commit |
|---|---|---|---|---|---|
| chipyard | `c9f704c0364ba5cafb83c4ec01478b90a40d5b1a` | Kimberley-Inti | 2026-03-04T22:27:08+08:00 | Initial commit | `b4be26b28b237996713b47f75cb9619cdc242d3b` |
| chipyard | `90bfa6c768b8fd1258d38cdffcfde862dfcc669d` | Kimberley-Inti | 2026-03-04T22:59:12+08:00 | Update .gitignore and remove untracked build artifacts | Metadata-only source record |
| rocket-chip | `9c6d44169365b1423f5aa8282def76b20e6c04fb` | Kimberley-Inti | 2026-03-05T22:41:45+08:00 | Update HPM logic in RocketCore | `e47da1fbea907868f45c3eeb56d8a5f7e1a41262` |
| chipyard | `6723407ba5ffb05d01757ef1c5d24a20218caffa` | Kimberley-Inti | 2026-03-05T22:42:48+08:00 | Track modified rocket-chip for SSA-HPM | Metadata-only source record |
| chipyard | `4c2e2c7b2aaab4388b9f91f64b22e751ddf283f1` | Kimberley-Inti | 2026-03-06T23:35:12+08:00 | Relink rocket-chip submodule to my personal fork | Metadata-only source record |
| chipyard | `710f951e2a3ec3ec1c050889c9ccf35e0e0ede1e` | Kimberley-Inti | 2026-03-22T21:26:42+08:00 | ssa_trap_mode connection logic | `826f5082206beef41b461c847ca4b0ca46bc60c3` |
| rocket-chip | `1543ea5445423aefae78c52b37c2521abea42fdc` | Kimberley-Inti | 2026-03-22T21:26:42+08:00 | ssa_trap_mode connection logic | `22ac074de75b476f2fcd44d01fa38039afe9e40a` |
| chipyard | `01b1aa69bce35971c9912e5706860d848adc6900` | Kimberley-Inti | 2026-03-28T08:01:21+08:00 | modified code sequence | `1f19a00316cebd0e9bd4b5ed784dbf0f6e44eeff` |
| rocket-chip | `1f200edb0eb0832a72d04d8d4f36b912e0e447dd` | Kimberley-Inti | 2026-03-28T08:01:21+08:00 | modified code sequence | `ec73be3357edd13ef4653ec62a1e3074159defa0` |
| rocket-chip | `d047a854895f008c586487e017f5346c4427c1af` | Kimberley-Inti | 2026-04-01T15:35:41+08:00 | forced exit | `5a37854211a9f1043de1eed9397e145a20ca8caf` |
| chipyard | `f98d756927cf59cfee20b1183f9247cab7e181b9` | Kimberley-Inti | 2026-04-01T15:35:42+08:00 | forced exit | Metadata-only source record |
| chipyard | `2cd92122a0fff0c4036d34e77e36470c22311f53` | Kimberley-Inti | 2026-04-12T08:02:41+08:00 | normal exit | Metadata-only source record |
| rocket-chip | `07a9c3fa809332daa19f8ca99e2573cd0ecaced1` | Kimberley-Inti | 2026-04-12T08:02:41+08:00 | normal exit | `48e9965c45221ff5a427e1e4bc53c2cc86e97ee5` |
| rocket-chip | `23f5a64f6144cd3ffc7b25d490b48f5d019ee718` | Kimberley-Inti | 2026-04-12T14:46:46+08:00 | normal exit | `1d5ae817964d3b13f1098431d0c4f71209ef59cb` |
| chipyard | `c2391670d8e1cc62369cfc3e96b58a9a8cc94dda` | Kimberley-Inti | 2026-04-12T14:46:47+08:00 | normal exit | `1d14fa7c7ff95029ee009465f95f30a35646e5a4` |
| rocket-chip | `539c3b10fee35fe0a2890083dd17c06688a704f8` | Kimberley-Inti | 2026-11-08T23:03:16+08:00 | Preserve inherited uncommitted SSA-HPM implementation | `d8390b3affa5c04d7b4e7b305b88a9f8900bba5a` |
| rocket-chip | `986407bc6df8d2a67572250f1df9eb2c0edeacf9` | Kimberley-Inti | 2026-11-09T06:18:46+08:00 | Fix SSA-HPM microcode retirement, context dictionary and counter attribution | `bc2b064fd2be342d51774e4c83c895457cf197b6` |
| chipyard | `375068b6180fa968f86f07fc4b2e1ec104f632ee` | Kimberley-Inti | 2026-11-09T06:19:08+08:00 | Add reproducible SSA-HPM Spike and Rocket RTL validation | `429b78c19191d4973042ac554ae3c71383ad5ff5` |

The machine-readable source records, original branch names and artifact mappings are in [provenance.json](provenance.json). [HISTORY_MAP.json](docs/HISTORY_MAP.json) maps historical branch/document names to functional names without changing original commit identities.

[Complete original source relationships](docs/SOURCE_HISTORY.json) retain the original technical tables, including intermediate source baselines and delivery mappings.

## Implementation patch identities

| Patch | Original commit | Original author | Original author date |
|---|---|---|---|
| [integration/ssa/linux/opensbi-rocket-platform.patch](integration/ssa/linux/opensbi-rocket-platform.patch) | `b778927a507e4ebcc43a8ecb8d495562ef48efb3` | Kimberley-Inti <KimIntizar@hotmail.com> | Mon, 9 Nov 2026 15:26:12 +0800 |
| [integration/ssa/linux/stack-pointer-declaration.patch](integration/ssa/linux/stack-pointer-declaration.patch) | `3b79ddfa2fb70707ace85385d6722925fffc8eea` | Kimberley-Inti <KimIntizar@hotmail.com> | Mon, 9 Nov 2026 14:56:49 +0800 |
| [integration/ssa/linux/linux-task-pools.patch](integration/ssa/linux/linux-task-pools.patch) | `0d6ec76e6f44802adab36e84c8ffd7b65187d91f` | Kimberley-Inti <KimIntizar@hotmail.com> | Mon, 9 Nov 2026 18:18:07 +0800 |
| [integration/ssa/linux/opensbi-dtlb-profile.patch](integration/ssa/linux/opensbi-dtlb-profile.patch) | `c83d3aadaef39a9ddb3cb2e25bb89399ff856126` | Kimberley-Inti <KimIntizar@hotmail.com> | Wed, 11 Nov 2026 00:04:46 +0800 |
| [integration/ssa/linux/linux-exec-lifecycle.patch](integration/ssa/linux/linux-exec-lifecycle.patch) | `f327da924b3515e2d4c33bc1a8eb1e0c38807d66` | Kimberley-Inti <KimIntizar@hotmail.com> | Tue, 10 Nov 2026 13:53:59 +0800 |
| [integration/ssa/linux/opensbi-cache-profile.patch](integration/ssa/linux/opensbi-cache-profile.patch) | `43f02ffb329d9c86b2ff2138dc450b2060778ffe` | Kimberley-Inti <KimIntizar@hotmail.com> | Thu, 12 Nov 2026 13:59:44 +0800 |
| [integration/ssa/linux/linux-dtlb-event.patch](integration/ssa/linux/linux-dtlb-event.patch) | `07fb4b1efd171f1453b1bcd13ce113a7e6f1b307` | Kimberley-Inti <KimIntizar@hotmail.com> | Wed, 11 Nov 2026 00:04:45 +0800 |
| [integration/ssa/linux/linux-result-export.patch](integration/ssa/linux/linux-result-export.patch) | `b92b11252f5b9a5ce2a3c33298fa3b8bef93c836` | Kimberley-Inti <KimIntizar@hotmail.com> | Wed, 11 Nov 2026 15:45:30 +0800 |
| [integration/ssa/linux/linux-cache-profile.patch](integration/ssa/linux/linux-cache-profile.patch) | `275125fabacde9e83f4bff6863bf25012537e0ed` | Kimberley-Inti <KimIntizar@hotmail.com> | Thu, 12 Nov 2026 13:59:44 +0800 |
| [integration/ssa/linux/linux-memory-classification.patch](integration/ssa/linux/linux-memory-classification.patch) | `e341319bc75a2c2c1443d4b8654c9270f922aaf8` | Kimberley-Inti <KimIntizar@hotmail.com> | Fri, 13 Nov 2026 13:32:38 +0800 |
| [integration/ssa/linux/linux-transparent-launch.patch](integration/ssa/linux/linux-transparent-launch.patch) | `8b865bfe4c40332446227e2fbf6b442ab0bc651a` | Kimberley-Inti <KimIntizar@hotmail.com> | Fri, 13 Nov 2026 20:32:01 +0800 |
| [integration/ssa/linux/linux-cost-probes.patch](integration/ssa/linux/linux-cost-probes.patch) | `bf5a1bc53f4131b9b7be9648f80b32d061cb0a09` | Kimberley-Inti <KimIntizar@hotmail.com> | Sat, 14 Nov 2026 14:20:56 +0800 |
| [integration/ssa/linux/linux-classification-contract.patch](integration/ssa/linux/linux-classification-contract.patch) | `3e7c06efefeda043f100ab635b1729ce7a11afd8` | Kimberley-Inti <KimIntizar@hotmail.com> | Sat, 14 Nov 2026 14:39:54 +0800 |
| [patches/chipyard/constellation-dependency.patch](patches/chipyard/constellation-dependency.patch) | `710f951e2a3ec3ec1c050889c9ccf35e0e0ede1e` | Kimberley-Inti <KimIntizar@hotmail.com> | Sun, 22 Mar 2026 21:26:42 +0800 |
| [patches/chipyard/fesvr-verilator-build.patch](patches/chipyard/fesvr-verilator-build.patch) | `375068b6180fa968f86f07fc4b2e1ec104f632ee` | Kimberley-Inti <KimIntizar@hotmail.com> | Mon, 9 Nov 2026 06:19:08 +0800 |
| [patches/chipyard/dtlb-hpm-config.patch](patches/chipyard/dtlb-hpm-config.patch) | `8d07f53b8ed7fa36eae0da59d35f07cf6fd861d3` | Kimberley-Inti <KimIntizar@hotmail.com> | Wed, 11 Nov 2026 00:19:30 +0800 |
| [patches/history/chipyard/original-tests.patch](patches/history/chipyard/original-tests.patch) | `c9f704c0364ba5cafb83c4ec01478b90a40d5b1a` | Kimberley-Inti <KimIntizar@hotmail.com> | Wed, 4 Mar 2026 22:27:08 +0800 |
| [patches/history/chipyard/legacy-test-revision.patch](patches/history/chipyard/legacy-test-revision.patch) | `01b1aa69bce35971c9912e5706860d848adc6900` | Kimberley-Inti <KimIntizar@hotmail.com> | Sat, 28 Mar 2026 08:01:21 +0800 |
| [patches/history/chipyard/legacy-microcode-build.patch](patches/history/chipyard/legacy-microcode-build.patch) | `c2391670d8e1cc62369cfc3e96b58a9a8cc94dda` | Kimberley-Inti <KimIntizar@hotmail.com> | Sun, 12 Apr 2026 14:46:47 +0800 |
| [patches/rocket-chip/hpm-context-tracking.patch](patches/rocket-chip/hpm-context-tracking.patch) | `9c6d44169365b1423f5aa8282def76b20e6c04fb` | Kimberley-Inti <KimIntizar@hotmail.com> | Thu, 5 Mar 2026 22:41:45 +0800 |
| [patches/rocket-chip/trap-mode-routing.patch](patches/rocket-chip/trap-mode-routing.patch) | `1543ea5445423aefae78c52b37c2521abea42fdc` | Kimberley-Inti <KimIntizar@hotmail.com> | Sun, 22 Mar 2026 21:26:42 +0800 |
| [patches/rocket-chip/trap-signal-placement.patch](patches/rocket-chip/trap-signal-placement.patch) | `1f200edb0eb0832a72d04d8d4f36b912e0e447dd` | Kimberley-Inti <KimIntizar@hotmail.com> | Sat, 28 Mar 2026 08:01:21 +0800 |
| [patches/rocket-chip/forced-monitor-exit.patch](patches/rocket-chip/forced-monitor-exit.patch) | `d047a854895f008c586487e017f5346c4427c1af` | Kimberley-Inti <KimIntizar@hotmail.com> | Wed, 1 Apr 2026 15:35:41 +0800 |
| [patches/rocket-chip/normal-monitor-exit.patch](patches/rocket-chip/normal-monitor-exit.patch) | `07a9c3fa809332daa19f8ca99e2573cd0ecaced1` | Kimberley-Inti <KimIntizar@hotmail.com> | Sun, 12 Apr 2026 08:02:41 +0800 |
| [patches/rocket-chip/monitor-exit-finalization.patch](patches/rocket-chip/monitor-exit-finalization.patch) | `23f5a64f6144cd3ffc7b25d490b48f5d019ee718` | Kimberley-Inti <KimIntizar@hotmail.com> | Sun, 12 Apr 2026 14:46:46 +0800 |
| [patches/rocket-chip/inherited-context-implementation.patch](patches/rocket-chip/inherited-context-implementation.patch) | `539c3b10fee35fe0a2890083dd17c06688a704f8` | Kimberley-Inti <KimIntizar@hotmail.com> | Sun, 8 Nov 2026 23:03:16 +0800 |
| [patches/rocket-chip/context-retirement-attribution.patch](patches/rocket-chip/context-retirement-attribution.patch) | `986407bc6df8d2a67572250f1df9eb2c0edeacf9` | Kimberley-Inti <KimIntizar@hotmail.com> | Mon, 9 Nov 2026 06:18:46 +0800 |
| [patches/rocket-chip/trap-context-isolation.patch](patches/rocket-chip/trap-context-isolation.patch) | `3f4ab938660454b101c67f6929bfebae5be1a138` | Kimberley-Inti <KimIntizar@hotmail.com> | Mon, 9 Nov 2026 09:05:25 +0800 |
| [patches/rocket-chip/sv39-pc-width.patch](patches/rocket-chip/sv39-pc-width.patch) | `41d297689890296699d4a45699bf7e5791d33b96` | Kimberley-Inti <KimIntizar@hotmail.com> | Mon, 9 Nov 2026 15:55:54 +0800 |
| [patches/rocket-chip/linux-user-pool-privileges.patch](patches/rocket-chip/linux-user-pool-privileges.patch) | `1c78413459344d7ca1d2b3cdedbdc4a16133dee9` | Kimberley-Inti <KimIntizar@hotmail.com> | Mon, 9 Nov 2026 18:16:47 +0800 |
| [patches/rocket-chip/dtlb-request-attribution.patch](patches/rocket-chip/dtlb-request-attribution.patch) | `469bfac7de26bfbb03298787ad030898c6de24c9` | Kimberley-Inti <KimIntizar@hotmail.com> | Wed, 11 Nov 2026 00:19:30 +0800 |
| [patches/rocket-chip/cache-event-trace.patch](patches/rocket-chip/cache-event-trace.patch) | `bccfc47a4aecbef59aa4d4c73f15159b78ab123c` | Kimberley-Inti <KimIntizar@hotmail.com> | Thu, 12 Nov 2026 14:11:23 +0800 |
| [patches/rocket-chip/memory-classification.patch](patches/rocket-chip/memory-classification.patch) | `bb5b1c26a8dae5d5afee716a1636b55a1bfe1ed2` | Kimberley-Inti <KimIntizar@hotmail.com> | Fri, 13 Nov 2026 13:46:31 +0800 |

## Technical evolution

Calling-context retirement and dictionary fixes established parent-sensitive record reuse. Trap isolation preserves application frames across privileged execution. Per-task physical pools and pause/resume snapshot correction provide single-hart process accounting. Exec freezes the old image, preserves failed pre-commit replacements, and starts a clean new session. Native PTW and D-cache request profiles extend interval accounting. Bounded chunked export separates transport integrity, abandoned calls and classification coverage. Rule1 classifies retired integer accesses with bounded session-local histories. Trusted automatic launch enables audited ordinary ELF targets. The final validation combines independent reconstruction, RTL/Linux correctness checks and target-side performance measurements.

The original loader-managed virtual-pool and helper-SRAM proposals are adapted to kernel-managed physical pools and generated private ROMs. Executable classification and lifecycle rules are project design supplements; [acceptance](docs/ACCEPTANCE.md) identifies their scope.

## Accepted releases and source identities

- `v0.1.0`: `0421e67203e0cfb63d96699f061ffa7d8d00fddf`.
- `v0.2.0`: `2adbfa5de81f341bd575e8498b370c5a12a02785`, accepted candidate `9c1fdfb0e147c27f7aca58f306e91f532c3fb609`.
- Final component identities: [source commits](evidence/final-validation/source-commits.json).
- Final behavior and remaining boundaries: [validation](docs/VALIDATION.md), [performance](docs/PERFORMANCE.md), [acceptance](docs/ACCEPTANCE.md).

Failed native/checker evidence and semantic negatives remain alongside final captures. Existing tags and original development history remain unchanged. The [Rocket archive assessment](docs/ROCKET_CHIP_ARCHIVE.md) documents retained development-fork dependencies.
