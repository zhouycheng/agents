# 开发能力与核验入口

本页用于定位工具和维护流程。版本、安装状态、SDK 组件和服务状态以本机观察及任务中的实际调用为准。

## 查找能力

在 `~/.agents/workstation` 执行：

```sh
bin/workstation inventory status
bin/workstation inventory show
```

清单包含 `generated_at`、`config_digest` 和 `sections`。所需分区位于 `sections.packages`、`sections.capabilities`、`sections.shell` 或 `sections.android_flutter`；先核对分区 `status`。超过 12 小时或配置摘要变化时执行 `bin/workstation inventory refresh`；`unknown` 表示探测失败，上一份成功观察值只供排障。

| 需要确认的内容 | 入口 | 核验方式 |
| --- | --- | --- |
| 包的期望配置 | `macos/manifest/Brewfile` | `bin/workstation check` 对比声明与直接安装的包 |
| CLI 和应用 | `macos/manifest/capabilities.json`、`sections.capabilities` | `command -v <命令>`，再做任务所需的最小实际调用 |
| Shell 受管配置 | `macos/manifest/zsh/zshrc.snippet` | `bin/workstation verify`；交互行为按 Shell 技能验证 |
| Android / Flutter | `macos/manifest/gradle/distributions.json`、`sections.android_flutter` | `android_env check` 核对工具、模板和 Wrapper 缓存 |
| 自管技能 | [技能目录](../../skills/README.md) | 读取相应 `SKILL.md`，确认本会话已发现并可调用其依赖 |
| Codex 工具与 MCP | 本会话工具列表、宿主管理的配置 | 核对实际 schema、授权和后台服务，执行无副作用读取 |

清单的新鲜度与分区状态分别判断。命令入口存在只能证明可发现；账号权限、网络、后台服务以及目标输入仍需在使用时核验。

## 运行时与移动端

优先读取业务项目的版本约束、锁文件和构建配置，再定位本机工具。Homebrew 包意图由 Brewfile 管理；Rust 工具链按 rustup 和项目的 `rust-toolchain.toml` 核验。安装或升级按 [工作站部署技能](../../skills/workstation-provision/SKILL.md) 执行。

Android SDK 默认位置为 `~/Library/Android/sdk`，实际路径以 `ANDROID_HOME`、`~/.androidrc` 和 IDE 设置为准。日常 SDK 包管理使用 `android sdk`；许可证及诊断可使用 `sdkmanager`。SDK 平台、NDK、系统镜像、IDE 插件和 iOS Simulator runtime 均按项目需求单独核验。

首次部署、工具升级或 Wrapper 缓存回收后，按 [Android / Flutter 技能](../../skills/android-flutter-env/SKILL.md) 执行：

```text
android_env check → prepare → verify
```

准备前核对实际模板与官方 SHA-256；`prepare` 会下载分发包。Java、Kotlin 和 Flutter 保持原生创建入口。下载源、JDK 工具链和验收边界见 [Gradle 环境说明](../../workstation/macos/manifest/gradle/README.md)。

## 宿主与部署

`~/.codex/AGENTS.md` 和 `~/.codex/environment` 由 `bin/workstation apply codex` 链接到 `~/.agents/codex/`。自管技能在 `~/.agents/skills/` 维护；同步到其他已安装宿主的方式见 [技能目录](../../skills/README.md#宿主同步)。宿主自带技能、插件、认证和会话由宿主管理。

FreeCAD 等应用工具还需要目标应用和 RPC 服务就绪；CodeGraph 按项目初始化、同步后查询。浏览器、文档运行时和其他内置工具以当前会话提供的能力为准。设备专属路径可记录在未提交的 `local.md`。

## 操作边界

工作站检查以只读观察为起点。软件安装、组件部署、SDK 下载和权限变更按明确授权及对应技能执行。代理软件的连接方式和开关由用户本人管理；需要不同网络条件的验收时，记录当前条件并提供用户手动测试步骤。

构建、IDE 操作、模拟器或真机运行分别提供对应条件下的证据。inventory 和工具版本核验不能代替项目验收。
