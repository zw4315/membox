#!/usr/bin/env bash
set -euo pipefail

#######################################
# membox-sync.sh — minimal & robust
#######################################

# -------- defaults (hard-coded, no env) --------
LOCAL_ROOT="$HOME/gdshare"
REMOTE_ROOT="gdrive:gdshare"
LOCAL_BACKUP_ROOT="$HOME/gdshare_backup"
REMOTE_BACKUP_ROOT="gdrive:gdshare_backup"

STATS="10s"
EXCLUDES=(
  ".git/**"
  "*.tmp"
)

# -------- args --------
SUBCMD="${1:-}"
shift || true

usage() {
  echo "Usage:"
  echo "  membox-sync.sh [--dry-run] [--no-progress] sync-down"
  echo "  membox-sync.sh [--dry-run] [--no-progress] sync-up"
}

DRY_RUN=0
NO_PROGRESS=0

# 先解析选项
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)      DRY_RUN=1 ;;
    --no-progress)  NO_PROGRESS=1 ;;
    -h|--help)      usage; exit 0 ;;
    --)             shift; break ;;   # 显式结束 option
    -*)             echo "Unknown option: $1"; usage; exit 1 ;;
    *)              break ;;           # 遇到第一个非 option，停止解析
  esac
  shift
done

# 再取 subcmd
SUBCMD="${1:-}"
shift || true

[[ -n "$SUBCMD" ]] || { echo "Missing subcmd"; usage; exit 1; }

case "$SUBCMD" in
  sync-down) ;;
  sync-up) ;;
  *) echo "Unknown subcmd: $SUBCMD"; usage; exit 1 ;;
esac
# -------- common rclone args --------
RCLONE_ARGS=(
  "--stats=$STATS"
  "--stats-one-line"
  "--fast-list"
)

for ex in "${EXCLUDES[@]}"; do
  RCLONE_ARGS+=( "--exclude" "$ex" )
done

[[ "$NO_PROGRESS" -eq 1 ]] || RCLONE_ARGS+=( "--progress" )
[[ "$DRY_RUN" -eq 1 ]] && RCLONE_ARGS+=( "--dry-run" )

SUFFIX=".$(date +%Y-%m-%d_%H-%M-%S).bak"
TODAY="$(date +%F)"

log() {
  printf "%s %s\n" "$(date '+%F %T')" "$*"
}

# -------- commands --------
case "$SUBCMD" in
  sync-down)
    BACKUP_DIR="$LOCAL_BACKUP_ROOT/$TODAY"
    mkdir -p "$BACKUP_DIR"

    log "== membox sync-down =="
    log "Remote   : $REMOTE_ROOT"
    log "Local    : $LOCAL_ROOT"
    log "Backup   : $BACKUP_DIR"
    log "Mode     : $([[ $DRY_RUN -eq 1 ]] && echo DRY-RUN || echo LIVE)"

    log ">>> rclone sync (remote → local)"
    rclone sync "$REMOTE_ROOT" "$LOCAL_ROOT" \
      --backup-dir "$BACKUP_DIR" \
      --suffix "$SUFFIX" \
      "${RCLONE_ARGS[@]}"
    ;;

  sync-up)
    BACKUP_DIR="$REMOTE_BACKUP_ROOT/$TODAY"

    log "== membox sync-up =="
    log "Local    : $LOCAL_ROOT"
    log "Remote   : $REMOTE_ROOT"
    log "Backup   : $BACKUP_DIR"
    log "Mode     : $([[ $DRY_RUN -eq 1 ]] && echo DRY-RUN || echo LIVE)"

    log ">>> rclone sync (local → remote)"
    rclone sync "$LOCAL_ROOT" "$REMOTE_ROOT" \
      --backup-dir "$BACKUP_DIR" \
      --suffix "$SUFFIX" \
      "${RCLONE_ARGS[@]}"
    ;;

  *)
    echo "Unknown subcmd: $SUBCMD"
    exit 1
    ;;
esac

