# 清单格式与维护

以下路径和命令以 `~/.agents/workstation` 为工作目录。包意图直接使用 Homebrew Bundle 的 Brewfile 语法，由共享脚本对账、编辑和验证。

## 格式

```ruby
# ==== 终端与 shell ====
brew "zoxide"                 # 智能目录跳转
cask "app-name"               # 应用
tap "owner/repo"              # 第三方 tap
mas "App Name", id: 123456    # App Store，需 mas
npm "@scope/package"          # 全局 npm 包
```

分类标记独占一行，格式固定为 `# ==== 名称 ====`；`declare.sh` 和 `probe.sh` 按这一约定解析。分类用于展示，安装范围按逐项确认的意图确定。行内注释说明用途。

直接安装的长期工具纳入 Brewfile，依赖交给包管理器解析，临时试用包在对账时决定。第三方插件由上游包管理器供给；本项目维护的资产放入 `macos/manifest/assets/`。

## 声明与观察

| 内容 | 载体 | 维护方式 |
| --- | --- | --- |
| 期望配置 | `macos/manifest/Brewfile` | 按确认的安装意图编辑，Git 保存差异 |
| 本机观察 | `~/.local/state/env/inventory.json` | 探测后原子更新，保留在仓库外 |

`brew bundle dump` 导出已安装状态，不能替代人工维护的期望配置。清单编辑与软件安装、卸载分别处理。

## 命令核验

```sh
brew bundle list --file=macos/manifest/Brewfile --all
brew bundle check --file=macos/manifest/Brewfile --verbose
```

`list --all` 枚举声明并校验语法，包名和安装状态仍需单独核验。安装命令会改变本机；按部署技能逐项取得授权。

## 脚本维护要点

### Shell 变量和字符

变量后紧跟非 ASCII 字符时写成 `${VAR}`，避免变量名解析歧义。`bash -n` 检查语法，实际分支仍需运行测试。macOS 的 BSD grep 字符范围按 POSIX 表达式处理；例如检查非 ASCII 后缀：

```sh
/usr/bin/grep -nE '\$[A-Za-z_][A-Za-z0-9_]*[^ -~]' scripts/*.sh macos/manifest/zsh/deploy.sh
```

### 直接安装与依赖

`brew list --formula` 包含依赖。对账复用 `scripts/probe.sh` 的观察结果；其 formula 集合依据 `brew info --json=v2 --installed` 的 `installed_on_request`，同时读取版本和安装时间。cask 和全局顶层 npm 包分别探测。

### 空 glob

zsh 默认在 glob 无匹配时失败。zsh 专属脚本可用 `(N)` 限定符；可移植脚本遍历前先检查文件是否存在。清理范围限定为本任务创建且已确认不再需要的文件。

### 宿主命令与权限

Agent 宿主可能在 PATH 前置命令包装器。先检查实际可执行入口、宿主权限和错误输出，区分命令失败与目标缺失；遵守宿主安全策略。系统命令的绝对路径需在本机核实，临时目录的创建和清理由共享脚本负责。

2026-09-24 的 WorkBuddy 环境曾将删除和改名命令转交包装器，改变回收站及补全缓存的行为。这是特定宿主的诊断记录；其他宿主需重新观察。操作成功后检查目标状态，不能只凭退出码断言文件已删除。

### 验证

非平凡部署逻辑修改运行工作站测试：

```sh
# 在 ~/.agents 执行
python3 -m unittest discover -s workstation/scripts -p 'test_*.py'
```

结合受管文件差异、`bin/workstation check`、`verify` 及 inventory 状态确认结果。
