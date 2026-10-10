---
name: workstation-provision
description: Reconcile the workstation Brewfile and deploy selected managed components after showing differences and agreeing on each package or configuration action. Use for new-machine setup or drift repair.
---

# Workstation provision

Run `bin/workstation check` before suggesting changes. Present missing declared packages and directly installed undeclared packages separately; distinguish dependencies and unknown probe results. The desired package list is `macos/manifest/Brewfile`. Never overwrite it with `brew bundle dump`; the snapshot at `~/.local/state/env/inventory.json` is observed state only.

Agree on the concrete package or configuration actions with the user before each installation or live configuration change. Do not run `brew bundle install` for the entire file. After each action, verify the package or component, then run `bin/workstation inventory refresh`. `scripts/declare.sh` edits package intent; removing a declaration does not uninstall a package. `bin/workstation apply codex|shell|android|gui` deploys only the named component, followed by `bin/workstation verify`.

For Brewfile format and the prior failure cases in its parser, read [manifest-format.md](references/manifest-format.md) when editing declarations. For Android/Flutter preparation, use the `android-flutter-env` project skill. For zsh changes, use `macos-shell-env`.
