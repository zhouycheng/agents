#!/bin/sh
set -eu

usage() {
  printf '%s\n' \
    '用法：gradle_mirror --check <项目目录>' \
    '      gradle_mirror --apply <项目目录>' \
    '检测或更新 Android/Flutter 项目的 Gradle Wrapper 镜像与 SHA-256。'
}

mode=${1:-}
project_dir=${2:-.}
if [ "$mode" != "--check" ] && [ "$mode" != "--apply" ]; then
  usage >&2
  exit 2
fi
if [ "$#" -gt 2 ]; then
  usage >&2
  exit 2
fi

project_dir=$(CDPATH= cd -- "$project_dir" && pwd)
properties=''
for candidate in \
  "$project_dir/gradle/wrapper/gradle-wrapper.properties" \
  "$project_dir/android/gradle/wrapper/gradle-wrapper.properties"
do
  if [ -f "$candidate" ]; then
    properties=$candidate
    break
  fi
done
if [ -z "$properties" ]; then
  printf 'Gradle Wrapper properties not found under %s\n' "$project_dir" >&2
  exit 1
fi
if [ -L "$properties" ]; then
  printf 'Refusing to rewrite a symlink: %s\n' "$properties" >&2
  exit 1
fi

old_url=$(sed -n 's/^distributionUrl=//p' "$properties" | sed -n '1p')
old_url=$(printf '%s' "$old_url" | sed 's/\\:/:/g; s/\\=/=/g')
filename=${old_url##*/}
case "$filename" in
  gradle-*-bin.zip)
    version=${filename#gradle-}
    version=${version%-bin.zip}
    ;;
  gradle-*-all.zip)
    version=${filename#gradle-}
    version=${version%-all.zip}
    ;;
  *)
    printf 'Unrecognized Gradle distribution URL: %s\n' "$old_url" >&2
    exit 1
    ;;
esac

mirror="https://mirrors.huaweicloud.com/gradle/gradle-${version}-bin.zip"
mirror_checksum_url="${mirror}.sha256"
official_checksum_url="https://services.gradle.org/distributions/gradle-${version}-bin.zip.sha256"

mirror_body=$(/usr/bin/curl --fail --silent --show-error --location \
  --connect-timeout 10 --max-time 45 "$mirror_checksum_url") || {
  printf 'Unable to fetch mirror checksum: %s\n' "$mirror_checksum_url" >&2
  exit 1
}
mirror_sum=$(printf '%s\n' "$mirror_body" | awk 'NR == 1 { print $1 }')
if [ "${#mirror_sum}" -ne 64 ]; then
  printf 'Mirror returned an invalid SHA-256 value.\n' >&2
  exit 1
fi
case "$mirror_sum" in
  *[!0123456789abcdefABCDEF]*)
    printf 'Mirror returned an invalid SHA-256 value.\n' >&2
    exit 1
    ;;
esac
mirror_sum=$(printf '%s' "$mirror_sum" | tr '[:upper:]' '[:lower:]')

official_sum=''
checksum_origin='official endpoint'
if official_body=$(/usr/bin/curl --fail --silent --show-error --location \
  --connect-timeout 8 --max-time 20 "$official_checksum_url" 2>/dev/null); then
  official_sum=$(printf '%s\n' "$official_body" | awk 'NR == 1 { print $1 }')
fi
if [ -z "$official_sum" ]; then
  script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
  official_sum=$(python3 - "$script_dir/distributions.json" "gradle-${version}-bin.zip" <<'PY'
import json, sys
manifest = json.load(open(sys.argv[1]))
checksums = {item['url'].rsplit('/', 1)[-1]: item['sha256'] for item in manifest['distributions']}
checksums.update(manifest.get('additional_official_checksums', {}))
print(checksums.get(sys.argv[2], ''))
PY
)
  checksum_origin='previously verified official pin in distributions.json'
fi
if [ -z "$official_sum" ]; then
  printf 'No trusted official checksum for Gradle %s; refusing to trust the mirror alone.\n' "$version" >&2
  exit 1
fi
if [ "$mirror_sum" != "$official_sum" ]; then
  printf 'Gradle mirror checksum differs from the official checksum for %s; refusing to update.\n' "$version" >&2
  exit 1
fi

current_sum=$(sed -n 's/^distributionSha256Sum=//p' "$properties" | sed -n '1p')
if [ "$old_url" = "$mirror" ] && [ "$current_sum" = "$official_sum" ]; then
  printf 'Already configured: %s\nChecksum: matches %s.\n' "$properties" "$checksum_origin"
  exit 0
fi

wrapper_dir=${properties%/*}
tmp=$(/usr/bin/mktemp "$wrapper_dir/gradle-wrapper.properties.XXXXXX")
cleanup() {
  if [ -n "${tmp:-}" ] && [ -f "$tmp" ]; then
    /bin/rm -f "$tmp"
  fi
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM
/bin/cp -p "$properties" "$tmp"
/usr/bin/awk '!/^distributionUrl=/ && !/^distributionSha256Sum=/' "$properties" > "$tmp"
printf '\ndistributionUrl=https\\://mirrors.huaweicloud.com/gradle/gradle-%s-bin.zip\n' "$version" >> "$tmp"
printf 'distributionSha256Sum=%s\n' "$mirror_sum" >> "$tmp"

if /usr/bin/cmp -s "$properties" "$tmp"; then
  printf 'Already configured: %s\n' "$properties"
  exit 0
fi

printf 'Project: %s\n' "$project_dir"
printf 'Wrapper: Gradle %s, Huawei mirror, -bin, SHA-256 pinned\n' "$version"
printf 'Checksum: matches %s.\n' "$checksum_origin"

if [ "$mode" = "--apply" ]; then
  /bin/mv "$tmp" "$properties"
  tmp=''
  printf 'Updated: %s\n' "$properties"
else
  printf 'Dry run only. Re-run with --apply to write this change.\n'
fi
