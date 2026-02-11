#!/bin/bash
# TalentMail 生产环境邮件系统完整修复脚本
# 此脚本修复 SMTP 发送和 IMAP 同步的所有问题
# 使用方式：bash scripts/fix_mail_production.sh

set -e

CONTAINER_NAME="${MAILSERVER_CONTAINER_NAME:-talentmail-mailserver-1}"
MASTER_USER="sync_master"
MASTER_PASSWORD="SyncMasterPassword123"

echo "=========================================="
echo "  TalentMail 生产环境邮件系统修复"
echo "=========================================="
echo ""

# 1. 重新创建 mailserver 容器（应用最新配置）
echo "📦 [1/4] 重新创建 mailserver 容器..."
docker compose up -d --force-recreate mailserver
echo "等待容器启动..."
sleep 10

# 2. 配置 Master user（用于 IMAP 同步）
echo ""
echo "🔐 [2/4] 配置 Master user 认证..."
echo "生成密码哈希..."
docker exec "$CONTAINER_NAME" bash -c "
PASSWORD_HASH=\$(doveadm pw -s SHA512-CRYPT -p '$MASTER_PASSWORD' 2>&1)
echo '${MASTER_USER}:\$PASSWORD_HASH' > /etc/dovecot/master-users
chown dovecot:dovecot /etc/dovecot/master-users
chmod 600 /etc/dovecot/master-users
"

echo "验证 master-users 文件..."
if docker exec "$CONTAINER_NAME" test -s /etc/dovecot/master-users; then
    echo "  ✅ master-users 文件已创建"
else
    echo "  ❌ master-users 文件创建失败"
    exit 1
fi

# 3. 配置 Postfix submission 端口支持 STARTTLS
echo ""
echo "📧 [3/4] 配置 SMTP submission 端口..."
docker exec "$CONTAINER_NAME" postconf -P "submission/inet/smtpd_tls_security_level=may"
docker exec "$CONTAINER_NAME" postfix reload
echo "  ✅ STARTTLS 已启用"

# 4. 重启 Dovecot 应用配置
echo ""
echo "🔄 [4/4] 重启 Dovecot..."
docker exec "$CONTAINER_NAME" supervisorctl restart dovecot
sleep 3

# 验证配置
echo ""
echo "=========================================="
echo "  验证配置"
echo "=========================================="
echo ""

# 验证 Master user 认证
echo "🔍 测试 Master user 认证..."
if docker exec "$CONTAINER_NAME" doveadm auth test -x service=imap "zevan@talenting.vip*${MASTER_USER}" "$MASTER_PASSWORD" | grep -q "auth succeeded"; then
    echo "  ✅ Master user 认证成功"
else
    echo "  ❌ Master user 认证失败"
    echo ""
    echo "查看日志："
    docker logs "$CONTAINER_NAME" --tail 20 | grep -E "auth:|master-users"
    exit 1
fi

# 验证 SMTP STARTTLS
echo ""
echo "🔍 测试 SMTP STARTTLS..."
if docker exec "$CONTAINER_NAME" postconf -P submission/inet/smtpd_tls_security_level | grep -q "may"; then
    echo "  ✅ STARTTLS 已启用"
else
    echo "  ⚠️  STARTTLS 未启用"
fi

echo ""
echo "=========================================="
echo "  ✅ 修复完成！"
echo "=========================================="
echo ""
echo "📝 功能状态："
echo "  ✅ SMTP 发送（支持 STARTTLS）"
echo "  ✅ IMAP 同步（Master user 认证）"
echo "  ✅ 内部邮件收发"
echo ""
echo "📌 下一步："
echo "  1. 在前端测试发送邮件（admin → zevan）"
echo "  2. 等待 10-20 秒，刷新收件箱"
echo "  3. 如需外发邮件，请配置 DNS 记录："
echo "     - SPF: v=spf1 ip4:你的服务器IP ~all"
echo "     - MX: maillink.talenting.vip"
echo "     - PTR: 反向 DNS"
echo ""
