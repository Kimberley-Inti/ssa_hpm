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

已验证平台是单核 RV64GC RocketConfig、裸机 M mode、关闭中断。Linux 生命周期和
loader/SP 集成、多核、地址缺页、调试/异常展开、协程/尾调用以及后续访存分类、
Cache/TLB 事件尚未验证；七个扩展事件槽仅预留。内存池必须事先映射且可访问。

## 内容组织

- `patches/rocket-chip/`：按原开发顺序应用的 8 个实现补丁，含 canonical 微码源码。
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
