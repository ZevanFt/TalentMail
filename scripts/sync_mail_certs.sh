#!/bin/bash

# =============================================================================
# TalentMail 邮件服务器证书同步脚本
# =============================================================================
# 使用方法：
#   1. 确保 MAIL_SERVER 域名证书已经签发
#   2. 运行此脚本：./scripts/sync_mail_certs.sh
#
# 支持两种证书来源：
#   - embedded: 从项目内置 caddy 容器复制（默认）
#   - host: 从宿主机目录复制
#
# 宿主机统一 Caddy 示例：
#   CADDY_CERT_SOURCE=host \
#   HOST_CERT_DIR=/var/lib/caddy/.local/share/caddy/certificates/acme-v02.api.letsencrypt.org-directory/${MAIL_SERVER} \
#   ./scripts/sync_mail_certs.sh
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🔐 TalentMail 邮件服务器证书同步${NC}"
echo ""

if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ 请在项目根目录运行此脚本${NC}"
    exit 1
fi

if [ ! -f ".env.domains" ]; then
    echo -e "${RED}❌ .env.domains 文件不存在，请先运行 deploy.sh${NC}"
    exit 1
fi

source .env.domains
if [ -z "$MAIL_SERVER" ]; then
    echo -e "${RED}❌ MAIL_SERVER 变量未设置${NC}"
    exit 1
fi

CERT_SOURCE="${CADDY_CERT_SOURCE:-embedded}"
CERT_DIR="./data/mailserver/config/ssl"
MAILSERVER_ENV="./config/mail/production/mailserver.env"
EMBEDDED_CERT_PATH="/data/caddy/certificates/acme-v02.api.letsencrypt.org-directory/${MAIL_SERVER}"
HOST_CERT_DIR_DEFAULT="/var/lib/caddy/.local/share/caddy/certificates/acme-v02.api.letsencrypt.org-directory/${MAIL_SERVER}"
HOST_CERT_DIR="${HOST_CERT_DIR:-$HOST_CERT_DIR_DEFAULT}"

mkdir -p "$CERT_DIR"

echo -e "📧 邮件服务器域名: ${YELLOW}${MAIL_SERVER}${NC}"
echo -e "📦 证书来源模式: ${YELLOW}${CERT_SOURCE}${NC}"
echo ""

copy_from_embedded_caddy() {
    echo -e "📂 正在从项目内置 Caddy 容器复制证书..."

    if ! docker compose ps --services --filter status=running | grep -qx caddy; then
        echo -e "${RED}❌ caddy 容器未运行${NC}"
        echo -e "${YELLOW}请改用以下任一方式：${NC}"
        echo "  1. 启动内置 Caddy：docker compose --profile embedded-caddy up -d caddy"
        echo "  2. 使用宿主机统一 Caddy：CADDY_CERT_SOURCE=host HOST_CERT_DIR=/your/cert/dir ./scripts/sync_mail_certs.sh"
        exit 1
    fi

    if ! docker compose exec -T caddy test -d "$EMBEDDED_CERT_PATH"; then
        echo -e "${RED}❌ Caddy 尚未获取 ${MAIL_SERVER} 的证书${NC}"
        echo -e "${YELLOW}请确保：${NC}"
        echo "  1. DNS 已正确配置指向此服务器"
        echo "  2. 防火墙已开放 80 和 443 端口"
        echo "  3. Caddy 容器正在运行"
        echo ""
        echo "可以查看 Caddy 日志：docker compose logs caddy"
        exit 1
    fi

    docker compose exec -T caddy cat "${EMBEDDED_CERT_PATH}/${MAIL_SERVER}.crt" > "${CERT_DIR}/cert.pem"
    docker compose exec -T caddy cat "${EMBEDDED_CERT_PATH}/${MAIL_SERVER}.key" > "${CERT_DIR}/key.pem"
}

copy_from_host_dir() {
    echo -e "📂 正在从宿主机目录复制证书..."
    echo -e "📁 证书目录: ${YELLOW}${HOST_CERT_DIR}${NC}"

    if [ ! -d "$HOST_CERT_DIR" ]; then
        echo -e "${RED}❌ 宿主机证书目录不存在: ${HOST_CERT_DIR}${NC}"
        echo -e "${YELLOW}请显式指定 HOST_CERT_DIR，例如：${NC}"
        echo "  CADDY_CERT_SOURCE=host HOST_CERT_DIR=/var/lib/caddy/.local/share/caddy/certificates/acme-v02.api.letsencrypt.org-directory/${MAIL_SERVER} ./scripts/sync_mail_certs.sh"
        exit 1
    fi

    cp "${HOST_CERT_DIR}/${MAIL_SERVER}.crt" "${CERT_DIR}/cert.pem"
    cp "${HOST_CERT_DIR}/${MAIL_SERVER}.key" "${CERT_DIR}/key.pem"
}

case "$CERT_SOURCE" in
    embedded)
        copy_from_embedded_caddy
        ;;
    host)
        copy_from_host_dir
        ;;
    *)
        echo -e "${RED}❌ 不支持的证书来源: ${CERT_SOURCE}${NC}"
        echo "可选值: embedded / host"
        exit 1
        ;;
esac

if [ ! -s "${CERT_DIR}/cert.pem" ] || [ ! -s "${CERT_DIR}/key.pem" ]; then
    echo -e "${RED}❌ 证书文件为空或复制失败${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 证书已复制到 ${CERT_DIR}${NC}"
echo ""
echo -e "📝 更新 mailserver.env 配置..."

cp "$MAILSERVER_ENV" "${MAILSERVER_ENV}.bak"

if grep -q "^SSL_TYPE=" "$MAILSERVER_ENV"; then
    sed -i 's/^SSL_TYPE=.*/SSL_TYPE=manual/' "$MAILSERVER_ENV"
else
    echo "SSL_TYPE=manual" >> "$MAILSERVER_ENV"
fi

echo -e "${GREEN}✅ mailserver.env 已更新${NC}"
echo ""
echo -e "📝 请确保 docker-compose.yml 中 mailserver 服务包含以下卷挂载："
echo -e "${YELLOW}      - ./data/mailserver/config/ssl/cert.pem:/tmp/docker-mailserver/ssl/cert.pem:ro${NC}"
echo -e "${YELLOW}      - ./data/mailserver/config/ssl/key.pem:/tmp/docker-mailserver/ssl/key.pem:ro${NC}"
echo ""
echo -e "🔄 重启邮件服务器..."
docker compose restart mailserver

echo ""
echo -e "${GREEN}✅ 证书同步完成！${NC}"
echo ""
echo "邮件服务器现在使用该证书。"
echo "您可以使用邮件客户端连接："
echo "  - IMAP: ${MAIL_SERVER}:993 (SSL/TLS)"
echo "  - SMTP: ${MAIL_SERVER}:587 (STARTTLS)"
