import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

import shell_config


ROOT = Path(__file__).resolve().parents[1]


class ShellBlockTests(unittest.TestCase):
    def setUp(self):
        self.snippet = shell_config.START + '\nexport MANAGED=1\n' + shell_config.END + '\n'

    def test_preserves_prefix_suffix_and_is_idempotent(self):
        current = 'export BEFORE=1\n' + self.snippet + '\nexport AFTER=1\n'
        new = self.snippet.replace('MANAGED=1', 'MANAGED=2')
        updated = shell_config.render(current, new)
        self.assertEqual(updated, current.replace('MANAGED=1', 'MANAGED=2'))
        self.assertEqual(shell_config.render(updated, new), updated)
        self.assertTrue(shell_config.matches(updated, new))

    def test_known_legacy_preserves_appended_user_content(self):
        legacy = shell_config.START + '\nexport OLD=1\n'
        with mock.patch.object(shell_config, 'LEGACY_BYTES', len(legacy.encode())), mock.patch.object(
                shell_config, 'LEGACY_SHA256', hashlib.sha256(legacy.encode()).hexdigest()):
            self.assertEqual(shell_config.render(legacy + 'export USER=1\n', self.snippet),
                             self.snippet + 'export USER=1\n')

    def test_rejects_unknown_legacy_and_malformed_delimiters(self):
        for current in (shell_config.START + '\nuser data\n', self.snippet * 2,
                        shell_config.END + '\n', shell_config.END + '\n' + shell_config.START):
            with self.subTest(current=current), self.assertRaises(ValueError):
                shell_config.render(current, self.snippet)


class ShellDeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.root = self.home / 'workstation'
        shutil.copytree(ROOT / 'macos/manifest', self.root / 'macos/manifest')
        (self.root / 'scripts').mkdir()
        shutil.copy(ROOT / 'scripts/shell_config.py', self.root / 'scripts/shell_config.py')
        self.snippet = (self.root / 'macos/manifest/zsh/zshrc.snippet').read_text()
        self.zshrc = self.home / '.zshrc'
        self.zshrc.write_text(self.snippet)
        self.assets = self.home / '.local/share/zsh/site-functions'
        self.assets.mkdir(parents=True)
        self.env = dict(os.environ, HOME=str(self.home), ENV_STATE_DIR=str(self.home / 'state'))
        self.env.pop('ZSHRC_OVERRIDE', None)

    def deploy(self, *args):
        return subprocess.run(['/bin/bash', str(self.root / 'macos/manifest/zsh/deploy.sh'), *args],
                              env=self.env, capture_output=True, text=True, timeout=15)

    def test_missing_assets_fail_check_then_apply_is_repeatable(self):
        self.assertEqual(self.deploy('--check').returncode, 1)
        self.assertEqual(self.deploy().returncode, 0)
        self.assertEqual(self.deploy('--check').returncode, 0)
        self.assertEqual(self.deploy().returncode, 0)

    def test_asset_conflicts_preserve_all_user_content(self):
        original = self.snippet + 'export USER=1\n'
        self.zshrc.write_text(original)
        victim = self.home / 'user-file'
        victim.write_text('keep')
        asset = next((self.root / 'macos/manifest/assets').iterdir())
        target = self.assets / asset.name
        for kind in ('link', 'broken-link', 'file'):
            with self.subTest(kind=kind):
                if kind == 'file':
                    target.write_text('keep')
                else:
                    target.symlink_to(victim if kind == 'link' else self.home / 'missing')
                self.assertNotEqual(self.deploy().returncode, 0)
                self.assertEqual(self.zshrc.read_text(), original)
                self.assertEqual(victim.read_text(), 'keep')
                target.unlink()

    def test_updates_only_bounded_block_and_preserves_mode(self):
        current = 'export BEFORE=1\n' + self.snippet.replace('compinit -i -D', 'compinit -i') + 'export AFTER=1\n'
        self.zshrc.write_text(current)
        self.zshrc.chmod(0o600)
        result = self.deploy()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.zshrc.read_text(), 'export BEFORE=1\n' + self.snippet + 'export AFTER=1\n')
        self.assertEqual(self.zshrc.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.deploy('--check').returncode, 0)

    def test_rejects_zshrc_symlink_and_invalid_syntax(self):
        victim = self.home / 'user-file'
        self.zshrc.rename(victim)
        self.zshrc.symlink_to(victim)
        self.assertNotEqual(self.deploy().returncode, 0)
        self.assertEqual(victim.read_text(), self.snippet)
        self.zshrc.unlink()
        current = 'if syntax is broken\n' + self.snippet.replace('compinit -i -D', 'compinit -i')
        self.zshrc.write_text(current)
        self.assertNotEqual(self.deploy().returncode, 0)
        self.assertEqual(self.zshrc.read_text(), current)

    def test_completion_ignores_unsafe_directory_and_writes_no_dump(self):
        safe = self.home / 'safe'
        unsafe = self.home / 'unsafe'
        for directory, command in ((safe, 'safecommand'), (unsafe, 'unsafecommand')):
            directory.mkdir()
            (directory / ('_' + command)).write_text('#compdef ' + command + '\nreturn 0\n')
        unsafe.chmod(0o777)
        dump = self.home / '.zcompdump'
        dump_text = 'print loaded > "$HOME/loaded-untrusted-dump"\n'
        dump.write_text(dump_text)
        init = next(line for line in self.snippet.splitlines() if line.startswith('autoload -Uz compinit'))
        code = 'fpath=("$1" "$2" $fpath)\n' + init + '\n[[ -n ${_comps[safecommand]} && -z ${_comps[unsafecommand]} ]]'
        result = subprocess.run(['/bin/zsh', '-f', '-c', code, 'test', str(safe), str(unsafe)],
                                env=self.env, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(self.home.glob('.zcompdump*')), [dump])
        self.assertEqual(dump.read_text(), dump_text)
        self.assertFalse((self.home / 'loaded-untrusted-dump').exists())


if __name__ == '__main__':
    unittest.main()
