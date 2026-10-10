# Workstation configuration project

This repository is the desired configuration for one macOS development workstation. The source of truth for packages, shell configuration, Gradle mirrors, Android/Flutter preparation and GUI environment is `macos/manifest/`. Codex is a consumer under `codex/`, not the owner of the whole workstation.

Start with `bin/workstation check` and `bin/workstation inventory status`; read `README.md` and the matching project skill in `.agents/skills/` before changing a component. `check` is read-only. `inventory refresh` observes the local machine and writes only `~/.local/state/env/inventory.json`. Its timestamp and `status` fields determine whether a targeted recheck is needed. A fresh inventory is a navigation aid, not proof that a command will work in the current process.

`bin/workstation apply codex|shell|android|gui` deploys one named component; `verify` checks deployed files. Do not treat the whole Brewfile as an install request. For packages, first show the observed difference and agree on each installation or configuration change with the user. On Android/Flutter upgrades, check actual templates and trustworthy checksums, then run `android_env check → prepare → verify`; normal shell startup never downloads distributions. Do not switch system proxy or TUN as part of ordinary checks.

Global Codex rules live in `codex/AGENTS.md` and deploy to `~/.codex/AGENTS.md`. Machine observations, credentials, caches, project builds and user apps stay outside Git. Preserve existing user files when a target is not recognizably owned by this project. Wiki records design and incidents; it is not a live inventory.
