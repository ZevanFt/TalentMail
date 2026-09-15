#!/usr/bin/env bash
# ─────────────────────────────────────────────────────
# TalentMail — PostgreSQL + uploads 备份脚本
#
# 用法:
#   ./scripts/backup-db.sh
#   systemctl start talentmail-backup
#
# 环境变量:
#   TALENTMAIL_BACKUP_DIR       备份目录，默认 /var/backups/talentmail
#   TALENTMAIL_BACKUP_KEEP      保留份数，默认 7
#   TALENTMAIL_BACKUP_ENCRYPT   设为 1 启用 openssl AES-256-GCM 加密
#   TALENTMAIL_BACKUP_PASSPHRASE 加密口令（启用加密时必填）
#   TALENTMAIL_BACKUP_UPLOADS   设为 1 同时打包 uploads 附件目录
#   TALENTMAIL_UPLOADS_DIR      uploads 路径，默认 backend/uploads
# ─────────────────────────────────────────────────────
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="${TALENTMAIL_BACKUP_DIR:-/var/backups/talentmail}"
KEEP_COUNT="${TALENTMAIL_BACKUP_KEEP:-7}"
ENCRYPT="${TALENTMAIL_BACKUP_ENCRYPT:-0}"
PASSPHRASE="${TALENTMAIL_BACKUP_PASSPHRASE:-}"
BACKUP_UPLOADS="${TALENTMAIL_BACKUP_UPLOADS:-0}"
UPLOADS_DIR="${TALENTMAIL_UPLOADS_DIR:-$ROOT/backend/uploads}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

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

set -a
# shellcheck disable=SC1091
source "$ROOT/.env"
set +a

PG_USER="${POSTGRES_USER:?POSTGRES_USER 未设置}"
PG_DB="${POSTGRES_DB:?POSTGRES_DB 未设置}"

if [ "$ENCRYPT" = "1" ] && [ -z "$PASSPHRASE" ]; then
    err "已启用加密但未设置 TALENTMAIL_BACKUP_PASSPHRASE"
    exit 1
fi

# 兼容 docker compose / docker-compose
if docker compose version >/dev/null 2>&1; then
    COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE=(docker-compose)
else
    err "未找到 docker compose 或 docker-compose"
    exit 1
fi

DB_STATE=$("${COMPOSE[@]}" -f "$ROOT/docker-compose.yml" ps db 2>/dev/null | grep -i running || true)
# 容器名直接探测（兼容旧 compose / Windows）
if [ -z "$DB_STATE" ]; then
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -qE 'talentmail-db|[-_]db[-_]1?$'; then
        DB_STATE="running"
    fi
fi
if [ -z "$DB_STATE" ]; then
    err "PostgreSQL 容器未运行，请先启动: docker compose up -d db"
    exit 1
fi

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR" 2>/dev/null || true

# ── 数据库备份 ──
DB_BASE="talentmail-${TIMESTAMP}.sql.gz"
DB_OUT="${BACKUP_DIR}/${DB_BASE}"
TMP_FILE="${BACKUP_DIR}/.${DB_BASE}.tmp"

log "开始备份 TalentMail 数据库 (${PG_DB})..."
# 优先用已知容器名，避免 compose 项目名差异
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^talentmail-db'; then
    docker exec talentmail-db-1 pg_dump -U "$PG_USER" -d "$PG_DB" --no-owner --no-acl \
        | gzip > "$TMP_FILE"
else
    "${COMPOSE[@]}" -f "$ROOT/docker-compose.yml" exec -T db \
        pg_dump -U "$PG_USER" -d "$PG_DB" --no-owner --no-acl \
        | gzip > "$TMP_FILE"
fi

if [ ! -s "$TMP_FILE" ]; then
    err "备份文件为空，备份失败！"
    rm -f "$TMP_FILE"
    exit 1
fi

if [ "$ENCRYPT" = "1" ]; then
    log "使用 openssl AES-256-GCM 加密..."
    ENC_TMP="${TMP_FILE}.enc"
    # -pbkdf2 提高抗暴力破解能力；salt 每次随机
    openssl enc -aes-256-gcm -pbkdf2 -iter 200000 -salt \
        -pass pass:"$PASSPHRASE" -in "$TMP_FILE" -out "$ENC_TMP"
    mv "$ENC_TMP" "$DB_OUT.enc"
    rm -f "$TMP_FILE"
    DB_OUT="${DB_OUT}.enc"
    DB_BASE="${DB_BASE}.enc"
else
    mv "$TMP_FILE" "$DB_OUT"
fi

chmod 600 "$DB_OUT" 2>/dev/null || true
BACKUP_SIZE=$(du -h "$DB_OUT" | cut -f1)
log "数据库备份完成: ${DB_OUT} (${BACKUP_SIZE})"

# ── uploads 备份（可选） ──
if [ "$BACKUP_UPLOADS" = "1" ]; then
    if [ -d "$UPLOADS_DIR" ]; then
        UP_BASE="talentmail-uploads-${TIMESTAMP}.tar.gz"
        UP_OUT="${BACKUP_DIR}/${UP_BASE}"
        log "打包 uploads: ${UPLOADS_DIR} ..."
        tar -czf "$UP_OUT.tmp" -C "$(dirname "$UPLOADS_DIR")" "$(basename "$UPLOADS_DIR")"
        if [ "$ENCRYPT" = "1" ]; then
            openssl enc -aes-256-gcm -pbkdf2 -iter 200000 -salt \
                -pass pass:"$PASSPHRASE" -in "$UP_OUT.tmp" -out "$UP_OUT.enc"
            rm -f "$UP_OUT.tmp"
            UP_OUT="${UP_OUT}.enc"
        else
            mv "$UP_OUT.tmp" "$UP_OUT"
        fi
        chmod 600 "$UP_OUT" 2>/dev/null || true
        log "uploads 备份完成: ${UP_OUT} ($(du -h "$UP_OUT" | cut -f1))"
    else
        warn "uploads 目录不存在，跳过: ${UPLOADS_DIR}"
    fi
fi

# ── 轮转旧备份 ──
if ! [[ "$KEEP_COUNT" =~ ^[1-9][0-9]*$ ]]; then
    warn "TALENTMAIL_BACKUP_KEEP 不是有效正整数 ($KEEP_COUNT)，跳过轮转"
    exit 0
fi

rotate() {
    local pattern="$1"
    local count=0
    while IFS= read -r old_backup; do
        count=$((count + 1))
        if [ "$count" -gt "$KEEP_COUNT" ]; then
            rm -f "$old_backup"
            log "已删除旧备份: $(basename "$old_backup")"
        fi
    done < <(ls -1t ${BACKUP_DIR}/${pattern} 2>/dev/null || true)
}

rotate "talentmail-*.sql.gz"
rotate "talentmail-*.sql.gz.enc"
rotate "talentmail-uploads-*.tar.gz"
rotate "talentmail-uploads-*.tar.gz.enc"

REMAINING=$(ls -1 "${BACKUP_DIR}"/talentmail-* 2>/dev/null | wc -l)
log "当前备份文件数: ${REMAINING}"
