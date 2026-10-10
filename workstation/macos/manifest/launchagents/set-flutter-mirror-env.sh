#!/bin/sh
set -eu

mirror_bypass_hosts='localhost,127.0.0.1,::1,.local,.aliyun.com,.huaweicloud.com,.flutter-io.cn'

set_mirror_bypass_hosts() {
  /bin/launchctl setenv NO_PROXY "$mirror_bypass_hosts"
  /bin/launchctl setenv no_proxy "$mirror_bypass_hosts"
}

case "${1:-mirror}" in
  mirror)
    /bin/launchctl setenv PUB_HOSTED_URL https://pub.flutter-io.cn
    /bin/launchctl setenv FLUTTER_STORAGE_BASE_URL https://storage.flutter-io.cn
    set_mirror_bypass_hosts
    ;;
  official)
    /bin/launchctl unsetenv PUB_HOSTED_URL
    /bin/launchctl unsetenv FLUTTER_STORAGE_BASE_URL
    set_mirror_bypass_hosts
    ;;
  *)
    printf '%s\n' 'Usage: set-flutter-mirror-env.sh [mirror|official]' >&2
    exit 2
    ;;
esac
