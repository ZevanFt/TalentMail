#!/bin/bash

# =============================================================================
# TalentMail 生产环境部署脚本
# =============================================================================
# 用法: ./deploy.sh
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
NC='\033[0m' # No Color

# 打印函数
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 开始部署 TalentMail 生产环境..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
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

# 1. 停止现有服务
info "🛑 停止现有服务..."
docker compose down 2>/dev/null || true

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

# 6. 构建 Docker 镜像
info "🏗️  构建 Docker 镜像..."
docker compose --env-file .env --env-file .env.domains build

# 7. 启动服务
info "▶️  启动服务..."
docker compose --env-file .env --env-file .env.domains up -d

# 8. 等待数据库就绪
info "⏳ 等待数据库就绪..."
sleep 10

# 9. 运行数据库迁移
info "🔄 运行数据库迁移..."
docker compose --env-file .env --env-file .env.domains exec -T backend alembic upgrade head || {
    warn "数据库迁移失败，可能是数据库还未完全就绪，等待后重试..."
    sleep 5
    docker compose --env-file .env --env-file .env.domains exec -T backend alembic upgrade head
}

# 读取生成的域名信息
WEB_DOMAIN=$(cat .env.domains | grep WEB_DOMAIN | cut -d'=' -f2)
MAIL_SERVER=$(cat .env.domains | grep MAIL_SERVER | cut -d'=' -f2)

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
success "🎉 部署完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
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