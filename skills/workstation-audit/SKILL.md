---
name: workstation-audit
description: Read-only audit of this macOS workstation against the managed Brewfile, capabilities catalog, local inventory and deployed configuration. Use for drift reports or post-upgrade checks, not installation.
---

# Workstation audit

These skills belong to the unified Agent workspace. Before running workstation commands, read `~/.agents/workstation/AGENTS.md` and use `~/.agents/workstation` as the working directory. Relative manifest and script paths below are relative to that directory. Skills live in `~/.agents/skills`; Codex navigation lives in `~/.agents/codex/environment`.

Start in the workstation module with `bin/workstation check`. `scripts/probe.sh` is the shared Brewfile observation engine; use `--json` for structured data. `bin/workstation inventory status` reports the last local snapshot. If missing or stale (over 12 hours or manifest digest changed), run `inventory refresh`; refresh only observes local state and does not download packages or Gradle distributions.

Report desired-versus-observed differences, including `unknown` separately from absent. The capability catalog at `macos/manifest/capabilities.json` lists observation targets; it is not a package installation list. Check the actual executable before a task depends on it. Android/Flutter checks use `macos/manifest/gradle/android-env.py check`, and SDK components are independent of Maven/Pub mirrors. Use `~/.agents/codex/environment/development.md` to locate capability checks and maintenance workflows.

For a new machine without Homebrew, report the missing prerequisite; do not infer package absence from failed probes. Do not change system proxy, TUN, caches, SDK or user projects during audit.
