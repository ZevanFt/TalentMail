#!/bin/bash
# 完整部署 Master user 认证配置
# 此脚本会重新创建 mailserver 容器以应用新的配置文件

set -e

CONTAINER_NAME="${MAILSERVER_CONTAINER_NAME:-talentmail-mailserver-1}"

echo "=== 部署 Master user 认证配置 ==="
echo ""

# 1. 停止并删除旧容器
echo "[1/3] 重新创建 mailserver 容器（应用新的 10-auth.conf）..."
docker compose up -d --force-recreate mailserver

# 2. 等待容器启动
echo "等待容器启动..."
sleep 10

# 3. 验证配置
echo ""
echo "[2/3] 验证配置..."
echo "检查 10-auth.conf 是否包含 auth-master.inc："
if docker exec "$CONTAINER_NAME" grep -q "auth-master.inc" /etc/dovecot/conf.d/10-auth.conf; then
    echo "  ✅ auth-master.inc 已引入"
else
    echo "  ❌ auth-master.inc 未引入"
    exit 1
fi

echo "检查 masterdb 文件："
if docker exec "$CONTAINER_NAME" test -f /etc/dovecot/masterdb; then
    echo "  ✅ masterdb 文件存在"
    docker exec "$CONTAINER_NAME" ls -la /etc/dovecot/masterdb
else
    echo "  ❌ masterdb 文件不存在"
    exit 1
fi

# 4. 测试认证
echo ""
echo "[3/3] 测试 Master user 认证..."
if docker exec "$CONTAINER_NAME" doveadm auth test -x service=imap "zevan@talenting.vip*sync_master" "SyncMasterPassword123" | grep -q "auth succeeded"; then
    echo ""
    echo "✅✅✅ Master user 认证成功！✅✅✅"
    echo ""
    echo "IMAP 同步现在应该可以正常工作了。"
    echo "请在前端测试发送邮件，看看是否能收到。"
else
    echo ""
    echo "❌ Master user 认证失败"
    echo ""
    echo "查看详细日志："
    docker logs "$CONTAINER_NAME" --tail 30 | grep -E "auth:|masterdb"
    exit 1
fi

echo ""
echo "=== 部署完成 ==="
