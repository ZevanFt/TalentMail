#!/bin/bash

# TalentMail 自定义配置脚本
# dovecot-pgsql 和 netcat 已在 Dockerfile 中预装
#
# 邮件投递架构：
#   外部邮件 → Postfix (port 25) → Dovecot LMTP (默认) → 邮件存储
#   Backend mail_sync.py 每 30 秒通过 IMAP Master user 同步到 PostgreSQL

echo "=== TalentMail 配置脚本开始 ==="

# ---- 1. Dovecot Master user（用于 IMAP 邮件同步）----
echo "配置 Dovecot Master user..."
MASTER_USER="${MAIL_MASTER_USER:-sync_master}"
MASTER_PASSWORD="${MAIL_MASTER_PASSWORD:-${ADMIN_PASSWORD}}"
if [ -z "$MASTER_PASSWORD" ]; then
    echo "❌ 未配置 MAIL_MASTER_PASSWORD（且 ADMIN_PASSWORD 为空），无法创建 master user"
    exit 1
fi
echo "${MASTER_USER}:{PLAIN}${MASTER_PASSWORD}" > /etc/dovecot/master-users
chown dovecot:dovecot /etc/dovecot/master-users
chmod 600 /etc/dovecot/master-users
echo "master-users 文件已创建"

# ---- 2. Dovecot 配置（master user + socket 权限）----
cat > /etc/dovecot/conf.d/99-talentmail.conf << 'DOVECOT_EOF'
# Master user 认证（用于 mail_sync.py 通过 IMAP 同步邮件到数据库）
auth_master_user_separator = *
passdb {
  driver = passwd-file
  master = yes
  args = /etc/dovecot/master-users
}

# LMTP socket 权限
service lmtp {
  unix_listener lmtp {
    mode = 0666
  }
}

# Auth socket 权限
service auth {
  unix_listener auth-userdb {
    mode = 0777
  }
}
DOVECOT_EOF
echo "Dovecot 99-talentmail.conf 已写入"

# ---- 3. Postfix SASL 配置 ----
# 延迟执行以确保 docker-mailserver 初始化完成
(
    sleep 10

    echo "配置 Postfix SASL..."
    postconf -e "smtpd_sasl_type=dovecot"
    postconf -e "smtpd_sasl_path=/dev/shm/sasl-auth.sock"
    postconf -e "smtpd_tls_auth_only=no"
    postconf -e "smtpd_tls_security_level=may"
    postconf -P "submission/inet/smtpd_tls_security_level=none"

    # 关键修复：移除已损坏的 dual-deliver 传输，恢复默认 Dovecot LMTP 投递
    CURRENT_TRANSPORT=$(postconf -h virtual_transport 2>/dev/null)
    if [ "$CURRENT_TRANSPORT" = "dual-deliver" ]; then
        echo "检测到 dual-deliver 传输，恢复默认 Dovecot LMTP..."
        postconf -e "virtual_transport=lmtp:unix:private/dovecot-lmtp"
    fi

    # 从 master.cf 移除 dual-deliver 配置（如有）
    if grep -q "dual-deliver" /etc/postfix/master.cf 2>/dev/null; then
        sed -i '/^# 双投递传输$/d' /etc/postfix/master.cf
        sed -i '/^dual-deliver /,/^[^ ]/{ /^dual-deliver /d; /^  /d; }' /etc/postfix/master.cf
        echo "已从 master.cf 移除 dual-deliver"
    fi

    # 重载配置
    postfix reload
    supervisorctl restart dovecot

    echo "=== Postfix/Dovecot 配置完成 ==="
) &

# ---- 4. OpenDKIM 配置 ----
if [ -f /etc/opendkim.conf ]; then
    if ! grep -q "^RequireSafeKeys" /etc/opendkim.conf; then
        echo "RequireSafeKeys no" >> /etc/opendkim.conf
    else
        sed -i 's/^RequireSafeKeys.*/RequireSafeKeys no/' /etc/opendkim.conf
    fi
    echo "OpenDKIM 配置完成"
fi

echo "=== TalentMail 配置脚本完成 ==="
