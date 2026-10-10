import os
from pathlib import Path
import subprocess
import unittest

SNIPPET = Path(__file__).resolve().parent.parent / 'zsh/zshrc.snippet'

class ProxyTests(unittest.TestCase):
    def run_shell(self, test):
        text = SNIPPET.read_text()
        start = text.index('typeset -g DEV_PROXY_HOST=')
        end = text.index('# 按用户要求，每个新开的交互式终端默认启用代理。')
        env = os.environ.copy()
        env['GRADLE_OPTS'] = "-Xmx2g -Dfoo='two words' -Dhttps.proxyHost=old -Dhttps.proxyPort=9"
        result = subprocess.run(['/bin/zsh', '-f', '-c', text[start:end] + '\n' + test], env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_switches_and_argument_integrity(self):
        self.run_shell('''
        proxy_on; proxy_off; proxy_on; proxy_off
        opts=("${(@Q)${(@z)GRADLE_OPTS}}")
        [[ "${opts[1]}" == '-Xmx2g' && "${opts[2]}" == '-Dfoo=two words' ]] || exit 10
        [[ "$GRADLE_OPTS" != *proxyHost* && -z "$HTTPS_PROXY" ]] || exit 11
        [[ "${opts[-1]}" == '-Dhttp.nonProxyHosts=*' ]] || exit 12
        ''')

    def test_external_changes(self):
        self.run_shell('''
        proxy_on
        GRADLE_OPTS="$GRADLE_OPTS -Dhttp.proxyHost=other -Dbar=keep"
        proxy_off
        [[ "$GRADLE_OPTS" != *proxyHost* && "$GRADLE_OPTS" == *-Dbar=keep* ]] || exit 13
        ''')

    def test_empty_options(self):
        self.run_shell('''
        unset GRADLE_OPTS
        proxy_off
        opts=("${(@Q)${(@z)GRADLE_OPTS}}")
        [[ ${#opts} == 2 && "${opts[1]}" == '-Djava.net.useSystemProxies=false' ]] || exit 15
        ''')

    def test_ide_reader_and_real_terminal_defaults(self):
        startup = SNIPPET.read_text().split('# 按用户要求，每个新开的交互式终端默认启用代理。', 1)[1].split('# 无主资产', 1)[0]
        self.run_shell('flutter_source() { :; }; INTELLIJ_ENVIRONMENT_READER=1\n' + startup + '''
        [[ -z "$HTTP_PROXY" && "$GRADLE_OPTS" != *proxyHost* ]] || exit 16
        unset INTELLIJ_ENVIRONMENT_READER
        ''' + startup + '''
        [[ -n "$HTTP_PROXY" && "$GRADLE_OPTS" == *proxyHost* ]] || exit 17
        ''')

    def test_status_does_not_match_partial_bypass(self):
        out = self.run_shell('proxy_on; proxy_status; proxy_off; proxy_status')
        self.assertEqual(out.count('HTTP(S) 全部直连'), 1)
        self.assertIn('Gradle JVM：已设置代理', out)

    def test_nested_shell_inherited_parameters(self):
        self.run_shell('''
        proxy_on
        inherited="$GRADLE_OPTS"
        GRADLE_OPTS="$inherited"
        proxy_off
        [[ "$GRADLE_OPTS" != *proxyHost* ]] || exit 14
        ''')

if __name__ == '__main__': unittest.main()
