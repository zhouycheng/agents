# Android / Flutter managed environment

## Daily use

Continue using Android Studio's built-in Java, Kotlin and Flutter project wizards, `android create`, and `flutter create` directly. The original generated Wrapper URL and version remain intact.

Run these commands after initial deployment, a tool upgrade, or removal of Wrapper caches:

```sh
android_env check
android_env prepare
android_env verify
```

`check` is local and read-only: it checks installed tool/template identities, deployed mirror configuration and standard Wrapper cache entries. It never downloads. `prepare` downloads missing distributions from Huawei using official SHA-256 pins in `distributions.json`. `verify` refuses missing distributions and runs each prepared Gradle version. Specify `--gradle-user-home /path/to/isolated-home` for an isolated environment; preparation deploys the managed init script and JDK toolchain paths there as well.

`check` exits 1 for missing distributions and 2 for configuration/tool drift. Unknown tool/template identities block preparation; they are not silently marked supported. After upgrades, inspect the installed Flutter Gradle template, Android CLI template archive and actual IDE wizard output, obtain SHA-256 values from Gradle's official release endpoint, and update the single manifest before repeating check → prepare → verify. If the official endpoint is unavailable, only previously verified pinned values may be reused. Do not accept mirror-only checksums for new versions.

Ordinary terminal startup loads the configured environment without preparing distributions. New interactive terminals default to `proxy on`. `proxy off` changes only that terminal's environment; system proxy and TUN remain separate controls. `proxy status` reports these layers separately, and mirror bypass patterns match only their named hosts.

## Distribution preparation

| Installed entry | Template distribution |
| --- | --- |
| Flutter 3.47.5, CLI and IDE | Gradle 9.3.1-all |
| Android Studio AI-261.26222.65.2614.16379836, Java/Kotlin | Gradle 9.6.0-bin |
| Android CLI 1.0.16406183, empty-activity | Gradle 9.1.0-bin |

`PrepareGradle.java` uses the installed Flutter SDK's official Wrapper implementation for URL hashing, locking, extraction, layout checks and completion markers. A download adapter substitutes the mirror transport and verifies the official checksum. Cache identity remains the complete original URL: official vs mirror URLs and bin vs all distributions are distinct. No second archive repository or global Gradle installation is maintained. Cache removal is recoverable by running `prepare` again.

Gradle logs may display the original URL before the adapter prints `Mirror download:`. The latter is the actual ZIP transport. An official ZIP request is not a prerequisite. SIGTERM during download removes the partial archive; existing ready distributions remain intact. SIGKILL cannot run cleanup hooks, but the official Wrapper removes/replaces its incomplete part on retry.

For existing projects explicitly opting into a mirror URL, retain:

```sh
gradle_mirror --check /path/to/project
gradle_mirror --apply /path/to/project
```

This helper converts the project distribution to Huawei `-bin`, pins its official checksum, and changes only Wrapper properties. `--check` previews without writing the project but may fetch checksum metadata. `flutter_new` remains a compatibility helper; it is not required for ordinary creation.

## Other downloads and Java

| Component | Managed source |
| --- | --- |
| Android Google Maven | Aliyun repository/google |
| Gradle plugins | Aliyun repository/gradle-plugin |
| Maven Central | Aliyun repository/central |
| Pub | pub.flutter-io.cn |
| Flutter engine | storage.flutter-io.cn |

The init script detects Android/Flutter builds, including the Flutter Gradle included build, and adds mirrors before existing fallback repositories. Gradle's error output retains missing component coordinates and attempted URLs. TLS validation stays enabled.

Gradle uses Homebrew JDK 21. The Android CLI template additionally requires a JDK 17 compilation toolchain; managed user `gradle.properties` points to both Homebrew installations to avoid automatic toolchain downloads. Other JVM options remain separate from managed proxy options.

The managed LaunchAgent supplies Flutter mirror variables to newly started GUI apps. Restart IDE after a source change. JetBrains also reads a login shell on startup. The managed zsh block recognizes `INTELLIJ_ENVIRONMENT_READER` and supplies direct-connect JVM options for that reader; real new terminals retain proxy-on defaults. Verify the IDE's current HTTP Proxy setting and actual Flutter/Gradle subprocess environment during acceptance; launchctl values alone do not prove what a running process received.

SDK platforms, build tools, NDK, emulator images and Marketplace plugins are separate from Maven/Pub mirrors. Check their actual installed versions and readiness against the project's requirements. Existing components provide evidence about that local environment; cold downloads require their own checks.

## Acceptance status and operation boundary

The complete three-entry, system-proxy-off and TUN-off acceptance is **pending**. Do not claim general no-proxy support based on normal-network builds or warm caches.

On 2026-09-25 the three pinned distributions were downloaded from mirrors into an empty isolated home and verified; the shared home was also prepared. Flutter CLI built an APK. Android CLI initially failed because JDK 17 was absent; with the installed Homebrew JDK 17 registered it built successfully. Both CLI APKs and the IDE Java app were installed and launched on the emulator. The IDE Kotlin app also launched; Java and Kotlin passed clean → IDE exit → Finder reopen → Run. Flutter IDE creation, Android build/install/run and clean → IDE exit → Finder reopen → Pub Get → Run also passed. These normal-network checks do not replace full no-proxy acceptance.

Automated local tests cover proxy round trips, quoting, inherited/external JVM options, partial bypass status, checksum rejection/recovery, concurrent preparation, URL identity and interrupted downloads preserving ready entries:

```sh
python3 macos/manifest/gradle/test-proxy.py
python3 macos/manifest/gradle/test-wrapper.py
python3 macos/manifest/gradle/test-mirror.py
```

Proxy application modes and switches are managed by the user. For acceptance requiring system proxy and TUN to be off, provide manual steps, wait for the user to establish that state, and record it alongside cache conditions and target processes. Agents do not toggle these settings.

## References

- Gradle Wrapper: https://docs.gradle.org/current/userguide/gradle_wrapper.html
- Flutter community mirror guidance: https://docs.flutter.dev/community/china

- JetBrains shell environment loading: https://youtrack.jetbrains.com/articles/SUPPORT-A-1727
