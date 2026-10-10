---
name: macos-shell-env
description: Deploy and troubleshoot this workstation project's zsh environment, completions, proxy functions and Flutter shell source while preserving unrelated user configuration.
---

# macOS shell environment

The managed zsh block starts at `# ---- zsh 补全系统`. `macos/manifest/zsh/zshrc.snippet` is its source; earlier lines in `~/.zshrc` are user-owned. Run `macos/manifest/zsh/deploy.sh --check` before deploying with `bin/workstation apply shell`; it validates generated syntax, keeps a single rollback backup and handles unowned completion assets. Check a fresh shell after deployment.

Refresh the local inventory after changing the managed shell block so other projects see the new observation.

`proxy on|off|status` controls terminal variables and managed Gradle JVM options. It does not switch system proxy, TUN or an already-running IDE. `flutter_source mirror|official|status` controls shell and future GUI processes; restart an IDE to observe GUI changes. For a completion failure use [zsh-completion.md](references/zsh-completion.md), selecting only the relevant diagnostic section.
