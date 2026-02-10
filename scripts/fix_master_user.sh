#!/bin/bash
# 修复 Dovecot Master user 认证配置

echo "=== 修复 Dovecot Master user 认证 ==="

# 1. 修复 auth-sql.conf.ext，去掉 pass = yes
cat > /tmp/auth-sql.conf.ext << 'EOFMASTER'
# Authentication for SQL users. Included from 10-auth.conf.
#
# <doc/wiki/AuthDatabase.SQL.txt>

# Master user passdb - 必须放在普通 SQL passdb 之前
# 支持 user@domain*masteruser 格式的登录
passdb {
  driver = passwd-file
  args = /etc/dovecot/master-users
  master = yes
}

passdb {
  driver = sql
  args = /etc/dovecot/dovecot-sql.conf.ext
}

userdb {
  driver = sql
  args = /etc/dovecot/dovecot-sql.conf.ext
}
EOFMASTER

# 2. 复制到容器内
docker cp /tmp/auth-sql.conf.ext talentmail-mailserver-1:/etc/dovecot/conf.d/auth-sql.conf.ext

# 3. 确保 master-users 文件存在且权限正确
docker exec talentmail-mailserver-1 bash -c 'echo "sync_master:{PLAIN}SyncMasterPassword123" > /etc/dovecot/master-users'
docker exec talentmail-mailserver-1 chown dovecot:dovecot /etc/dovecot/master-users
docker exec talentmail-mailserver-1 chmod 600 /etc/dovecot/master-users

# 4. 重启 Dovecot
echo "重启 Dovecot..."
docker exec talentmail-mailserver-1 supervisorctl restart dovecot

# 5. 等待启动
sleep 3

# 6. 测试认证
echo ""
echo "=== 测试 Master user 认证 ==="
docker exec talentmail-mailserver-1 doveadm auth test -x service=imap zevan@talenting.vip*sync_master SyncMasterPassword123

echo ""
echo "=== 查看最近的认证日志 ==="
docker logs talentmail-mailserver-1 --tail 10 | grep auth

echo ""
echo "=== 完成 ==="
