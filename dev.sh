#!/bin/bash

# =============================================================================
# TalentMail 开发环境部署脚本
# =============================================================================
# 用法: ./dev.sh [命令]
#   无参数  - 启动开发环境
#   stop    - 停止开发环境
#   restart - 重启开发环境
#   logs    - 查看日志
#   clean   - 清理并重新构建
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

# 检查 .env 文件是否存在
check_env() {
    if [ ! -f .env ]; then
        error "未找到 .env 文件！"
        info "正在从 .env.example 创建..."
        cp .env.example .env
        warn "请编辑 .env 文件并填写必要的配置，然后重新运行此脚本。"
        exit 1
    fi
}

# 从 config.json 读取配置并生成 .env.caddy
generate_caddy_env() {
    info "🔧 从 config.json 生成 Caddy 环境变量..."
    
    if [ ! -f config.json ]; then
        error "未找到 config.json 文件！"
        exit 1
    fi
    
    # 读取当前环境
    local CURRENT_ENV=$(grep -o '"currentEnvironment"[[:space:]]*:[[:space:]]*"[^"]*"' config.json | cut -d'"' -f4)
    if [ -z "$CURRENT_ENV" ]; then
        CURRENT_ENV="development"
    fi
    info "   📍 当前环境: ${CURRENT_ENV}"
    
    # 读取对应环境的配置
    local BASE_DOMAIN=$(python3 -c "
import json
with open('config.json') as f:
    config = json.load(f)
env = config.get('environments', {}).get('$CURRENT_ENV', {})
print(env.get('baseDomain', 'talenting.test'))
" 2>/dev/null || echo "talenting.test")
    info "   📍 基础域名: ${BASE_DOMAIN}"
    
    local WEB_PREFIX=$(python3 -c "
import json
with open('config.json') as f:
    config = json.load(f)
env = config.get('environments', {}).get('$CURRENT_ENV', {})
print(env.get('webPrefix', 'mail'))
" 2>/dev/null || echo "mail")
    info "   📍 Web 前缀: ${WEB_PREFIX}"
    
    local MAIL_SERVER_PREFIX=$(python3 -c "
import json
with open('config.json') as f:
    config = json.load(f)
env = config.get('environments', {}).get('$CURRENT_ENV', {})
print(env.get('mailServerPrefix', 'maillink'))
" 2>/dev/null || echo "maillink")
    info "   📍 邮件服务器前缀: ${MAIL_SERVER_PREFIX}"
    
    local WEB_DOMAIN="${WEB_PREFIX}.${BASE_DOMAIN}"
    local MAIL_SERVER="${MAIL_SERVER_PREFIX}.${BASE_DOMAIN}"
    
    # 生成 .env.caddy
    echo "WEB_DOMAIN=${WEB_DOMAIN}" > .env.caddy
    
    success "已生成 .env.caddy"
    echo ""
    echo "   🌐 Web 域名: ${WEB_DOMAIN}"
    echo "   📧 邮件服务器: ${MAIL_SERVER}"
    echo ""
    
    # 导出变量供后续使用
    export GENERATED_WEB_DOMAIN="${WEB_DOMAIN}"
    export GENERATED_BASE_DOMAIN="${BASE_DOMAIN}"
}

# 从 .env 文件读取变量值
get_env_value() {
    local key=$1
    grep -E "^${key}=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'"
}

# 生成 dovecot-sql.conf.ext 配置文件
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

# 检查必要的环境变量
check_required_vars() {
    REQUIRED_VARS=(
        "POSTGRES_USER"
        "POSTGRES_PASSWORD"
        "POSTGRES_DB"
        "DATABASE_URL_DOCKER"
        "SECRET_KEY"
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
}

# 启动开发环境
start() {
    info "🚀 启动 TalentMail 开发环境..."
    
    check_env
    check_required_vars
    
    # 从 config.json 生成 Caddy 环境变量
    generate_caddy_env
    
    # 生成 Dovecot SQL 配置文件（从 .env 读取数据库密码）
    generate_dovecot_sql_config
    
    # 构建并启动服务
    info "🏗️  构建 Docker 镜像..."
    docker compose -f docker-compose.dev.yml build
    
    info "▶️  启动服务..."
    docker compose -f docker-compose.dev.yml up -d
    
    # 等待数据库就绪
    info "⏳ 等待数据库就绪..."
    sleep 5
    
    # 运行数据库迁移
    info "🔄 运行数据库迁移..."
    docker compose -f docker-compose.dev.yml exec -T backend alembic upgrade head || {
        warn "数据库迁移失败，可能是数据库还未完全就绪，等待后重试..."
        sleep 5
        docker compose -f docker-compose.dev.yml exec -T backend alembic upgrade head
    }
    
    # 读取生成的域名
    local WEB_DOMAIN=$(cat .env.caddy | grep WEB_DOMAIN | cut -d'=' -f2)
    local BASE_DOMAIN=$(echo $WEB_DOMAIN | cut -d'.' -f2-)
    
    echo ""
    success "🎉 开发环境启动完成！"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📌 访问地址："
    echo "   - 前端: http://localhost:3000"
    echo "   - 后端 API: http://localhost:8000"
    echo "   - API 文档: http://localhost:8000/docs"
    echo "   - HTTPS (需配置 hosts): https://${WEB_DOMAIN}"
    echo ""
    echo "📌 默认管理员账户："
    echo "   - 邮箱: admin@${BASE_DOMAIN}"
    echo "   - 密码: (查看 .env 中的 ADMIN_PASSWORD)"
    echo ""
    echo "📌 常用命令："
    echo "   - 查看日志: ./dev.sh logs"
    echo "   - 停止服务: ./dev.sh stop"
    echo "   - 重启服务: ./dev.sh restart"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# 停止开发环境
stop() {
    info "🛑 停止开发环境..."
    docker compose -f docker-compose.dev.yml down
    success "开发环境已停止"
}

# 重启开发环境
restart() {
    info "🔄 重启开发环境..."
    docker compose -f docker-compose.dev.yml restart
    success "开发环境已重启"
}

# 查看日志
logs() {
    info "📋 查看日志 (Ctrl+C 退出)..."
    docker compose -f docker-compose.dev.yml logs -f
}

# 清理并重新构建
clean() {
    warn "⚠️  这将删除所有容器和镜像，但保留数据卷。"
    read -p "确定要继续吗？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "🧹 清理开发环境..."
        docker compose -f docker-compose.dev.yml down --rmi local
        success "清理完成"
        
        info "🏗️  重新构建..."
        start
    else
        info "已取消"
    fi
}

# 主入口
case "${1:-}" in
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    clean)
        clean
        ;;
    *)
        start
        ;;
esac