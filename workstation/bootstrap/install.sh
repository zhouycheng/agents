#!/bin/sh
set -eu
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if [ "$#" -eq 0 ]; then
  printf '%s\n' 'Use bin/workstation check, then bin/workstation apply codex|shell|android|gui.'
  exit 0
fi
exec "$repo_dir/bin/workstation" "$@"
