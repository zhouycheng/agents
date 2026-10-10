import importlib.machinery
import importlib.util
import plistlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('workstation', str(ROOT / 'bin/workstation'))
spec = importlib.util.spec_from_loader(loader.name, loader)
workstation = importlib.util.module_from_spec(spec)
loader.exec_module(workstation)


class DeploymentTests(unittest.TestCase):
    def test_codex_links_use_sibling_module_and_apply_is_repeatable(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            with mock.patch.object(workstation, 'HOME', home):
                workstation.apply('codex')
                workstation.apply('codex')
            self.assertEqual((home / '.codex/AGENTS.md').readlink(), ROOT.parent / 'codex/AGENTS.md')
            self.assertEqual((home / '.codex/environment').readlink(), ROOT.parent / 'codex/environment')

    def test_unrelated_link_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            destination = home / 'target'
            unrelated = home / 'user-owned'
            unrelated.write_text('user data')
            destination.symlink_to(unrelated)
            with self.assertRaisesRegex(ValueError, 'refusing unrelated link'):
                workstation.link(ROOT.parent / 'codex/AGENTS.md', destination)
            self.assertEqual(destination.readlink(), unrelated)
            self.assertEqual(unrelated.read_text(), 'user data')

    def test_unrelated_real_file_and_directory_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            source = home / 'source'
            source.write_text('managed data')
            file = home / 'file'
            file.write_text('user data')
            directory = home / 'directory'
            directory.mkdir()
            for destination in (file, directory):
                with self.assertRaisesRegex(ValueError, 'refusing existing unverified path'):
                    workstation.link(source, destination)
            self.assertEqual(file.read_text(), 'user data')
            self.assertTrue(directory.is_dir())

    def test_generated_files_do_not_replace_links(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            source = home / 'source'
            source.write_text('user data')
            destination = home / 'target'
            destination.symlink_to(source)
            with self.assertRaisesRegex(ValueError, 'refusing unrelated link'):
                workstation.write_owned(destination, b'managed data')
            self.assertEqual(source.read_text(), 'user data')

    def test_launchagents_keep_schedule_and_use_new_paths(self):
        inventory, label = workstation.gui_plist('inventory')
        data = plistlib.loads(inventory)
        self.assertEqual(label, 'com.zhou.workstation.inventory')
        self.assertEqual(data['ProgramArguments'], ['/usr/bin/python3', str(ROOT / 'scripts/inventory.py'), 'refresh'])
        self.assertEqual(data['StartCalendarInterval'], [{'Hour': hour, 'Minute': 0} for hour in (0, 6, 12, 18)])
        flutter, label = workstation.gui_plist('flutter')
        data = plistlib.loads(flutter)
        self.assertEqual(label, 'com.zhou.workstation.flutter-mirrors')
        self.assertEqual(data['ProgramArguments'], ['/bin/sh', str(ROOT / 'macos/manifest/launchagents/set-flutter-mirror-env.sh'), 'mirror'])
        self.assertTrue(data['RunAtLoad'])


if __name__ == '__main__':
    unittest.main()
