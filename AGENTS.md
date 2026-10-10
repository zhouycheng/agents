# Agent workspace

本仓库是 Agent 技能、macOS 工作站期望配置和 Codex 全局规则的唯一自管来源。先判断任务属于哪个模块，再沿模块规则执行；不要把宿主自己管理的数据混进仓库。

| 模块 | 管理范围 | 入口 |
| --- | --- | --- |
| `skills/` | 自管技能的说明、脚本、资源及宿主同步流程 | [技能导航](skills/README.md) |
| `workstation/` | 本机期望配置、观察、组件部署与验证 | [工作站规则](workstation/AGENTS.md)、[工作站说明](workstation/README.md) |
| `codex/` | Codex 全局行为规则与能力导航 | [Codex 规则](codex/AGENTS.md)、[能力索引](codex/environment/INDEX.md) |

本文件约束整个仓库的维护方式。进入模块后继续读取最近作用域的 `AGENTS.md`、README 和任务对应的 Skill；更具体的规则负责定义该模块的命令、配置和验收。`codex/AGENTS.md` 部署后约束 Codex 的运行行为，不替代本仓库维护规则。

## 开始任务

1. 先查看当前分支、工作区状态和已有差异；区分本任务修改与用户已有内容，不覆盖、重置或顺手清理无关改动。
2. 确认目标文件的管理者和权威来源。改技能时以 `skills/` 为源；改工作站期望配置时以 `workstation/macos/manifest/` 为源；改 Codex 全局规则和导航时以 `codex/` 为源。
3. 读取目标模块的局部规则、相关 Skill、调用脚本和验收入口，再决定修改范围。使用能力索引定位工具；版本、安装和运行状态以本机观察及任务中的实际调用核验。
4. 让改动落在声明它的唯一来源中，检查调用示例、引用文档、部署链接和受影响的验证流程。

## 文档与提交

在本仓库新增、修改或整理任何文档时，必须先按 [`no-negative-echo`](skills/no-negative-echo/SKILL.md) 的流程确定已接受的目标状态、读者需要的事实及必要边界，再检查正文、标题、文件名、链接和最终交付面。这个要求也适用于 `AGENTS.md`、README、技能说明、参考资料、提交说明及 PR 文案。安全、准确、兼容、审计或明确比较所必需的限制照实保留。

提交标题使用 `<type>: <中文说明>`：类型使用英文 Conventional Commit 风格，例如 `feat`、`fix`、`refactor`、`docs`、`test`、`build`、`ci` 或 `chore`；冒号后的说明使用简体中文，准确概括当前改动。示例：`docs: 完善工作站维护指引`、`fix: 修复清单刷新路径`。专有名词、路径和代码标识符可按原样保留。提交正文如有需要也使用简体中文，说明背景、改动和验证，不把会话中被放弃的方案写成结果。

按主题组织提交：同一方面的一组改动放在一次提交；彼此独立的方面分开提交。提交前检查完整 staged diff，只纳入本任务所属文件，并复核提交信息。提交、推送、创建 PR、部署及其他外部持久状态变更都需要用户明确授权；这些动作分别确认，不互相推定。

## 仓库与本机管理

### 工作站配置

工作站命令以 `~/.agents/workstation` 为工作目录。改动前读取 `workstation/AGENTS.md` 和对应技能；从只读的 `bin/workstation check` 与 `bin/workstation inventory status` 开始。配置声明只在 `workstation/macos/manifest/` 维护，机器观察写入仓库外的 `~/.local/state/env/inventory.json`。当 `generated_at` 超过 12 小时、`config_digest` 变化、所需分区为 `unknown` 或任务依赖某项能力时，运行 `bin/workstation inventory refresh` 并核对对应分区。刷新只更新观察记录，不等于部署，也不证明目标应用或当前进程可用。

安装、升级或配置组件前，先核对期望与实际差异及影响范围。按用户授权选择单个组件部署，再运行相应 `verify` 并刷新 inventory。Android / Flutter 变更按工作站规则核对模板、可信校验值及 `android_env check → prepare → verify`。Brewfile 记录安装意图，不代表批量安装授权。

### 技能和 Codex 宿主

技能源文件在 `skills/`。向其他宿主同步时使用 [技能目录说明](skills/README.md) 中的受管流程，先核对目标宿主和已有文件；宿主自带技能、插件、凭据、缓存和会话仍由宿主管理。Codex 规则和能力导航在 `codex/`；按授权在 `~/.agents/workstation` 执行 `bin/workstation apply codex`，随后运行 `bin/workstation verify`。不要直接修改宿主私有数据库或会话存储。

### 系统盘点与清理

用户明确要求系统级盘点时，从只读清单和任务相关的实际状态开始，按来源区分仓库声明、机器观察、宿主管理内容、用户数据、缓存和临时产物；只扫描与目标有关的范围，并在结论中区分已验证事实和待核实项。

清理前确认路径、归属、用途和影响。只删除本任务创建且确认不再需要的内容，或用户明确纳入范围的目标；归属不明的文件、共享缓存和用户数据先保留并报告。不要默认创建额外备份或快照，也不要用宽泛通配符扩大删除范围。不得操作代理软件的连接方式或开关。迁移不增加旧路径兼容链接。

## 验证与收尾

验证按改动类型选择，不用无关的大范围测试替代定向检查：

- 文档改动检查 `git diff --check`、修改后的本地链接和最终文件内容。
- 技能同步逻辑修改运行 `python3 -m unittest discover -s skills/scripts -p 'test_*.py'`。
- 非平凡工作站部署逻辑修改运行 `python3 -m unittest discover -s workstation/scripts -p 'test_*.py'`。
- 工作站部署或迁移完成后，核对受管链接、对应组件的 `verify` 和 inventory 时效。

任务结束时检查 Git 状态及最终交付物，清理本任务创建且确定无用的临时内容。报告实际完成、验证结果和仍未验证的事项；清单、静态链接或命令退出码不能单独证明部署、运行或外部验收完成。
