#!/usr/bin/env bash
# deploy.sh —— 把 manifest 的 shell 声明落到本机
#
# 用法:
#   deploy.sh            部署：对齐 ~/.zshrc 的补全块 + 落位 assets/
#   deploy.sh --check    只读：报告差异，不做任何改动
#   deploy.sh --help
#
# 写入范围（仅这两处）:
#   ~/.zshrc                                  仅起止标记之间的受管块
#   ~/.local/share/zsh/site-functions/        无主资产的落点
# ~/.zshrc 回滚点只保留一个：已有唯一备份原样保留；没有时才创建；多个时拒绝写入。
#
# 边界:
#   - 本脚本**不安装任何 brew 包**。装包属于对账协商流程，由 Agent 在用户逐项确认后执行
#   - 保留归属不明的已有文件和链接
#   - 写 ~/.zshrc 前先 /bin/zsh -n 校验，不过则不落盘
set -uo pipefail

REPO_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
MANIFEST="$REPO_DIR/macos/manifest"
ASSETS_DIR="$MANIFEST/assets"
SNIPPET="$MANIFEST/zsh/zshrc.snippet"
ZSHRC="${ZSHRC_OVERRIDE:-$HOME/.zshrc}"
SITE_FUNCS="$HOME/.local/share/zsh/site-functions"
STATE_DIR="${ENV_STATE_DIR:-$HOME/.local/state/env}"

RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; NC=$'\033[0m'
info() { printf '%s\n' "$*"; }
ok()   { printf '%s\n' "${GREEN}✓${NC} $*"; }
warn() { printf '%s\n' "${YELLOW}!${NC} $*"; }
err()  { printf '%s\n' "${RED}✗${NC} $*" >&2; }

TMP="$(mktemp -d "${TMPDIR:-/tmp}/env-deploy.XXXXXX")" || exit 1
trap 'case "$TMP" in */env-deploy.*) /bin/rm -rf "$TMP" ;; esac' EXIT

find_zsh_backup() {
  local candidate count=0 found=""
  BACKUP_EXISTS=false
  for candidate in "$STATE_DIR"/backup/zshrc.*.bak; do
    [ -f "$candidate" ] || continue
    count=$((count + 1))
    found="$candidate"
  done
  if [ "$count" -gt 1 ]; then
    err "回滚目录中发现 $count 个 zshrc 备份，拒绝再生成副本；请先保留一个后重试。"
    return 1
  fi
  if [ "$count" -eq 1 ]; then
    BACKUP_FILE="$found"
    BACKUP_EXISTS=true
  else
    BACKUP_FILE="$STATE_DIR/backup/zshrc.latest.bak"
  fi
}

case "${1:-deploy}" in
  --help|-h|help)
    awk 'NR > 1 && /^set -uo pipefail/ { exit } NR > 1 { sub(/^# ?/, ""); print }' "$0"
    exit 0 ;;
  --check|check) CHECK=true ;;
  deploy) CHECK=false ;;
  *) err "未知子命令: $1"; info "可用: deploy | --check | --help"; exit 2 ;;
esac

[ -f "$SNIPPET" ] || { err "缺失配置片段: $SNIPPET"; exit 1; }

newf="$TMP/zshrc.new"
python3 "$REPO_DIR/scripts/shell_config.py" render "$ZSHRC" "$SNIPPET" "$newf" || exit 2
if ! /bin/zsh -n "$newf" 2>"$TMP/zshrc.err"; then
  err "生成的新配置语法检查未通过，已放弃写入："
  sed 's/^/    /' "$TMP/zshrc.err" >&2
  exit 2
fi

# 在写入任何配置前检查所有资产，冲突时整次部署保持原状。
if [ -L "$SITE_FUNCS" ]; then
  err "资产目录为软链接，请先确认归属: $SITE_FUNCS"; exit 2
fi
for f in "$ASSETS_DIR"/*; do
  [ -f "$f" ] || continue
  t="$SITE_FUNCS/$(basename "$f")"
  if [ -L "$t" ] || { [ -e "$t" ] && ! cmp -s "$f" "$t"; }; then
    err "已有资产归属或内容不同，保留原状: $t"; exit 2
  fi
done

changes=0

# ---------- 1. 对齐 ~/.zshrc ----------
info "${GREEN}▸${NC} shell 配置块"
if cmp -s "$ZSHRC" "$newf"; then
  ok "已与 zshrc.snippet 一致，跳过"
else
  warn "与 zshrc.snippet 不一致（将对齐）"; changes=$((changes + 1))
fi

if [ "$changes" -gt 0 ] && [ "$CHECK" != "true" ]; then
  if [ -f "$ZSHRC" ]; then
    find_zsh_backup || exit 1
    if [ "$BACKUP_EXISTS" = "true" ]; then
      info "  保留现有唯一回滚点: ${BACKUP_FILE/#$HOME/~}"
    else
      mkdir -p "$STATE_DIR/backup" || { err "无法创建备份目录"; exit 1; }
      cp "$ZSHRC" "$TMP/zshrc.backup.new" || { err "备份暂存失败，中止"; exit 1; }
      mv "$TMP/zshrc.backup.new" "$BACKUP_FILE" || { err "创建唯一回滚备份失败，中止"; exit 1; }
      info "  已创建唯一回滚点: ${BACKUP_FILE/#$HOME/~}"
    fi
  fi
  # 同目录原子替换，保留已有配置文件的权限。
  staged="$(mktemp "${ZSHRC}.XXXXXX")" || exit 1
  if { [ ! -f "$ZSHRC" ] || cp -p "$ZSHRC" "$staged"; } && cat "$newf" > "$staged" && mv -f "$staged" "$ZSHRC"; then
    ok "已对齐 ~/.zshrc 受管块"
  else
    /bin/rm -f "$staged"
    err "写入 $ZSHRC 失败"; exit 1
  fi
fi

# ---------- 2. 落位无主资产 ----------
info ""
info "${GREEN}▸${NC} 无主资产 → ${SITE_FUNCS/#$HOME/~}"
if [ ! -d "$ASSETS_DIR" ] || [ -z "$(ls -A "$ASSETS_DIR" 2>/dev/null)" ]; then
  info "  无 assets，跳过"
else
  for f in "$ASSETS_DIR"/*; do
    [ -f "$f" ] || continue
    b="$(basename "$f")"
    t="$SITE_FUNCS/$b"
    if [ -e "$t" ] && cmp -s "$f" "$t"; then
      ok "已落位且一致: $b"; continue
    fi
    changes=$((changes + 1))
    if [ "$CHECK" = "true" ]; then
      if [ -e "$t" ]; then warn "内容不同，待落位: $b"; else warn "未落位: $b"; fi
      continue
    fi
    mkdir -p "$SITE_FUNCS" || { err "无法创建落点目录: $SITE_FUNCS"; exit 1; }
    # 独占创建，防止预检后出现的新文件或软链接被覆盖。
    (set -o noclobber; cat "$f" > "$t") || { err "落位失败: $b"; exit 1; }
    ok "已落位: $b"
  done
fi

# ---------- 汇总 ----------
info ""
if [ "$CHECK" = "true" ]; then
  if [ "$changes" -eq 0 ]; then
    ok "无差异。"
  else
    warn "$changes 处差异待处理。执行 $0 以落位。"
    exit 1
  fi
else
  ok "完成。新开终端（或 exec zsh）后生效。"
  info "复核: $REPO_DIR/scripts/probe.sh"
fi
