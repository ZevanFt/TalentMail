#!/bin/bash
# TalentMail - mkcert 本地证书安装脚本
# 此脚本将安装 mkcert 并生成本地可信的 HTTPS 证书

set -e

echo "=========================================="
echo "  TalentMail mkcert 证书安装脚本"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CERT_DIR="$PROJECT_ROOT/config/caddy/certs"

echo ""
echo -e "${YELLOW}[Step 1/4]${NC} 安装 mkcert..."
if command -v mkcert &> /dev/null; then
    echo -e "${GREEN}✓ mkcert 已安装${NC}"
else
    echo "正在安装 mkcert 和 libnss3-tools..."
    sudo apt update
    sudo apt install -y mkcert libnss3-tools
    echo -e "${GREEN}✓ mkcert 安装完成${NC}"
fi

echo ""
echo -e "${YELLOW}[Step 2/4]${NC} 安装本地 CA 到系统和浏览器..."
mkcert -install
echo -e "${GREEN}✓ 本地 CA 已安装${NC}"

echo ""
echo -e "${YELLOW}[Step 3/4]${NC} 创建证书目录..."
mkdir -p "$CERT_DIR"
echo -e "${GREEN}✓ 证书目录已创建: $CERT_DIR${NC}"

echo ""
echo -e "${YELLOW}[Step 4/4]${NC} 生成域名证书..."
cd "$CERT_DIR"
mkcert -key-file key.pem -cert-file cert.pem \
    mail.talenting.test \
    "*.talenting.test" \
    localhost \
    127.0.0.1 \
    ::1

echo -e "${GREEN}✓ 证书生成完成${NC}"

echo ""
echo "=========================================="
echo -e "${GREEN}  安装完成！${NC}"
echo "=========================================="
echo ""
echo "证书文件位置:"
echo "  - 证书: $CERT_DIR/cert.pem"
echo "  - 密钥: $CERT_DIR/key.pem"
echo ""
echo "下一步:"
echo "  1. 重启 Docker 容器: docker compose -f docker-compose.dev.yml down && docker compose -f docker-compose.dev.yml up -d"
echo "  2. 访问: https://mail.talenting.test"
echo ""
echo -e "${YELLOW}注意: 如果你使用 Firefox，可能需要重启浏览器才能信任新证书${NC}"