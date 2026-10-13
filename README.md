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

## 能力导航与维护

从 [Codex 能力导航](codex/environment/INDEX.md) 找到任务入口；版本和实际安装状态通过本机 inventory 及具体工具核验。设备专属补充信息写入未提交的 `codex/environment/local.md`。

文档按 [no-negative-echo](skills/no-negative-echo/SKILL.md) 整理，以当前目标、职责和操作事实组织内容。修改技能时同时核对引用文档、调用示例和依赖入口；工作站声明变更后按对应组件验证。

```sh
# 在 ~/.agents 执行
python3 -m unittest discover -s skills/scripts -p 'test_*.py'
python3 -m unittest discover -s workstation/scripts -p 'test_*.py'
```

技能同步逻辑和非平凡部署逻辑修改分别运行上述对应测试。提交、推送和部署按明确授权执行。

GitHub Actions 在 macOS 上执行这两组隔离测试及 Shell 语法检查；测试使用临时目录，不部署运行器的个人环境。工作站测试覆盖受管块边界、资产冲突、权限检查、包声明事务和状态报告。
