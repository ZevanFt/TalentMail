#!/usr/bin/env bash
# ─────────────────────────────────────────────────────
# TalentMail — PostgreSQL 数据库恢复脚本
#
# 用法:
#   ./scripts/restore-db.sh /var/backups/talentmail/talentmail-20260426-030000.sql.gz
#
# 注意: 恢复前会自动做一次安全备份
# ─────────────────────────────────────────────────────
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# ── 颜色 ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { printf "${GREEN}[✓]${NC} %s\n" "$*"; }
warn() { printf "${YELLOW}[!]${NC} %s\n" "$*"; }
err()  { printf "${RED}[✗]${NC} %s\n" "$*" >&2; }

# ── 参数检查 ──
if [ $# -lt 1 ]; then
    echo "用法: $0 <备份文件路径>"
    echo "示例: $0 /var/backups/talentmail/talentmail-20260426-030000.sql.gz"
    echo ""
    echo "可用备份:"
    ls -lht /var/backups/talentmail/talentmail-*.sql.gz 2>/dev/null || echo "  (无备份文件)"
    exit 1
fi

RESTORE_FILE="$1"

if [ ! -f "$RESTORE_FILE" ]; then
    err "备份文件不存在: $RESTORE_FILE"
    exit 1
fi

if [ ! -s "$RESTORE_FILE" ]; then
    err "备份文件为空: $RESTORE_FILE"
    exit 1
fi

# ── 读取配置 ──
if [ ! -f "$ROOT/.env" ]; then
    err "未找到 .env 文件: $ROOT/.env"
    exit 1
fi

set -a
# shellcheck disable=SC1091
source "$ROOT/.env"
set +a

PG_USER="${POSTGRES_USER:?POSTGRES_USER 未设置}"
PG_DB="${POSTGRES_DB:?POSTGRES_DB 未设置}"

# ── 检查容器 ──
DB_STATE=$(docker compose -f "$ROOT/docker-compose.yml" ps db --format json 2>/dev/null \
    | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('State',''))" 2>/dev/null || true)
if [ "$DB_STATE" != "running" ]; then
    err "PostgreSQL 容器未运行 (state=$DB_STATE)，请先启动: docker compose up -d db"
    exit 1
fi

# ── 安全确认 ──
warn "即将恢复数据库 ${PG_DB}，当前数据将被覆盖！"
warn "备份文件: $RESTORE_FILE"
echo ""
printf "  确认恢复？输入 YES 继续: "
read -r confirm
if [ "$confirm" != "YES" ]; then
    warn "已取消恢复"
    exit 0
fi

# ── 恢复前先做安全备份 ──
SAFETY_DIR="/var/backups/talentmail"
SAFETY_FILE="${SAFETY_DIR}/talentmail-before-restore-$(date +%Y%m%d-%H%M%S).sql.gz"
mkdir -p "$SAFETY_DIR"

log "正在做安全备份 (恢复前快照)..."
docker compose -f "$ROOT/docker-compose.yml" exec -T db \
    pg_dump -U "$PG_USER" -d "$PG_DB" --no-owner --no-acl \
    | gzip > "$SAFETY_FILE"

if [ -s "$SAFETY_FILE" ]; then
    log "安全备份完成: $SAFETY_FILE"
else
    warn "安全备份为空（数据库可能已是空的），继续恢复..."
fi

# ── 停止 backend（防止恢复时有写入冲突） ──
log "停止 backend 容器..."
docker compose -f "$ROOT/docker-compose.yml" stop backend 2>/dev/null || true

# ── 执行恢复 ──
log "正在恢复数据库..."

# 先删除所有表再恢复（pg_dump --no-owner 不含 DROP，需要手动清理）
docker compose -f "$ROOT/docker-compose.yml" exec -T db \
    psql -U "$PG_USER" -d "$PG_DB" -c "
        DO \$\$
        DECLARE r RECORD;
        BEGIN
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(r.tablename) || ' CASCADE';
            END LOOP;
        END \$\$;
    " >/dev/null 2>&1

gunzip -c "$RESTORE_FILE" | docker compose -f "$ROOT/docker-compose.yml" exec -T db \
    psql -U "$PG_USER" -d "$PG_DB" >/dev/null 2>&1

log "数据库恢复完成！"

# ── 重启 backend ──
log "重启 backend 容器..."
docker compose -f "$ROOT/docker-compose.yml" start backend

echo ""
log "恢复完成！如果遇到问题，安全备份在: $SAFETY_FILE"
