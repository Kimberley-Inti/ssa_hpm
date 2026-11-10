# 开发历史与发布提交映射

原开发仓库和分支不重写、不删除。本仓库是普通独立 Git 仓库；以下仅导入项目补丁、
测试和验证资料，原始 SHA 是来源标识，不作为新仓库的 Git parent。原作者、作者日期和
提交说明按 Git 记录保留；导入提交的 committer/date 属于本次整理。跨仓库同时间的排列
只用于整理，不推断原操作的绝对先后。

## 原仓库核验

- 登录已恢复为 `Kimberley-Inti`（ID `185574409`）。`SSA-HPM` 是私有旧开发仓库；
  之前的 Repository not found 来自错误账号/不可见，而不是仓库 URL 错误。
  Rocket 403 来自 `jeffli999` 没有写权限；凭据库的 Kimberley 旧项还返回 401。
- 仅在相关仓库增加 `github-authenticated` 远端和 gh helper 覆盖，原 origin/my-fork 保留。
- 旧 Chipyard `main` 仍是 `4c2e2c7b2aaab4388b9f91f64b22e751ddf283f1`；
  Rocket `SSA-HPM` 仍是 `1f200edb0eb0832a72d04d8d4f36b912e0e447dd`，未被改写。
- 两个旧仓库均新增 `archive/ssa-hpm-local-20261108`，分别保存本地原 main `c2391670…`
  和原 SSA-HPM `23f5a64f…`；此前超前的 3 个 Rocket 提交现在均可在 GitHub 查到。
- 两层 `ssa-hpm-completion-20261108` 已原样推送：Chipyard 为
  `375068b6180fa968f86f07fc4b2e1ec104f632ee`，Rocket 为
  `986407bc6df8d2a67572250f1df9eb2c0edeacf9`，gitlink 对应正确。
- 原始工作树差异恢复点 `539c3b10fee35fe0a2890083dd17c06688a704f8` 也可从 GitHub 访问。
  所有表内原始提交均已逐条通过已认证 GitHub commit API 核验，见
  `evidence/publication/original-commits.json`。
- Rocket Draft PR: https://github.com/Kimberley-Inti/rocket-chip/pull/1 （base `SSA-HPM`）。
- Chipyard Draft PR: https://github.com/Kimberley-Inti/SSA-HPM/pull/1 （base `main`）。
  后者以独立 `ssa-hpm-publication-20261109` 分支附加一个复现入口修补提交，补收忽略的
  env.sh 并保护缺失旧 C 原型的默认构建，未移动已验收分支。先合 Rocket，再合 Chipyard。
- 原工作树、原分支、初始未跟踪文件及 `ssa/handoff/` 均保留；不上传这些 bundle。

## 原始记录 → 新提交

所有完整 SHA、作者、日期、改动路径和具体产物亦见 `provenance.json`。

| 原仓库 / 原分支 | 原始 SHA | 作者日期 | 原说明 | 新提交 / 整理说明 |
| --- | --- | --- | --- | --- |
| chipyard / main | `c9f704c0364ba5cafb83c4ec01478b90a40d5b1a` | 2026-03-04T22:27:08+08:00 | Initial commit | `b4be26b28b237996713b47f75cb9619cdc242d3b`；`patches/history/chipyard/0001-original-tests.patch` |
| chipyard / main | `90bfa6c768b8fd1258d38cdffcfde862dfcc669d` | 2026-03-04T22:59:12+08:00 | Update .gitignore and remove untracked build artifacts | 仅记录：仓库忽略规则、无关子模块移除或路径/gitlink 配置；复现改用可获取基线 |
| rocket-chip / SSA-HPM | `9c6d44169365b1423f5aa8282def76b20e6c04fb` | 2026-03-05T22:41:45+08:00 | Update HPM logic in RocketCore | `e47da1fbea907868f45c3eeb56d8a5f7e1a41262`；`patches/rocket-chip/0001-9c6d44169.patch` |
| chipyard / main | `6723407ba5ffb05d01757ef1c5d24a20218caffa` | 2026-03-05T22:42:48+08:00 | Track modified rocket-chip for SSA-HPM | 仅记录：仓库忽略规则、无关子模块移除或路径/gitlink 配置；复现改用可获取基线 |
| chipyard / main | `4c2e2c7b2aaab4388b9f91f64b22e751ddf283f1` | 2026-03-06T23:35:12+08:00 | Relink rocket-chip submodule to my personal fork | 仅记录：仓库忽略规则、无关子模块移除或路径/gitlink 配置；复现改用可获取基线 |
| chipyard / main | `710f951e2a3ec3ec1c050889c9ccf35e0e0ede1e` | 2026-03-22T21:26:42+08:00 | ssa_trap_mode connection logic | `826f5082206beef41b461c847ca4b0ca46bc60c3`；`patches/chipyard/0001-constellation-dependency.patch` |
| rocket-chip / SSA-HPM | `1543ea5445423aefae78c52b37c2521abea42fdc` | 2026-03-22T21:26:42+08:00 | ssa_trap_mode connection logic | `22ac074de75b476f2fcd44d01fa38039afe9e40a`；`patches/rocket-chip/0002-1543ea544.patch` |
| chipyard / main | `01b1aa69bce35971c9912e5706860d848adc6900` | 2026-03-28T08:01:21+08:00 | modified code sequence | `1f19a00316cebd0e9bd4b5ed784dbf0f6e44eeff`；`patches/history/chipyard/0002-legacy-test-revision.patch` |
| rocket-chip / SSA-HPM | `1f200edb0eb0832a72d04d8d4f36b912e0e447dd` | 2026-03-28T08:01:21+08:00 | modified code sequence | `ec73be3357edd13ef4653ec62a1e3074159defa0`；`patches/rocket-chip/0003-1f200edb0.patch` |
| rocket-chip / SSA-HPM | `d047a854895f008c586487e017f5346c4427c1af` | 2026-04-01T15:35:41+08:00 | forced exit | `5a37854211a9f1043de1eed9397e145a20ca8caf`；`patches/rocket-chip/0004-d047a8548.patch`；原本超前的 3 个本地提交之一 |
| chipyard / main | `f98d756927cf59cfee20b1183f9247cab7e181b9` | 2026-04-01T15:35:42+08:00 | forced exit | 仅记录：仓库忽略规则、无关子模块移除或路径/gitlink 配置；复现改用可获取基线 |
| chipyard / main | `2cd92122a0fff0c4036d34e77e36470c22311f53` | 2026-04-12T08:02:41+08:00 | normal exit | 仅记录：仓库忽略规则、无关子模块移除或路径/gitlink 配置；复现改用可获取基线 |
| rocket-chip / SSA-HPM | `07a9c3fa809332daa19f8ca99e2573cd0ecaced1` | 2026-04-12T08:02:41+08:00 | normal exit | `48e9965c45221ff5a427e1e4bc53c2cc86e97ee5`；`patches/rocket-chip/0005-07a9c3fa8.patch`；原本超前的 3 个本地提交之一 |
| rocket-chip / SSA-HPM | `23f5a64f6144cd3ffc7b25d490b48f5d019ee718` | 2026-04-12T14:46:46+08:00 | normal exit | `1d5ae817964d3b13f1098431d0c4f71209ef59cb`；`patches/rocket-chip/0006-23f5a64f6.patch`；原本超前的 3 个本地提交之一 |
| chipyard / main | `c2391670d8e1cc62369cfc3e96b58a9a8cc94dda` | 2026-04-12T14:46:47+08:00 | normal exit | `1d14fa7c7ff95029ee009465f95f30a35646e5a4`；`patches/history/chipyard/0003-legacy-microcode-build.patch` |
| rocket-chip / ssa-hpm-completion-20261108 | `539c3b10fee35fe0a2890083dd17c06688a704f8` | 2026-11-08T23:03:16+08:00 | Preserve inherited uncommitted SSA-HPM implementation | `d8390b3affa5c04d7b4e7b305b88a9f8900bba5a`；`patches/rocket-chip/0007-539c3b10f.patch` |
| rocket-chip / ssa-hpm-completion-20261108 | `986407bc6df8d2a67572250f1df9eb2c0edeacf9` | 2026-11-09T06:18:46+08:00 | Fix SSA-HPM microcode retirement, context dictionary and counter attribution | `bc2b064fd2be342d51774e4c83c895457cf197b6`；`patches/rocket-chip/0008-986407bc6.patch` |
| chipyard / ssa-hpm-completion-20261108 | `375068b6180fa968f86f07fc4b2e1ec104f632ee` | 2026-11-09T06:19:08+08:00 | Add reproducible SSA-HPM Spike and Rocket RTL validation | `429b78c19191d4973042ac554ae3c71383ad5ff5`；`patches/chipyard/0002-fesvr-verilator-build.patch`, `integration/ssa/.gitignore` 等 |

## 整理范围与后续维护

- Rocket 的 8 次实现修改逐个保留为补丁及对应导入提交，包含原始未提交差异的恢复提交 `539c3b10f`。
- Chipyard 中纯 gitlink 更新与 URL 调整不重复制造代码副本，其与 Rocket 原始提交的对应关系保留在上述记录中。
- `710f951e` 里的 Constellation 固定作为单独依赖补丁；`375068b6` 仅提取两个实际需要的仿真构建文件，
  测试另作为独立文件安装，避免同一改动在 patch 和文件中交付两次。
- 旧 `.gitignore`、商业/ESP 子模块移除和旧 tests/Makefile 不进入当前复现补丁；旧测试演进只保留历史系列。
- 本次发布整理提交新增 README/HISTORY、许可证材料、公开基线安装器、来源清单、完整历史审计、发布核验及
  本次发布回归证据。该提交由 `v0.1.0` 标签标识；不借用旧作者日期给发布新增材料溯源。
- `ssa/env.sh` 是已验收工作目录里的忽略文件，原交付 commit 没有包含它；本发布显式补齐，来源单列。
- 新仓库提交 SHA 与原始 SHA 不同，因为其内容是筛选后的补丁/资料而非原源码树，且不继承上游 parents。
- 后续工作继续在本仓库增加版本；禁止改写已有版本标签或用强推覆盖原开发记录。

发布后补充提交：原 Chipyard `ssa-hpm-publication-20261109` 的 `58a7acde9598b4e08d11e5b5f3da0e146e138078` 由本次发布整理创建；在独立包中，其 env 辅助文件由发布整理提交收录，历史 Makefile 防护无需应用到干净上游，因为独立包没有引入过时的默认测试目标。

发布包的后续两个新提交分别整理复现/来源/许可证材料，以及记录本次公开基线重建和实际回归。
这两次整理保留当前作者日期，没有改写前面 13 个按原作者日期导入的提交；版本由 v0.1.0 标记。


## stage2-trap-isolation (development, no new tag)

Based on unchanged v0.1.0 `0421e67203e0cfb63d96699f061ffa7d8d00fddf`.
The publication environment fix `58a7acde9598b4e08d11e5b5f3da0e146e138078`
was replayed on the Chipyard development branch as
`339d349d35e308f2912c5db55c42c6e4adcb18ba` (identical tree).

| Source repository | Source base | New source commit | Artifact |
| --- | --- | --- | --- |
| Rocket Chip | `986407bc6df8d2a67572250f1df9eb2c0edeacf9` | `3f4ab938660454b101c67f6929bfebae5be1a138` | `patches/rocket-chip/0009-trap-context-isolation.patch` |
| Chipyard | `339d349d35e308f2912c5db55c42c6e4adcb18ba` | `fa0ccc7be59a624acc1dcd80af211919be17cd56` | Updated standalone `integration/ssa` test files; no duplicate test patch |

This stage implements normal architectural trap isolation, nested resume, a
read-only state CSR and fail-closed overflow. `docs/STAGE2.md` records design
review, the old-RTL failure, unchanged counting semantics and validation scope.
First-stage main/tag and the two existing Draft PR branches are not moved.


本轮独立维护仓库的实现/测试整理提交为 `3ecec6adc0c6e483d5b386f1239e5a596a545153`。
其后的验证提交收录独立公开基线重建、339 个 Rocket Scala 源文件编译、新 RTL 和新
Verilator 的 16 项实际结果。原始验收证据与本次 baseline/development/independent
证据分开保存；全部实现位于本轮独立分支，v0.1.0 和 main 保持不变。


## stage3-process-isolation

从 stage2 独立维护仓库提交 `2d646a615b357e3e883289d91d0b903ac14baec4` 新建分支。
已回读 GitHub stage2 分支与 Draft PR #1，二者 head 一致；未移动 main、v0.1.0 或旧 PR。

| 原仓库/分支 | 本轮基线 | 本轮源码提交 | 独立仓库对应内容 |
| --- | --- | --- | --- |
| Kimberley-Inti/SSA-HPM / stage3-process-isolation | fa0ccc7be59a624acc1dcd80af211919be17cd56 | 503d5ccdb6634a05f46181ecd23648cfbb4e61b8 | integration/ssa 的进程协议、双栈调度及验证器；不重复打测试补丁 |
| Rocket Chip | 3f4ab938660454b101c67f6929bfebae5be1a138 | 无新源码提交 | 原有 0001–0009 补丁保持不变，expected_tree 同 stage2 |

本轮原创提交未重写先前开发历史。首次实现提交和后续独立重建证据提交形成两个
有意义的维护仓库提交；其 SHA 可由本分支 git log 核验。源码提交说明为
“Add single-hart monitoring pool lifecycle and off-CPU attribution regression”。
Chipyard ssa/README.md 的本轮说明在维护仓库整理为 docs/STAGE3.md；运行源文件
和 Makefile 一致，历史 integration/ssa/README.md 不替代当前阶段说明。

本轮接口与测试整理提交：`aad36f0ecad6fce9fbd661760c9505bc1e653e6d`，对应 Chipyard `503d5ccdb6634a05f46181ecd23648cfbb4e61b8`。后续验证提交仅补充实际重建证据和文档。

## Stage4 Linux bootstrap (work in progress)

Branch starts at stage3 418692f75b3895cbb084e26276ba7267b9f8efee.

| Source | Baseline | New commit | Delivery |
| --- | --- | --- | --- |
| Rocket | 3f4ab938660454b101c67f6929bfebae5be1a138 | 41d297689890296699d4a45699bf7e5791d33b96 | 0010-sv39-pc-width.patch |
| Chipyard | 503d5ccdb6634a05f46181ecd23648cfbb4e61b8 | cad6278c2a079e8ffa3b371158bb6f41aca64ffb | integration/ssa boot entry and tests, no duplicate test patch |
| Linux | 5f5fd87b36e21ed59b759b69eebfa1c74955cb37 | 3b79ddfa2fb70707ace85385d6722925fffc8eea | integration/ssa/linux/0001-stack-pointer-declaration.patch |
| OpenSBI | a98258d0b537a295f517bbc8d813007336731fa9 | b778927a507e4ebcc43a8ecb8d495562ef48efb3 | integration/ssa/linux/0001-opensbi-rocket-platform.patch |

Kernel and firmware development commits are local; reproduction fetches the
public pinned baselines and applies the patches, never fetching those local
commits. The independent bootstrap already matched both source tree hashes.
The first-stage Sv39 regression uses the same ELF: old RTL exits 42, Spike and
fixed RTL exit zero. Linux boot and subsequent real-process acceptance are
separate gates; implementation commits do not imply they have passed.

Stage4 Linux integration implementation (runtime gates pending):
- Rocket `1c78413459344d7ca1d2b3cdedbdc4a16133dee9`: supervisor-only pool selection,
  opt-in U-mode notification policy and trusted ROM physical memory access;
  distributed as patch0011. Parent is the stage4 Sv39 PC fix41d2976.
- Linux `0d6ec76e6f44802adab36e84c8ffd7b65187d91f`: per-task ownership, fork reset,
  scheduler pause/resume of open frames, bounded exit export and test diagnostics.
  Local development commit, reconstructed with integration/ssa/linux/0002 patch
  after the public baseline and stack-pointer compatibility patch.
- Chipyard `8bb4bb28` (full SHA in provenance): kernel patch, user-mode probes,
  real Linux process fixtures, pinned build entry and strict attribution grader.
  Standalone project files are delivered once under integration/ssa; the gitlink
  records the Rocket dependency without requiring a private/local commit fetch.
- Chipyard `ffa17056` (full SHA in provenance): remove unused legacy PTYs,
  correct RISC-V syslog ABI and retain an initramfs-only rebuild entry. The signal
  and permission ABI diagnostic passed on baseline Linux/Spike; no SSA claim.
- Chipyard `1462d8ba` (full SHA in provenance): require reciprocal B sleep-frame
  pause/resume/rebasing evidence in the Linux grader, in addition to A's timer
  preemption evidence. This changes the checker only, not the kernel or image.
- Chipyard `40287b89` / `2813cd71` (full final SHA in provenance): document the
  task/selector ownership, prctl lifecycle, physical-pool ABI and exact counter
  boundaries, with guarded-failure scope clarified. Documentation only.
  These stage4 source revisions are retained locally; this private standalone
  repository carries their patches/files and does not require fetching local SHAs.
- Chipyard e6a1537e /3776fab1 /59255bbf /325b441a: strengthen Linux evidence checks
  with global sample chronology, actual embedded user ELF symbols, mandatory loop
  instructions, independent open-frame interval sums and parent-frame exclusion.
  These checker-only commits do not change the already-built RTL/kernel/image.
- Chipyard `68611650` (full SHA in provenance): specify the exact pre-context-switch
  S/R sampling boundary and which outgoing/incoming handoff costs remain charged.
  Documentation only; running RTL, kernel and initramfs are unchanged.

Stage4 final acceptance: final Rocket Linux boot A passed, real uid1000 process
monitoring/exit export and permission probes B passed, and all four real Linux
preemption trials C completed with clean power-down/exit0. The final checker
passed173 checks on the original log and again from the public-source reconstructed
project directory. Corrected A common instret short/long is278450/278470 (delta20);
legacy is1545490/1753452 (delta207962). All16+3+5 existing/new low-level checks
remain passed, including the expected-exit42 legacy control. No new tag, main
update, PR merge or public repository visibility change is part of this delivery.

## Stage5 Linux exec lifecycle

Development starts from maintenance55104eb22d160d9bf9e1e7388866ba7482a2785a
(stage4 Draft PR#3, unchanged), not from main or an unmerged upstream PR.

| Repository | Local baseline | Local stage5 commit | Standalone delivery |
| --- | --- | --- | --- |
| Linux | 0d6ec76e6f44802adab36e84c8ffd7b65187d91f | f327da924b3515e2d4c33bc1a8eb1e0c38807d66 | integration/ssa/linux/0003-linux-exec-lifecycle.patch |
| Chipyard | 68611650d79c7635a7f1b28935c758f2f12fa3b8 | 6621ef7ca88a1091c13fe2e050746d3e7e6fee11 | standalone build/fixtures/checker in integration/ssa/linux |
| Rocket | 1c78413459344d7ca1d2b3cdedbdc4a16133dee9 | unchanged | existing patches0001..0011 |
| OpenSBI | b778927a507e4ebcc43a8ecb8d495562ef48efb3 | unchanged | existing platform patch |

Linux commit separates post-commit exec retirement from normal exit, labels
sessions/image epochs and abandoned frames, and preserves pre-commit failed exec.
Chipyard commit adds the same-PID replacement and ENOENT fixtures, pinned image
build and native checker, followed by the unchanged stage4 Linux regression.
These source commits are retained in local source repositories, with author/date
and commit text preserved in the kernel format-patch. Reproduction uses public
baselines and these patches/files; it never needs the local SHAs to be fetchable.
Runtime evidence and final maintenance commit mapping follow after native completion.

Chipyard follow-up `02ddc90abb4806e136f1e96b1580702df39cc4b7` documents session retirement and counter boundaries in ABI.md; it does not alter the built image or RTL.
