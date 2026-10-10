---
name: android-flutter-env
description: Prepare, verify and troubleshoot native Android Studio, Android CLI and Flutter project creation, Gradle Wrapper distributions, mirrors, SDK and IDE environment on this Mac.
---

# Android and Flutter environment

Read `macos/manifest/gradle/README.md` and `distributions.json` before modifying the distribution set. Run `android_env check` after tool upgrades. Compare real Flutter, Android Studio and Android CLI template versions, original complete Wrapper URLs, `bin/all`, and SHA-256 from Gradle's official release information. Unknown versions or missing trusted checksums stop preparation. When current pins match, use `android_env check → prepare → verify`; `prepare` downloads from the mirror into the standard Wrapper cache via the official Wrapper. Shell startup never prepares distributions.

Retain original `flutter create`, `android create` and Android Studio wizard flows. `gradle_mirror --check|--apply` and `flutter_new` remain compatibility tools for projects that explicitly choose rewritten URLs. Validate Maven/plugin, Wrapper, Pub/engine, SDK/NDK, emulator images and Marketplace as separate download layers. The global Gradle init script and Flutter GUI LaunchAgent are deployed via `bin/workstation apply android` and `apply gui`.

Refresh the local inventory after installing/upgrading a tool or completing Wrapper preparation so Codex sees the new observation time and distribution status.

For proxy or IDE environment issues read [jvm-proxy.md](references/jvm-proxy.md). `proxy off` affects the current shell; system proxy and TUN are independent. Do not toggle them or erase Gradle caches as part of a routine check. For acceptance, record the actual network state and cache conditions rather than inferring them from a successful warm build.
