#!/usr/bin/env python3
"""Prepare current Android tool templates without changing their Wrapper URLs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
HOME = Path.home()
BREW_PREFIX = Path(os.environ.get('HOMEBREW_PREFIX') or ('/opt/homebrew' if Path('/opt/homebrew').exists() else '/usr/local'))
FLUTTER = BREW_PREFIX / 'share/flutter'
STUDIO = Path('/Applications/Android Studio.app/Contents')
JAVA = BREW_PREFIX / 'opt/openjdk@21/bin/java'
WRAPPER = FLUTTER / 'bin/cache/artifacts/gradle_wrapper/gradle/wrapper/gradle-wrapper.jar'
LOCK = ROOT / 'distributions.json'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def facts():
    sdk = Path(os.environ.get('ANDROID_HOME', HOME / 'Library/Android/sdk'))
    def read_or_missing(reader):
        try:
            return reader()
        except (OSError, ValueError, KeyError, subprocess.SubprocessError):
            return 'missing or unreadable'
    return {
        'flutter': read_or_missing(lambda: json.loads((FLUTTER / 'bin/cache/flutter.version.json').read_text())['frameworkVersion']),
        'studio': read_or_missing(lambda: json.loads((STUDIO / 'Resources/product-info.json').read_text())['version']),
        'android_cli': read_or_missing(lambda: subprocess.check_output(
            [shutil.which('android') or str(BREW_PREFIX / 'bin/android'), '--version'],
            text=True, timeout=15, stderr=subprocess.DEVNULL).strip()),
        'android_templates_sha256': read_or_missing(lambda: sha(sdk / 'build/templates/android-project-templates.zip')),
        'wrapper_sha256': read_or_missing(lambda: sha(WRAPPER)),
    }


def configuration(home, prepare):
    issues = []
    target = home / 'init.d/10-codex-android-mirrors.init.gradle'
    source = ROOT / 'codex-android-mirrors.init.gradle'
    if prepare and not target.exists() and not target.is_symlink():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(source)
    if not target.exists() or target.read_bytes() != source.read_bytes():
        issues.append(f'Gradle init configuration missing or different: {target}')
    java_properties = home / 'gradle.properties'
    prefix = str(BREW_PREFIX)
    expected_paths = (f'{prefix}/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home,'
                      f'{prefix}/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home')
    if prepare and not java_properties.exists() and not java_properties.is_symlink():
        java_properties.write_text(f'org.gradle.java.installations.paths={expected_paths}\n')
    if not java_properties.exists() or f'org.gradle.java.installations.paths={expected_paths}' not in java_properties.read_text():
        issues.append(f'JDK toolchain paths missing: {java_properties}')
    if not Path(prefix, 'opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin/java').exists():
        issues.append('Homebrew openjdk@17 is required by Android CLI templates')
    sdk = Path(os.environ.get('ANDROID_HOME', HOME / 'Library/Android/sdk'))
    for component in ('platform-tools/adb', 'platforms/android-36/android.jar',
                      'platforms/android-37.0/android.jar', 'build-tools/36.0.0/aapt2',
                      'ndk/28.2.13676358/source.properties', 'cmake/3.22.1/bin/cmake',
                      'system-images/android-37.0/google_apis/arm64-v8a/package.xml'):
        if not (sdk / component).exists():
            issues.append(f'SDK component missing (outside Maven mirror scope): {component}')
    # Inspect deployed shell without starting a shell or changing GUI environment.
    snippet = (ROOT.parent / 'zsh/zshrc.snippet').read_text()
    zshrc_path = HOME / '.zshrc'
    zshrc = zshrc_path.read_text() if zshrc_path.is_file() else ''
    if not zshrc.endswith(snippet):
        issues.append('zsh deployment differs; run manifest/zsh/deploy.sh')
    for key, expected in {'PUB_HOSTED_URL': 'https://pub.flutter-io.cn',
                          'FLUTTER_STORAGE_BASE_URL': 'https://storage.flutter-io.cn'}.items():
        actual = subprocess.run(['/bin/launchctl', 'getenv', key], text=True, capture_output=True).stdout.strip()
        if actual != expected:
            issues.append(f'GUI {key} is not the managed mirror; run flutter_source mirror')
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['check', 'prepare', 'verify'])
    parser.add_argument('--gradle-user-home', type=Path, default=Path(os.environ.get('GRADLE_USER_HOME', HOME / '.gradle')))
    args = parser.parse_args()
    lock = json.loads(LOCK.read_text())
    actual = facts()
    errors = [f'Tool/template drift: {key}: expected {value}, found {actual.get(key)}'
              for key, value in lock['tools'].items() if actual.get(key) != value]
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        print('Re-inspect installed templates and official checksums; update distributions.json before prepare.', file=sys.stderr)
        return 2
    home = args.gradle_user_home.expanduser().resolve()
    errors = configuration(home, args.mode == 'prepare')
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        if args.mode != 'check':
            return 2
    if args.mode == 'check':
        for name, value in actual.items():
            print(f'TOOL\t{name}\t{value}')
    lines = []
    for item in lock['distributions']:
        if len(item['sha256']) != 64 or any(c not in '0123456789abcdef' for c in item['sha256']):
            raise ValueError('Invalid pinned checksum')
        lines.append('\t'.join(item[key] for key in ('url', 'mirror', 'sha256')))
    env = os.environ.copy()
    for key in ('JAVA_OPTS', 'JAVA_TOOL_OPTIONS', '_JAVA_OPTIONS', 'GRADLE_OPTS'):
        env.pop(key, None)
    with tempfile.TemporaryDirectory(prefix='android-env-') as temporary:
        records = Path(temporary) / 'records.tsv'
        records.write_text('\n'.join(lines) + '\n')
        command = [str(JAVA), '-Djava.net.useSystemProxies=false', '--class-path', str(WRAPPER),
                   str(ROOT / 'PrepareGradle.java'), args.mode, str(home), str(records)]
        if args.mode == 'check':
            result = subprocess.run(command, env=env, text=True, capture_output=True)
            print(result.stdout, end=''); print(result.stderr, end='', file=sys.stderr)
            return result.returncode or (2 if errors else 1 if 'MISSING\t' in result.stdout else 0)
        return subprocess.call(command, env=env)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'android_env: {error}', file=sys.stderr)
        sys.exit(2)
