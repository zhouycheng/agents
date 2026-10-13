import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DeclarationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'scripts').mkdir()
        (self.root / 'macos/manifest').mkdir(parents=True)
        shutil.copy(ROOT / 'scripts/declare.sh', self.root / 'scripts/declare.sh')
        self.brewfile = self.root / 'macos/manifest/Brewfile'
        self.brewfile.write_text('# ==== Tools ====\nnpm "existing"')
        self.original = self.brewfile.read_bytes()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        brew = self.bin / 'brew'
        brew.write_text('#!/bin/sh\nexit "${VALIDATION_EXIT:-0}"\n')
        brew.chmod(0o755)
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ['PATH'])

    def run_declare(self, *args):
        return subprocess.run(['/bin/bash', str(self.root / 'scripts/declare.sh'), *args],
                              env=self.env, text=True, capture_output=True, timeout=10)

    def test_failed_validation_preserves_original_with_new_section_and_no_newline(self):
        self.env['VALIDATION_EXIT'] = '1'
        result = self.run_declare('new', '--npm', '--section', 'New', '--new-section')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.brewfile.read_bytes(), self.original)
        self.assertEqual(list(self.brewfile.parent.glob('.env-declare.*')), [])

    def test_successful_new_section_and_remove(self):
        self.brewfile.chmod(0o600)
        result = self.run_declare('@scope/package', '--npm', '--section', 'New', '--new-section')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('# ==== New ====\nnpm "@scope/package"', self.brewfile.read_text())
        self.assertEqual(self.brewfile.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.run_declare('--remove', '@scope/package', '--npm').returncode, 0)
        self.assertNotIn('@scope/package', self.brewfile.read_text())

    def test_invalid_arguments_are_rejected_without_writing(self):
        for args in (('--section',), ('--remove',), ('bad"; code', '--npm', '--section', 'Tools'),
                     ('new', '--section', 'Injected\ncode', '--new-section')):
            with self.subTest(args=args):
                self.assertEqual(self.run_declare(*args).returncode, 2)
                self.assertEqual(self.brewfile.read_bytes(), self.original)

    def test_existing_declaration_does_not_normalize_original(self):
        self.assertEqual(self.run_declare('existing', '--npm').returncode, 0)
        self.assertEqual(self.brewfile.read_bytes(), self.original)


if __name__ == '__main__':
    unittest.main()
