# Agents

个人全局 Agent 工作空间：统一管理技能、工作站能力和 Codex 全局规则。

| 目录 | 职责 |
| --- | --- |
| [skills/](skills/README.md) | 所有自管技能，包括工作站审计、部署和环境维护技能 |
| [workstation/](workstation/README.md) | macOS 期望配置、能力探测、组件部署和验证 |
| [codex/](codex/) | Codex 全局规则与能力导航，部署到 `~/.codex` |

## 安装和使用

```sh
git clone https://github.com/zhouycheng/agents.git ~/.agents
cd ~/.agents/workstation
bin/workstation check
bin/workstation inventory refresh
bin/workstation inventory status
```

先读取差异，再按用户明确决定部署对应组件并验证。工作站入口为 `~/.agents/workstation/bin/workstation`，支持 `check`、`inventory refresh|show|status`、`apply codex|shell|android|gui` 和 `verify`。

技能入口保持 `~/.agents/skills/`。需要向其他已安装宿主同步时，在交互式终端运行 `python3 ~/.agents/skills/scripts/sync.py`，选择目标宿主；同步保留宿主的真实目录和文件。

## 维护边界

Git 根目录只在 `~/.agents/`；所有模块都是普通目录。工作站声明只在 `workstation/macos/manifest/` 维护。本机观察结果保存在 `~/.local/state/env/`，凭据、缓存、插件和聊天记录由宿主管理。

`AGENTS.md` 管本仓库维护，`codex/AGENTS.md` 管部署给 Codex 的全局行为。工作站技能执行前定位 `~/.agents/workstation` 并读取其规则。

## 历史来源

本仓库沿用 skills 仓库，以普通迁移提交调整目录，再通过不压缩的 Git subtree 导入 workstation-config 完整提交历史。原有提交保留，不强推或改写历史。

导入前的工作站文件历史仍使用原仓库路径；追溯时可从导入提交的第二父提交查看。GitHub 的 Wiki、Issue 和 PR 不随 Git 历史导入。旧工作站的 [Wiki](https://github.com/zhouycheng/workstation-config/wiki) 保留作历史资料；后续配置维护以本仓库为准。
