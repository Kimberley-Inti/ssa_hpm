# 从公开上游基线复现

## 准确来源

| 层 | 可获取的来源 | 基线完整 SHA |
| --- | --- | --- |
| Chipyard | https://github.com/ucb-bar/chipyard.git | `2d03d10837fc1a7569d10ae2c91c8132c7fee77d` |
| Rocket Chip | https://github.com/chipsalliance/rocket-chip.git | `44b0b8249279d25bd75ea693b725d9ff1b96e2ab` |
| Constellation 依赖 | https://github.com/ucb-bar/constellation.git | `dce9eb03b44ad442a552242546f1672bdc15fce3` |

两个主基线均已通过新的网络 fetch 获取，未从虚拟机的本地 Git 对象库借用。
Chipyard 上游 gitlink 原本就指向上述可获取的 Rocket 基线。原本已验收的顶层基线
`c2391670d8e1cc62369cfc3e96b58a9a8cc94dda` 指向仅在原开发树保存的 Rocket
`23f5a64f6144cd3ffc7b25d490b48f5d019ee718`，因此不能把“checkout 该本地 SHA”
作为外部复现步骤。此发布包从公开基线重放全部 SSA-HPM 补丁，消除了该依赖。

依赖顺序：获取两个基线 → 应用 `patches/chipyard/0001`、`0002` → 按文件名依次
依次应用当前分支的全部 12 个 Rocket 补丁 → 安装 `integration/ssa`。历史补丁**不应用**。Rocket 最终
树必须与本分支 `provenance.json` 的 `rocket_chip.expected_tree` 完全相同（
v0.1.0 对应 `986407bc6df8d2a67572250f1df9eb2c0edeacf9` 的历史树），
同时核对核心 Scala、微码、构建文件及测试的 SHA-256。应用得到的新 commit SHA
可能因 committer 日期而变化，不以它作为远端 fetch 依赖。顶层 gitlink 保持可获取
的上游基线，Rocket 子工作树含补丁提交；不要用 submodule update 把它退回基线。

## 安装和依赖

需要 Git、Python 3、RISC-V GCC/binutils、Spike（参考测试）、Java 17、sbt、Verilator
及 Chipyard 对应版本的构建依赖。参考环境版本记录在 `evidence/acceptance/versions.txt`。

```bash
# 在本发布仓库根目录执行；目标必须不存在或为空
python3 scripts/apply.py /tmp/my-ssa-chipyard --report /tmp/my-ssa-apply.json

# 首次使用：从上游获取 RocketConfig 构建所用的固定依赖（没有复用虚拟机的源码）
python3 scripts/init_build_dependencies.py /tmp/my-ssa-chipyard
```

跨机器构建还需按 Chipyard 1.8 对应环境准备 sbt、Verilator 等系统依赖。上述初始化
只选取记录的 RocketConfig 依赖，避免无关商业 VLSI/ESP 依赖；网络获取所有依赖的
可用性并未逐个重新验证。不要在已打补丁后执行会覆盖 Rocket checkout 的全量
子模块初始化；特别不要对 `generators/rocket-chip` 本身执行 submodule update。

本次虚拟机发布验证复用现有依赖，使用以下替代步骤。脚本只向**新重建目录**链接
匹配固定 SHA、无已跟踪改动的本地模块，拒绝不匹配版本，不修改原开发源码：

```bash
python3 scripts/link_existing_dependencies.py /tmp/my-ssa-chipyard /home/lxf/chipyard \
  --report /tmp/my-ssa-dependencies.json
```

此路径仍从 GitHub 获取两个主基线，并重新应用补丁、编译新的 Rocket 源码与 RTL；
依赖和工具链复用必须与“完整无缓存构建”区分。已有模块若被此脚本链接，不要再对
这些符号链接运行网络初始化；两种依赖准备路径二选一。

## 构建与回归

```bash
cd /tmp/my-ssa-chipyard
source ssa/env.sh
python3 ssa/gen_rom.py --check
make -C ssa -j2 all
make -C sims/verilator CONFIG=RocketConfig -j8 LINK='/usr/bin/g++ -B/usr/bin/'
python3 ssa/verify.py
python3 ssa/analyze.py ssa/results/rtl-context.txt --elf ssa/test.riscv \
  --json ssa/results/contexts.json
```

`env.sh` 优先使用系统编译/链接工具，避免 Conda 旧 glibc sysroot 无法解析安装的
FESVR `statx`。C++17 要贯穿 Verilator 的递归 make；ABI2 使用一个预留槽记录 DTLB 请求，其余扩展槽仍留待后续。

单项硬件仿真：

```bash
sims/verilator/simulator-chipyard-RocketConfig +permissive \
  +loadmem=ssa/test.hex +max-cycles=5000000 +permissive-off ssa/test.riscv
```

这里的 `+loadmem` 接受十六进制行文件，不能传 ELF。Makefile 使用 objcopy 与
`elf_to_hex.py` 自动转换。bare-metal 测试不需要 pk/newlib；SCBaseReg=0 关闭监测，
测试在物理内存 `[0x85c00000,0x88000000)` 预留 36 MiB。实际 loader 必须清零整个
字典并初始化元数据；测试只初始化其可达桶，不代表已实现 Linux 自动分配。

通过条件：每项退出码为 0，且出现预期 PASS 标记。上下文测试必须有 6 条记录、
result=46、返回后 depth=0；两条父路径的 common instret 为 14452/7226（相同输入和
工具链），父记录包含其子调用。跨工具链可出现不同指令数量，应先检查调用图、复用、
父子归属和对应计数关系；Spike 与 RTL 周期数不应要求相等。


## stage2-trap-isolation 开发分支

本分支仍从上表两个公开基线重建，按序在 v0.1.0 的 8 个 Rocket 补丁后追加第 9 个
陷阱隔离补丁；不需要等待第一阶段旧仓库 PR 合并。顶层复现辅助文件已显式收录，
原发布补充提交 `58a7acde9598b4e08d11e5b5f3da0e146e138078` 在实际源码新分支上
重放为 `339d349d35e308f2912c5db55c42c6e4adcb18ba`；只补环境入口及旧原型构建防护。

`make -C ssa all` 现在也构建陷阱用例。完整回归仍用 `python3 ssa/verify.py`；可指定
`--only-traps` 只跑本轮用例，`--spike-only` / `--rtl-only` 区分模型，
`--out-dir /tmp/ssa-stage2-results` 避免覆盖归档证据。六项新增 RTL 用例分别是
`trap`、`trap-status`、`trap-nested`、`trap-irq`、`trap-overflow`、`trap-readonly`；
两项新增 Spike 用例只验证标准陷阱/定时器指令，不验证自定义 CSR 或透明上下文。
状态 CSR、溢出和计数口径详见 `docs/STAGE2.md`。本分支不发布新标签。


## 第三阶段（基于 stage2）

使用本分支的 apply.py 与 provenance.json，仍应用 9 个 Rocket 补丁和 2 个 Chipyard
补丁，Rocket tree 与 stage2 相同。安装新的 integration/ssa（包含 process.h、
process_entry.S、processes.c、verify_process.py）；不再重复交付 Chipyard 测试补丁。
本轮有修改的源码仓库仅 Chipyard，Rocket 依赖 3f4ab938660454b101c67f6929bfebae5be1a138。
按前述 make 命令重新生成 RTL，然后运行原 16 项与新进程协议测试：

```bash
python3 ssa/verify.py --out-dir /tmp/stage3-regression
python3 ssa/verify_process.py --out-dir /tmp/stage3-process
# 在独立项目仓库中执行：
python3 scripts/check_process_evidence.py /tmp/stage3-process --report /tmp/stage3-relationships.json
```

新 suite 包含 Spike 参考通过、旧协议 RTL 预期退出 42、修复协议 RTL 退出 0。
负对照绝不可当作普通退出零测试。实际两个任务与 Linux 进程集成的区别、三种
计数器的归因区间和剩余依赖见 docs/STAGE3.md。原 16 项回归数量不变。

## 第四阶段 Linux

先完成上述补丁安装、依赖准备和 RocketConfig 模型构建，再按
[integration/ssa/linux/README.md](integration/ssa/linux/README.md)
构建固定版本的 Linux/OpenSBI/最小 initramfs。启动 A 使用 `build-a.py` 与
`verify-a.py`；进程用例使用 `build-a.py --process` 与 `run-process.py`。
后者会保存实际退出结果并调用严格的双向帧归因检查。

本分支启动 A 已实际通过。单进程监测与权限检查 B、真实双进程抢占隔离 C 均已通过；
原始仿真退出 0，最终统一脚本 173 项检查通过。
已有 16+3 项回归和 5 项裸机探针的证据在 `evidence/stage4/regression-final.json`。
复用现有工具链和依赖缓存；Linux 与 OpenSBI 源码则从固定公共基线独立获取，
不得将 Spike 参考输出当作 Rocket Linux 或 SSA 实现的验收。


复核已提交的原始 Linux 日志，无需重复长仿真：

```bash
python3 integration/ssa/linux/grade-process.py \
  evidence/stage4/BC-rocket-linux-process.txt --exit-code 0 \
  --symbols evidence/stage4/user-symbols.json --out /tmp/ssa-linux-regrade.json
```

`BC-execution.json` 保存实际命令、退出码、时长及镜像/模型哈希。此次独立重建
运行复用了开发树重新构建的 RTL 模型和固定工具链缓存；没有声称重复编译第二份
RTL 或重复运行 Linux。原始完整配置启动超时的尝试与后续成功结果分开记录。

## Stage5 Linux exec lifecycle

See [STAGE5.md](docs/STAGE5.md) for the success/ENOENT fixture, full stage4 regression and counter boundaries. Use build-a.py --exec followed by run-exec.py; --reference is ABI-only.

## Stage6 DTLB event profile

See [STAGE6.md](docs/STAGE6.md). Use SSAHPMEventRocketConfig, --event image build
and run, then grade-events.py. Default RocketConfig and ABI1 remain available.
The default DTLB profile reserves one standard40-bit HPM3 counter for accepted PTW requests;
this is not a Spike event model or a generic perf multiplexing interface.

## Stage7 full-result export

Use the same stage6 hash-verified SSAHPMEventRocketConfig model. After installing
the current patch/suite set, build `ssa/linux/build-a.py --export` into a NEW
workspace, then `ssa/linux/run-exec.py --export` into a NEW result directory.
It chains the actual41/2/0/open-frame fixture and unchanged stage6/5/4 suites.
`export_results.py` writes versioned JSON; `test_export_results.py` separately
checks host-only faults/capacity. Commands and cached-build distinctions are in
[STAGE7.md](docs/STAGE7.md); no stage7 Rocket/OpenSBI source change is required.

Stage7 acceptance completed on the independently built image: native exit0 and
normal power-down,25/70/37/179 check gates. See evidence/stage7/summary.json,
linux/execution.json and independent-final-check.json. The independent checker
replay uses the same raw run; it is not a second native simulation. Fresh --export
runs default to172800 host seconds; the actual long run's original43200 limit
was preserved using the separately audited runner-only pause/resume protocol.
For a cheap committed-log recheck, use the two commands at the end of STAGE7.md.

## Stage8 fixed Cache profile

Use `build-a.py --cache` and `run-exec.py --cache` with SSAHPMEventRocketConfig;
see docs/STAGE8.md for exact build, RTL/source oracle and Linux commands. Public
patch order adds Rocket0013, Linux0006 after0005, and OpenSBI0003 after0002.
The builder applies both kernel/firmware profile flags together; default builds
retain DTLB. Data-stream metadata distinguishes the profiles within memory ABI2.

Stage8 acceptance finished: actual corrected Cache/Linux image exit0 + normal
power-down,39 aggregate/all-counter,69 Cache/timer/exec and24 export gates.
The independent installed checker replays that same complete log identically.
See evidence/stage8/summary.json, linux/execution.json, source-commits.json,
linux-image-build.json and independent-final-check.json; no second independent
full model rebuild or second accepted full Linux run is implied. The final
STAGE8.md block rechecks committed raw evidence without simulation.


## Stage9 memory classification (rule1)

Use the same public Chipyard/Rocket bases and full ordered patch chain;0014 adds
classification without changing the ROMs or ABI1/2 HPM layouts. The installed
suite includes the independent reference, four real RTL fixtures and a directed
Linux lifecycle fixture. See docs/CLASSIFICATION.md and docs/STAGE9.md for the
bounded observation semantics and exact commands. `--classification` builds a
fresh Cache-profile Linux image with the classification patch; default base,
`--event` DTLB and `--cache` entries remain compatible.

```sh
python3 ssa/classification/test_reference.py
make -C ssa classification
python3 ssa/classification/run.py --simulator sims/verilator/simulator-chipyard-SSAHPMEventRocketConfig --out-dir /tmp/ssa-rule1-rtl
python3 ssa/classification/build-trace.py --workspace "$PWD" --config SSAHPMEventRocketConfig --out /tmp/ssa-rule1-wb-model
/tmp/ssa-rule1-wb-model/simulator-progress +permissive +loadmem=ssa/classification-fault.hex +max-cycles=5000000 +permissive-off ssa/classification-fault.riscv > /tmp/ssa-rule1-wb.txt 2>&1
python3 ssa/classification/check_wb.py /tmp/ssa-rule1-wb.txt --out /tmp/ssa-rule1-wb.json
python3 ssa/linux/build-a.py --classification --work /tmp/ssa-rule1-linux --jobs 6
python3 ssa/linux/run-classification.py --work /tmp/ssa-rule1-linux --simulator sims/verilator/simulator-chipyard-SSAHPMEventRocketConfig --out-dir /tmp/ssa-rule1-linux-results
python3 ssa/linux/classification_results.py /tmp/ssa-rule1-linux-results/rocket-linux-classification.txt --out /tmp/ssa-rule1-classified.json
```

Use new work/results directories. The read-only WB harness links the unchanged
model archive and observes candidates before the clock edge; it does not write
RTL state. Linux execution records exact native status and hashes before grading;
an in-progress prefix is not a full passing boot. Rules/profile metadata and both
base and classification terminal checksums must pass. Kernel/SBI/source dependency
caches may be reused; source reconstruction and rebuilt test/user images are
reported separately from reuse of an already verified model.


## Stage10 controlled transparent launch

See docs/STAGE10.md and integration/ssa/linux/transparent/POLICY.md. The new
--transparent entry reconstructs Linux with incremental patch0008 and builds
ordinary static ELF, standard musl PT_INTERP/DSO and manual compatibility fixtures.
The fixed target selection is made by the trusted test init before privilege drop;
targets contain no SSA API calls. run.py freezes native status and grades both
automatic and old manual suites; do not infer success from an incomplete prefix.
