<h1 align="center">Workstation</h1>

<p align="center"><strong>用于检查、部署和持续维护 macOS 开发工作站的期望配置。</strong></p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-macOS-000000?logo=apple&logoColor=white" alt="macOS">
  <img src="https://img.shields.io/badge/config-Homebrew%20%C2%B7%20Shell%20%C2%B7%20Android-555555" alt="Managed config">
  <img src="https://img.shields.io/badge/workflow-check%20%E2%86%92%20apply%20%E2%86%92%20verify-2F80ED" alt="Workflow">
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> ·
  <a href="#工作机制">工作机制</a> ·
  <a href="#定期检查">定期检查</a>
</p>

## 它是什么

这个模块保存 macOS 开发工作站的**期望配置**，覆盖 Homebrew、Shell、Android / Gradle、GUI 环境和 Codex 配置。

Git 负责保存可复现的配置声明与部署逻辑；当前机器的实际状态由本地 inventory 记录：

```text
~/.local/state/env/inventory.json
```

这样可以把“工作站应该是什么状态”和“当前机器实际是什么状态”分开管理，并通过统一命令完成检查、部署与验证。

## 快速开始

```sh
git clone https://github.com/zhouycheng/agents.git ~/.agents
cd ~/.agents/workstation

bin/workstation check
bin/workstation inventory refresh
bin/workstation inventory status
```

查看差异后，按组件部署需要的配置：

```sh
bin/workstation apply codex
bin/workstation apply shell
bin/workstation apply android
bin/workstation apply gui

bin/workstation verify
```

`check` 用于只读检查；`apply` 负责落位指定组件；`verify` 用于完成后的统一验证。

`check`、`verify` 和 `inventory status` 在检测到差异、缺失或未知状态时返回非零退出码；`inventory status` 也将过期快照视为待处理。`probe.sh --json` 的退出码表示探测是否成功，JSON 的 `status` 表示是否符合声明，`observation_status` 表示包探测完整性。

Shell 检查覆盖受管块、补全资产和目录权限。受管块的起止标记之外可保留用户配置；部署遇到归属不明的文件或链接时保留现场并报错。

## 工作机制

| 阶段 | 作用 |
| --- | --- |
| `check` | 读取当前工作站状态，检查配置与能力 |
| `apply <component>` | 部署指定组件，目前支持 `codex`、`shell`、`android`、`gui` |
| `inventory refresh` | 刷新本机状态快照 |
| `inventory status` | 查看 inventory 的更新时间与状态摘要 |
| `verify` | 验证已部署配置是否正确落位 |

工作站技能统一位于 `../skills/`。使用前读取本模块 `AGENTS.md`，工作目录设为 `~/.agents/workstation`。Codex 全局规则与稳定能力导航位于 `../codex/`。

Android / Flutter 工具升级后，使用下面的流程重新核验环境：

```text
android_env check → prepare → verify
```

同时核对 `macos/manifest/gradle/distributions.json` 与实际模板及官方 SHA-256。

## 定期检查

执行一次 `bin/workstation apply gui` 后，会安装本机 LaunchAgent，并立即刷新一次 inventory。之后按本地时间定期执行只读刷新：

```text
00:00  ·  06:00  ·  12:00  ·  18:00
```

inventory 超过 12 小时，或配置摘要发生变化时，会标记为 `stale`。需要依赖某项具体能力时，再对对应组件做一次定向核验。

分区状态使用 `ok`、`drift`、`missing`、`partial`、`unknown` 区分符合声明、存在差异、缺少能力、部分探测成功与探测失败。配置摘要同时覆盖 manifest、工作站入口和探测脚本，脚本修复后需要刷新快照。

日常维护可以保持下面这条路径：

```text
check → 查看差异 → apply 对应组件 → verify
```

需要随时确认机器状态时，执行：

```sh
bin/workstation inventory status
```

## 目录

| 路径 | 用途 |
| --- | --- |
| `macos/manifest/` | Brewfile、能力探测目标、zsh、Android / Gradle 与 GUI 环境声明 |
| `../codex/` | 部署到 `~/.codex` 的全局规则和能力导航 |
| `../skills/` | 工作站审计、供给、Android / Flutter、Shell 技能 |
| `scripts/` | Brewfile 探测、声明、验证脚本与本机状态生成器 |
| `bin/workstation` | 工作站检查、状态读取、组件部署与落位验证入口 |

本模块聚焦可复现配置与工作站状态管理。凭据、完整环境变量、Gradle 缓存和测试工程由本机环境管理；系统代理与 TUN 保持独立控制。
