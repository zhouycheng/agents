# 清单维护规则

清单是这套机制里**唯一需要人手维护**的东西。本文件说明怎么维护，5 分钟读完。

## 文件构成

| 路径 | 作用 | 谁维护 |
|---|---|---|
| `Brewfile` | Homebrew 管辖的全部包（formula / cask / tap / mas / npm） | **人** |
| `androidrc` | Android CLI 的 SDK 根目录模板；部署时按本机 HOME 生成 `~/.androidrc` | **人** |
| `gradle/` | Android/Flutter Maven 镜像、Gradle Wrapper 工具与 JDK 路径模板 | **人** |
| `launchagents/` | Flutter 镜像源脚本；GUI Agent 由 `bin/workstation apply gui` 按本机路径生成并加载 | **人** |
| `assets/` | 无主资产：有上游的一律不进 | **人** |
| `zsh/zshrc.snippet` | `~/.zshrc` 补全块的唯一真相源 | **人** |
| `zsh/deploy.sh` | 把 snippet 对齐进 `~/.zshrc`、把 assets 落位 | 脚本 |

本目录是环境清单的唯一维护位置：`~/.agents/workstation/macos/manifest/`。四个工作站技能统一位于 `~/.agents/skills/`，共用此处声明和 `workstation/scripts/`。

Flutter 的 `PUB_HOSTED_URL` 与 `FLUTTER_STORAGE_BASE_URL` 同时用于终端和从 Finder/Dock 启动的 Android Studio。LaunchAgent 在每次登录时为新启动的 GUI 进程设置 CFUG 默认源，并将 Aliyun、Huawei 与 CFUG 镜像域名放进 `NO_PROXY`，避免配置的本机代理不可用时镜像流量仍被送进代理；Gradle init script 也为这些域名加 Java `nonProxyHosts`。`flutter_source mirror|official` 会同步当前终端与 launchd 的后续进程环境。已经打开的 IDE 不会自动改变环境，切源后需重启 IDE。发布 Dart 包前执行 `flutter_source official` 并重新启动使用 Flutter 的 GUI 应用，避免把发布请求送到镜像。

**实际状态不在本目录。** `scripts/probe.sh --json` 从 Homebrew、npm 和本机配置读取观察结果，`bin/workstation inventory refresh` 将结果与 CLI、应用、Android/Flutter 状态一起原子写入 `~/.local/state/env/inventory.json`。失败的分区标为 `unknown`，保留上一份成功观察值供排障。声明与实际分离；不要用 `brew bundle dump` 回写 Brewfile。

Homebrew Bundle 也支持 npm 全局包，写成 `npm "package-name"`。脚本对账只比较 npm 全局顶层包；修改 Brewfile 由 Git diff 留痕，不生成额外备份副本。

## 加一个包

```bash
../scripts/declare.sh <包名> --section "终端与 shell"
../scripts/declare.sh @scope/package --npm --section "开发工具"
```

- 分类必须已存在；要新建分类加 `--new-section`（**不要**硬塞进最接近的那一段——分类失真比缺分类更糟）
- 全局 npm 包显式加 `--npm`，与同名 formula/cask 分开识别
- 脚本会在分类内按名称字典序插入，写前用 `brew bundle list` 校验语法
- 已声明则幂等跳过

手工编辑也允许，但必须放进已有的 `# ==== <分类> ====` 段内。

## 减一个包

```bash
../scripts/declare.sh --remove <包名>
../scripts/declare.sh --remove <包名> --npm
```

**只改声明，不卸载。** `--npm` 可限定只移除同名 npm 声明。是否真的卸载需在对账协商中单独确认——移除声明和卸载软件是两件事。

## 写行内注释

每条尽量带一句说明用途：

```ruby
brew "zoxide"                  # 智能 cd
```

清单会长期存在。半年后你只会看到一个包名，想不起为什么装了它——而"想不起为什么"正是下次清理时误删的原因。

## 分类约定

分类用注释标记，只用于**分组呈现**，不控制安装：

```ruby
# ==== 终端与 shell ====
```

不要用分类做什么"按 profile 一键装齐"——那是对账机制要避免的语义。

## 三类不该进清单的东西

1. **有上游的第三方代码**（zsh 插件本体、下载的二进制）→ 交给包管理器，不进 `assets/`
2. **作为依赖被装入的包** → 不需要声明，`brew bundle` 会自行解析依赖
3. **一时试验的包** → 先用着，下次对账时再决定要不要纳入

反过来：**你自己写的、没有上游的脚本应当进 `assets/`**。它没有上游可竞争，丢了就没了。

## 改动之后

```bash
../scripts/probe.sh          # 确认没有意外差异
git -C ../../.. diff -- workstation/macos/manifest/  # 复核
```

提交由你决定，脚本不会自动 commit。
