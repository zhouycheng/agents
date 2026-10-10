# Android / Flutter 下载链与 JVM 代理诊断

本参考页先说明 **2026-09-25 这台 Mac 的当前配置**，再保留 2026-09-24 的历史代理/插件故障。版本、IDE 菜单、网络客户端和下载端点都可能改变；先看 `~/.agents/workstation/macos/manifest/gradle/README.md` 与 `distributions.json`，再检查实际进程，勿照旧案例预设全局 JVM 代理。

## 当前默认方案：按下载阶段定位

| 阶段 | 当前受管办法 | 排查入口 |
| --- | --- | --- |
| Gradle Wrapper 分发 ZIP | `android_env prepare` 按工具模板的原始完整 URL，从华为镜像下载、对照官方固定 SHA-256，交给官方 Wrapper 建标准缓存 | `android_env check`、`verify`；检查项目 `gradle-wrapper.properties`、原始 URL、`bin/all`、对应缓存身份 |
| Gradle 插件与 Google Maven / Maven Central | 用户级 `init.d/10-codex-android-mirrors.init.gradle` 让阿里云镜像优先；包含 Flutter Gradle included build | 检查 init 脚本是否真正进入选定 `GRADLE_USER_HOME`，记录缺失构件坐标与尝试地址 |
| Pub 与 Flutter engine | CFUG 镜像变量由 zsh 和受管 LaunchAgent 提供给新启动的终端/GUI 应用 | `flutter_source status`，检查 Android Studio/Flutter 子进程收到的实际环境，改动后重启 IDE |
| Android SDK/NDK、AVD 系统镜像、Marketplace 插件 | SDK Manager 与 IDE 自身网络链路，**不属于**上述 Maven/Pub 镜像 | 分别看目标下载地址、IDE/SDK Manager 有效代理设置与实际错误 |

三种日常入口是 Android Studio 内置向导、`android create`、`flutter create`，无需 `flutter_new`。Gradle init 脚本在 Wrapper 分发下载**之后**才运行；新工程若首先报 `services.gradle.org/distributions/...` 连接失败，先查 `android_env` 的版本身份和分发缓存，不能仅调整 Maven 仓库。旧项目明确要求改变自己的 Wrapper URL 时才用 `gradle_mirror --check|--apply`；这会改变标准缓存身份。

首次部署、工具升级或缓存回收后：

```sh
android_env check
android_env prepare
android_env verify
```

`check` 仅读本地状态，不下载；缺分发与工具/模板漂移要分开处理。未知版本没有从 Gradle 官方发布信息取得可信 SHA-256 时停止，不用镜像自报校验值替代。普通 shell 启动不自动联网准备。

## 四层代理状态，不能混为一谈

1. `proxy on|off|status` 控制**当前交互终端**及其子进程的 shell 代理变量和本工具管理的 `GRADLE_OPTS`。新终端默认 `on` 是用户偏好；受管镜像域名按 `NO_PROXY` / Java `nonProxyHosts` 绕行。`off` 清理本工具的旧代理参数，但保留其他 JVM 参数与引号。
2. `JAVA_OPTS`、`JAVA_TOOL_OPTIONS`、`_JAVA_OPTIONS` 和项目级/用户级 `gradle.properties` 可能另带代理参数。`proxy status` 可提示部分残留，但不应自动抹去他人设置；要逐项确认来源和实际进程参数。
3. macOS 系统代理用 `scutil --proxy` 检查；TUN/VPN 需看代理应用状态和实际路由。`proxy off` 不改变这两层。`nonProxyHosts=*.aliyun.com|...` 只绕过匹配域名，不能当作“所有主机直连”；完全直连状态必须分别取证。
4. Finder/Dock 启动的 Android Studio 从 GUI/launchd 环境启动；JetBrains 还可能读取登录 shell。当前 IDE HTTP Proxy 采用 `No Proxy`，受管 `INTELLIJ_ENVIRONMENT_READER` 分支给环境读取器直连参数，LaunchAgent 提供 Flutter 镜像变量。修改后退出 IDE 并重开，检查实际 Flutter/Gradle 子进程，而不是只看配置文件或 `launchctl getenv`。

Java 网络代理不应概括成“JVM 绝不读取系统代理”：具体程序、JDK 的 `java.net.useSystemProxies`、IDE 自身代理设置和底层 HTTP 客户端会影响行为；shell 的 `HTTP_PROXY` 也不是所有 Java 客户端都自动读取。判断应以目标版本、有效 JVM 属性、进程环境与同一 URL 的对照结果为准。当前镜像优先方案避免为了正常构建而长期给全部 Java 进程设置本机代理端口。

## 有证据的诊断顺序

1. 先记录失败**构件/ZIP、地址、阶段和错误**。Wrapper、Gradle 插件、Pub、SDK manifest 与 Marketplace 不互相代替。
2. 记录工具和模板版本，运行只读 `android_env check`；对照项目 Wrapper URL 与 `distributions.json`，确认是否版本漂移、缺缓存或 URL 身份不同。
3. 查选定 `GRADLE_USER_HOME` 的 init/toolchain 落位和 IDE 子进程；针对 SDK/Marketplace 另查其自身代理设置。必要时比较同一目标直连与代理路径，但区分连接失败、TLS 握手失败、下载截断和校验失败。
4. 用空隔离 Wrapper 缓存验证镜像准备；再用单独的冷 Gradle 依赖/Pub 缓存验证后续下载。已有 SDK、热缓存或模拟器运行成功只证明对应条件。
5. 如需验证系统代理与 TUN 均关闭，先告知用户并遵守其当次授权；记录开关、DNS/路由、进程参数和缓存条件。失败时保留“未通过”，不禁用 TLS，也不暗中恢复代理来通过测试。

Agent 宿主可能自行注入 `HTTP_PROXY` / `HTTPS_PROXY`，且网络策略与用户登录终端不同。2026-09-24 曾出现 `flutter doctor` 在 Agent shell 内报 `Connection terminated during handshake`，清除宿主代理变量后诊断结果改变。宿主测试不能直接代表用户终端；同一问题要核对真实目标进程。

## 2026-09-24 的历史案例与时效性

早期 `sdkmanager --licenses` 在 manifest 下载阶段报 `IO exception while downloading manifest`；当时同一目标的 JVM 显式 HTTP(S) 代理参数对照曾改变结果，后续 Android 许可证已接受。这个案例证明**那次 SDK Manager 下载链路**受代理配置影响，不证明所有 JVM 工具必须写 `JAVA_TOOL_OPTIONS`，也不证明当前无代理镜像方案需要相同设置。许可证状态以当前 `sdkmanager`/`flutter doctor` 结果为准，不用历史中间输出推断准确数量。

Android Studio Marketplace 的 Dart/Flutter 插件也曾遇到下载中断、TLS 或 PAC 配置问题。历史排查发现 IDE build 要从 `Android Studio.app/Contents/Resources/build.txt` 读带 `AI-` 的完整值；Flutter 的插件 XML id 是 `io.flutter`，旧任务曾把它与显示名及其他编号混淆。2026-09-25 环境文档显示 Dart 509.0.0、Flutter 96.0.0 已加载，但历史记录对最终是 Marketplace 内安装还是 ZIP 安装的表述不一致，故只确认当前加载状态，不把安装途径写成事实。插件下载是 IDE 市场自身链路，不能由 Gradle/Pub 镜像通过来推出它能冷下载。

旧版建议曾把 `JAVA_TOOL_OPTIONS`、用户 Gradle `systemProp.*` 和 IDE Manual proxy 作为三条长期默认配置通道。在目前这台机器的目标设计中，它们不是日常默认方案；尤其全局 JVM 代理容易让已关闭的本机代理端口成为新故障。若未来有明确必须走代理的 SDK/Marketplace 目标，应先定位该下载阶段、核对当前 IDE/JDK 文档和进程状态，只对所需范围临时设置并复测，不把参数写进项目 `gradle.properties` 污染其他人。
