# SSA-HPM

Software Semantic Aware Hardware Performance Monitoring：为 RISC-V Rocket 的硬件性能
计数增加软件调用上下文。此仓库是项目的独立私有维护仓库，使用独立 Git 历史；
不包含 Chipyard/Rocket 完整源码树，也不替代原开发仓库的历史档案。

第一阶段版本为 `v0.1.0`，后续阶段继续在本仓库维护。开发记录、原始 SHA、新提交
映射见 [HISTORY.md](HISTORY.md)，可机器读取的版本在 [provenance.json](provenance.json)。

## 已实现

- 退休 JAL/JALR 驱动的调用/返回监测，维护父上下文和 SCStack。
- 256 层栈、256K 桶链式 SCDict、128 B HPERecords；完整键比较、复用和容量保护。
- 按上下文累计 cycle、instret、CLINT mtime；同一函数在不同父路径中分开记录。
- 修复微码 PC/重放/退休握手、前端更新、返回识别和跨微码入口的长延迟写回 bank。
- 补齐 C++17/FESVR/Verilator 构建兼容、正确十六进制 loadmem、自动验收与调用树 JSON 导出。

计数是**包含子调用和快照区间内监测开销的累计值**，未扣除微码开销。实际验收得到
6 条预期上下文记录；`parent_a/common`、`parent_b/common` 的 instret 分别为
**14452、7226**。短函数的 mtime 增量可为 0，不能用 Spike cycle 冒充 RTL 周期。

## 验证与边界

既有验收：实际 Scala 编译、RTL 生成及 Verilator 构建成功；3 项 Spike 参考测试、
5 项 Rocket RTL 仿真通过。Spike **没有 SSA 扩展**：它验证显式调用同一汇编例程的
参考数据结构行为，以及基础指令；Rocket RTL 验证透明硬件路径，包括嵌套、重复、
不同父上下文、返回恢复、哈希碰撞、258 次递归/256 帧容量、记录耗尽、x5 链接、
普通间接跳转、寄存器保护和延迟除法写回。

- [既有验收证据](evidence/acceptance/summary.json) 来自已验收交付，保留原始数值。
- [本次发布验证](evidence/publication/) 来自新下载的上游基线和补丁重建，独立标注。
- [复现指南](REPRODUCE.md) 给出准确基线、依赖、应用顺序和实际命令。

v0.1.0 验证平台是单核 RV64GC RocketConfig、裸机 M mode、关闭中断。后续阶段
分别增加 trap 与受控任务切换验证；本分支已通过真实 Rocket Linux 启动，进程监测
验收状态见第四阶段说明。完整 loader/exec、多核、任务迁移、非局部展开和后续
访存分类、Cache/TLB 事件仍未验证；七个扩展事件槽仅预留。

## 内容组织

- `patches/rocket-chip/`：按顺序应用的 11 个实现补丁（v0.1.0 为前 8 个），含 canonical 微码源码。
- `patches/chipyard/`：可获取的 Constellation 依赖固定与仿真器构建补丁。
- `patches/history/`：旧测试版本补丁，仅用于开发档案，不参与当前复现。
- `integration/ssa/`：原创测试与构建/分析脚本；由安装脚本放入 Chipyard 的 `ssa/`。
- `scripts/`：发布包安装、依赖复用、审计和验证入口。
- `evidence/`、`docs/`：已有验收及本次发布证据；不分发原始 PDF、二进制、备份或 bundle。

`microcode.S` 只在 Rocket 补丁中交付一次；安装器创建测试目录的相对链接。测试源码
只作为独立文件交付，不再重复嵌入 Chipyard 补丁。上游归属和许可见
[THIRD_PARTY.md](THIRD_PARTY.md) 及 `LICENSES/`。


## 开发档案与合并

原私有开发仓库与 Rocket fork 的访问和写权限已恢复；原主分支未改写。原本只在
本地的开发提交已经推送到明确命名的 archive/交付分支，完整远端核验记录见
`evidence/publication/original-commits.json` 和 `github-access.json`。

- [Rocket Draft PR](https://github.com/Kimberley-Inti/rocket-chip/pull/1)
- [Chipyard Draft PR](https://github.com/Kimberley-Inti/SSA-HPM/pull/1)，依赖前者。

这些 PR 仅为草稿，未合并。本独立仓库首次版本直接推送 `main` 和 `v0.1.0`，
不创建首次导入 PR，不创建公开 release，也不更改私有可见性。

本次发布验证也已完成：从公开上游基线重新获取、补丁干净应用、Rocket 最终 tree 和源码哈希一致，
在独立检出中重新编译 339 个 Rocket Scala 源文件、生成 RTL、构建新 Verilator 仿真器，
3 项 Spike 参考测试与 5 项 RTL 回归全部通过；6 条记录及 14452/7226 的 instret 再次一致。
依赖源码与工具链缓存复用原 VM，依赖 SHA 均核对；没有声称完成全新机器的冷启动安装。
详见 [本次发布验证汇总](evidence/publication/summary.json)。


## 第二阶段：stage2-trap-isolation

本轮修复陷阱处理函数被错误加入应用调用树的问题：旧 RTL 的处理函数入口为
`depth=3,next_id=4`，新实现保持应用的 `2,3`，并在嵌套异常和真实定时器 IRQ 返回后
恢复父上下文。只读 `0xcc0` 提供深度/溢出状态；第 256 层进入使监测保持关闭直到
复位，未完成记录必须丢弃。计数口径仍为区间累计，包含处理函数时间与监测开销。

开发工作树和独立公开基线重建均通过 **16 项测试：5 Spike 参考/指令测试、11 RTL
仿真**；其中原第一阶段 8 项保持通过，6 条记录及 `14452/7226` 不变。实际命令、
源码提交及模型范围见 [阶段说明](docs/STAGE2.md) 和
[分层验证汇总](evidence/stage2/summary.json)。本分支不发布新标签、不修改 main。


## 第三阶段：stage3-process-isolation

基于 stage2，补齐单 hart 调度器监测池暂停、恢复、退出协议。恢复时校正所有开放
调用帧的计数快照，排除其他任务的执行区间。两个实际整数 CPU 上下文在同一
Rocket hart 上交替运行，池分离、未返回帧恢复、退出结果读取和拒绝非法生命周期
均通过 RTL 测试。旧直接切池的 A.common.instret 为 1486/4952；新协议为 215/215。

这是 M-mode 受控调度闭环，尚非 Linux 进程集成。Rocket 源码依赖 stage2，未新增
RTL 修改；公开基线与原有九个 Rocket 补丁不变，新增接口和测试仅在 integration
交付一次。详见 [STAGE3](docs/STAGE3.md)；最终证据见
[evidence/stage3/summary.json](evidence/stage3/summary.json)。


第三阶段最终验证：开发树与独立公开基线重建均通过原 16 项回归及新增进程协议
检查（含旧协议预期退出 42 的负对照）。独立重编译 Scala、RTL 和 Verilator 通过。
Spike 仍无 SSA 扩展；Linux 集成尚未完成，详见阶段说明。

## 当前开发分支：stage4-linux-process-isolation

已在实际 Rocket/Verilator 上启动单 hart Linux 5.7-rc3，运行 PID1 并正常关机，
退出码为 0。新增 Sv39 PC 宽度修复、U-mode 池选择保护、私有 ROM 物理访存
和内核任务池生命周期/调度接口。全部 16 项第二阶段、3 项第三阶段及 5 项新增
裸机探针通过；真实 Linux 单进程监测、退出导出、权限检查和双进程抢占隔离均已通过，
统一验收 173 项检查通过，仿真正常关机并退出 0。

详见 [第四阶段说明](docs/STAGE4.md)、[启动证据](evidence/stage4/A-summary.json)
与 [Linux 复现入口](integration/ssa/linux/README.md)。本分支仅用于草稿审查，
不更新 main、不发布标签。

第四阶段完整证据见 [汇总](evidence/stage4/summary.json)。A 的短长 B 工作量
`instret` 差值：旧协议 `207962`，修正后 `20`；保留明确采样边界外的调度、
恢复和监测开销，不宣称精确用户态时间。两个真实 Linux 进程的开放帧、记录
隔离和退出均已在 Rocket RTL 上验证，完整 exec、多核及 Cache/TLB 仍待后续。

Stage5 development: [Linux exec lifecycle](docs/STAGE5.md). Runtime acceptance is pending the actual Rocket/Verilator execution.
