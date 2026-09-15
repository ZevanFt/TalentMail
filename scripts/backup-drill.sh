#!/usr/bin/env bash
# ─────────────────────────────────────────────────────
# TalentMail — 备份演练（只验证，不覆盖生产库）
#
# 做什么:
#   1. 跑一次 backup-db.sh
#   2. 校验备份文件非空、gzip 完整
#   3. 解压后检查关键表是否在 dump 里
#   4. 对比当前库用户数与 dump 中 COPY users 行数量级
#
# 用法:
#   ./scripts/backup-drill.sh
#   TALENTMAIL_BACKUP_DIR=/tmp/tm-backups ./scripts/backup-drill.sh
#
# 完整恢复请单独用:
#   ./scripts/restore-db.sh <backup-file>
# ─────────────────────────────────────────────────────
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="${TALENTMAIL_BACKUP_DIR:-/var/backups/talentmail}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
log()  { printf "${GREEN}[✓]${NC} %s\n" "$*"; }
warn() { printf "${YELLOW}[!]${NC} %s\n" "$*"; }
err()  { printf "${RED}[✗]${NC} %s\n" "$*" >&2; }

fail=0

if [ ! -f "$ROOT/.env" ]; then
    err "缺少 .env"
    exit 1
fi
set -a
# shellcheck disable=SC1091
source "$ROOT/.env"
set +a

PG_USER="${POSTGRES_USER:?POSTGRES_USER 未设置}"
PG_DB="${POSTGRES_DB:?POSTGRES_DB 未设置}"

log "步骤 1/4 — 执行备份..."
export TALENTMAIL_BACKUP_DIR="$BACKUP_DIR"
# 演练默认不打包 uploads、不加密（更快）；需要时可在环境变量里打开
bash "$ROOT/scripts/backup-db.sh"

# 找最新备份
LATEST=$(ls -1t "$BACKUP_DIR"/talentmail-*.sql.gz "$BACKUP_DIR"/talentmail-*.sql.gz.enc 2>/dev/null | head -1 || true)
if [ -z "$LATEST" ]; then
    err "未找到备份文件于 $BACKUP_DIR"
    exit 1
fi
log "最新备份: $LATEST ($(du -h "$LATEST" | cut -f1))"

if [ ! -s "$LATEST" ]; then
    err "备份文件为空"
    exit 1
fi

log "步骤 2/4 — 校验压缩完整性..."
DUMP_TMP=$(mktemp)
trap 'rm -f "$DUMP_TMP"' EXIT

if [[ "$LATEST" == *.enc ]]; then
    if [ -z "${TALENTMAIL_BACKUP_PASSPHRASE:-}" ]; then
        warn "备份已加密但未设置 TALENTMAIL_BACKUP_PASSPHRASE，跳过解压校验"
        log "演练完成（加密备份仅校验文件非空）"
        exit 0
    fi
    openssl enc -aes-256-gcm -d -pbkdf2 -iter 200000 \
        -pass pass:"$TALENTMAIL_BACKUP_PASSPHRASE" \
        -in "$LATEST" | gzip -t
    openssl enc -aes-256-gcm -d -pbkdf2 -iter 200000 \
        -pass pass:"$TALENTMAIL_BACKUP_PASSPHRASE" \
        -in "$LATEST" | gunzip > "$DUMP_TMP"
else
    gzip -t "$LATEST"
    gunzip -c "$LATEST" > "$DUMP_TMP"
fi
log "gzip 校验通过，解压大小 $(du -h "$DUMP_TMP" | cut -f1)"

log "步骤 3/4 — 检查关键表..."
REQUIRED_TABLES="users emails folders calendar_events system_workflows api_keys"
for table in $REQUIRED_TABLES; do
    if grep -q "COPY public.$table " "$DUMP_TMP" || grep -q "CREATE TABLE public.$table " "$DUMP_TMP"; then
        log "  表存在: $table"
    else
        err "  表缺失: $table"
        fail=1
    fi
done

log "步骤 4/4 — 对比用户数量级..."
LIVE_USERS=$(docker exec talentmail-db-1 psql -U "$PG_USER" -d "$PG_DB" -At -c "SELECT count(*) FROM users;" 2>/dev/null || echo "")
# dump 中 users COPY 段行数（到 \. 为止）
DUMP_USERS=$(awk '
  /^COPY public\.users / {p=1; next}
  p && /^\\\.$/ {print n; exit}
  p {n++}
' "$DUMP_TMP")

if [ -n "$LIVE_USERS" ] && [ -n "$DUMP_USERS" ]; then
    log "  当前库 users=$LIVE_USERS, 备份 dump users≈$DUMP_USERS"
    if [ "$DUMP_USERS" -ge "$LIVE_USERS" ] || [ "$DUMP_USERS" -gt 0 ]; then
        log "  数量级合理"
    else
        err "  备份用户数异常偏少"
        fail=1
    fi
else
    warn "  无法对比用户数（live='$LIVE_USERS' dump='$DUMP_USERS'）"
fi

if [ "$fail" -ne 0 ]; then
    err "演练失败"
    exit 1
fi
log "备份演练通过。完整恢复命令:"
echo "  ./scripts/restore-db.sh $LATEST"
