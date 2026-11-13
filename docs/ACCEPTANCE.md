# SSA-HPM 项目验收清单

本清单是项目完成度的判定入口。证据范围严格限定为实际运行的配置和调用约定；“某阶段通过”不等于全部设想都已实现。页码为本地原始设计 PDF 的物理页码（共14页），HPM 参考共13页。第七阶段重新渲染查看中文、表格和手写修订；原始 PDF 不随项目发布。

## 需求类别与判定层次

- **原始核心要求**：原文第一阶段明确的层次调用上下文与 cycle/time/instret，以及上下文和性能数据的保存、离线还原。导出格式、OS细节在原文中留为 TODO，由当前受测适配具体化。
- **已采用的适配**：36MiB 固定物理池、64B 栈帧、显式启停、单 hart、可信内核、采样区间扣除、开放帧标记、版本化串口转主机文件。这些不是原文已经定义的 OS ABI，也不能冒充通用 Linux 产品。
- **原文后续数据流目标**：第12页明确列出标量/流式/随机分类及 Cache/TLB 事件，但明确第一阶段仅做三个基本计数器。它们是完整数据流愿景的后续需求；未实现的部分不能因当前单事件通过而标为完成。
- **可选扩展**：多核迁移、所有厂商事件、非局部展开、自动符号化UI等，原文没有给出相应协议和验收标准，当前单 hart/LIFO profile 不以它们为完成前置条件。

## 需求—实现—证据映射

| ID / 类别 | 来源 | 要求或边界 | 实现与实际证据 | 当前判定 |
| --- | --- | --- | --- | --- |
| C01 核心 | 设计p1、p4 | 动态调用栈构成层次上下文，同一被调函数在不同父路径下不同 | Rocket JAL/JALR通知、microcode；stage1 summary、stage6/golden-contexts.json：6记录、14452/7226 | 已验收，限支持的调用ABI |
| C02 核心 | 设计p8–9 | SCStack维护调用/返回，默认256层 | 64B帧（手写修订）保存record和快照；stage1 boundary实际258层展开、stage2 trap/IRQ | 已验收；溢出帧按既定spill规则，不是任意展开 |
| C03 核心 | 设计p9–11 | SCDict键为(parent,callee)，链式碰撞、记录只增不删、0保留 | 完整PC、256K桶、ID链；stage1碰撞/复用/容量保护RTL；stage6同父非零重复事件 | 已验收 |
| C04 核心 | 设计p11–12，HPM p3 | HPERecords包含cycle/time/instret | 128B记录，64位三计数；time取CLINT及同源SBI time；stage1/4/6原始日志 | 已验收；父计数包含子调用和区间内开销 |
| C05 核心与适配 | 设计p8、p11–13 | 软件透明地维护上下文；预留36MiB、SCBaseReg、SCCodeTable | Rocket私有ROM，无逐函数插桩；独占固定物理池和显式prctl替代通用loader/SP调整；stage4 U/S权限探针 | 函数监测透明已验收；通用不修改应用的自动启用/loader方案未验收 |
| C06 适配 | 设计p6进程背景、p12–13；stage2语义 | trap不生成应用调用上下文、返回恢复 | trap depth/overflow、U-only通知、IRQ屏蔽私有ROM；stage2实际陷阱与中断、stage4实际Linux | 已验收；不声称过滤trap事件计数 |
| C07 适配 | 设计p11–13生命周期未细化；stage3/4 ABI | 单hart任务独占池，开放帧跨抢占恢复，排除采样暂停区间 | task descriptor、S/R、所有开放帧平移；stage4/5/6真实A→B→A，stage6校正7与负对照1130 | 已验收；不是硬件缓存分区 |
| C08 适配 | 设计p13–14 TODO；stage5规则 | exec旧/新会话区分、失败返回旧会话、退出导出 | post-exec_mmap hook、session/self_exec_id、ENOENT；stage5 37检查、stage6 ABI2旧64/新128/失败128 | 已验收，限pre-commit ENOENT/非多线程/非setuid |
| C09 核心 | 设计p13 §4/p14 §4.1–4.2 TODO | 将性能数据与上下文存入文件并离线重建 | stage7冻结会话→16记录批次→主机JSON；parent/callee与开放帧RID足以还原树，无须转储哈希桶 | 已验收：真实Rocket/Linux退出0，25项导出检查；见evidence/stage7/summary.json |
| C10 核心导出边界 | 设计p10–11记录空间；stage7用户要求 | 全部已分配记录，而非32条截断 | 最多262143有效ID；逐批映射/拷贝2KiB；实际41条/3块、零/少量/开放帧；最大容量算术与故障注入单列 | 已验收：真实41条/3块、2条、0条及开放帧；不声称真实串口跑满262143条 |
| D01 后续数据流目标与适配 | 设计p12，HPM p4–5 | 可编程事件随软件上下文记录 | stage6现有DTLB accepted PTW requests，selector0x1002、40位；实际源→HPM→上下文→Linux导出 | 一种TLB事件已验收；按增量发生区间，非请求发起者标签 |
| D02 原文后续目标与规则1适配 | 设计p12 §3.1(2)；[CLASSIFICATION.md](CLASSIFICATION.md)补充未定义细节 | 标量/流式/未识别规律访存分类 | 退休整数load/store虚拟地址，按epoch/RID/PC/op/width维护16项FIFO历史；2次预热、重复地址/固定步长/非规则；63行独占计数；4项RTL、独立重建4项、WB重放/异常参考核对及首份真实Linux STOP导出已通过 | 进行中：尚待原Linux仿真完整生命周期、双任务抢占及正常关机验收；不能据首份结果标为已验收 |
| D03 原文后续目标与明确适配 | 设计p12 Cache miss/TLB miss；stage8原生事件定义 | Cache与TLB访问行为扩展，至少一种真实Cache事件 | stage6 DTLB与stage8原生D$ miss条目0x202：实际完成的D-cache TL A事务，40位；5项RTL及真实Linux39/69/24检查、41条分批导出，见stage8 summary | 一种Cache事件缺口已关闭；按声明的原生事务区间口径，非退休load唯一miss；全部Cache/TLB种类仍可选 |
| X01 可选 | 原文未给多hart协议；stage2–6显式排除 | 多核隔离、任务迁移、计数epoch | 内核拒绝SMP；只验证单hart | 未实现/未验证；不属于当前受测profile |
| X02 可选/需规范 | 设计p4/p6的LIFO调用返回；没有非局部展开协议 | longjmp/C++异常/协程/信号非局部跳转 | 不自动重建栈；普通trap返回不同于软件栈展开 | 未验收；若支持这些程序，必须先定义恢复或可靠失败状态 |
| X03 可选产品化 | 设计p13–14离线分析TODO | 符号化、可视化、压缩/二进制流、guest文件/网络服务 | 树ID和计数的主机JSON校验是本轮基础；已有裸机analyze.py可用ELF命名 | 通用GUI、guest磁盘API非本轮要求 |

## 不可混淆的计数语义

cycle/instret/time顺序沿用内存ABI（原文列举顺序不是内存布局）；三者64位。ABI2第四字段在record+40/frame+32，为DTLB accepted PTW requests，40位模运算。DTLB源无U/S/trap过滤，已注册增量可能跨调用/返回边界；按实际采样区间归属。父记录包含子调用。调度仅扣除S到R，不扣除S之前、R之后的kernel/restore工作及本任务恢复产生的TLB事件。开放帧不伪造成正常返回，不补未完成激活的部分计数。counteren是访问控制，不是源事件过滤（HPM p5）。

## 第七阶段的完成门槛

1. 保留第六阶段分支/PR/源码，固定实际完整SHA（用户文字中的维护SHA少了一位，实际为`1c48e93b0055e92a565eb455a057c1e45618d81c`）。
2. 新Rocket/Linux镜像实际导出41条已分配记录，ID/父/地址/四计数元数据可核验；同样接受2条、0条和带开放帧的不完整会话。
3. 冻结和池所有权持续到结束标记；STOP显式导出不重复，exec/exit先导出再释放；主机验证池复用顺序。
4. 解析器检测缺块、重复、截断、校验值、越界、跨会话混用；真实逻辑状态不完整与传输损坏分开表示。
5. 受影响stage6事件、stage5生命周期、stage4抢占回归在本轮真实Linux执行；不重复未修改的Rocket RTL构建。最大容量与错误注入明确标为主机覆盖。
6. 当前补丁在独立检出可应用，工具链/模型/镜像/日志哈希、命令、退出码和原始日志均记录；远端Draft PR回读核验。

## 后续“必做”与可选扩展

- **要宣称完整原始数据流愿景完成**：D03的一种真实Cache事件已按stage8声明口径完成；剩余必做是定义并实现D02三类访存，提供分类边界与端到端证据，不能以已有Cache/TLB计数替代分类。
- **要宣称通用Linux软件透明监测完成**：必须补不改应用的启动/exec启用策略、动态链接边界及相应测试；当前显式prctl测试环境是已采用的有限适配。
- **当前单hart受限profile**：C01–C10/D01与上述门槛已按stage7实际覆盖收尾，统一证据为evidence/stage7/summary.json；完整传输24会话/87记录，25/70/37/179项本轮真实Linux检查通过。未修改的低层RTL/Spike采用已核验历史证据，不伪称重跑。
- **可选扩展**：多hart/迁移、所有厂商Cache/TLB事件、非局部展开、perf共享、多线程/setuid/复杂exec、最大容量长时串口压力、GUI/guest文件服务。它们未在原文给出当前profile的可执行要求，不擅自提升为本轮阻塞。

相关来源与证据入口：[第一阶段](accepted-delivery.md)、[stage2](STAGE2.md)、[stage3](STAGE3.md)、[stage4](STAGE4.md)、[stage5](STAGE5.md)、[stage6](STAGE6.md)、[历史](../HISTORY.md)、[ABI](../integration/ssa/linux/ABI.md)。

第七阶段验收补充：41条实际记录解除原32条上限，3块及END校验/树匹配通过；
最大262143条边界、缺块/重复/截断和校验错误是主机逻辑覆盖，未跑满容量串口。
同一次真实Linux执行包含STOP/零记录/开放帧/两种ABI的exec及池释放、DTLB暂停
扣除与旧协议负对照。在第七阶段当时，原设计数据流愿景的D02/D03及通用透明Linux的C05限制仍保留。
第八阶段已完成D03的一种真实Cache事件（源码、RTL与真实Linux证据见STAGE8.md及evidence/stage8/summary.json）；下一轮仅推进D02分类规范和实现。

第八阶段收尾：新模型实际重跑29项既有低层测试（23RTL/6Spike参考），5项Cache
RTL通过；独立安装的新测试镜像复跑5项Cache检查时明确复用已核验新模型。
实际Linux为一轮通过的修正镜像完整执行，另保留一次用户态前中止的准备启动；
不能仅以该模拟器的退出0判断通过。最终正常关机、退出码和全部检查已满足。
Cache按增量采样区间而非请求发起者归因，包含PTW/内核/微码/非缓存事务；
真实父子关系、开放帧恢复、暂停扣除、旧协议负对照及exec/完整导出均通过。
当前单hart显式启用profile的D03收尾不代表严格退休load miss计数或全事件集合完成。
