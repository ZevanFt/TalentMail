#!/bin/bash
# TalentMail DKIM 配置脚本
# 此脚本为邮件服务器配置 DKIM 签名，防止邮件进垃圾箱
# 使用方式：bash scripts/setup_dkim.sh

set -e

CONTAINER_NAME="${MAILSERVER_CONTAINER_NAME:-talentmail-mailserver-1}"
DOMAIN="talenting.vip"
SELECTOR="mail"  # DKIM 选择器，可以是任意名称

echo "==========================================="
echo "  TalentMail DKIM 配置"
echo "==========================================="
echo ""
echo "域名: $DOMAIN"
echo "选择器: $SELECTOR"
echo ""

# 检查容器是否运行
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ 容器 $CONTAINER_NAME 未运行，请先启动邮件服务器"
    exit 1
fi

# 1. 生成 DKIM 密钥对
echo "📝 [1/4] 生成 DKIM 密钥对..."
docker exec "$CONTAINER_NAME" bash -c "
    # 创建 DKIM 配置目录
    mkdir -p /tmp/docker-mailserver/opendkim/keys/$DOMAIN

    # 生成 DKIM 密钥对（2048 位）
    cd /tmp/docker-mailserver/opendkim/keys/$DOMAIN
    opendkim-genkey -b 2048 -d $DOMAIN -s $SELECTOR

    # 修改权限
    chown -R opendkim:opendkim /tmp/docker-mailserver/opendkim
    chmod 600 /tmp/docker-mailserver/opendkim/keys/$DOMAIN/$SELECTOR.private
"

if [ $? -eq 0 ]; then
    echo "  ✅ DKIM 密钥对生成成功"
else
    echo "  ❌ DKIM 密钥对生成失败"
    exit 1
fi

# 2. 配置 OpenDKIM
echo ""
echo "📧 [2/4] 配置 OpenDKIM..."
docker exec "$CONTAINER_NAME" bash -c "
    # 配置 KeyTable（密钥表）
    echo '$SELECTOR._domainkey.$DOMAIN $DOMAIN:$SELECTOR:/tmp/docker-mailserver/opendkim/keys/$DOMAIN/$SELECTOR.private' > /tmp/docker-mailserver/opendkim/KeyTable

    # 配置 SigningTable（签名表）
    echo '*@$DOMAIN $SELECTOR._domainkey.$DOMAIN' > /tmp/docker-mailserver/opendkim/SigningTable

    # 配置 TrustedHosts（信任主机）
    cat > /tmp/docker-mailserver/opendkim/TrustedHosts << EOF
127.0.0.1
localhost
$DOMAIN
*.$DOMAIN
EOF

    # 修改权限
    chown opendkim:opendkim /tmp/docker-mailserver/opendkim/*
"

if [ $? -eq 0 ]; then
    echo "  ✅ OpenDKIM 配置完成"
else
    echo "  ❌ OpenDKIM 配置失败"
    exit 1
fi

# 3. 重启 OpenDKIM 服务
echo ""
echo "🔄 [3/4] 重启 OpenDKIM 服务..."
docker exec "$CONTAINER_NAME" supervisorctl restart opendkim
sleep 2

if docker exec "$CONTAINER_NAME" supervisorctl status opendkim | grep -q "RUNNING"; then
    echo "  ✅ OpenDKIM 服务运行正常"
else
    echo "  ⚠️  OpenDKIM 服务状态异常，请检查日志"
fi

# 4. 输出 DNS 记录
echo ""
echo "==========================================="
echo "  ✅ DKIM 配置完成！"
echo "==========================================="
echo ""
echo "📋 请在 Cloudflare DNS 管理中添加以下 TXT 记录："
echo ""
echo "-------------------------------------------"

# 提取并格式化 DKIM 公钥
DKIM_RECORD=$(docker exec "$CONTAINER_NAME" cat /tmp/docker-mailserver/opendkim/keys/$DOMAIN/$SELECTOR.txt)

# 解析记录
echo "$DKIM_RECORD" | sed 's/[()]//g' | sed 's/\"//g' | awk '
BEGIN {
    print "类型: TXT"
    print "名称: '"$SELECTOR"'._domainkey"
    print "内容:"
}
/v=DKIM1/ {
    content = ""
    for (i=1; i<=NF; i++) {
        if ($i ~ /v=DKIM1/ || $i ~ /k=rsa/ || $i ~ /p=/) {
            content = content $i
        }
    }
    print "  " content
}
'

echo "-------------------------------------------"
echo ""
echo "📝 Cloudflare 配置步骤："
echo "  1. 登录 Cloudflare，进入 talenting.vip 域名管理"
echo "  2. 点击 'DNS' → 'Records' → 'Add record'"
echo "  3. 类型选择: TXT"
echo "  4. 名称输入: $SELECTOR._domainkey"
echo "  5. 内容输入: (复制上面的内容，去掉所有空格和换行)"
echo "  6. TTL: Auto"
echo "  7. 点击 'Save'"
echo ""
echo "⏱️  DNS 记录通常 1-5 分钟生效（Cloudflare 很快）"
echo ""
echo "🔍 验证 DKIM 记录："
echo "  等待 5 分钟后，在本地执行："
echo "  nslookup -type=TXT $SELECTOR._domainkey.$DOMAIN 8.8.8.8"
echo ""
echo "📧 配置完成后，重新发送测试邮件到外部邮箱（QQ、163）"
echo "   应该就不会进垃圾箱了！"
echo ""
