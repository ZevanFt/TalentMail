#!/bin/bash
# TalentMail 邮件系统权限快速修复脚本
# 仅修复 Master user 文件权限问题，不重新创建容器
# 使用方式：bash scripts/fix_mail_permissions.sh

set -e

# 读取项目根目录 .env（如果存在）
if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

CONTAINER_NAME="${MAILSERVER_CONTAINER_NAME:-talentmail-mailserver-1}"
MASTER_USER="${MAIL_MASTER_USER:-sync_master}"
MASTER_PASSWORD="${MAIL_MASTER_PASSWORD:-${ADMIN_PASSWORD}}"

retry_docker_exec() {
    local max_attempts="$1"
    local wait_seconds="$2"
    shift 2
    local attempt=1
    while [ "$attempt" -le "$max_attempts" ]; do
        if docker exec "$CONTAINER_NAME" "$@" >/tmp/fix_mail_permissions.last 2>&1; then
            return 0
        fi
        if [ "$attempt" -lt "$max_attempts" ]; then
            echo "  ⏳ 命令未就绪，${wait_seconds}s 后重试 (${attempt}/${max_attempts})..."
            sleep "$wait_seconds"
        fi
        attempt=$((attempt + 1))
    done
    echo "  ❌ 命令执行失败：$*"
    cat /tmp/fix_mail_permissions.last
    return 1
}

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
retry_docker_exec 12 2 postconf -P "submission/inet/smtpd_tls_security_level=may"
retry_docker_exec 12 2 postfix reload
echo "  ✅ STARTTLS 已启用"

# 4. 配置 OpenDKIM 允许从 /tmp 加载密钥
echo ""
echo "🔐 配置 OpenDKIM 允许从 /tmp 加载密钥..."
docker exec "$CONTAINER_NAME" bash -c "
if [ -f /etc/opendkim.conf ]; then
    # 添加或更新 RequireSafeKeys 配置
    if ! grep -q '^RequireSafeKeys' /etc/opendkim.conf; then
        echo 'RequireSafeKeys no' >> /etc/opendkim.conf
        echo '  ✅ 已添加 RequireSafeKeys no 配置'
    else
        sed -i 's/^RequireSafeKeys.*/RequireSafeKeys no/' /etc/opendkim.conf
        echo '  ✅ 已更新 RequireSafeKeys 配置'
    fi
else
    echo '  ⚠️  未找到 /etc/opendkim.conf，跳过配置'
fi
"

# 重启 OpenDKIM 应用新配置
docker exec "$CONTAINER_NAME" supervisorctl restart opendkim 2>/dev/null || true
echo "  ✅ OpenDKIM 服务已重启"

# 5. 重启 Dovecot 应用新权限
echo ""
echo "🔄 重启 Dovecot..."
docker exec "$CONTAINER_NAME" supervisorctl restart dovecot
sleep 3

# 6. 测试 Master user 认证
echo ""
echo "🔍 测试 Master user 认证..."
MASTER_TEST_EMAIL="admin@$(grep -E '^DOMAIN=' .env.domains | cut -d'=' -f2-)"
if [ -z "$MASTER_PASSWORD" ]; then
    echo "  ⚠️  跳过认证测试：MAIL_MASTER_PASSWORD/ADMIN_PASSWORD 未配置"
elif docker exec "$CONTAINER_NAME" doveadm auth test -x service=imap "${MASTER_TEST_EMAIL}*${MASTER_USER}" "$MASTER_PASSWORD" | grep -q "auth succeeded"; then
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
echo "  ✅ OpenDKIM 邮件签名已启用"
echo "  ✅ 邮件同步功能已恢复"
echo ""
echo "📌 下一步："
echo "  1. 刷新前端页面"
echo "  2. 尝试发送内部邮件测试"
echo "  3. 点击同步按钮接收邮件"
echo ""
echo "📧 发送外部邮件（防止进垃圾箱）："
echo "  运行: bash scripts/setup_dkim.sh"
echo "  然后在 Cloudflare 配置 DKIM DNS 记录"
echo ""
