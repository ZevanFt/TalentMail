#!/bin/bash

# =============================================================================
# TalentMail 生产环境部署脚本
# =============================================================================
# 用法: ./deploy.sh [选项]
#
# 选项:
#   --fresh    全新部署（清空数据库重新创建）
#   --migrate  迁移部署（保留数据，仅更新代码和运行迁移）
#   --auto     自动检测模式（默认）
#
# 部署前请确保:
#   1. 已修改 config.json 中的生产环境配置
#   2. 已创建 .env 文件并填写所有必需变量
#   3. DNS 已正确配置指向此服务器
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印函数
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

run_alembic_migration() {
    local MIGRATION_LOG
    set +e
    MIGRATION_LOG=$(docker compose --env-file .env --env-file .env.domains exec -T backend alembic upgrade head 2>&1)
    local status=$?
    set -e

    if [ $status -eq 0 ]; then
        echo "$MIGRATION_LOG"
        return 0
    fi

    echo "$MIGRATION_LOG"
    if echo "$MIGRATION_LOG" | grep -qi "Multiple head revisions"; then
        warn "检测到 Alembic 多 head，自动尝试 alembic upgrade heads..."
        docker compose --env-file .env --env-file .env.domains exec -T backend alembic upgrade heads
        return $?
    fi

    return $status
}

# 解析命令行参数
DEPLOY_MODE=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --fresh)
            DEPLOY_MODE="fresh"
            shift
            ;;
        --migrate)
            DEPLOY_MODE="migrate"
            shift
            ;;
        --auto)
            DEPLOY_MODE="auto"
            shift
            ;;
        *)
            echo "未知选项: $1"
            echo "用法: $0 [--fresh|--migrate|--auto]"
            exit 1
            ;;
    esac
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${CYAN}🚀 TalentMail 生产环境部署${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 如果没有通过命令行指定模式，显示交互式菜单
if [ -z "$DEPLOY_MODE" ]; then
    echo "请选择部署模式："
    echo ""
    echo -e "  ${GREEN}[A]${NC} 🆕 全新部署 (Fresh Deploy)"
    echo "      - 清空现有数据库，从头创建所有表"
    echo "      - 适用于首次部署或需要重置数据库"
    echo -e "      ${RED}⚠️  警告：会删除所有现有数据！${NC}"
    echo ""
    echo -e "  ${GREEN}[B]${NC} 📦 迁移部署 (Migrate Deploy)"
    echo "      - 保留现有数据，仅运行数据库迁移"
    echo "      - 适用于代码更新、功能升级"
    echo ""
    echo -e "  ${GREEN}[C]${NC} 🔍 自动检测 (Auto Detect)"
    echo "      - 自动检测数据库状态并选择合适的方式"
    echo ""
    read -p "请输入选项 [A/B/C]: " choice
    
    case $choice in
        [Aa])
            DEPLOY_MODE="fresh"
            ;;
        [Bb])
            DEPLOY_MODE="migrate"
            ;;
        [Cc]|"")
            DEPLOY_MODE="auto"
            ;;
        *)
            error "无效选项！"
            exit 1
            ;;
    esac
fi

# 如果选择全新部署，需要二次确认
if [ "$DEPLOY_MODE" = "fresh" ]; then
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}⚠️  警告：全新部署将删除所有现有数据！${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    read -p "确定要继续吗？请输入 'YES' 确认: " confirm
    if [ "$confirm" != "YES" ]; then
        info "操作已取消"
        exit 0
    fi
fi

echo ""
info "部署模式: $DEPLOY_MODE"
echo ""

# 从 .env 文件读取变量值（与 dev.sh 保持一致）
get_env_value() {
    local key=$1
    grep -E "^${key}=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'"
}

# 生成 dovecot-sql.conf.ext 配置文件（与 dev.sh 保持一致）
generate_dovecot_sql_config() {
    info "🔧 生成 Dovecot SQL 配置文件..."
    
    local POSTGRES_USER=$(get_env_value "POSTGRES_USER")
    local POSTGRES_PASSWORD=$(get_env_value "POSTGRES_PASSWORD")
    local POSTGRES_DB=$(get_env_value "POSTGRES_DB")
    
    if [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ] || [ -z "$POSTGRES_DB" ]; then
        error "无法从 .env 文件读取数据库配置！"
        exit 1
    fi
    
    # 从模板生成配置文件
    if [ -f "config/mail/dovecot-sql.conf.ext.template" ]; then
        sed -e "s/__POSTGRES_USER__/${POSTGRES_USER}/g" \
            -e "s/__POSTGRES_PASSWORD__/${POSTGRES_PASSWORD}/g" \
            -e "s/__POSTGRES_DB__/${POSTGRES_DB}/g" \
            config/mail/dovecot-sql.conf.ext.template > config/mail/dovecot-sql.conf.ext
        success "已生成 config/mail/dovecot-sql.conf.ext"
    else
        error "未找到模板文件 config/mail/dovecot-sql.conf.ext.template"
        exit 1
    fi
}

# 同步运行时 mailserver 配置（data 目录不受 git 管理）
sync_mail_runtime_config() {
    info "🔄 同步 mailserver 运行时配置..."

    local runtime_dir="data/mailserver/config"
    mkdir -p "${runtime_dir}"

    if [ -f "config/mail/user-patches.sh" ]; then
        cp config/mail/user-patches.sh "${runtime_dir}/user-patches.sh"
        chmod +x "${runtime_dir}/user-patches.sh"
        success "已同步 user-patches.sh 到 ${runtime_dir}"
    else
        warn "未找到 config/mail/user-patches.sh，跳过同步"
    fi
}

# 全新部署时需要清空数据库卷
if [ "$DEPLOY_MODE" = "fresh" ]; then
    info "🛑 停止所有服务并清空数据..."
    docker compose down -v --remove-orphans 2>/dev/null || true
    
    info "🗑️  删除数据库卷..."
    docker volume rm talentmail_postgres_data 2>/dev/null || true
    docker volume ls -q | grep -i talentmail | xargs -r docker volume rm 2>/dev/null || true
else
    # 1. 停止现有服务
    info "🛑 停止现有服务..."
    docker compose down 2>/dev/null || true
fi

# 2. 检查 .env 文件
if [ ! -f .env ]; then
    error "未找到 .env 文件！"
    info "请运行 'cp .env.example .env' 并填写必需的配置变量。"
    exit 1
fi

# 3. 检查必需的环境变量
info "🔍 检查环境变量..."
REQUIRED_VARS=(
    DATABASE_URL_DOCKER
    REFRESH_TOKEN_EXPIRE_DAYS
    JWT_ALGORITHM
    ADMIN_PASSWORD
    SECRET_KEY
    POSTGRES_PASSWORD
    POSTGRES_USER
    POSTGRES_DB
)

missing=()
for v in "${REQUIRED_VARS[@]}"; do
    if ! grep -qE "^${v}=" .env; then
        missing+=("$v")
    fi
done

if [ ${#missing[@]} -ne 0 ]; then
    error "以下必需的环境变量在 .env 中缺失："
    for v in "${missing[@]}"; do
        echo "  - $v"
    done
    exit 1
fi
success "环境变量检查通过"

# 4. 根据 config.json 生成生产环境域名配置
info "⚙️  根据 config.json 生成域名配置文件 (.env.domains)..."
python3 scripts/generate_domains.py
if [ $? -ne 0 ]; then
    error "生成 .env.domains 文件失败，请检查错误信息。"
    exit 1
fi

# 5. 生成 Dovecot SQL 配置文件（与开发环境保持一致）
generate_dovecot_sql_config

# 5.1 同步运行时 mailserver 配置（修复迁移部署后未更新 user-patches 的问题）
sync_mail_runtime_config

# 6. 构建 Docker 镜像
info "🏗️  构建 Docker 镜像..."
docker compose --env-file .env --env-file .env.domains build

# 7. 启动服务
info "▶️  启动服务..."
docker compose --env-file .env --env-file .env.domains up -d

# 8. 等待数据库就绪
info "⏳ 等待数据库就绪..."
sleep 10

# 9. 根据部署模式执行数据库操作
FIRST_DEPLOY=false

if [ "$DEPLOY_MODE" = "fresh" ]; then
    # 全新部署：直接从 models 创建所有表
    info "🆕 执行全新部署..."
    
    info "🔧 从 Models 创建数据库表..."
    docker compose --env-file .env --env-file .env.domains exec -T backend python << 'PYTHON_SCRIPT'
from db.database import engine, Base
from db.models import *
import sys

print("正在创建所有表...")
try:
    Base.metadata.create_all(bind=engine)
    print("表创建成功！")
except Exception as e:
    print(f"表创建失败: {e}")
    sys.exit(1)
PYTHON_SCRIPT

    if [ $? -ne 0 ]; then
        error "数据库表创建失败！"
        exit 1
    fi

    # 标记迁移为最新
    info "📝 标记迁移为最新状态..."
    docker compose --env-file .env --env-file .env.domains exec -T backend alembic stamp head
    
    # 初始化默认数据
    info "👤 初始化管理员用户和默认数据..."
    docker compose --env-file .env --env-file .env.domains exec -T backend python << 'PYTHON_SCRIPT'
from initial.initial_data import init_db
print("初始化默认数据...")
try:
    init_db()
    print("默认数据初始化完成！")
except Exception as e:
    print(f"警告：初始化数据时出现错误: {e}")
PYTHON_SCRIPT

    FIRST_DEPLOY=true

elif [ "$DEPLOY_MODE" = "migrate" ]; then
    # 迁移部署：运行数据库迁移
    info "📦 执行迁移部署..."
    
    info "🔄 运行数据库迁移..."
    if ! run_alembic_migration; then
        error "数据库迁移失败（已禁止自动 init_db 回退以保护现有数据）。请先修复迁移后重试。"
        exit 1
    fi

else
    # 自动检测模式
    info "🔍 检测数据库状态..."
    DB_STATUS=$(docker compose --env-file .env --env-file .env.domains exec -T backend python -c "
from sqlalchemy import text
from db.database import engine
try:
    with engine.connect() as conn:
        result = conn.execute(text(\"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'\"))
        count = result.scalar()
        print(f'TABLE_COUNT:{count}')
except Exception as e:
    print(f'ERROR:{e}')
" 2>&1)

    TABLE_COUNT=$(echo "$DB_STATUS" | grep "TABLE_COUNT:" | cut -d':' -f2)

    if [ -z "$TABLE_COUNT" ] || [ "$TABLE_COUNT" = "0" ]; then
        warn "🆕 检测到全新数据库，执行首次初始化..."
        
        info "🔧 从 Models 创建数据库表..."
        docker compose --env-file .env --env-file .env.domains exec -T backend python << 'PYTHON_SCRIPT'
from db.database import engine, Base
from db.models import *
import sys

print("正在创建所有表...")
try:
    Base.metadata.create_all(bind=engine)
    print("表创建成功！")
except Exception as e:
    print(f"表创建失败: {e}")
    sys.exit(1)
PYTHON_SCRIPT

        if [ $? -ne 0 ]; then
            error "数据库表创建失败！"
            exit 1
        fi

        info "📝 标记迁移为最新状态..."
        docker compose --env-file .env --env-file .env.domains exec -T backend alembic stamp head
        
        info "👤 初始化管理员用户和默认数据..."
        docker compose --env-file .env --env-file .env.domains exec -T backend python << 'PYTHON_SCRIPT'
from initial.initial_data import init_db
print("初始化默认数据...")
try:
    init_db()
    print("默认数据初始化完成！")
except Exception as e:
    print(f"警告：初始化数据时出现错误: {e}")
PYTHON_SCRIPT

        FIRST_DEPLOY=true
    else
        info "📊 检测到已有 ${TABLE_COUNT} 个表，执行增量迁移..."
        
        info "🔄 运行数据库迁移..."
        if ! run_alembic_migration; then
            error "数据库迁移失败（已禁止自动 init_db 回退以保护现有数据）。请先修复迁移后重试。"
            exit 1
        fi
    fi
fi

# 11. 确保管理员用户存在
info "🔍 检查管理员用户..."
docker compose --env-file .env --env-file .env.domains exec -T backend python << 'PYTHON_SCRIPT'
from db.database import SessionLocal
from db.models.user import User
from core.config import settings

db = SessionLocal()
admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
if admin:
    print(f"✅ 管理员用户已存在: {settings.ADMIN_EMAIL}")
else:
    print(f"⚠️ 管理员用户不存在，正在创建...")
    from initial.initial_data import _create_initial_admin
    _create_initial_admin(db)
    db.commit()
    print(f"✅ 管理员用户已创建: {settings.ADMIN_EMAIL}")
db.close()
PYTHON_SCRIPT

# 12. 自动修复邮件系统（权限 + STARTTLS 配置）
info "🔧 自动修复邮件系统..."
echo ""

# 调用邮件修复脚本
if [ -f "scripts/fix_mail_permissions.sh" ]; then
    bash scripts/fix_mail_permissions.sh || {
        warn "邮件系统自动修复失败"
        warn "请稍后手动执行: bash scripts/fix_mail_permissions.sh"
    }
else
    warn "修复脚本不存在，跳过邮件系统修复"
    warn "邮件功能可能需要手动修复"
fi

echo ""

# 13. 自动配置 DKIM 签名（防止邮件进垃圾箱）
info "🔐 自动配置 DKIM 邮件签名..."
echo ""

# 调用 DKIM 配置脚本
if [ -f "scripts/setup_dkim.sh" ]; then
    bash scripts/setup_dkim.sh || {
        warn "DKIM 配置失败"
        warn "请稍后手动执行: bash scripts/setup_dkim.sh"
    }
else
    warn "DKIM 配置脚本不存在，跳过 DKIM 配置"
    warn "发送外部邮件可能进垃圾箱"
fi

echo ""

# 读取生成的域名信息
WEB_DOMAIN=$(cat .env.domains | grep WEB_DOMAIN | cut -d'=' -f2)
MAIL_SERVER=$(cat .env.domains | grep MAIL_SERVER | cut -d'=' -f2)
ADMIN_EMAIL=$(get_env_value "ADMIN_EMAIL")

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
success "🎉 部署完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
if [ "$FIRST_DEPLOY" = true ]; then
    echo "🆕 这是首次部署！"
    echo ""
    echo "📌 管理员账户信息："
    echo "   - 邮箱: ${ADMIN_EMAIL}"
    echo "   - 密码: 请查看 .env 文件中的 ADMIN_PASSWORD"
    echo ""
fi
echo "📌 访问信息："
echo "   - Web 应用: https://${WEB_DOMAIN}"
echo "   - 邮件服务器: ${MAIL_SERVER}"
echo ""
echo "📌 重要提醒："
echo "   1. 确保 DNS 已正确配置指向此服务器"
echo "   2. 确保防火墙已开放以下端口："
echo "      - 80, 443 (HTTP/HTTPS)"
echo "      - 25, 587 (SMTP)"
echo "      - 143, 993 (IMAP)"
echo ""
echo "📌 常用命令："
echo "   - 查看日志: docker compose logs -f"
echo "   - 停止服务: docker compose down"
echo "   - 重启服务: docker compose restart"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
