#!/usr/bin/env python3
"""Refresh or read this Mac's local, untracked workstation inventory."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / 'macos/manifest'
STATE = Path(os.environ.get('ENV_STATE_DIR', Path.home() / '.local/state/env'))
SNAPSHOT = STATE / 'inventory.json'
MAX_AGE_SECONDS = 12 * 60 * 60


def config_digest():
    digest = hashlib.sha256()
    for path in sorted(MANIFEST.rglob('*')):
        if not path.is_file() or '__pycache__' in path.parts or path.suffix == '.pyc':
            continue
        digest.update(str(path.relative_to(MANIFEST)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def run_local(command, timeout=90):
    env = os.environ.copy()
    env['HOMEBREW_NO_AUTO_UPDATE'] = '1'
    env['HOMEBREW_NO_ANALYTICS'] = '1'
    env['PATH'] = run_path()
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, env=env)


def package_section():
    try:
        result = run_local([str(ROOT / 'scripts/probe.sh'), '--json'])
    except (OSError, subprocess.SubprocessError) as error:
        return {'status': 'unknown', 'error': str(error)}
    try:
        section = json.loads(result.stdout)
        if not isinstance(section, dict) or 'status' not in section:
            raise ValueError('invalid probe result')
    except (ValueError, json.JSONDecodeError):
        return {'status': 'unknown', 'error': (result.stderr or 'probe returned invalid JSON').strip()}
    if result.returncode and section.get('status') != 'unknown':
        section = {'status': 'unknown', 'error': (result.stderr or 'probe failed').strip()}
    return section


def command_section(packages):
    catalog = json.loads((MANIFEST / 'capabilities.json').read_text())
    if catalog.get('schema_version') != 1:
        raise ValueError('unsupported capabilities catalog')
    known_versions = {}
    installed = packages.get('installed', {})
    for item in installed.get('formulae', []) + installed.get('npm', []):
        known_versions[item['name']] = item.get('version')
    commands = {}
    for name in catalog['commands']:
        path = shutil.which(name, path=run_path())
        commands[name] = {'present': path is not None, 'path': path,
                          'package_version': known_versions.get(name)}
    applications = {}
    for name, path in catalog['applications'].items():
        applications[name] = {'present': Path(path).is_dir(), 'path': path}
    return {'status': 'ok', 'commands': commands, 'applications': applications,
            'missing_commands': [name for name, item in commands.items() if not item['present']],
            'missing_applications': [name for name, item in applications.items() if not item['present']]}


def run_path():
    return os.pathsep.join((
        '/opt/homebrew/bin', '/opt/homebrew/sbin', '/usr/local/bin',
        '/usr/bin', '/bin', '/usr/sbin', '/sbin',
        str(Path.home() / '.cargo/bin'), str(Path.home() / '.local/bin'),
        str(Path.home() / '.kimi-code/bin'),
        str(Path.home() / 'Library/Android/sdk/platform-tools'),
        str(Path.home() / 'Library/Android/sdk/emulator'),
        str(Path.home() / 'Library/Android/sdk/cmdline-tools/latest/bin'),
        '/opt/homebrew/opt/openjdk@21/bin', '/opt/homebrew/share/flutter/bin',
        os.environ.get('PATH', ''),
    ))


def android_section():
    try:
        result = run_local([sys.executable, str(MANIFEST / 'gradle/android-env.py'), 'check'], timeout=60)
    except (OSError, subprocess.SubprocessError) as error:
        return {'status': 'unknown', 'error': str(error)}
    tools = {}
    distributions = []
    for line in result.stdout.splitlines():
        fields = line.split('\t')
        if len(fields) >= 3 and fields[0] == 'TOOL':
            tools[fields[1]] = fields[2]
        elif len(fields) >= 3 and fields[0] in ('READY', 'MISSING'):
            distributions.append({'ready': fields[0] == 'READY', 'url': fields[1], 'cache': fields[2]})
    stderr = result.stderr.strip()
    if result.returncode == 0:
        status = 'ok'
    elif 'Tool/template drift:' in stderr or 'configuration missing or different:' in stderr:
        status = 'drift'
    elif result.returncode == 1 or 'MISSING\t' in result.stdout:
        status = 'missing'
    else:
        status = 'unknown'
    return {'status': status, 'tools': tools, 'distributions': distributions,
            'error': stderr or None}


def load_snapshot():
    try:
        result = json.loads(SNAPSHOT.read_text())
        if result.get('schema_version') != 1:
            raise ValueError('unsupported inventory schema')
        return result
    except (FileNotFoundError, ValueError, OSError) as error:
        raise ValueError(f'No usable local inventory: {error}') from error


def freshness(snapshot):
    try:
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(snapshot['generated_at'])).total_seconds()
        digest_matches = snapshot['config_digest'] == config_digest()
    except (KeyError, TypeError, ValueError, OSError):
        return 'unknown'
    return 'fresh' if 0 <= age <= MAX_AGE_SECONDS and digest_matches else 'stale'


def atomic_write(payload):
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.umask(0o077)
    descriptor, temporary = tempfile.mkstemp(prefix='.inventory.', suffix='.tmp', dir=STATE)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, SNAPSHOT)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def refresh():
    packages = package_section()
    try:
        previous = load_snapshot()
    except ValueError:
        previous = None
    payload = {
        'schema_version': 1,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'config_digest': config_digest(),
        'sections': {'packages': packages},
    }
    payload['sections']['capabilities'] = command_section(packages)
    payload['sections']['shell'] = packages.get('shell', {'status': 'unknown'})
    payload['sections']['android_flutter'] = android_section()
    if previous:
        for name, section in payload['sections'].items():
            old = previous.get('sections', {}).get(name, {})
            if section.get('status') == 'ok':
                continue
            if old.get('status') == 'ok':
                section['last_successful'] = {
                    'observed_at': previous.get('generated_at'),
                    'result': old,
                }
            elif old.get('last_successful'):
                section['last_successful'] = old['last_successful']
    atomic_write(payload)
    print(f'{SNAPSHOT} ({freshness(payload)})')
    return 0 if all(item.get('status') == 'ok' for item in payload['sections'].values()) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('refresh', 'show', 'status'))
    args = parser.parse_args()
    if args.command == 'refresh':
        return refresh()
    snapshot = load_snapshot()
    if args.command == 'show':
        print(json.dumps(snapshot, ensure_ascii=False, indent=2))
    else:
        print(f'{freshness(snapshot)}\t{snapshot["generated_at"]}\t{SNAPSHOT}')
        for name, section in snapshot.get('sections', {}).items():
            print(f'{name}\t{section.get("status", "unknown")}')
            if name == 'capabilities':
                for group in ('missing_commands', 'missing_applications'):
                    if section.get(group):
                        print(f'  {group}: {", ".join(section[group])}')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'inventory: {error}', file=sys.stderr)
        sys.exit(2)
