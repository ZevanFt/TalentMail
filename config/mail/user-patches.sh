#!/bin/bash

# This script is executed during docker-mailserver startup
# It installs dovecot-pgsql for PostgreSQL authentication support
# and configures Postfix to use Dovecot SASL

echo "=== TalentMail 自定义配置脚本 ==="

# 使用阿里云镜像源加速下载（解决网络慢的问题）
# 备份原有源
cp /etc/apt/sources.list /etc/apt/sources.list.bak 2>/dev/null || true

# 检测 Debian 版本并设置镜像源
if [ -f /etc/os-release ]; then
    . /etc/os-release
    CODENAME=${VERSION_CODENAME:-bookworm}
else
    CODENAME="bookworm"
fi

# 写入阿里云镜像源
cat > /etc/apt/sources.list << EOF
deb https://mirrors.aliyun.com/debian/ ${CODENAME} main contrib non-free non-free-firmware
deb https://mirrors.aliyun.com/debian/ ${CODENAME}-updates main contrib non-free non-free-firmware
deb https://mirrors.aliyun.com/debian-security ${CODENAME}-security main contrib non-free non-free-firmware
EOF

echo "使用阿里云镜像源加速下载..."

# 检查 dovecot-pgsql 是否已安装
if ! dpkg -l | grep -q dovecot-pgsql; then
    echo "安装 dovecot-pgsql..."
    apt-get update -qq
    apt-get install -y -qq dovecot-pgsql
    echo "dovecot-pgsql 安装成功"
else
    echo "dovecot-pgsql 已安装，跳过"
fi

# 配置 Postfix 使用 Dovecot SASL 认证
# 这样 Postfix 会通过 Dovecot 来验证用户，而 Dovecot 会查询我们的 PostgreSQL 数据库
echo "配置 Postfix 使用 Dovecot SASL..."
postconf -e "smtpd_sasl_type=dovecot"
postconf -e "smtpd_sasl_path=/dev/shm/sasl-auth.sock"
# 允许非加密连接进行认证（解决开发环境 Thunderbird 连接超时问题）
postconf -e "smtpd_tls_auth_only=no"
# 尝试降低 TLS 安全级别，允许自签名证书
postconf -e "smtpd_tls_security_level=may"
# 强制覆盖 submission 服务的 TLS 设置（如果需要完全禁用 TLS，可以使用 none）
postconf -P "submission/inet/smtpd_tls_security_level=none"

# 配置 Dovecot 允许用户名中包含 * 字符（用于 Master user 认证）
echo "配置 Dovecot 允许 Master user 认证格式 (user*master)..."
if ! grep -q "auth_username_chars" /etc/dovecot/dovecot.conf 2>/dev/null; then
    echo "auth_username_chars = abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890.-_@*" >> /etc/dovecot/dovecot.conf
    echo "添加 auth_username_chars 配置成功"
else
    sed -i 's/^auth_username_chars.*/auth_username_chars = abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890.-_@*/' /etc/dovecot/dovecot.conf
    echo "更新 auth_username_chars 配置成功"
fi

# 配置 docker-mailserver 标准 Master user（使用 auth-master.inc）
echo "配置 docker-mailserver Master user..."
MASTER_USER="sync_master"
MASTER_PASSWORD="SyncMasterPassword123"

# 生成 SHA512-CRYPT 密码哈希
echo "生成 Master user 密码哈希..."
PASSWORD_HASH=$(doveadm pw -s SHA512-CRYPT -p "$MASTER_PASSWORD" | cut -d'}' -f2)

# 创建 masterdb 文件（docker-mailserver 标准路径）
echo "${MASTER_USER}:{SHA512-CRYPT}${PASSWORD_HASH}" > /etc/dovecot/masterdb
chown dovecot:dovecot /etc/dovecot/masterdb
chmod 600 /etc/dovecot/masterdb
echo "masterdb 文件已创建"

# 在 10-auth.conf 中启用 auth-master.inc
if ! grep -q "!include auth-master.inc" /etc/dovecot/conf.d/10-auth.conf; then
    sed -i "/!include auth-sql.conf.ext/i !include auth-master.inc" /etc/dovecot/conf.d/10-auth.conf
    echo "已在 10-auth.conf 中启用 auth-master.inc"
else
    echo "auth-master.inc 已启用，跳过"
fi

echo "=== TalentMail 自定义配置完成 ==="