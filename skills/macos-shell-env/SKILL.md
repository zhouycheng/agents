---
name: macos-shell-env
description: Deploy and troubleshoot this workstation project's zsh environment, completions, proxy functions and Flutter shell source while preserving unrelated user configuration.
---

# macOS shell environment

These skills belong to the unified Agent workspace. Before running workstation commands, read `~/.agents/workstation/AGENTS.md` and use `~/.agents/workstation` as the working directory. Relative manifest and script paths below are relative to that directory. Skills live in `~/.agents/skills`; Codex navigation lives in `~/.agents/codex/environment`.

The managed zsh block starts at `# ---- zsh 补全系统` and ends at `# ---- agents/workstation 受管配置结束 ----`. `macos/manifest/zsh/zshrc.snippet` is its source; content outside these markers is user-owned. The known legacy block is migrated by its pinned digest, preserving any suffix; other legacy content requires manual boundary review. Run `macos/manifest/zsh/deploy.sh --check` before deploying with `bin/workstation apply shell`; drift returns a nonzero exit code. Deployment validates syntax, keeps the existing single rollback backup, and preserves conflicting files and links. Check completion behavior after deployment; source only the completion section during automated checks so GUI and network environment stay unchanged.

Refresh the local inventory after changing the managed shell block so other projects see the new observation.

`proxy on|off|status` controls terminal variables and managed Gradle JVM options. It does not switch system proxy, TUN or an already-running IDE. `flutter_source mirror|official|status` controls shell and future GUI processes; restart an IDE to observe GUI changes. For a completion failure use [zsh-completion.md](references/zsh-completion.md), selecting only the relevant diagnostic section.
