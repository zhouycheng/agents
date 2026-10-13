"""Locate the managed zsh block and audit completion permissions without sourcing zshrc."""

import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys


START = '# ---- zsh 补全系统'
END = '# ---- agents/workstation 受管配置结束 ----'
# Identify the deployed pre-delimiter block before preserving any user suffix.
LEGACY_BYTES = 12016
LEGACY_SHA256 = '919131e6614b1c031b6449a55436fc55deeb4b3afe865cfd17a7713723d4ec44'


def bounds(text):
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.startswith(START)]
    ends = [i for i, line in enumerate(lines) if line.rstrip('\r\n') == END]
    if not starts and not ends:
        return None
    if len(starts) != 1 or len(ends) > 1:
        raise ValueError('受管标记重复或不完整，请先确认配置归属')
    start = sum(map(len, lines[:starts[0]]))
    if ends:
        if ends[0] <= starts[0]:
            raise ValueError('受管标记顺序错误')
        return start, sum(map(len, lines[:ends[0] + 1]))
    legacy = text[start:].encode('utf-8')[:LEGACY_BYTES]
    if hashlib.sha256(legacy).hexdigest() != LEGACY_SHA256:
        raise ValueError('旧受管块内容无法确认，请先人工划定结束位置')
    return start, start + len(legacy.decode('utf-8'))


def render(current, snippet):
    span = bounds(snippet)
    if span != (0, len(snippet)) or not snippet.endswith(END + '\n'):
        raise ValueError('配置片段须完整包含唯一的起止标记')
    span = bounds(current)
    if span is None:
        return current + ('\n' if current and not current.endswith('\n') else '') + snippet
    return current[:span[0]] + snippet + current[span[1]:]


def matches(current, snippet):
    try:
        return current == render(current, snippet)
    except ValueError:
        return False


def audit_permissions():
    prefix = os.environ.get('HOMEBREW_PREFIX', '/opt/homebrew')
    return subprocess.run(
        ['/bin/zsh', '-f', '-c',
         'fpath=("$1" "$2" $fpath); autoload -Uz compaudit; compaudit',
         'audit', str(Path.home() / '.local/share/zsh/site-functions'),
         str(Path(prefix) / 'share/zsh-completions')],
        text=True, capture_output=True, timeout=15)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('check', 'render'):
        command = sub.add_parser(name)
        command.add_argument('zshrc', type=Path)
        command.add_argument('snippet', type=Path)
        if name == 'render':
            command.add_argument('output', type=Path)
    sub.add_parser('audit')
    args = parser.parse_args()
    if args.command == 'audit':
        result = audit_permissions()
        print(result.stdout, end='')
        print(result.stderr, end='', file=sys.stderr)
        return result.returncode
    if args.zshrc.is_symlink():
        raise ValueError('请先确认 .zshrc 软链接归属')
    current = args.zshrc.read_text() if args.zshrc.exists() else ''
    updated = render(current, args.snippet.read_text())
    if args.command == 'render':
        args.output.write_text(updated)
        return 0
    return int(current != updated)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'shell_config: {error}', file=sys.stderr)
        sys.exit(2)
