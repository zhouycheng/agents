# Agent workspace

本仓库是全局 Agent 能力的唯一自管来源。`skills/` 管技能，`workstation/` 管本机期望配置与部署，`codex/` 管 Codex 全局规则和能力导航。

修改工作站前读取 `workstation/AGENTS.md` 和对应技能；所有工作站命令以 `workstation/` 为工作目录。配置声明只在 `workstation/macos/manifest/` 维护；实际状态位于 `~/.local/state/env/`，不进 Git。

`codex/AGENTS.md` 是部署给 Codex 的全局规则；本文件是仓库维护规则，两者保持各自作用域。技能统一在 `skills/` 维护，宿主自带技能、插件、认证、缓存和会话仍由宿主管理。

保持原有用户文件与无关配置。不要操作用户代理软件的连接方式或开关。迁移不维护旧路径兼容入口。Commit、push、仓库设置和部署按用户明确授权执行。

撰写或整理面向用户、项目或外部发布的文档时，使用 `skills/no-negative-echo/SKILL.md`。从已确认的目标状态和必要事实组织内容；安全、准确、兼容、审计或明确比较所需的限制照实保留，并复核标题、文件名、链接和最终交付面。

迁移或部署后验证受管链接、工作站 check/verify、清单时效；修改技能同步逻辑时运行 `python3 -m unittest discover -s skills/scripts -p 'test_*.py'`。非平凡部署逻辑运行 `python3 -m unittest discover -s workstation/scripts -p 'test_*.py'`。
