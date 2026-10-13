import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

import inventory


ROOT = Path(__file__).resolve().parents[1]


class InventoryTests(unittest.TestCase):
    def test_missing_capability_is_not_ok(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory)
            (manifest / 'capabilities.json').write_text(json.dumps({
                'schema_version': 1, 'commands': ['missing-command'], 'applications': {}}))
            with mock.patch.object(inventory, 'MANIFEST', manifest), mock.patch.object(
                    inventory.shutil, 'which', return_value=None):
                result = inventory.command_section({})
            self.assertEqual(result['status'], 'missing')
            self.assertEqual(result['missing_commands'], ['missing-command'])

    def test_status_fails_for_stale_or_unhealthy_snapshot(self):
        for freshness, status, expected in (('fresh', 'ok', 0), ('stale', 'ok', 1),
                                            ('fresh', 'missing', 1), ('fresh', 'unknown', 1)):
            with self.subTest(freshness=freshness, status=status):
                snapshot = {'generated_at': 'test', 'sections': {'shell': {'status': status}}}
                with mock.patch.object(inventory, 'load_snapshot', return_value=snapshot), mock.patch.object(
                        inventory, 'freshness', return_value=freshness), mock.patch(
                        'sys.argv', ['inventory', 'status']), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(inventory.main(), expected)

    def test_observed_package_drift_is_preserved(self):
        result = subprocess.CompletedProcess([], 0, json.dumps({'status': 'drift'}), '')
        with mock.patch.object(inventory, 'run_local', return_value=result):
            self.assertEqual(inventory.package_section()['status'], 'drift')


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.root = self.home / 'workstation'
        shutil.copytree(ROOT / 'macos/manifest', self.root / 'macos/manifest')
        (self.root / 'scripts').mkdir()
        for name in ('probe.sh', 'shell_config.py'):
            shutil.copy(ROOT / 'scripts' / name, self.root / 'scripts' / name)
        (self.root / 'macos/manifest/Brewfile').write_text('brew "needed"\n')
        shutil.copy(self.root / 'macos/manifest/zsh/zshrc.snippet', self.home / '.zshrc')
        self.assets = self.home / '.local/share/zsh/site-functions'
        shutil.copytree(self.root / 'macos/manifest/assets', self.assets)
        self.prefix = self.home / 'brew'
        self.completions = self.prefix / 'share/zsh-completions'
        self.completions.mkdir(parents=True)
        fake = self.home / 'bin'
        fake.mkdir()
        brew = fake / 'brew'
        brew.write_text('''#!/usr/bin/env python3
import json, os, sys
if sys.argv[1] == '--prefix': print(os.environ['HOMEBREW_PREFIX'])
elif sys.argv[1] == '--version': print('Homebrew fixture')
elif sys.argv[1] == 'info':
    print(json.dumps({'formulae': [{'name': name, 'installed': [{'version': '1', 'installed_on_request': True}]} for name in os.environ.get('TEST_INSTALLED', 'needed').split()]}))
''')
        npm = fake / 'npm'
        npm.write_text('#!/bin/sh\nprintf \'{"dependencies":{}}\\n\'\n')
        for p in (brew, npm):
            p.chmod(0o755)
        self.env = dict(os.environ, HOME=str(self.home), HOMEBREW_PREFIX=str(self.prefix),
                        PATH=str(fake) + os.pathsep + os.environ['PATH'])
        for key in ('ZSHRC_OVERRIDE', 'ENV_STATE_DIR'):
            self.env.pop(key, None)

    def probe(self):
        result = subprocess.run(['/bin/bash', str(self.root / 'scripts/probe.sh'), '--json'],
                                env=self.env, text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_missing_and_extra_packages_have_health_status(self):
        for installed, expected in (('needed', 'ok'), ('', 'missing'), ('needed extra', 'drift')):
            with self.subTest(installed=installed):
                self.env['TEST_INSTALLED'] = installed
                result = self.probe()
                self.assertEqual(result['status'], expected)
                self.assertEqual(result['observation_status'], 'ok')

    def test_missing_asset_is_reported_as_shell_drift(self):
        next(self.assets.iterdir()).unlink()
        result = self.probe()['shell']
        self.assertEqual(result['status'], 'drift')
        self.assertEqual(result['deployment_exit_code'], 1)

    def test_permissions_are_reported_even_when_config_matches(self):
        self.completions.chmod(0o777)
        result = self.probe()['shell']
        self.assertEqual(result['deployment_exit_code'], 0)
        self.assertEqual(result['permissions_status'], 'insecure')
        self.assertEqual(result['status'], 'drift')
        self.assertIn(str(self.completions), result['insecure_directories'])


if __name__ == '__main__':
    unittest.main()
