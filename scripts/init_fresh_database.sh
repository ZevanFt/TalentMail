#!/bin/bash

# =============================================================================
# TalentMail 全新数据库初始化脚本
# =============================================================================
# 用途：直接从 SQLAlchemy models 创建所有表，跳过历史迁移
# 适用于：首次全新部署，数据库完全为空的情况
#
# 用法:
#   生产环境: ./scripts/init_fresh_database.sh prod
#   开发环境: ./scripts/init_fresh_database.sh dev
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
echo -e "${BLUE}🚀 TalentMail 全新数据库初始化${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

info "🛑 停止所有服务..."
docker compose -f $COMPOSE_FILE down 2>/dev/null || true

info "🗑️  删除数据库卷..."
docker volume rm talentmail_postgres_data 2>/dev/null || true

info "🚀 启动数据库..."
docker compose -f $COMPOSE_FILE $ENV_FILES up -d db

info "⏳ 等待数据库就绪..."
sleep 10

info "🚀 启动后端服务..."
docker compose -f $COMPOSE_FILE $ENV_FILES up -d backend
sleep 5

info "🔧 从 Models 直接创建数据库表..."
docker compose -f $COMPOSE_FILE $ENV_FILES exec -T backend python -c "
from db.database import engine, Base
from db.models import user, template, workflow, billing, drive, features, system

print('正在创建所有表...')
Base.metadata.create_all(bind=engine)
print('表创建完成！')
"

info "📝 标记迁移为最新状态..."
docker compose -f $COMPOSE_FILE $ENV_FILES exec -T backend alembic stamp head

info "▶️  启动所有服务..."
docker compose -f $COMPOSE_FILE $ENV_FILES up -d

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
success "🎉 数据库初始化完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "现在数据库已包含所有最新的表结构。"
echo "后续更新使用 ./deploy.sh 即可正常运行增量迁移。"
echo ""