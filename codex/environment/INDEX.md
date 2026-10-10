# 本机能力导航

这里帮助 Codex 找到工具说明。实际状态以 `~/.local/state/env/inventory.json` 为准：先读 `generated_at`、`config_digest` 和所需分区的 `status`；过期、unknown 或即将依赖某项工具时，执行定向核验。`~/.workstation-config/bin/workstation inventory status` 可快速查看新鲜度，`inventory refresh` 只读本机并更新清单。

| 任务 | 说明 |
| --- | --- |
| 开发工具、Android/Flutter 和 Codex 集成 | [development.md](development.md)（带日期的核验快照与使用边界） |
| 文档、PDF、表格 | [documents.md](documents.md) |
| 公开研究 | [research.md](research.md) |

受管探测目标在 `~/.workstation-config/macos/manifest/capabilities.json`，期望安装包在 `Brewfile`；二者用途不同。私有或设备专属补充信息可放在未提交的 `~/.codex/environment/local.md`。
