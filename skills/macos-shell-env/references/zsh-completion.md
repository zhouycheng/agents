# zsh 补全诊断

仅在补全或交互启动故障时读取。本页路径以 `~/.agents/workstation` 为工作目录；受管源为 `macos/manifest/zsh/zshrc.snippet`，用户的 `~/.zshrc` 前置内容保持其原有归属。

## 先确认初始化

```sh
/bin/zsh -i -c 'whence -w compdef'
rg -n 'compinit|fpath' ~/.zshrc /etc/zshrc
/bin/zsh -i -c 'print -r -- ${+_comps[brew]}'
```

`compdef: none` 表示当前进程未加载补全函数；先检查初始化链。`${+_comps[brew]}` 为 1 表示 brew 补全已注册。嵌套 shell 可能提前展开变量，复杂探针使用脚本文件传递。缓存文件缺失只是线索，结合进程状态判断。

确认 `fpath` 在 `compinit` 前包含 `~/.local/share/zsh/site-functions` 和 Homebrew 的 `share/zsh-completions`。

## 插件与加载顺序

| 插件 | 作用 | Homebrew 路径 |
| --- | --- | --- |
| zsh-completions | 补全定义 | `share/zsh-completions`，加入 fpath |
| fzf-tab | Tab 候选选择器，依赖 fzf | `opt/fzf-tab/share/fzf-tab/fzf-tab.zsh` |
| zsh-autosuggestions | 行内建议 | `share/zsh-autosuggestions/zsh-autosuggestions.zsh` |
| zsh-syntax-highlighting | 命令高亮 | `share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh` |

这些路径相对于实际 Homebrew prefix，包声明位于 Brewfile。受管加载顺序为：

```text
fpath + zstyle → compinit → fzf-tab → autosuggestions → syntax-highlighting
```

fzf-tab 和 autosuggestions 在初始化后加载；syntax-highlighting 最后加载。其他修改同一批 ZLE widgets 的插件可能冲突，接入前核对当前插件组合。

修改受管配置时编辑 snippet，按授权部署并验证；直接改生成块会造成声明与本机差异。

## 交互验证

复用现有验证器：

```sh
/bin/bash scripts/verify.sh
```

它包含启动 stderr、pty 握手、补全与 widget 注册、建议文字回显、资产及目录权限检查。阅读 pass、skip 和 fail；skip 保留其未验证范围。

定向观察可用：

```sh
/usr/bin/script -q /dev/null /bin/zsh -i -c 'print -r -- ${+_comps[brew]}'
```

ZLE widgets 需要真实交互环境。Widget 数量会随插件版本变化；最终还需在目标终端观察 Tab、建议接受和高亮行为。当前受管建议策略为 `(history completion)`；使用已知历史前缀验证可重复的建议，不以任意前缀为空直接判故障。方向键显示绑定到 `forward-char` 时仍可能经过建议插件包装。

## fzf 启动与测试历史

`fzf --zsh` 的按键集成仅在交互式 TTY 中加载：

```zsh
[[ -t 0 && -o interactive ]] && source <(fzf --zsh)
```

`-i` 本身不能证明 stdin 是 TTY。对照检查非 TTY 启动 stderr 与 pty 中的 fzf widget；`can't change option: zle` 是需要核对这一加载条件的线索。该集成可能位于用户前置配置，修改前确认归属。

测试历史在 shell 启动后用 `fc -R <测试文件>` 注入，并先设 `SAVEHIST=0`，避免写入用户真实历史；macOS 系统 zshrc 可能重设 HISTFILE。

## 缓存与权限

受管初始化使用 `compinit -i -D`。每次启动执行权限审计，`-i` 忽略不安全目录；`-D` 在内存中初始化补全，不读取旧 dump 或写入新缓存。新补全会在下次初始化时重新发现，代价是每个交互式 shell 都需要扫描补全目录。`probe.sh` 和 inventory 的 Shell 分区独立报告权限异常。

`compdump` 先写入 `.zcompdump.<host>.<pid>`，再改名为主缓存。2026-09-24 的 WorkBuddy 宿主曾限制补全目录读取并拒绝临时文件改名，报告 `Brokered host rename source refused by file policy`；这是特定宿主的记录。当前故障需检查实际 PATH、权限、缓存及 stderr，遵守宿主策略。

清理缓存临时件前逐项确认文件归属和写入状态，避免删除另一个 shell 正在使用的文件。验证器将已知宿主噪音标为 skip 并保留消息。

出现 `insecure directories` 时先查看 `bin/workstation check` 的具体路径。修正 Homebrew 目录权限由用户本人执行，Agent 不代跑 chmod；修正后再次核验。系统工具的路径与可执行性也需确认，macOS 超时工具若缺失则使用现有 `gtimeout` 或工具自己的超时选项。
