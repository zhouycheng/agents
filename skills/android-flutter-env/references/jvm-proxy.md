# Android / Flutter 下载链与 JVM 代理诊断

以 [受管 Gradle 环境](../../../workstation/macos/manifest/gradle/README.md)、`distributions.json` 和目标进程为依据。工具、模板、IDE 菜单和网络端点变化时重新核验。

## 按下载阶段定位

| 阶段 | 受管办法 | 排查入口 |
| --- | --- | --- |
| Gradle Wrapper ZIP | `android_env prepare` 按原始完整 URL 建立标准缓存，从华为镜像下载并核验官方 SHA-256 | `check`、`verify`；项目 Wrapper URL、`bin/all` 和缓存身份 |
| Gradle 插件、Google Maven、Maven Central | 用户级 init script 为 Android/Flutter 构建及 Flutter included build 提供阿里云镜像 | 所选 `GRADLE_USER_HOME` 中的 init script、缺失构件坐标和尝试地址 |
| Pub、Flutter engine | zsh 与 LaunchAgent 为新启动进程提供 CFUG 镜像变量 | `flutter_source status`、IDE 和 Flutter 子进程实际环境 |
| SDK、NDK、AVD 镜像、Marketplace | SDK Manager 和 IDE 自身下载链 | 目标地址、有效代理配置、TLS 与下载错误 |

日常入口为 Android Studio 内置向导、`android create` 和 `flutter create`。Gradle init script 在 Wrapper 分发下载之后运行；首先报分发 ZIP 连接失败时，查工具身份和分发缓存。旧项目明确选择改写 Wrapper URL 时使用 `gradle_mirror --check|--apply`，并核对新的缓存身份。

首次部署、升级或缓存回收后执行 `android_env check → prepare → verify`。`check` 仅读本地状态；未知模板或缺少官方可信 SHA-256 时停止准备。普通 shell 启动只加载环境。

## 核对进程中的代理层次

| 层次 | 观察内容 |
| --- | --- |
| 当前终端 | `proxy status`、shell 代理变量、受管 `GRADLE_OPTS` |
| JVM 与 Gradle 配置 | `JAVA_OPTS`、`JAVA_TOOL_OPTIONS`、`_JAVA_OPTIONS`、项目及用户 `gradle.properties` |
| 系统网络 | `scutil --proxy`；用户提供的 TUN/VPN 状态及可读取的路由信息 |
| GUI / IDE | IDE HTTP Proxy 设置、登录 shell 环境读取器、Flutter/Gradle 子进程 |

`proxy on|off` 管理当前终端环境及受管 JVM 选项；外部 JVM 参数保留原有归属。`NO_PROXY` 和 Java `nonProxyHosts` 只匹配列出的域名。判断网络路径时同时核对 JDK 的 `java.net.useSystemProxies`、IDE 和所用 HTTP 客户端。

Finder/Dock 启动的进程从 GUI 环境继承变量，JetBrains 还可能读取登录 shell。受管 `INTELLIJ_ENVIRONMENT_READER` 分支为环境读取器提供直连参数。调整源后重启 IDE，并检查实际子进程收到的环境。

代理软件的连接方式和开关由用户本人管理。Agent 只读观察；需要另一网络条件的验收时提供手动步骤，等用户建立对应状态后记录条件和结果。

## 诊断顺序

1. 记录失败构件或 ZIP、地址、下载阶段及完整错误；区分连接失败、TLS、下载截断和校验失败。
2. 运行 `android_env check`，对比实际工具、模板、原始 Wrapper URL 和分发缓存。
3. 检查选定 Gradle home 的 init script、JDK 路径及目标子进程；SDK 和 Marketplace 单独核验。
4. 需要冷下载证据时使用任务专用隔离缓存，保留用户共享缓存。Wrapper 分发、Maven 依赖和 Pub 缓存分别记录。
5. 复核 IDE 创建、构建、安装和运行；记录网络状态、缓存条件、设备与实际下载地址。验收缺口按原状态报告，保持 TLS 校验。

## 诊断记录的适用范围

2026-09-24 的 Agent shell 曾在 `flutter doctor` 中报告 `Connection terminated during handshake`；同一任务在不同进程环境下结果不同。宿主注入的环境需与用户终端、IDE 子进程分别比较。

同日 SDK Manager 曾报告 `IO exception while downloading manifest`，Marketplace 插件也出现下载中断。它们提供对应下载层的故障线索；当前许可证和插件状态仍需重新读取。IDE build 从 `Android Studio.app/Contents/Resources/build.txt` 取得完整 `AI-` 标识，Flutter 插件 XML id 为 `io.flutter`。
