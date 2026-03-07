#!/bin/bash
# TalentMail DKIM 配置脚本
# 此脚本为邮件服务器配置 DKIM 签名，防止邮件进垃圾箱
# 使用方式：bash scripts/setup_dkim.sh

set -e

CONTAINER_NAME="${MAILSERVER_CONTAINER_NAME:-talentmail-mailserver-1}"
DOMAIN="${DOMAIN:-}"
SELECTOR="${DKIM_SELECTOR:-mail}"  # DKIM 选择器，可以是任意名称
FORCE_REGEN="${FORCE_DKIM_REGEN:-0}"
STRICT_DOMAIN_CHECK="${STRICT_DKIM_DOMAIN_CHECK:-0}"

if [ -z "$DOMAIN" ] && [ -f ".env.domains" ]; then
    DOMAIN=$(grep -E '^DOMAIN=' .env.domains | cut -d'=' -f2- | tr -d '"' | tr -d "'")
fi

if [ -z "$DOMAIN" ]; then
    DOMAIN="talenting.vip"
    echo "⚠️  未检测到 DOMAIN，使用默认值: $DOMAIN"
fi

echo "==========================================="
echo "  TalentMail DKIM 配置"
echo "==========================================="
echo ""
echo "域名: $DOMAIN"
echo "选择器: $SELECTOR"
echo "强制重生成: $FORCE_REGEN"
echo "严格域名检查: $STRICT_DOMAIN_CHECK"
echo ""

# 检查容器是否运行
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ 容器 $CONTAINER_NAME 未运行，请先启动邮件服务器"
    exit 1
fi

# 0. 检查历史 DKIM 域名与当前部署域名是否一致
echo "🔎 [0/4] 检查 DKIM 域名一致性..."
EXISTING_DKIM_DOMAINS=$(docker exec "$CONTAINER_NAME" bash -c '
KEY_ROOT=/tmp/docker-mailserver/opendkim/keys
if [ -d "$KEY_ROOT" ]; then
  find "$KEY_ROOT" -mindepth 1 -maxdepth 1 -type d -printf "%f\n" | sort
fi
')

TARGET_KEY_EXISTS=$(docker exec "$CONTAINER_NAME" bash -c "
if [ -f /tmp/docker-mailserver/opendkim/keys/$DOMAIN/$SELECTOR.private ] && [ -f /tmp/docker-mailserver/opendkim/keys/$DOMAIN/$SELECTOR.txt ]; then
  echo yes
else
  echo no
fi
")

if [ -n "$EXISTING_DKIM_DOMAINS" ]; then
    echo "  已存在 DKIM 域名目录:"
    echo "$EXISTING_DKIM_DOMAINS" | sed 's/^/    - /'
fi

if [ "$TARGET_KEY_EXISTS" = "no" ] && [ -n "$EXISTING_DKIM_DOMAINS" ]; then
    echo "  ⚠️  当前部署域名 $DOMAIN 没有现成 DKIM 密钥，但容器里存在其他历史域名密钥。"
    echo "  ⚠️  这通常表示曾经用错域名（例如 .test -> .vip）或发生域名迁移。"
    if [ "$STRICT_DOMAIN_CHECK" = "1" ]; then
        echo "  ❌ 严格模式已开启，停止执行。请确认 DOMAIN 与 DNS 配置后重试。"
        exit 1
    fi
fi

KEYTABLE_DOMAIN=$(docker exec "$CONTAINER_NAME" bash -c '
if [ -f /tmp/docker-mailserver/opendkim/KeyTable ]; then
  awk "NF>0 {print \$2; exit}" /tmp/docker-mailserver/opendkim/KeyTable | cut -d: -f1
fi
')
if [ -n "$KEYTABLE_DOMAIN" ] && [ "$KEYTABLE_DOMAIN" != "$DOMAIN" ]; then
    echo "  ⚠️  KeyTable 当前域名为 $KEYTABLE_DOMAIN，与部署域名 $DOMAIN 不一致。"
    echo "  ⚠️  本次会按 $DOMAIN 重写 OpenDKIM 配置。"
fi
echo "  ✅ 域名检查完成"

# 1. 生成/复用 DKIM 密钥对（幂等）
echo "📝 [1/4] 检查 DKIM 密钥对..."
docker exec "$CONTAINER_NAME" bash -c "
    set -e
    KEY_DIR=/tmp/docker-mailserver/opendkim/keys/$DOMAIN
    PRIVATE_KEY=\$KEY_DIR/$SELECTOR.private
    PUBLIC_KEY=\$KEY_DIR/$SELECTOR.txt
    mkdir -p \$KEY_DIR

    if [ \"$FORCE_REGEN\" = \"1\" ]; then
        echo '强制重生成 DKIM 密钥对...'
        rm -f \$PRIVATE_KEY \$PUBLIC_KEY
    fi

    if [ -f \$PRIVATE_KEY ] && [ -f \$PUBLIC_KEY ]; then
        echo '检测到已有 DKIM 密钥，复用现有密钥'
    else
        echo '未检测到完整 DKIM 密钥，开始生成...'
        cd \$KEY_DIR
        opendkim-genkey -b 2048 -d $DOMAIN -s $SELECTOR
    fi

    chown -R opendkim:opendkim /tmp/docker-mailserver/opendkim
    chmod 600 \$PRIVATE_KEY
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

# 提取并格式化 DKIM 公钥（提取所有引号内的内容并合并成一行）
DKIM_PUBLIC_KEY=$(docker exec "$CONTAINER_NAME" cat /tmp/docker-mailserver/opendkim/keys/$DOMAIN/$SELECTOR.txt | grep -o '"[^"]*"' | tr -d '"\n' | sed 's/  */ /g' | sed 's/^ //;s/ $//')

echo "类型: TXT"
echo "名称: $SELECTOR._domainkey"
echo ""
echo "内容（直接复制下面这一整行）："
echo "-------------------------------------------"
echo "$DKIM_PUBLIC_KEY"
echo "-------------------------------------------"

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
