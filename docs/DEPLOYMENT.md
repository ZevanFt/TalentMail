# TalentMail 云端部署文档

## 📋 目录

- [概述](#概述)
- [前置要求](#前置要求)
- [服务器配置](#服务器配置)
- [DNS 配置](#dns-配置)
- [部署步骤](#部署步骤)
- [邮件系统配置](#邮件系统配置)
- [验证和测试](#验证和测试)
- [故障排查](#故障排查)
- [维护脚本](#维护脚本)

---

## 概述

TalentMail 是一个基于 Docker 的完整邮件系统，包含：

- **前端**：Vue 3 + Nuxt 3 邮件客户端
- **后端**：FastAPI + PostgreSQL
- **邮件服务器**：docker-mailserver (Postfix + Dovecot)
- **数据库**：PostgreSQL
- **反向代理**：Nginx

**核心功能**：
- ✅ 内部邮件收发
- ✅ 外部邮件发送（SPF + DKIM + PTR 认证）
- ✅ IMAP 邮件同步（Master user 认证）
- ✅ SMTP 发送（STARTTLS 加密）
- ✅ Web 邮件客户端

---

## 前置要求

### 服务器要求

- **CPU**：2 核及以上
- **内存**：4GB 及以上
- **磁盘**：20GB 及以上
- **系统**：Ubuntu 20.04+ / Debian 11+
- **网络**：公网 IP，开放以下端口

### 必需端口

| 端口 | 协议 | 用途 |
|------|------|------|
| 80 | HTTP | Web 访问（自动跳转 HTTPS） |
| 443 | HTTPS | Web 访问 |
| 25 | SMTP | 邮件接收（可选，外部邮件接收） |
| 587 | SMTP | 邮件发送（STARTTLS） |
| 143 | IMAP | 邮件客户端访问 |
| 993 | IMAPS | 邮件客户端访问（SSL） |

### 必需软件

```bash
# Docker 和 Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Git
sudo apt update
sudo apt install -y git

# Node.js 18+ (本地开发用)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

---

## 服务器配置

### 1. 克隆项目

```bash
cd /root/projects
git clone https://github.com/你的用户名/TalentMail.git
cd TalentMail
```

### 2. 修改配置文件

#### `config.json`

```json
{
  "currentEnvironment": "production",
  "environments": {
    "production": {
      "baseDomain": "talenting.vip",
      "webPrefix": "mail",
      "mailServerPrefix": "maillink",
      "smtpPort": 587,
      "mailStarttls": true,
      "mailUseSsl": false,
      "strictEmailValidation": true,
      "useCredentials": true
    }
  }
}
```

**注意**：
- `currentEnvironment` 必须设置为 `production`
- `baseDomain` 改为你的域名
- `webPrefix` 是前端访问域名前缀（如 `mail.talenting.vip`）
- `mailServerPrefix` 是邮件服务器域名前缀（如 `maillink.talenting.vip`）

#### `.env`（如有需要）

生产环境的敏感配置（数据库密码、JWT 密钥等）。

---

## DNS 配置

### 必需的 DNS 记录

在你的 DNS 服务商（如 Cloudflare、阿里云）配置以下记录：

#### 1. A 记录

| 类型 | 名称 | 内容 | TTL |
|------|------|------|-----|
| A | mail | 你的服务器 IP | Auto |
| A | maillink | 你的服务器 IP | Auto |

#### 2. MX 记录

| 类型 | 名称 | 内容 | 优先级 | TTL |
|------|------|------|--------|-----|
| MX | @ | maillink.talenting.vip | 10 | Auto |

#### 3. SPF 记录（防止邮件被当作垃圾邮件）

| 类型 | 名称 | 内容 | TTL |
|------|------|------|-----|
| TXT | @ | v=spf1 mx ip4:你的服务器IP -all | Auto |

**示例**：
```
v=spf1 mx ip4:111.91.23.109 -all
```

#### 4. PTR 记录（反向 DNS）

**华为云配置**：
1. 进入 **弹性云服务器 ECS**
2. 点击你的服务器 → **弹性公网IP** → **反向解析**
3. 填写：
   - IP 地址：你的服务器 IP
   - 域名：`maillink.talenting.vip`
   - TTL：300

**验证**：
```bash
nslookup 你的服务器IP
# 应该返回 maillink.talenting.vip
```

#### 5. DKIM 记录（邮件签名）

**配置步骤**：见 [邮件系统配置 - DKIM 配置](#3-配置-dkim-签名)

#### 6. DMARC 记录（可选，提升信誉）

| 类型 | 名称 | 内容 | TTL |
|------|------|------|-----|
| TXT | _dmarc | v=DMARC1; p=none; rua=mailto:admin@talenting.vip | Auto |

---

## 部署步骤

### 方式一：全新部署（无数据）

```bash
cd /root/projects/TalentMail
bash deploy.sh
```

在交互式菜单中选择 **1) 全新部署（清空数据）**

### 方式二：更新部署（保留数据）

```bash
cd /root/projects/TalentMail
bash deploy.sh
```

在交互式菜单中选择 **2) 更新部署（保留数据）**

### 手动部署步骤

如果需要手动控制每一步：

```bash
# 1. 拉取最新代码
git pull

# 2. 停止旧容器
docker compose down

# 3. 构建前端（如果代码有更新）
cd frontend
npm install
npm run build
cd ..

# 4. 启动所有服务
docker compose up -d

# 5. 等待服务启动
sleep 30

# 6. 初始化数据库（仅全新部署）
docker compose exec backend python -c "
from backend.database import init_db
init_db()
"

# 7. 创建初始管理员账户（仅全新部署）
docker compose exec backend python scripts/create_admin.py

# 8. 查看日志确认服务正常
docker compose logs -f --tail 50
```

---

## 邮件系统配置

### 1. 创建邮箱账号

邮箱账号通过前端注册或后端 API 创建，会自动同步到 docker-mailserver。

**手动创建测试账号**：

```bash
docker compose exec backend python scripts/create_test_users.py
```

### 2. 配置 Master User 认证（IMAP 同步）

**一键修复脚本**（推荐）：

```bash
bash scripts/fix_mail_production.sh
```

此脚本会：
- ✅ 重新创建 mailserver 容器
- ✅ 配置 Master user 认证（sync_master）
- ✅ 配置 SMTP STARTTLS
- ✅ 重启 Dovecot 服务
- ✅ 验证所有配置

**验证 Master user 认证**：

```bash
docker exec talentmail-mailserver-1 doveadm auth test -x service=imap \
  "admin@talenting.vip*sync_master" "SyncMasterPassword123"
```

应该看到 `auth succeeded`。

### 3. 配置 DKIM 签名

**一键配置脚本**：

```bash
bash scripts/setup_dkim.sh
```

此脚本会：
1. ✅ 生成 DKIM 密钥对（2048 位）
2. ✅ 配置 OpenDKIM
3. ✅ 重启 OpenDKIM 服务
4. ✅ **输出 DNS TXT 记录**

**复制脚本输出的内容，添加到 Cloudflare**：

```
类型: TXT
名称: mail._domainkey
内容: v=DKIM1; h=sha256; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A...
```

**验证 DKIM 记录**：

```bash
nslookup -type=TXT mail._domainkey.talenting.vip 8.8.8.8
```

应该看到你配置的公钥。

---

## 验证和测试

### 1. 验证服务状态

```bash
docker compose ps
```

所有服务应该都是 `Up` 状态。

### 2. 验证前端访问

浏览器访问：`https://mail.talenting.vip`

应该能看到登录界面。

### 3. 测试内部邮件收发

1. 注册两个账号：`admin@talenting.vip` 和 `zevan@talenting.vip`
2. 用 admin 发送邮件给 zevan
3. 等待 10-20 秒（IMAP 同步间隔）
4. zevan 刷新收件箱，应该能看到邮件

### 4. 测试外部邮件发送

1. 用 admin@talenting.vip 发送邮件到你的 QQ 邮箱或 163 邮箱
2. 检查收件箱（不是垃圾箱），应该能收到邮件

**如果进垃圾箱**，检查：
- ✅ SPF 记录是否配置
- ✅ PTR 记录是否生效
- ✅ DKIM 记录是否生效
- ✅ DMARC 记录是否配置（可选）

### 5. 验证 SMTP 和 IMAP 端口

```bash
# 测试 SMTP 连接
telnet maillink.talenting.vip 587

# 测试 IMAP 连接
telnet maillink.talenting.vip 143
```

---

## 故障排查

### 问题 1：前端无法访问

**检查**：
```bash
docker compose logs frontend
docker compose logs nginx
```

**常见原因**：
- Nginx 配置错误
- 域名解析未生效
- SSL 证书问题

### 问题 2：邮件发送失败

**检查后端日志**：
```bash
docker compose logs backend | grep -E "SMTP|mail"
```

**常见错误**：
- `SMTP AUTH extension not supported` → STARTTLS 未启用
- `Connection refused` → 邮件服务器未启动
- `Authentication failed` → SMTP 用户名密码错误

**解决**：
```bash
bash scripts/fix_mail_production.sh
```

### 问题 3：邮件无法接收（IMAP 同步失败）

**检查 Master user 认证**：
```bash
docker exec talentmail-mailserver-1 doveadm auth test -x service=imap \
  "admin@talenting.vip*sync_master" "SyncMasterPassword123"
```

**检查后端日志**：
```bash
docker compose logs backend | grep -E "IMAP|sync"
```

**常见错误**：
- `Username character disallowed` → auth_username_chars 未配置
- `Authentication failed` → masterdb 文件未创建或密码错误
- `PRIVACYREQUIRED` → STARTTLS 未启用

**解决**：
```bash
bash scripts/fix_mail_production.sh
```

### 问题 4：外发邮件进垃圾箱

**检查 DNS 记录**：
```bash
# SPF
nslookup -type=TXT talenting.vip 8.8.8.8

# PTR
nslookup 你的服务器IP

# DKIM
nslookup -type=TXT mail._domainkey.talenting.vip 8.8.8.8
```

**解决**：
```bash
# 重新配置 DKIM
bash scripts/setup_dkim.sh
```

### 问题 5：数据库连接失败

**检查数据库状态**：
```bash
docker compose logs db
docker compose exec db psql -U talentmail -d talentmail -c "SELECT 1;"
```

**重启数据库**：
```bash
docker compose restart db
```

---

## 维护脚本

### 1. `scripts/fix_mail_production.sh`

**用途**：一键修复所有邮件系统问题

**功能**：
- 重新创建 mailserver 容器
- 配置 Master user 认证
- 配置 SMTP STARTTLS
- 重启 Dovecot
- 验证配置

**使用**：
```bash
bash scripts/fix_mail_production.sh
```

---

### 2. `scripts/setup_dkim.sh`

**用途**：配置 DKIM 邮件签名

**功能**：
- 生成 DKIM 密钥对（2048 位）
- 配置 OpenDKIM（KeyTable, SigningTable, TrustedHosts）
- 重启 OpenDKIM 服务
- 输出 DNS TXT 记录配置说明

**使用**：
```bash
bash scripts/setup_dkim.sh
```

**配置后续步骤**：
1. 复制脚本输出的 TXT 记录内容
2. 登录 Cloudflare DNS 管理
3. 添加 TXT 记录：
   - 类型：TXT
   - 名称：mail._domainkey
   - 内容：（粘贴脚本输出）
   - TTL：Auto

---

### 3. `scripts/deploy_master_user.sh`

**用途**：部署 Master user 认证配置（带容器重建）

**使用**：
```bash
bash scripts/deploy_master_user.sh
```

---

### 4. `scripts/setup_master_user.sh`

**用途**：配置 Master user 认证（不重建容器）

**使用**：
```bash
bash scripts/setup_master_user.sh
```

---

### 5. `scripts/init_fresh_database.sh`

**用途**：初始化全新数据库（会清空所有数据）

**警告**：此操作会删除所有数据，仅用于全新部署！

**使用**：
```bash
bash scripts/init_fresh_database.sh
```

---

## 配置文件说明

### 关键配置文件

| 文件路径 | 用途 |
|---------|------|
| `config.json` | 环境配置（域名、端口、SMTP/IMAP 设置） |
| `config/mail/user-patches.sh` | Mailserver 启动脚本（安装 dovecot-pgsql、配置 STARTTLS） |
| `config/mail/dovecot/10-auth.conf` | Dovecot 认证配置（启用 Master user + SQL 认证） |
| `config/mail/dovecot/dovecot-sql.conf.ext` | Dovecot SQL 认证配置（PostgreSQL 查询） |
| `docker-compose.yml` | Docker 服务编排 |
| `nginx/conf.d/default.conf` | Nginx 反向代理配置 |

### Master User 认证

**用户名格式**：`实际用户@域名*master用户`

**示例**：
```
用户邮箱：admin@talenting.vip
Master user：sync_master
Master password：SyncMasterPassword123

IMAP 登录用户名：admin@talenting.vip*sync_master
IMAP 登录密码：SyncMasterPassword123
```

**配置文件位置**：
- `/etc/dovecot/masterdb`（容器内）
- 格式：`sync_master:{SHA512-CRYPT}$6$...`

---

## 安全建议

### 1. 修改默认密码

**Master user 密码**：

编辑 `config/mail/user-patches.sh`:
```bash
MASTER_PASSWORD="你的强密码"
```

**数据库密码**：

编辑 `.env` 或 `docker-compose.yml` 中的数据库密码。

### 2. 防火墙配置

```bash
# 仅开放必要端口
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 25/tcp    # SMTP
sudo ufw allow 587/tcp   # SMTP Submission
sudo ufw allow 143/tcp   # IMAP
sudo ufw allow 993/tcp   # IMAPS
sudo ufw enable
```

### 3. 定期更新

```bash
cd /root/projects/TalentMail
git pull
bash deploy.sh  # 选择 "更新部署（保留数据）"
```

### 4. 备份数据库

```bash
# 备份数据库
docker compose exec db pg_dump -U talentmail talentmail > backup_$(date +%Y%m%d).sql

# 恢复数据库
docker compose exec -T db psql -U talentmail talentmail < backup_20240211.sql
```

---

## 常用命令

### 查看日志

```bash
# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f mailserver
docker compose logs -f frontend

# 查看最近 50 行日志
docker compose logs --tail 50
```

### 重启服务

```bash
# 重启所有服务
docker compose restart

# 重启特定服务
docker compose restart backend
docker compose restart mailserver
```

### 进入容器

```bash
# 进入后端容器
docker compose exec backend bash

# 进入邮件服务器容器
docker compose exec mailserver bash

# 进入数据库容器
docker compose exec db psql -U talentmail
```

### 清理容器和镜像

```bash
# 停止并删除所有容器
docker compose down

# 清理未使用的 Docker 镜像
docker system prune -a
```

---

## 性能优化

### 1. 数据库优化

编辑 `docker-compose.yml`，增加 PostgreSQL 内存：

```yaml
db:
  environment:
    - POSTGRES_SHARED_BUFFERS=512MB
    - POSTGRES_EFFECTIVE_CACHE_SIZE=2GB
```

### 2. 前端构建优化

```bash
# 使用生产环境构建
cd frontend
npm run build  # 已包含压缩和优化
```

### 3. Nginx 缓存

编辑 `nginx/conf.d/default.conf`，添加缓存配置（已配置）。

---

## 总结

本文档涵盖了 TalentMail 邮件系统的完整部署流程，包括：

✅ 服务器配置
✅ DNS 记录配置（A、MX、SPF、PTR、DKIM、DMARC）
✅ Docker 容器部署
✅ 邮件系统配置（Master user、DKIM、STARTTLS）
✅ 验证和测试
✅ 故障排查
✅ 维护脚本使用

遵循本文档，你可以快速将 TalentMail 部署到任何支持 Docker 的云服务器。

---

**文档版本**：v2.0
**最后更新**：2026-02-11
**维护者**：TalentMail Team
