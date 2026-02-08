#!/bin/bash

# =============================================================================
# TalentMail 数据库重置脚本
# =============================================================================
# 用途：清空现有数据库并从头运行所有迁移
# 警告：此操作会删除所有数据！仅用于开发或首次生产部署
#
# 用法:
#   生产环境: ./scripts/reset_database.sh prod
#   开发环境: ./scripts/reset_database.sh dev
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

ENV=${1:-dev}

if [ "$ENV" = "prod" ]; then
    COMPOSE_FILE="docker-compose.yml"
    ENV_FILES="--env-file .env --env-file .env.domains"
elif [ "$ENV" = "dev" ]; then
    COMPOSE_FILE="docker-compose.dev.yml"
    ENV_FILES="--env-file .env"
else
    error "未知环境: $ENV"
    echo "用法: $0 [dev|prod]"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${RED}⚠️  警告：此操作将删除所有数据！${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "确定要重置 $ENV 环境的数据库吗？输入 'yes' 确认: " confirm

if [ "$confirm" != "yes" ]; then
    info "操作已取消"
    exit 0
fi

echo ""
info "🛑 停止所有服务..."
docker compose -f $COMPOSE_FILE down 2>/dev/null || true

info "🗑️  删除数据库卷..."
docker volume rm talentmail_postgres_data 2>/dev/null || true

info "🚀 重新启动服务..."
docker compose -f $COMPOSE_FILE $ENV_FILES up -d db

info "⏳ 等待数据库就绪..."
sleep 10

info "🔄 运行数据库迁移..."
if [ "$ENV" = "prod" ]; then
    docker compose -f $COMPOSE_FILE $ENV_FILES up -d backend
    sleep 5
    docker compose -f $COMPOSE_FILE $ENV_FILES exec -T backend alembic upgrade head
else
    docker compose -f $COMPOSE_FILE $ENV_FILES up -d backend
    sleep 5
    docker compose -f $COMPOSE_FILE $ENV_FILES exec -T backend alembic upgrade head
fi

info "▶️  启动所有服务..."
docker compose -f $COMPOSE_FILE $ENV_FILES up -d

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
success "🎉 数据库重置完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"