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
# 在 dovecot.conf 中添加 auth_username_chars 配置
if ! grep -q "auth_username_chars" /etc/dovecot/dovecot.conf 2>/dev/null; then
    echo "auth_username_chars = abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890.-_@*" >> /etc/dovecot/dovecot.conf
    echo "添加 auth_username_chars 配置成功"
else
    # 如果已存在，则更新配置
    sed -i 's/^auth_username_chars.*/auth_username_chars = abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890.-_@*/' /etc/dovecot/dovecot.conf
    echo "更新 auth_username_chars 配置成功"
fi

# 配置 Dovecot Master user passdb
echo "配置 Dovecot Master user passdb..."
# 复制 Master users 文件到 Dovecot 配置目录
if [ -f /tmp/docker-mailserver/dovecot-master-users ]; then
    cp /tmp/docker-mailserver/dovecot-master-users /etc/dovecot/master-users
    chmod 600 /etc/dovecot/master-users
    echo "Master users 文件已复制"
fi

# 在 auth-sql.conf.ext 中添加 Master passdb（在 SQL passdb 之前）
if ! grep -q "# Master user passdb" /etc/dovecot/conf.d/auth-sql.conf.ext; then
    # 备份原文件
    cp /etc/dovecot/conf.d/auth-sql.conf.ext /etc/dovecot/conf.d/auth-sql.conf.ext.bak

    # 在文件开头添加 Master passdb 配置
    cat > /etc/dovecot/conf.d/auth-sql.conf.ext << 'EOFMASTER'
# Authentication for SQL users. Included from 10-auth.conf.
#
# <doc/wiki/AuthDatabase.SQL.txt>

# Master user passdb - 必须放在普通 SQL passdb 之前
# 支持 user@domain*masteruser 格式的登录
passdb {
  driver = passwd-file
  args = /etc/dovecot/master-users
  master = yes
  pass = yes
}

passdb {
  driver = sql

  # Path for SQL configuration file, see example-config/dovecot-sql.conf.ext
  args = /etc/dovecot/dovecot-sql.conf.ext
}

# "prefetch" user database means that the passdb already provided the
# needed information and there's no need to do a separate userdb lookup.
# <doc/wiki/UserDatabase.Prefetch.txt>
#userdb {
#  driver = prefetch
#}

userdb {
  driver = sql
  args = /etc/dovecot/dovecot-sql.conf.ext
}

# If you don't have any user-specific settings, you can avoid the user_query
# by using userdb static instead of userdb sql, for example:
# <doc/wiki/UserDatabase.Static.txt>
#userdb {
  #driver = static
  #args = uid=vmail gid=vmail home=/var/vmail/%u
#}
EOFMASTER
    echo "Master passdb 配置已添加到 auth-sql.conf.ext"
else
    echo "Master passdb 配置已存在，跳过"
fi

echo "=== TalentMail 自定义配置完成 ==="