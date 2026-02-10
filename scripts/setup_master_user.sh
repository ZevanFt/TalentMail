#!/bin/bash
# 配置 docker-mailserver 的 Dovecot Master user 用于 IMAP 同步
# 此脚本使用 docker-mailserver 的标准 Master user 机制

set -e  # 遇到错误立即退出

CONTAINER_NAME="${MAILSERVER_CONTAINER_NAME:-talentmail-mailserver-1}"
MASTER_USER="sync_master"
MASTER_PASSWORD="SyncMasterPassword123"

echo "=== 配置 docker-mailserver Dovecot Master User ==="
echo "容器名称: $CONTAINER_NAME"
echo "Master 用户: $MASTER_USER"
echo ""

# 1. 生成 SHA512-CRYPT 密码哈希
echo "[1/5] 生成密码哈希..."
PASSWORD_HASH=$(docker exec "$CONTAINER_NAME" doveadm pw -s SHA512-CRYPT -p "$MASTER_PASSWORD" | cut -d'}' -f2)
echo "密码哈希已生成"

# 2. 创建 masterdb 文件（docker-mailserver 标准路径）
echo ""
echo "[2/5] 创建 /etc/dovecot/masterdb 文件..."
docker exec "$CONTAINER_NAME" bash -c "echo '${MASTER_USER}:{SHA512-CRYPT}${PASSWORD_HASH}' > /etc/dovecot/masterdb"
docker exec "$CONTAINER_NAME" chown dovecot:dovecot /etc/dovecot/masterdb
docker exec "$CONTAINER_NAME" chmod 600 /etc/dovecot/masterdb
echo "masterdb 文件已创建"

# 3. 在 10-auth.conf 中启用 auth-master.inc（如果还没启用）
echo ""
echo "[3/5] 配置 10-auth.conf 启用 Master user..."
docker exec "$CONTAINER_NAME" bash -c '
if ! grep -q "!include auth-master.inc" /etc/dovecot/conf.d/10-auth.conf; then
    # 在 auth-sql.conf.ext 之前添加 auth-master.inc
    sed -i "/!include auth-sql.conf.ext/i !include auth-master.inc" /etc/dovecot/conf.d/10-auth.conf
    echo "已添加 auth-master.inc 引入"
else
    echo "auth-master.inc 已经被引入，跳过"
fi
'

# 4. 重启 Dovecot
echo ""
echo "[4/5] 重启 Dovecot..."
docker exec "$CONTAINER_NAME" supervisorctl restart dovecot
sleep 3
echo "Dovecot 已重启"

# 5. 测试认证
echo ""
echo "[5/5] 测试 Master user 认证..."
echo "测试用户: zevan@talenting.vip*sync_master"

if docker exec "$CONTAINER_NAME" doveadm auth test -x service=imap "zevan@talenting.vip*${MASTER_USER}" "$MASTER_PASSWORD" | grep -q "auth succeeded"; then
    echo ""
    echo "✅ Master user 认证成功！"
    echo ""
    echo "现在可以使用以下格式登录任何用户的邮箱："
    echo "  用户名: user@domain*sync_master"
    echo "  密码: $MASTER_PASSWORD"
    echo ""
    echo "IMAP 同步应该现在可以正常工作了。"
else
    echo ""
    echo "❌ Master user 认证失败！"
    echo ""
    echo "请查看详细日志："
    echo "  docker logs $CONTAINER_NAME --tail 50 | grep auth"
    exit 1
fi

echo ""
echo "=== 配置完成 ==="
