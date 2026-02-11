# 邮件发送故障排查指南

本文档记录了 TalentMail 邮件系统常见的发送故障及解决方案。

---

## 故障 1：邮件发送失败 - 451 4.7.1 Service unavailable

### 错误信息
```
ERROR:core.mail:Failed to send email: (451, b'4.7.1 Service unavailable - try again later')
smtplib.SMTPDataError: (451, b'4.7.1 Service unavailable - try again later')
```

### 根本原因
这个错误通常由 **OpenDKIM** 配置问题导致，有以下两种情况：

#### 情况 1：DKIM 密钥路径不安全
**日志特征：**
```
opendkim[836]: mail._domainkey.talenting.vip: key data is not secure: /tmp can be read or written by other users
opendkim[836]: error loading key 'mail._domainkey.talenting.vip'
postfix/sender-cleanup/cleanup: milter-reject: END-OF-MESSAGE ... 4.7.1 Service unavailable
```

**原因分析：**
- OpenDKIM 拒绝从 `/tmp` 目录加载 DKIM 私钥
- 虽然密钥文件权限正确（`-rw------- opendkim:opendkim`），但父目录 `/tmp` 权限是 `drwxrwxrwt`（所有用户可读写）
- OpenDKIM 默认配置 `RequireSafeKeys yes` 拒绝加载来自不安全路径的密钥

**解决方案：**

**方法 1：手动修复（立即生效）**
```bash
# 1. 配置 OpenDKIM 允许从 /tmp 加载密钥
docker exec talentmail-mailserver-1 bash -c "
    if [ -f /etc/opendkim.conf ]; then
        if ! grep -q '^RequireSafeKeys' /etc/opendkim.conf; then
            echo 'RequireSafeKeys no' >> /etc/opendkim.conf
        else
            sed -i 's/^RequireSafeKeys.*/RequireSafeKeys no/' /etc/opendkim.conf
        fi
    fi
"

# 2. 重启 OpenDKIM 服务
docker exec talentmail-mailserver-1 supervisorctl restart opendkim

# 3. 验证服务状态
docker exec talentmail-mailserver-1 supervisorctl status opendkim
```

**方法 2：自动修复（集成到部署脚本）**
- 已集成到 `scripts/fix_mail_permissions.sh`
- 部署时自动执行，无需手动干预

#### 情况 2：DKIM 密钥丢失或未生成
**日志特征：**
```
opendkim[836]: error loading key 'mail._domainkey.talenting.vip'
```

**原因分析：**
- 容器重建后 DKIM 密钥丢失
- DKIM 密钥存储在容器内的 `/tmp/docker-mailserver/opendkim/keys/`
- 虽然有 volume 持久化到宿主机 `./data/mailserver/config/`，但首次部署或重建容器后需要重新生成

**解决方案：**

**手动生成 DKIM 密钥：**
```bash
bash scripts/setup_dkim.sh
```

**自动生成（集成到部署脚本）：**
- 已集成到 `deploy.sh` 步骤 13
- 部署时自动生成 DKIM 密钥

**DKIM 配置完成后会显示 DNS 配置说明：**
- 需要在 Cloudflare 添加 TXT 记录
- 格式：`mail._domainkey` → `v=DKIM1; h=sha256; k=rsa; p=...`
- 用于发送外部邮件，内部邮件不需要 DNS 配置

---

## 故障 2：IMAP 邮件同步失败 - Permission denied

### 错误信息
```
Permission denied (euid=109(dovecot) egid=112(dovecot) missing +r perm: /etc/dovecot/master-users
```

### 根本原因
Dovecot Master user 认证文件权限或所有者不正确。

**对比正常与异常情况：**
```bash
# ✅ 正常（本地开发环境）
-rw------- dovecot:dovecot /etc/dovecot/master-users

# ❌ 异常（云端生产环境）
-rw------- root:root /etc/dovecot/master-users
```

### 解决方案

**手动修复：**
```bash
docker exec talentmail-mailserver-1 chown dovecot:dovecot /etc/dovecot/master-users
docker exec talentmail-mailserver-1 chmod 600 /etc/dovecot/master-users
docker exec talentmail-mailserver-1 supervisorctl restart dovecot
```

**自动修复：**
- 已集成到 `scripts/fix_mail_permissions.sh`
- 部署时自动执行

**验证修复：**
```bash
# 检查权限
docker exec talentmail-mailserver-1 ls -la /etc/dovecot/master-users

# 应该显示：
# -rw------- 1 dovecot dovecot ... /etc/dovecot/master-users
```

---

## 故障 3：SMTP STARTTLS 不支持

### 错误信息
```
SMTPNotSupportedError: STARTTLS extension not supported by server
```

### 根本原因
Postfix submission 端口（587）未启用 STARTTLS 加密。

### 解决方案

**手动修复：**
```bash
docker exec talentmail-mailserver-1 postconf -P "submission/inet/smtpd_tls_security_level=may"
docker exec talentmail-mailserver-1 postfix reload
```

**自动修复：**
- 已集成到 `scripts/fix_mail_permissions.sh`
- 部署时自动执行

**验证 STARTTLS 是否启用：**
```bash
# 测试连接
nc -v maillink.talenting.vip 587

# 手动发送 EHLO 命令查看支持的扩展
telnet maillink.talenting.vip 587
> EHLO test
> QUIT

# 应该看到 STARTTLS 在支持列表中
```

---

## 故障 4：外部邮件进垃圾箱

### 症状
- 内部邮件发送正常
- 发送到外部邮箱（QQ、163、Gmail）进垃圾箱或被拒收

### 根本原因
缺少反垃圾邮件配置：
1. **SPF 记录** - 授权哪些 IP 可以代表你的域名发邮件
2. **DKIM 签名** - 邮件数字签名
3. **DMARC 记录** - 邮件验证策略
4. **PTR 记录**（反向 DNS）- IP 地址反向解析

### 解决方案

#### 1. 配置 SPF 记录
在 Cloudflare DNS 中添加 TXT 记录：
```
类型: TXT
名称: @
内容: v=spf1 mx a ip4:你的服务器IP ~all
```

#### 2. 配置 DKIM 签名
```bash
# 运行 DKIM 配置脚本
bash scripts/setup_dkim.sh

# 根据脚本输出，在 Cloudflare DNS 中添加 TXT 记录：
# 类型: TXT
# 名称: mail._domainkey
# 内容: v=DKIM1; h=sha256; k=rsa; p=MIIBIjANBg...（复制脚本输出的完整公钥）
```

#### 3. 配置 DMARC 记录
在 Cloudflare DNS 中添加 TXT 记录：
```
类型: TXT
名称: _dmarc
内容: v=DMARC1; p=quarantine; rua=mailto:dmarc@talenting.vip
```

#### 4. 配置 PTR 记录（反向 DNS）
联系云服务提供商配置 PTR 记录，将服务器 IP 反向解析到 `maillink.talenting.vip`。

#### 验证配置
```bash
# 验证 SPF
nslookup -type=TXT talenting.vip 8.8.8.8

# 验证 DKIM
nslookup -type=TXT mail._domainkey.talenting.vip 8.8.8.8

# 验证 DMARC
nslookup -type=TXT _dmarc.talenting.vip 8.8.8.8

# 验证 PTR
nslookup 你的服务器IP 8.8.8.8
```

---

## 故障 5：容器重建后邮件功能异常

### 症状
- 全新部署或使用 `docker compose down -v` 后邮件无法发送
- DKIM 密钥丢失
- Master user 权限异常

### 根本原因
- DKIM 密钥存储在容器内，重建后丢失
- Master user 配置在 `user-patches.sh` 中，只在容器首次构建时执行
- OpenDKIM 配置同样只在首次构建时执行

### 解决方案

**使用迁移部署模式（推荐）：**
```bash
# 迁移部署：保留数据，仅更新代码
bash deploy.sh --migrate
```

**如果必须全新部署：**
```bash
# 全新部署：会清空所有数据
bash deploy.sh --fresh
```

**部署完成后自动执行的修复：**
- ✅ 步骤 12：自动修复邮件系统（Master user 权限 + STARTTLS + OpenDKIM）
- ✅ 步骤 13：自动配置 DKIM 签名

---

## 一键部署流程

### 首次部署
```bash
# 1. 克隆代码
git clone https://github.com/ZevanFt/TalentMail.git
cd TalentMail

# 2. 配置环境变量
cp .env.example .env
vim .env  # 修改必需的配置

# 3. 配置域名
vim config.json  # 修改域名配置

# 4. 执行部署
bash deploy.sh --fresh
```

### 更新部署
```bash
# 1. 拉取最新代码
cd TalentMail
git stash  # 暂存本地修改
git pull
git stash pop  # 恢复本地修改

# 2. 执行迁移部署
bash deploy.sh --migrate
```

### 部署后验证
```bash
# 1. 检查服务状态
docker compose ps

# 2. 检查邮件服务日志
docker compose logs mailserver --tail 50

# 3. 测试邮件发送
# 登录前端，发送内部邮件测试
# 发送外部邮件测试（确保已配置 DNS）

# 4. 检查 DKIM 状态
docker exec talentmail-mailserver-1 supervisorctl status opendkim

# 5. 检查 Master user 权限
docker exec talentmail-mailserver-1 ls -la /etc/dovecot/master-users
```

---

## 常用故障排查命令

### 查看邮件服务日志
```bash
# 查看 mailserver 日志
docker compose logs mailserver --tail 100 -f

# 查看 backend 日志
docker compose logs backend --tail 100 -f

# 过滤 DKIM 相关日志
docker compose logs mailserver | grep -i dkim

# 过滤邮件发送日志
docker compose logs backend | grep -i "send_email"
```

### 检查邮件队列
```bash
# 查看 Postfix 邮件队列
docker exec talentmail-mailserver-1 mailq

# 清空邮件队列
docker exec talentmail-mailserver-1 postsuper -d ALL
```

### 检查服务状态
```bash
# 查看 mailserver 内所有服务状态
docker exec talentmail-mailserver-1 supervisorctl status

# 重启特定服务
docker exec talentmail-mailserver-1 supervisorctl restart postfix
docker exec talentmail-mailserver-1 supervisorctl restart dovecot
docker exec talentmail-mailserver-1 supervisorctl restart opendkim
```

### 测试 SMTP 连接
```bash
# 测试端口连通性
nc -zv maillink.talenting.vip 587

# 手动测试 SMTP 认证
telnet maillink.talenting.vip 587
> EHLO test
> STARTTLS
> QUIT
```

### 测试 IMAP 连接
```bash
# 测试 IMAP 连接
telnet maillink.talenting.vip 143

# 测试 Master user 认证
# 格式：username@domain*master_username
# 密码：master_password
```

---

## 联系支持

如果以上方案无法解决问题，请：
1. 收集完整的错误日志
2. 记录复现步骤
3. 提交 Issue 到 GitHub：https://github.com/ZevanFt/TalentMail/issues

---

**最后更新：** 2026-02-12
**维护者：** TalentMail Team
