# 工作站清单维护

本目录保存 macOS 工作站的期望配置。以下命令均以 `~/.agents/workstation` 为工作目录；修改前读取该模块的 `AGENTS.md`。

## 配置与状态

| 路径 | 职责 |
| --- | --- |
| `Brewfile` | 直接安装的 formula、cask、tap、mas 和全局 npm 包意图 |
| `capabilities.json` | CLI 与应用的探测目标 |
| `androidrc` | 按本机 HOME 生成 `~/.androidrc` 的 SDK 路径模板 |
| `gradle/` | Maven 镜像、Wrapper 版本与校验值、JDK 路径模板 |
| `launchagents/` | GUI Flutter 镜像源脚本；LaunchAgent 由工作站入口生成 |
| `assets/` | 本项目维护的补全等资产 |
| `zsh/zshrc.snippet` | `~/.zshrc` 受管块的源文件 |
| `zsh/deploy.sh` | Shell 配置与资产部署脚本 |

自管技能位于 `~/.agents/skills/`，共用本目录声明和 `workstation/scripts/`。实际状态位于仓库外的 `~/.local/state/env/inventory.json`；`bin/workstation inventory refresh` 将观察结果原子写入该文件。失败分区标为 `unknown`，上一份成功观察值只供排障。

Brewfile 按人工确认的安装意图维护。探测结果用于对比差异；用 `brew bundle dump` 覆盖声明会丢失这一意图。

## 包声明

```sh
cd ~/.agents/workstation
scripts/declare.sh <包名> --section "终端与 shell"
scripts/declare.sh @scope/package --npm --section "开发工具"
scripts/declare.sh --remove <包名>
scripts/declare.sh --remove <包名> --npm
```

分类使用独占一行的 `# ==== 分类名 ====`，用于分组展示。新增分类加 `--new-section`；全局 npm 包加 `--npm`，与同名 formula/cask 分开识别。脚本按字典序插入，写前校验 Brewfile 语法，已声明条目幂等跳过。手工编辑遵循同样格式。

每条声明附简短用途说明。直接安装的长期工具纳入 Brewfile；依赖由包管理器解析；临时试用的工具在对账时决定是否纳管。第三方插件和二进制由上游包管理器供给，本项目资产放入 `assets/`。

`declare.sh` 只编辑声明。安装、升级和卸载需分别获得明确授权，按 [工作站部署技能](../../../skills/workstation-provision/SKILL.md) 执行。

## Shell 与 GUI 环境

Flutter 镜像变量由 zsh 和受管 LaunchAgent 提供给新启动的终端及 GUI 应用。Aliyun、Huawei、CFUG 镜像域名配置在 `NO_PROXY` 和 Java `nonProxyHosts`；镜像选择、JDK 和下载层次见 [Gradle 环境说明](gradle/README.md)。

`flutter_source mirror|official|status` 管理源选择及后续进程环境。切源后重启 IDE，再检查实际子进程；发布 Dart 包前选择官方源。代理软件的连接方式和开关由用户本人管理。

## 修改后核验

```sh
bin/workstation check
git diff -- macos/manifest/   # 在模块目录查看本目录差异
```

部署按授权选择 `bin/workstation apply codex|shell|android|gui` 中的一个组件，随后运行 `bin/workstation verify` 和 `bin/workstation inventory refresh`。声明变更与部署、验证分别记录；提交和推送按明确授权执行。
