# 开发与工具能力

以下内容来自 2026 年 9 月 20 日的本机实测（系统重装后的恢复基线）；Android/iOS 工具链于 2026 年 9 月 24 日复核。CLI 统计以 `command -v` 能找到入口为准；MCP 统计来自 `~/.codex/config.toml`。

## 概览

| 类型 | 数量 | 当前状态 |
| --- | ---: | --- |
| CLI 命令 | 56 | 均可在当前 `PATH` 中找到（含 `codegraph`、`firecrawl`、Android SDK 工具与 CocoaPods） |
| Codex MCP | 6 | 5 个启用、`computer-use` 停用，见下表 |
| Skills | 72 | `~/.agents/skills/` 全部就位 |

## CLI 清单

| 类别 | 数量 | 命令 |
| --- | ---: | --- |
| Shell、源码和终端 | 22 | `rg`、`git`、`gh`、`git-filter-repo`、`jq`、`bat`、`lazygit`、`brew`、`curl`、`rsync`、`ssh`、`openssl`、`zip`、`unzip`、`starship`、`tmux`、`yazi`、`zoxide`、`eza`、`btop`、`htop`、`codegraph` |
| 运行时和包管理 | 19 | `uv`、`uvx`、`python3`、`pip3`、`node`、`npm`、`npx`、`ruby`、`bundle`、`gem`、`rustc`、`cargo`、`rustup`、`java`、`javac`、`dart`、`flutter`、`android`、`pod` |
| 构建与 Android 平台工具 | 11 | `make`、`cmake`、`ninja`、`xcodebuild`、`swift`、`clang`、`clang++`、`lldb`、`adb`、`emulator`、`sdkmanager` |
| 网页检索 | 1 | `firecrawl` |
| 数据 | 1 | `sqlite3` |
| 文档提取 | 2 | `pdftotext`、`pdftoppm` |

## 关键运行时

- Rust：由 rustup 官方安装管理（`~/.cargo`、`~/.rustup`），stable 1.98.1，支持 `rust-toolchain.toml` 钉版本。
- Flutter：3.47.5 stable，Homebrew Cask 管理（`/opt/homebrew/share/flutter`），内置 Dart 3.13.4 与 DevTools。升级用 `HOMEBREW_NO_AUTO_UPDATE=1 brew upgrade --cask --greedy flutter`，不运行 `flutter upgrade` 绕开包管理器。
- Java：Homebrew OpenJDK 21.0.12.1，由 `openjdk@21` 管理；另有 JDK 17.0.20.1 供 Android CLI 模板编译，Gradle 仍运行于 JDK 21；`java` 与 `javac` 在当前终端可用。
- Node：Homebrew 管理 node/npm/npx；npm 全局前缀为 `/opt/homebrew`，全局包在 Brewfile 声明对账。
- Firecrawl CLI：`firecrawl` 1.24.4，通过 npm 全局安装，已纳入 Brewfile。

## Android / iOS 移动端工具链（2026-09-24 复核）

| 项目 | 当前状态 |
| --- | --- |
| Android Studio | 2026.1.4 Patch 1，位于 `/Applications/Android Studio.app` |
| Flutter / Dart IDE 插件 | Dart 509.0.0、Flutter 96.0.0 已从 Android Studio Marketplace 安装并加载；新 Flutter 项目被识别，`main.dart` 可从 Android Studio 运行到 Medium Phone AVD |
| Flutter / Dart SDK | Flutter 3.47.5 stable、Dart 3.13.4，由 Homebrew Cask 管理 |
| Android SDK 根目录 | `/Users/zhou/Library/Android/sdk`；`ANDROID_HOME` 指向此目录，不设置已弃用的 `ANDROID_SDK_ROOT` |
| Android 命令 | `adb` 37.0.1、`sdkmanager` 22.0、Android CLI 1.0.16406183；Android CLI 由 Homebrew Cask 管理，`android info` 已指向上述 SDK |
| 已装 SDK 包 | Platform Tools 37.0.1、Emulator 37.1.11、Build Tools 36.0.0、Android Platform 37.0、Sources 37.0 |
| Android 模拟器 | Medium Phone AVD 已创建，Android 17 / API 37.0 Google APIs ARM64；`flutter emulators` 可列出。当前是否连接取决于 AVD 是否启动 |
| Android 许可证 | 已全部接受；`flutter doctor -v` 通过 Android toolchain 检查 |
| CocoaPods | 1.17.0，Homebrew 管理；`flutter doctor -v` 已检测到 |
| Xcode / iOS Simulator | Xcode 27.0 位于 `/Applications/Xcode.app`，`xcode-select` 指向其 Developer 目录；当前没有可列出的 Simulator runtime。用户暂不需要 iPhone 模拟器，未安装 runtime |
| Flutter / Android 下载源 | Gradle Wrapper 由 `android_env check|prepare|verify` 从华为镜像校验并准备标准缓存，原生创建入口保留原始 Wrapper URL；Android/Gradle 插件与 Maven Central 优先使用阿里云；Pub 与 Flutter engine 用 CFUG 镜像。受管 LaunchAgent 为 Finder/Dock 启动的应用设置镜像变量并绕过镜像域名代理，`flutter_source mirror|official` 控制新启动进程 |

Android SDK 的日常包管理使用 `android sdk`；保留 `sdkmanager` 仅用于许可证、兼容性及故障诊断。不要运行 `android init` 安装额外 skills/resources；SDK 与命令入口分别由 Homebrew 和标准 `~/Library/Android/sdk` 管理。

`flutter doctor -v` 已确认 Flutter/Dart、Android SDK、Homebrew JDK 21、Android 许可证、代理和网络资源可用。唯一报告项是 Xcode 无法枚举已安装的 Simulator runtimes；这与当前不安装 iOS 模拟器的决定一致。

2026-09-24 用新建的 Android Studio Java、Kotlin 模板和 Android-only Flutter 模板验证了 Android 开发闭环：Gradle 镜像冷下载/构建通过；Java 与 Kotlin 项目在 Android Studio 中运行成功，清理 build 后关闭、重开并重新运行成功；Flutter 项目在 Android Studio 中完成 Pub Get、运行成功，执行 `flutter clean` 后关闭、重开、Pub Get 并重新运行成功。三类应用都安装到 Medium Phone API 37 模拟器。本次 Gradle 冷构建移除了 shell 代理变量并禁用了 Java system-proxy 选择；按用户要求没有关闭 macOS 系统代理或 Clash TUN，因此不能据此保证关闭 TUN 后也能访问镜像。具体镜像、校验和与操作边界见 `~/.agents/workstation/macos/manifest/gradle/README.md`。

环境探测还发现 `/opt/homebrew/share` 对组可写，zsh 补全探测会告警。受管配置带 `compinit -i -C` 以免 shell 启动阻塞；按本机权限边界，由用户本人执行 `chmod go-w /opt/homebrew/share` 后再运行 `probe.sh --brief` 复核。

## Codex MCP（当前配置）

| 名称 | 入口 | 状态和用途 |
| --- | --- | --- |
| `node_repl` | Codex 内置 Node.js REPL | 启用；执行受信任的本机 JavaScript 工具调用 |
| `computer-use` | Codex Computer Use 客户端 | 停用（`enabled = false`） |
| `context7` | `npx @upstash/context7-mcp` | 启用；查询库和框架文档 |
| `lark_mcp` | `npx @larksuiteoapi/lark-mcp` | 启用；飞书能力，待用户 Access Token 授权后可调用 |
| `codegraph` | `codegraph serve --mcp` | 启用；预索引代码知识图谱，token 高效读项目；每个项目首次使用前跑 `codegraph init` 建图 |
| `freecad` | `uvx freecad-mcp` | 启用；需 FreeCAD 应用打开且 RPC Server 运行中 |

MCP 显示为已加载只说明配置会被 Codex 读取。真正调用前还要确认相应应用、网络、账号和后台服务已经就绪。

## 已知边界

重装后有明确决策或暂缓的项，任务涉及时应先与用户确认而不是假定存在：

- **iOS Simulator 暂不启用**：Xcode 已安装，但当前没有已安装的 Simulator runtime；用户目前只要求 Android 模拟器，不下载 iOS runtime。
- **Android 模拟器已配置**：Medium Phone API 37.0 AVD 已创建，Android 许可证已接受；已装 NDK 28.2.13676358 与 CMake 3.22.1；额外版本按项目需要准备。
- `scrcpy`、`apktool`、`jadx` 未安装；当前模拟器目标不需要它们。
- **ffmpeg 按决策不装**：framelean 项目自包含 ffmpeg，系统级安装没有必要。
- **容器与数据客户端未装**：`docker`、`kubectl`、`psql`、`redis-cli`、`mysql`、`mongosh`、`duckdb` 等；需要时 `brew install` 即可。
- **文档转换链未装**：`pandoc`、`qpdf`、`soffice`、`magick`、`tesseract`、`d2`、`glow` 等；需要时 `brew install`。
- **其他 Agent CLI 不在 PATH**：`codex`、`claude`、`playwright` 缺失；Firecrawl CLI 已全局安装并由 Brewfile 管理，Codex 桌面版内置 CLI 仍可用。
- **SSH 密钥未重建**：`ssh` 命令可用，但 `~/.ssh` 为空，SSH 远端登录和 git SSH 协议暂不可用（gh 走 HTTPS 正常）。
- FreeCAD 及其 MCP 未安装，`uvx freecad-mcp` 调用前需先恢复该链路。

## 当前运行条件

- 终端为 Ghostty；`~/.zshrc` 加载 uv、cargo、starship、zoxide，提示符带时间戳，`history -i` 可查历史时间。
- `zoxide` 已初始化，`z 关键词` 智能跳转可用。
- `~/.codex/AGENTS.md` 与本 environment 目录软链自 `~/.agents/codex/`，修改后提交到 `~/.agents` 仓库保持同步。

项目自己的运行时、包管理、构建、测试和格式规则优先。每次调用会改写文件、外部系统或账号数据的工具前，都要重新确认作用域和当前状态。

2026-09-25：受管 Wrapper 清单、准备命令、JDK 17 编译工具链与代理开关修复已部署。常规网络下的三入口样例构建与运行已通过；最终关闭系统代理和 TUN 的验收由用户自行进行，因此仍未验证。测试项目、隔离缓存和下载目录里的旧 `test_demo` 已按用户要求清理。升级后运行 `android_env check → prepare → verify`，版本漂移必须重新核验模板和官方校验值。
