"""Exercise official-checksum fallback without network access or user projects."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent

class MirrorTests(unittest.TestCase):
    def test_pinned_fallback_unknown_version_and_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wrapper = root / 'project/gradle/wrapper'
            wrapper.mkdir(parents=True)
            properties = wrapper / 'gradle-wrapper.properties'
            manifest = json.loads((ROOT / 'distributions.json').read_text())
            (root / 'distributions.json').write_text(json.dumps(manifest))
            trusted = manifest['additional_official_checksums']['gradle-9.3.1-bin.zip']
            curl = root / 'curl'
            script = root / 'use-mirrors.sh'
            script.write_text((ROOT / 'use-mirrors.sh').read_text().replace('/usr/bin/curl', str(curl)))
            def run(version, mirror_sum):
                curl.write_text('#!/bin/sh\ncase "$*" in *services.gradle.org*) exit 7;; esac\necho ' + mirror_sum + '\n')
                curl.chmod(0o755)
                properties.write_text(f'distributionUrl=https\\://mirrors.huaweicloud.com/gradle/gradle-{version}-bin.zip\ndistributionSha256Sum={trusted}\n')
                before = properties.read_bytes()
                result = subprocess.run(['/bin/sh', str(script), '--check', str(root / 'project')], capture_output=True, text=True)
                self.assertEqual(properties.read_bytes(), before)
                return result
            known = run('9.3.1', trusted)
            self.assertEqual(known.returncode, 0, known.stderr)
            self.assertIn('previously verified official pin', known.stdout)
            self.assertIn('Already configured', known.stdout)
            unknown = run('99.0.0', trusted)
            self.assertNotEqual(unknown.returncode, 0)
            self.assertIn('No trusted official checksum', unknown.stderr)
            mismatch = run('9.3.1', '0' * 64)
            self.assertNotEqual(mismatch.returncode, 0)
            self.assertIn('differs', mismatch.stderr)

if __name__ == '__main__':
    unittest.main()
