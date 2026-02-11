#!/bin/bash
# TalentMail 邮件系统权限快速修复脚本
# 仅修复 Master user 文件权限问题，不重新创建容器
# 使用方式：bash scripts/fix_mail_permissions.sh

set -e

CONTAINER_NAME="${MAILSERVER_CONTAINER_NAME:-talentmail-mailserver-1}"
MASTER_USER="sync_master"
MASTER_PASSWORD="SyncMasterPassword123"

echo "=========================================="
echo "  TalentMail 邮件权限快速修复"
echo "=========================================="
echo ""

# 1. 检查容器是否运行
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ 错误：mailserver 容器未运行！"
    echo "请先启动容器：docker compose up -d"
    exit 1
fi

# 2. 修复 master-users 文件权限
echo "🔧 修复 master-users 文件权限..."
docker exec "$CONTAINER_NAME" bash -c "
if [ -f /etc/dovecot/master-users ]; then
    # 修复权限
    chown dovecot:dovecot /etc/dovecot/master-users
    chmod 600 /etc/dovecot/master-users
    echo '✅ 权限已修复'
    ls -la /etc/dovecot/master-users
else
    echo '❌ 错误：master-users 文件不存在！'
    echo '需要运行完整修复脚本：bash scripts/fix_mail_production.sh'
    exit 1
fi
"

# 3. 配置 Postfix submission 端口支持 STARTTLS
echo ""
echo "📧 配置 SMTP submission 端口支持 STARTTLS..."
docker exec "$CONTAINER_NAME" postconf -P "submission/inet/smtpd_tls_security_level=may"
docker exec "$CONTAINER_NAME" postfix reload
echo "  ✅ STARTTLS 已启用"

# 4. 重启 Dovecot 应用新权限
echo ""
echo "🔄 重启 Dovecot..."
docker exec "$CONTAINER_NAME" supervisorctl restart dovecot
sleep 3

# 5. 测试 Master user 认证
echo ""
echo "🔍 测试 Master user 认证..."
if docker exec "$CONTAINER_NAME" doveadm auth test -x service=imap "admin@talenting.vip*${MASTER_USER}" "$MASTER_PASSWORD" | grep -q "auth succeeded"; then
    echo "  ✅ Master user 认证成功"
else
    echo "  ❌ Master user 认证失败"
    echo ""
    echo "查看日志："
    docker logs "$CONTAINER_NAME" --tail 20 | grep -E "auth:|master-users"
    exit 1
fi

echo ""
echo "=========================================="
echo "  ✅ 邮件系统修复完成！"
echo "=========================================="
echo ""
echo "📝 功能状态："
echo "  ✅ SMTP 发送（支持 STARTTLS）"
echo "  ✅ IMAP Master user 认证正常"
echo "  ✅ 邮件同步功能已恢复"
echo ""
echo "📌 下一步："
echo "  1. 刷新前端页面"
echo "  2. 尝试发送邮件测试"
echo "  3. 点击同步按钮接收邮件"
echo ""
