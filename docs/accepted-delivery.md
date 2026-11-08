> Archived report from accepted Chipyard commit 375068b6180fa968f86f07fc4b2e1ec104f632ee. Local paths, old remotes and commands describe that acceptance run; use the release README and REPRODUCE.md for this standalone package.

# SSA-HPM 可复现验收

本目录对应设计 PDF 的第一阶段：透明 JAL/JALR 调用上下文与 cycle、time、instret
归因。实际硬件入口为 Chipyard `chipyard.TestHarness.RocketConfig`，不是 Spike 插件。
内存 ABI 和流水线约定见
[SCCodeTable 说明](../generators/rocket-chip/src/main/resources/ssa/README.md)。

## 构建与运行

在 `/home/lxf/chipyard` 执行：

```bash
source ssa/env.sh
python3 ssa/gen_rom.py --check
make -C ssa -j2 all
make -C sims/verilator CONFIG=RocketConfig -j8 LINK='/usr/bin/g++ -B/usr/bin/'
python3 ssa/verify.py
python3 ssa/analyze.py ssa/results/rtl-context.txt --elf ssa/test.riscv --json ssa/results/contexts.json
```

`verify.py` 仅执行测试，不隐式启动 RTL 构建。可用 `--spike-only` 或 `--rtl-only`。
每个测试必须进程退出码为 0 且出现预期 PASS 标记；超时或 FAILED 都算失败。
构建可能需要数分钟；不要同时启动两份 make/sbt。

单项 RTL 最小复现（修改前保存的仿真器也接受同一形式的参数）：

```bash
sims/verilator/simulator-chipyard-RocketConfig +permissive \
  +loadmem=ssa/test.hex +max-cycles=5000000 +permissive-off ssa/test.riscv
```

`+verbose` 可打开提交跟踪。旧 SimDRAM 的 `+loadmem` 是反向字节序十六进制行文件，
**不能传 ELF**。`elf_to_hex.py` 配合 objcopy 自动生成正确文件；不指定 loadmem
则走较慢的 TSI 加载。`test.riscv` 的 entry 是 0x80000000，使用 HTIF 裸机启动，
不需要 pk、newlib 或重建 libgloss。测试池固定在 `[0x85c00000,0x88000000)`，
位于实际 RocketConfig 的 256 MiB DRAM 范围内。测试仅清零可达的桶；实际 loader
必须清零整个 1 MiB 字典并初始化元数据。

## 覆盖与预期

| 测试 | Spike | Rocket RTL | 必须满足的关系 |
| --- | --- | --- | --- |
| context | 显式调用同一份汇编参考例程 | 硬件自动拦截，无函数插桩 | 6 条记录、result=46、最终栈深度 0 |
| context 父路径 | 同上 | 同上 | parent_a/common 与 parent_b/common 的 id 不同 |
| context 重复 | 同上 | 同上 | A 调用 2 次，每次 common 2 次；B 调用 2 次，每次 common 1 次；复用既有 id |
| context 恢复 | 同上 | 同上 | common 返回后父函数读到 depth=1 |
| context 碰撞 | 同上 | 同上 | 两入口相隔 0x80000，强制同桶；记录 6 的 next=5，键仍可分别找到 |
| context 计数 | ISA 级计数参考 | 实际 RTL cycle/instret、CLINT mtime | common@A instret > common@B；父记录 instret > 对应子记录 |
| boundary | 显式参考 | 自动透明路径 | 258 层递归只分配 256 帧，完整展开后 depth/spill=0 |
| boundary 耗尽 | 显式参考 | 自动透明路径 | next_id 到 262144 时不越界写，error=1，返回恢复父上下文 |
| abi | 仅检查基础指令执行，禁用其软件监测 | 检查自动监测及 ABI | a0..a7、t2..t6 保持；x5 call/ret；普通 jr t1 不弹栈 |
| late | 不声称覆盖硬件银行切换 | 真实长延迟 divu 跨入微码 | 商写回用户 a6，寄存器校验通过 |
| disabled-reference | 参考程序本身 | SCBaseReg=0 跑参考程序 | 普通 Rocket 执行同一数据结构算法成功 |

计数是**包含子调用的累计值**，在每次返回时累加快照差。区间内含监测微码开销，
不能解释为已经扣除开销的纯应用指令/周期数。短函数的 mtime 差可以为 0；较长的
common 函数提供非零 time 检查数据。Spike 使用 ISA 级的 cycle/instret 模型，
数值不可与 RTL 周期逐项相等比较。测试没有人为生成 Cache/TLB 事件。

`analyze.py` 将 UART/HTIF 输出持久化为 JSON，按 parent id 还原调用树，并可用 ELF
符号命名。这是对文档 4.1/4.2 TODO 的最小可用实现；尚未实现 Linux 退出时自动
转储整个进程监测空间。

## 设计取舍与边界

- 保留已有影子整数寄存器和注入 ROM 的方案；改成一次一条指令完成/重放后再发射。
  不再以 watchdog 强制退出当作成功。
- SCStack 采用文档手写补充的 64 B x 256 帧，存放 entry 计数快照；与文档正文
  原先的 8 B 栈条目不同。字典 256K 桶、记录 128 B x 256K，整体预留 36 MiB。
- parent id 与完整 callee PC 分开保存，避免压缩指令入口仅半字对齐时丢掉 bit1。
  哈希具体公式为 `(parent ^ (callee >> 1)) & 262143`，链表比较完整键。
- time 取真实 RocketConfig CLINT mtime 地址 0x200bff8。此树没有直接可用的 time CSR
  实现；没有用 cycle 冒充 time。换平台时需要调整该地址。
- 长延迟整数写回保留发出指令的寄存器组归属；监测期间暂缓接收中断。
- 验收环境是单核 RV64GC、裸机 M mode、关闭中断。Linux loader/SP 自动预留、
  上下文切换、地址缺页、动态链接、调试入口、多核共享尚未验证。池必须事先映射。
- 尾调用、协程 pop+push、longjmp、异常展开不属于此版已验证的调用 ABI。
- 标量/流式/随机访存分类、Cache miss、TLB miss 和额外 HPM 选择器是设计后续阶段，
  当前七个扩展计数槽仅预留，没有宣称实现或仿真通过。

旧 `tests/test_ssa.c`、`tests/ssa_microcode.S`、`ssa_firmware/` 是接手时的历史原型，
使用不同布局；本次验收只使用这里的入口与 Rocket Chip 的 canonical microcode。
它们的原文件保留在工作树及 handoff 备份中，未与新 ABI 混用。

## 环境与保全

- Spike `/opt/riscv/bin/spike`: 1.1.1-dev；与 `/home/lxf/spike/riscv-isa-sim/build/spike`
  相同安装版本，源码 commit `065950a045d88f7558295df43416dfc25d1aeaf1`，未发现 SSA 补丁。
  顶层子模块中的 Spike 是另一份源码 `ce42f1b55a3fa5a3a522439b5370be2256f68862`。
- RISC-V GCC 15.1.0；Verilator 4.226；sbt 1.5.5；Scala 2.12.10；Chisel 3.5.2；
  FIRRTL 1.5.1；实际最终构建使用系统 Java 17。
- FESVR 使用 C++17 的 std::optional，因此仿真器默认 C++17；Conda Verilator 自带
  gnu++14 参数也需要被覆盖。Conda glibc sysroot 无法链接安装的 FESVR statx，
  所以上述命令选择系统链接器及系统 PATH。
- 两层交付分支均为 `ssa-hpm-completion-20261108`。
- Rocket Chip 最终交付：`986407bc6df8d2a67572250f1df9eb2c0edeacf9`；顶层 gitlink 固定到此提交。
- Chipyard 原始分支 `main` 比本地 `origin/main` 超前 5 个提交，全部保留。
- Chipyard 原始 HEAD：`c2391670d8e1cc62369cfc3e96b58a9a8cc94dda`。
- Rocket Chip 原始 HEAD：`23f5a64f6144cd3ffc7b25d490b48f5d019ee718`；原有三个本地提交
  `d047a8548`, `07a9c3fa8`, `23f5a64f6` 全部保留。
- 原始 RocketCore 未提交差异另存为 commit
  `539c3b10fee35fe0a2890083dd17c06688a704f8`，新修复在此基础上提交。
- `ssa/handoff/`（本地忽略）保存两仓库 bundle、原始 diff 及顶层未跟踪文件归档。
  初始检查、构建、故障跟踪日志在 `/tmp/ssa-handoff/`。

## 远端与后续发布

`.gitmodules` 确认 `Kimberley-Inti/SSA-HPM` 对应 Chipyard 顶层，
`Kimberley-Inti/rocket-chip` 对应 Rocket Chip 子模块。远端 rocket 的 SSA-HPM 分支
仍在 `1f200edb0`，与本地记录吻合。顶层 SSA-HPM 地址当前返回 Repository not found；
可能是私有仓库访问范围或地址变化，不能自动改推到另一仓库。

本机 gh/git 使用 jeffli999，rocket push dry-run 返回 403；已连接 GitHub App 对
rocket 的元数据显示另一个有写权限的会话，但它没有可用于本地 Git 对象传输的
认证凭据。未改变账号配置，未强推，未创建指向不匹配提交的 PR。

恢复相应仓库的 Git 写权限后，可执行：

```bash
git -C generators/rocket-chip push -u origin ssa-hpm-completion-20261108
gh pr create --repo Kimberley-Inti/rocket-chip --draft --base SSA-HPM \
  --head ssa-hpm-completion-20261108 --title 'Fix SSA-HPM microcode retirement and context attribution' \
  --body-file ssa/rocket-pr.md
# 先核实/恢复顶层 origin 地址与权限，再发布顶层：
git push -u origin ssa-hpm-completion-20261108
gh pr create --repo Kimberley-Inti/SSA-HPM --draft --base main \
  --head ssa-hpm-completion-20261108 --title 'Add reproducible SSA-HPM RTL and Spike validation' \
  --body-file ssa/chipyard-pr.md
```

顶层提交的 gitlink 固定到最终 Rocket Chip 交付提交；应先发布子模块，再发布顶层。

## 本次根因与设计映射

| 部件 | 接手状态 / 根因 | 本次结果 |
| --- | --- | --- |
| 流水线 / SCCodeTable | 微码 PC 在 decode stall 下侧带移位，重放时不能可靠对应真实流水级；CSR 是否只读还使用原 ibuf 的 rs1 | 单指令在途，使用真实 WB PC 与下一 PC 重定向；CSR 使用注入指令的 rs1 |
| 前端 | 私有 PC 的分支仍更新 BTB/BHT，watchdog 退出后触发 might_request 断言 | 私有代码不训练前端；取消静默 watchdog 成功回退 |
| 返回识别 | 任意 rd=0 的 JALR 都当成返回 | 只识别 rs1=x1/x5、imm=0 的返回；普通间接跳转不弹栈 |
| SCStack | 历史微码仅用 512 B / 32 B 帧，缺少容量处理 | 256 x 64 B，快照与溢出深度完整维护 |
| SCDict | 桶非空就复用，没有比较 callee/parent 或处理冲突 | 完整键匹配、链式哈希、重复调用复用、不同父上下文分开 |
| HPERecords | 只累计 cycle/instret；备用 C 固件与实际 ROM、测试布局不一致 | canonical 汇编统一 ABI，补 CLINT time；记录耗尽显式计错且不越界 |
| 长延迟写回 | 用当前 trap 状态选择 bank，调用前 divu 在微码内完成会污染影子组 | WB 保存发出者 bank；加载完成握手匹配 shadow bank 和目标寄存器 |
| SCBaseReg | 已有 CSR 0x800 | 复用；loader 初始化非零启用，写 0 关闭 |
| 构建 | C++11 / Conda gnu++14 与 FESVR std::optional 冲突；旧 sysroot 缺 statx | C++17 贯穿递归构建，使用系统链接工具链 |
| 仿真入口 | ELF 直接当作 +loadmem 十六进制文件会加载错误指令 | 提供正确 objcopy/hex 流程，自动检查退出码和 PASS |

关键 RTL 输出（完整结果见 `results/rtl-context.txt`）：

| ID | 上下文 | instret | 预期关系 |
| --- | --- | ---: | --- |
| 1 | parent_a | 14791 | 大于其子上下文 14452，包含子调用 |
| 2 | parent_a/common | 14452 | 4 次调用累计，恰为另一父路径的 2 倍 |
| 3 | parent_b | 7427 | 大于其子上下文 7226 |
| 4 | parent_b/common | 7226 | 2 次调用累计，与 ID 2 分开 |
| 5 | collision_a | 44 | 2 次调用复用 |
| 6 | collision_b | 22 | 1 次调用，同桶链 next=5 |

这些 instret 来自实际仿真，不是手工模拟的事件数。cycle/time 也逐条导出；它们随
缓存状态、平台 RTC 比例等变化，不使用跨模型精确数值相等作为验收条件。

最终 `verify.py` 记录 8/8 项通过，退出码均为 0。完整命令、耗时与 PASS 输出保存在
`results/summary.json` 及对应 `.txt`；实际 Scala/RTL/仿真器构建摘要在
`results/build.txt`，源码与可执行文件的 SHA-256 在 `results/built-source.sha256`。

另外，保存的旧仿真器配合原始 `tests/test_ssa.riscv` 及其正确 hex 加载文件，
也已实际复现同一 watchdog/Frontend 断言（约 89819 核周期）。该日志为
`/tmp/ssa-handoff/baseline-original-correct.log`，关键失败行已收录在 `results/failures.txt`。
原始测试使用旧 compact ABI，作为历史复现保留；修复后的验收入口采用上文统一 ABI。
