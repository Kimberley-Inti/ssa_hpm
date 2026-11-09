# stage3-process-isolation

范围：单 hart、M-mode、两个独立物理监测池的调度协议与实际 Rocket RTL 验证。
基于已验收 stage2，而非 main；不等待 stage2 合并，不更新 main 或标签。
这不是 Linux 进程验收。两个任务使用独立 CPU 栈、同一入口和函数地址，通过
ECALL / 保存所有整数寄存器 / 切换帧 SP / MRET 交替运行。

## 设计审查与最小选择

主要依据本地设计 PDF 第 11–13 页的进程私有 36 MiB 池、SCBaseReg、SCStack、
SCDict、HPERecords 和第 13–14 页尚为 TODO 的导出/生命周期。HPM 参考 PDF
第 3 页区分 cycle、真实时钟 time、退休指令 instret。原 PDF 不随仓库分发。

| 分类 | 核对结果 | 本轮处理 |
| --- | --- | --- |
| 已有实现、缺少验证 | 换池后栈、字典、记录分离；当前 record 从栈中恢复 | 两个同地址函数、不同池，开放两层调用帧切换；恢复后正常返回 |
| 需要补齐实现 | 全局计数器快照不随任务停走，直接切池会把其他任务记入开放帧 | 调度器暂停/恢复 ABI，恢复时平移全部开放帧的三个快照 |
| 已有实现 | hart trap 深度、溢出封闭、trap 不入应用调用树 | 保持 stage2 原样，重跑 16 项回归 |
| 设计未明确 | OS 生命周期、调度计数边界、退出导出协议 | 明确状态机与采样边界，退出后读内存；暂不设计磁盘格式 |
| 后续依赖 | Linux loader/kernel/SBI、池固定与映射、用户态计数访问 | 本轮不宣称 Linux 验收 |
| 后续范围 | 多核/迁移、非局部展开、访存分类、Cache/TLB 归因 | 不扩展本轮事件模型 |

检查 FireMarshal：系统 Python 缺少 GitPython；改用已有 Conda Python 后通过 import，
启动仍报 `No riscv toolchain detected. Please install riscv-tools.`。默认 images 目录
只有 .gitignore；没有现成内核/根文件系统镜像，未找到 Linux cross GCC。sudo 提示
来自 FireMarshal 的 `sudo -ln true` 检测，并非本轮必须请求的提权步骤。进一步还缺少
内核调度/exec/exit 钩子、SBI/CSR 访问桥接，以及私有 ROM 在 U/S-mode 下的权限和
物理 CLINT 访问集成。安装一个 Python 包不能完成这些依赖，故选择实际 RTL 闭环。

## 状态归属与接口

`integration/ssa/process.h` 是可信单 hart 调度器接口；在 trap 内、屏蔽中断时调用。
不修改 Rocket RTL，因为 stage2 已将上下文状态存入所选内存池，并隔离了 trap
中的 JAL/JALR。不要把本软件协议误称为自动硬件进程切换或安全地址空间隔离。

- 进程：独立池、metadata、栈及所有帧、字典、记录；`SSAProcess` 描述符保存
  base、生命周期、暂停快照和累计排除量，未来可放进 task_struct。
- hart：SCBaseReg 是当前池选择器；trap 深度/溢出、全局三计数器属于 hart。
  不为进程恢复 trap 深度；正常 MRET 自然完成本次异常返回。
- 微码私有寄存器/执行 PC：硬件原有串行协议保护，scheduler 不在微码中抢占。
- 初始化：调用者分配独占且常驻的 36 MiB 区域，base 为排他上界，清零 metadata
  和完整 256K 桶，next_id=1。描述符 NEW、累计排除量清零；记录仅在分配时初始化。
  定向测试只会触达两个已知桶，故每轮清零这两个桶，避免无关模拟耗时。
- `ssa_pause`：RUNNING → PAUSED，校验当前 selector 与 hart trap 状态，采样三个
  全局计数器后关闭 selector；池内帧保持原状。
- `ssa_resume`：仅允许 selector=0、正常 trap 状态和 NEW/PAUSED。新池须无开放帧；
  拒绝 depth>256。暂停池计算 Δ=恢复采样−暂停采样，并给每个开放帧快照加 Δ；
  保留 spilled_depth、record ID 和全部累计记录，然后启用池。
- `ssa_exit`：仅 PAUSED 且 depth=spill=0 → EXITED；池仍归退出进程所有，可导出。
  EXITED 不可恢复或再次退出；释放内存由调用者在导出完成后负责。

调用者必须序列化调度、保证指针/池有效且不重叠，保护描述符和计数器配置。
本轮不实现虚拟内存保护、fork/exec、抢占中途恢复、FP/vector 上下文或自动资源回收。
`LEGACY_SWITCH` 只用于负对照：同一测试源码、相同调度过程，跳过快照平移。
两个 ELF 不是同一个二进制；硬件均为同一 stage2 Rocket 实现。

## 计数口径

记录仍是 inclusive：父记录包含子调用及快照区间的监测开销。没有任务切换的
原有用例不变，仍是六条记录和 14452/7226。

每种计数器分别在 pause/resume 中顺序采样。排除的是各自两次采样之间的区间，
包含另一任务及这段调度工作；切出 trap 入口到 pause 采样之前、resume 采样到
MRET 及后续微码的开销仍归原任务。恢复遍历帧本身的开销也保留。
不是精确的纯用户态时间；不会自动扣除所有内核或监测指令。time 来自真实 CLINT
MMIO mtime，低分辨率下短调用允许为零；cycle 受 cache/流水线变化影响，不能
要求短/长实验完全相等。无中断/重配的单 hart 下使用 unsigned 64-bit 模差值。

开发树实测：B 循环 7 次与 700 次，A 的 common 旧口径 instret 为 1486/4952；
新协议为 215/215。A 排除量 1314/4780，相差 3466，恰好解释旧口径串扰量。
父记录 instret 两次均为 314（包含 common 的 215）。cycle/time 实测见关系 JSON，
检查排除区间随 B 工作量增长；不把 cache 预热差异归为错误。完整输出在 evidence。

## 运行与验收

```bash
source ssa/env.sh
make -C ssa -j2 all
make -C sims/verilator CONFIG=RocketConfig -j8 LINK='/usr/bin/g++ -B/usr/bin/'
python3 ssa/verify.py --out-dir /tmp/stage3-regression
python3 ssa/verify_process.py --out-dir /tmp/stage3-process
# 从独立维护仓库执行：
python3 scripts/check_process_evidence.py /tmp/stage3-process --report /tmp/stage3-relationships.json
```

`verify_process.py` 的 legacy RTL 必须退出 42，错误 mask 仅 0x1000，代表串扰对照
成功；修复版本及 Spike 参考版本必须退出 0。Spike 没有 SSA 扩展，REFERENCE 完全
跳过 CSR 0x800 和监测断言，只验证整数上下文/栈切换、ECALL、MRET 和退出路径。
Rocket 版本才验证硬件透明调用/返回及实际池和计数。

独立重建依照 REPRODUCE.md：两个公共基线真实 fetch、原有 9 个 Rocket 补丁及
2 个 Chipyard 补丁干净应用，安装更新的独立测试/接口文件。Rocket expected_tree
保持 stage2 的 535c551af33cce20384ca2f8c3560ac5e70cdca4，不增加空补丁。
独立工作区重新编译 Scala、生成 RTL/构建 Verilator；可复用固定 SHA 的依赖和
VM 工具链缓存，不能复制开发工作树的模拟器冒充独立构建。最终结果以
`evidence/stage3/summary.json` 为准，baseline/development/independent 分开记录。


最终验收：开发树和独立重建均为原 16 项全部通过，加上 1 项 Spike 调度指令参考、
1 项旧协议 RTL 预期失败（退出 42、mask=0x1000）、1 项修复 RTL 通过（退出 0）。
独立构建退出 0；全部验证入口退出 0。两处定量关系检查均通过，A common 的
1486/4952 → 215/215 以及 3466 条串扰排除一致。两处原始六记录和 14452/7226
不变。源码 Chipyard 为 503d5ccdb6634a05f46181ecd23648cfbb4e61b8；Rocket 沿用
3f4ab938660454b101c67f6929bfebae5be1a138。原始完整构建日志及独立源文件哈希
随 evidence/stage3/independent 提供。开发树 make 复用了原有 RTL，独立重建才是
本轮重新编译 Scala/生成 RTL 的证据；依赖与工具缓存复用已明确记录。
