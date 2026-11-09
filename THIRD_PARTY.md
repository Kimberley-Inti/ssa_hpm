# 来源、版权和许可

本发布仓库不包含上游完整源码树或上游 Git ancestry。统一 diff/format-patch 中的
上下文和删除行仍来自原源码，并不因以补丁交付而改变其原有版权和许可。

| 材料 | 来源 / 适用说明 |
| --- | --- |
| Rocket Scala 及其补丁上下文 | chipsalliance/rocket-chip，基线 `44b0b8249279d25bd75ea693b725d9ff1b96e2ab`；源文件头指向 Berkeley 和 SiFive 许可证 |
| Chipyard 构建文件及补丁上下文 | ucb-bar/chipyard，基线 `2d03d10837fc1a7569d10ae2c91c8132c7fee77d`；仓库 BSD-3-Clause 与 SiFive 许可 |
| Constellation 依赖 | 仅记录仓库 URL / gitlink SHA，不在此仓库复制其源码 |
| 历史 SSA 测试补丁 | 原 Kimberley-Inti/SSA-HPM 项目提交中的新增测试；原始 commit/作者字段见 HISTORY.md |
| 微码、测试、验收/分析/安装脚本 | SSA-HPM 项目新增文件；验收阶段由项目维护者与编码助手协作形成，来源与后续发布新增文件分别记录 |
| 验收结果 | 原验收提交中的文本、JSON 与源/产物哈希；不包含被哈希的编译产物 |

上游许可全文分别保存在 `LICENSES/`，保留其原有版权、条件和免责声明；Rocket
SiFive 文件包含 Apache-2.0 文本。本仓库没有为全部项目原创材料另行选择统一的
开源许可证；普通私有仓库用于项目归档与协作。后续公开或统一授权由维护者决定，
不会以此说明替换上游许可。

来源审计中特别发现：原验收工作树的 `ssa/env.sh` 被 `env.sh` 忽略规则排除，实际
不在 `375068b6` 提交中。本次显式收录该复现辅助文件，并将其作为发布整理新增
材料记录；其他被安装的测试脚本按原提交字节保留。canonical 微码只存在于 Rocket
补丁里，不另复制一份容易失配的源码。

排除材料：两份本地设计 PDF（仅核对，不分发）；`ssa/handoff/` 的原始/交付 bundle、
归档与备份；整个 Chipyard/Rocket 源树、第三方子模块源码、二进制和生成 RTL；
凭据与账号配置；未纳入当前统一 ABI 的工作树原型（如未跟踪的 ssa_firmware、旧
微码汇编和旧 C 测试）。这些原文件保留在原开发目录/本地备份中，未被删除或改写。
历史提交中已纳入版本控制的旧测试只以 `patches/history/` 保存一次。
