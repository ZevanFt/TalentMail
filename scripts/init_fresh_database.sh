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

info "🛑 停止所有服务并彻底清理..."
docker compose -f $COMPOSE_FILE down -v --remove-orphans 2>/dev/null || true

info "🗑️  确保数据库卷已删除..."
docker volume rm talentmail_postgres_data 2>/dev/null || true

# 列出所有 talentmail 相关的卷并删除
info "🗑️  删除所有 talentmail 相关卷..."
docker volume ls -q | grep -i talentmail | xargs -r docker volume rm 2>/dev/null || true

info "🧹 清理系统缓存..."
docker system prune -f 2>/dev/null || true
docker volume prune -f 2>/dev/null || true

info "🚀 重新启动数据库..."
docker compose -f $COMPOSE_FILE $ENV_FILES up -d db

info "⏳ 等待数据库完全就绪..."
sleep 10

info "🚀 启动后端服务（用于执行数据库操作）..."
docker compose -f $COMPOSE_FILE $ENV_FILES up -d backend
sleep 10

info "🔧 直接用 SQL 创建所有表..."
docker compose -f $COMPOSE_FILE $ENV_FILES exec -T backend python << 'PYTHON_SCRIPT'
import sys
from sqlalchemy import text
from db.database import engine

# 先删除所有现有表（如果存在）
print("清理现有数据库对象...")
with engine.connect() as conn:
    # 删除所有表
    conn.execute(text("DROP SCHEMA public CASCADE"))
    conn.execute(text("CREATE SCHEMA public"))
    conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
    conn.commit()
    print("数据库已清理")

# 现在创建所有表
print("正在创建所有表...")
from db.database import Base
from db.models import *

Base.metadata.create_all(bind=engine)
print("表创建完成！")

# 验证表是否创建成功
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"数据库中共有 {len(tables)} 个表:")
for t in sorted(tables):
    print(f"  - {t}")
PYTHON_SCRIPT

if [ $? -ne 0 ]; then
    error "创建表失败！"
    exit 1
fi

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