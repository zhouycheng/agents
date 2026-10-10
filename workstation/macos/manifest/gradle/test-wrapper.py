import hashlib
import http.server
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
import zipfile

ROOT = Path(__file__).resolve().parent
JAVA = '/opt/homebrew/opt/openjdk@21/bin/java'
JAR = '/opt/homebrew/share/flutter/bin/cache/artifacts/gradle_wrapper/gradle/wrapper/gradle-wrapper.jar'

class WrapperTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='android-wrapper-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.archive = self.root / 'fixture.zip'
        with zipfile.ZipFile(self.archive, 'w') as z:
            z.writestr('gradle-1.0/', '')
            z.writestr('gradle-1.0/bin/', '')
            z.writestr('gradle-1.0/lib/', '')
            z.writestr('gradle-1.0/bin/gradle', '#!/bin/sh\necho Gradle 1.0\n')
            z.writestr('gradle-1.0/lib/gradle-launcher-1.0.jar', 'fixture')
        self.sum = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.records = self.root / 'records'
        self.records.write_text(f'https://services.gradle.org/distributions/gradle-1.0-bin.zip\t{self.archive.as_uri()}\t{self.sum}\n')

    def command(self, mode):
        return [JAVA, '--class-path', JAR, str(ROOT/'PrepareGradle.java'), mode, str(self.root/'cache'), str(self.records)]

    def run_mode(self, mode):
        return subprocess.run(self.command(mode), capture_output=True, text=True)

    def test_bad_checksum_then_recovery(self):
        good = self.records.read_text()
        self.records.write_text(good.replace(self.sum, '0'*64))
        self.assertNotEqual(self.run_mode('prepare').returncode, 0)
        self.assertFalse(list((self.root/'cache').rglob('*.ok')))
        self.assertFalse(list((self.root/'cache').rglob('*.part')))
        self.records.write_text(good)
        self.assertEqual(self.run_mode('prepare').returncode, 0)
        self.assertEqual(self.run_mode('verify').returncode, 0)

    def test_concurrent_preparation_and_idempotence(self):
        procs = [subprocess.Popen(self.command('prepare'), stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
        results = [(p, p.communicate(timeout=30)) for p in procs]
        for p, (out, err) in results:
            self.assertEqual(p.returncode, 0, out+err)
        markers = list((self.root/'cache').rglob('*.ok'))
        self.assertEqual(len(markers), 1)
        self.archive.unlink()  # ready distributions must not redownload
        self.assertEqual(self.run_mode('prepare').returncode, 0)
        self.assertEqual(self.run_mode('verify').returncode, 0)

    def test_original_url_identity_and_missing(self):
        self.assertIn('MISSING', self.run_mode('check').stdout)
        self.assertNotEqual(self.run_mode('verify').returncode, 0)
        self.assertEqual(self.run_mode('prepare').returncode, 0)
        self.records.write_text(self.records.read_text().replace('https://services.gradle.org/distributions/', 'https://other.invalid/'))
        self.assertIn('MISSING', self.run_mode('check').stdout)
        self.assertEqual(len(list((self.root/'cache').rglob('*.ok'))), 1)

    def test_interrupted_download_preserves_ready_distribution(self):
        self.assertEqual(self.run_mode('prepare').returncode, 0)
        ready = list((self.root/'cache').rglob('*.ok'))[0]
        initial = ready.stat().st_mtime_ns
        started, release = threading.Event(), threading.Event()
        class SlowDownload(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-Length', '1000000')
                self.end_headers()
                self.wfile.write(b'partial archive')
                self.wfile.flush()
                started.set()
                release.wait(20)
            def log_message(self, *args): pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), SlowDownload)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.records.write_text(self.records.read_text() +
            f'https://services.gradle.org/distributions/gradle-2.0-bin.zip\thttp://127.0.0.1:{server.server_port}/slow.zip\t{self.sum}\n')
        proc = subprocess.Popen(self.command('prepare'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            self.assertTrue(started.wait(15))
            proc.terminate()
            proc.communicate(timeout=10)
            self.assertNotEqual(proc.returncode, 0)
            self.assertFalse(list((self.root/'cache').rglob('*.part')))
            self.assertEqual(ready.stat().st_mtime_ns, initial)
            self.assertEqual(len(list((self.root/'cache').rglob('*.ok'))), 1)
        finally:
            if proc.poll() is None:
                proc.kill(); proc.communicate()
            release.set()
            server.shutdown(); server.server_close()

if __name__ == '__main__': unittest.main()
