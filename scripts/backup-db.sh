#!/usr/bin/env bash
# ─────────────────────────────────────────────────────
# TalentMail — PostgreSQL 数据库备份脚本
#
# 用法:
#   ./scripts/backup-db.sh              # 交互式执行
#   systemctl start talentmail-backup   # systemd timer 触发
#
# 备份位置: /var/backups/talentmail/
# 保留策略: 最近 7 份（可通过 TALENTMAIL_BACKUP_KEEP 覆盖）
# ─────────────────────────────────────────────────────
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="${TALENTMAIL_BACKUP_DIR:-/var/backups/talentmail}"
KEEP_COUNT="${TALENTMAIL_BACKUP_KEEP:-7}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_FILE="talentmail-${TIMESTAMP}.sql.gz"
TMP_FILE="${BACKUP_DIR}/.${BACKUP_FILE}.tmp"

# ── 颜色 ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { printf "${GREEN}[✓]${NC} %s\n" "$*"; }
warn() { printf "${YELLOW}[!]${NC} %s\n" "$*"; }
err()  { printf "${RED}[✗]${NC} %s\n" "$*" >&2; }

# ── 前置检查 ──
if [ ! -f "$ROOT/.env" ]; then
    err "未找到 .env 文件: $ROOT/.env"
    exit 1
fi

# 从 .env 读取数据库配置
set -a
# shellcheck disable=SC1091
source "$ROOT/.env"
set +a

PG_USER="${POSTGRES_USER:?POSTGRES_USER 未设置}"
PG_DB="${POSTGRES_DB:?POSTGRES_DB 未设置}"

# 检查 docker compose 可用
DB_STATE=$(docker compose -f "$ROOT/docker-compose.yml" ps db --format json 2>/dev/null \
    | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('State',''))" 2>/dev/null || true)
if [ "$DB_STATE" != "running" ]; then
    err "PostgreSQL 容器未运行 (state=$DB_STATE)，请先启动: docker compose up -d db"
    exit 1
fi

# ── 创建备份目录 ──
mkdir -p "$BACKUP_DIR"

# ── 执行备份 ──
log "开始备份 TalentMail 数据库 (${PG_DB})..."

docker compose -f "$ROOT/docker-compose.yml" exec -T db \
    pg_dump -U "$PG_USER" -d "$PG_DB" --no-owner --no-acl \
    | gzip > "$TMP_FILE"

# ── 校验 ──
if [ ! -s "$TMP_FILE" ]; then
    err "备份文件为空，备份失败！"
    rm -f "$TMP_FILE"
    exit 1
fi

# 原子重命名
mv "$TMP_FILE" "${BACKUP_DIR}/${BACKUP_FILE}"
BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)
log "备份完成: ${BACKUP_DIR}/${BACKUP_FILE} (${BACKUP_SIZE})"

# ── 轮转旧备份 ──
if ! [[ "$KEEP_COUNT" =~ ^[1-9][0-9]*$ ]]; then
    warn "TALENTMAIL_BACKUP_KEEP 不是有效正整数 ($KEEP_COUNT)，跳过轮转"
    exit 0
fi

# 按时间排序，删除超出保留数量的旧文件
BACKUP_COUNT=0
while IFS= read -r old_backup; do
    BACKUP_COUNT=$((BACKUP_COUNT + 1))
    if [ "$BACKUP_COUNT" -gt "$KEEP_COUNT" ]; then
        rm -f "$old_backup"
        log "已删除旧备份: $(basename "$old_backup")"
    fi
done < <(ls -1t "${BACKUP_DIR}"/talentmail-*.sql.gz 2>/dev/null)

REMAINING=$(ls -1 "${BACKUP_DIR}"/talentmail-*.sql.gz 2>/dev/null | wc -l)
log "当前备份数: ${REMAINING}/${KEEP_COUNT}"
