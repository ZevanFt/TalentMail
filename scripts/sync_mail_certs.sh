#!/bin/bash

# =============================================================================
# TalentMail 邮件服务器证书同步脚本
# =============================================================================
# 此脚本将 Caddy 获取的 Let's Encrypt 证书同步到 docker-mailserver
#
# 使用方法：
#   1. 首次部署后，等待 Caddy 获取证书（通常几分钟）
#   2. 运行此脚本：./scripts/sync_mail_certs.sh
#   3. 脚本会自动更新 mailserver.env 并重启邮件服务器
#
# 注意：需要在项目根目录运行此脚本
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 TalentMail 邮件服务器证书同步${NC}"
echo ""

# 检查是否在项目根目录
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 检查 .env.domains 是否存在
if [ ! -f ".env.domains" ]; then
    echo -e "${RED}❌ .env.domains 文件不存在，请先运行 deploy.sh${NC}"
    exit 1
fi

# 读取邮件服务器域名
source .env.domains
if [ -z "$MAIL_SERVER" ]; then
    echo -e "${RED}❌ MAIL_SERVER 变量未设置${NC}"
    exit 1
fi

echo -e "📧 邮件服务器域名: ${YELLOW}${MAIL_SERVER}${NC}"

# Caddy 证书路径 (在 Docker volume 中)
# Caddy 使用 ACME 目录结构: /data/caddy/certificates/acme-v02.api.letsencrypt.org-directory/{domain}/
CADDY_CERT_BASE="caddy_data"

# 目标证书目录
CERT_DIR="./data/mailserver/config/ssl"
mkdir -p "$CERT_DIR"

echo ""
echo -e "📂 正在从 Caddy 容器复制证书..."

# 从 Caddy 容器复制证书
# Caddy 存储证书的路径格式
CADDY_CERT_PATH="/data/caddy/certificates/acme-v02.api.letsencrypt.org-directory/${MAIL_SERVER}"

# 检查证书是否存在
if ! docker compose exec -T caddy test -d "$CADDY_CERT_PATH"; then
    echo -e "${RED}❌ Caddy 尚未获取 ${MAIL_SERVER} 的证书${NC}"
    echo -e "${YELLOW}请确保：${NC}"
    echo "  1. DNS 已正确配置指向此服务器"
    echo "  2. 防火墙已开放 80 和 443 端口"
    echo "  3. Caddy 容器正在运行"
    echo ""
    echo "可以查看 Caddy 日志：docker compose logs caddy"
    exit 1
fi

# 复制证书文件
echo "  复制证书文件..."
docker compose exec -T caddy cat "${CADDY_CERT_PATH}/${MAIL_SERVER}.crt" > "${CERT_DIR}/cert.pem"
docker compose exec -T caddy cat "${CADDY_CERT_PATH}/${MAIL_SERVER}.key" > "${CERT_DIR}/key.pem"

# 验证证书文件
if [ ! -s "${CERT_DIR}/cert.pem" ] || [ ! -s "${CERT_DIR}/key.pem" ]; then
    echo -e "${RED}❌ 证书文件为空或复制失败${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 证书已复制到 ${CERT_DIR}${NC}"

# 更新 mailserver.env
echo ""
echo -e "📝 更新 mailserver.env 配置..."

MAILSERVER_ENV="./config/mail/production/mailserver.env"

# 备份原配置
cp "$MAILSERVER_ENV" "${MAILSERVER_ENV}.bak"

# 更新 SSL_TYPE
if grep -q "^SSL_TYPE=" "$MAILSERVER_ENV"; then
    sed -i 's/^SSL_TYPE=.*/SSL_TYPE=manual/' "$MAILSERVER_ENV"
else
    echo "SSL_TYPE=manual" >> "$MAILSERVER_ENV"
fi

echo -e "${GREEN}✅ mailserver.env 已更新${NC}"

# 更新 docker-compose.yml 中的证书挂载
echo ""
echo -e "📝 请确保 docker-compose.yml 中 mailserver 服务包含以下卷挂载："
echo -e "${YELLOW}      - ./data/mailserver/config/ssl/cert.pem:/tmp/docker-mailserver/ssl/cert.pem:ro${NC}"
echo -e "${YELLOW}      - ./data/mailserver/config/ssl/key.pem:/tmp/docker-mailserver/ssl/key.pem:ro${NC}"

# 重启邮件服务器
echo ""
echo -e "🔄 重启邮件服务器..."
docker compose restart mailserver

echo ""
echo -e "${GREEN}✅ 证书同步完成！${NC}"
echo ""
echo "邮件服务器现在使用 Let's Encrypt 证书。"
echo "您可以使用邮件客户端连接："
echo "  - IMAP: ${MAIL_SERVER}:993 (SSL/TLS)"
echo "  - SMTP: ${MAIL_SERVER}:587 (STARTTLS)"