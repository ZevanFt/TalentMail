# TalentMail 部署指南

## 前置要求

### 服务器要求

| 项目 | 最低要求 | 推荐 |
|------|---------|------|
| CPU | 2 核 | 4 核 |
| 内存 | 4 GB | 8 GB |
| 磁盘 | 20 GB SSD | 50 GB SSD |
| 系统 | Ubuntu 22.04 / 24.04 | Ubuntu 24.04 LTS |
| 网络 | 25 端口开放 | 独立 IP |

### 软件要求

- Docker Engine 24+
- Docker Compose v2
- Git
- 宿主机 Caddy（推荐）或其他反向代理

### 域名准备

需要一个域名（以 `example.com` 为例）：
- `mail.example.com` — Web 应用访问地址
- `maillink.example.com` — 邮件服务器地址（**不可经过 CDN 代理**）

---

## 第一步：获取代码

```bash
# 克隆仓库
git clone <repository-url> /opt/talentmail
cd /opt/talentmail

# 创建配置文件
cp .env.example .env
nano .env
```

### 配置 .env

```bash
# 必填项
SECRET_KEY=<openssl rand -hex 32 生成>
POSTGRES_PASSWORD=<强密码>
ADMIN_PASSWORD=<管理员密码>
DEFAULT_MAIL_PASSWORD=<邮箱账户默认密码>
ENCRYPTION_KEY=<openssl rand -hex 32 生成>
MAIL_MASTER_PASSWORD=<Dovecot 主用户密码>

# 可选
ENABLE_INTERNAL_LMTP=false
```

### 配置 config.json

```json
{
  "currentEnvironment": "production",
  "environments": {
    "production": {
      "baseDomain": "example.com",
      "webPrefix": "mail",
      "mailServerPrefix": "maillink"
    }
  }
}
```

---

## 第二步：DNS 配置

在域名解析面板添加以下记录：

| 类型 | 名称 | 值 | 代理 | 说明 |
|------|------|----|------|------|
| A | `mail` | 服务器 IP | 可代理 (Cloudflare Proxied) | Web 应用 |
| A | `maillink` | 服务器 IP | **DNS Only (不代理!)** | 邮件服务器 |
| MX | `@` | `maillink.example.com` | - | 优先级 10 |
| TXT | `@` | `v=spf1 mx ~all` | - | SPF 记录 |

### DKIM 配置

首次部署后生成 DKIM 密钥：

```bash
# 启动 mailserver 后执行
bash deploy.sh --setup-dkim

# 输出 DKIM TXT 记录，添加到 DNS
# 名称: mail._domainkey
# 值: v=DKIM1; k=rsa; p=MIGfMA0GCS...
```

### DMARC（可选但推荐）

```
类型: TXT
名称: _dmarc
值:   v=DMARC1; p=quarantine; rua=mailto:admin@example.com
```

---

## 第三步：首次部署

```bash
# 赋予执行权限
chmod +x deploy.sh

# 全新部署（首次使用）
bash deploy.sh --fresh
```

`--fresh` 会执行：
1. 构建 Docker 镜像 (backend + frontend)
2. 启动 PostgreSQL → 等待健康检查通过
3. 运行 Alembic 数据库迁移
4. 执行种子数据初始化（管理员账户、系统模板、工作流）
5. 启动所有 5 个服务
6. 配置邮件服务器（Postfix + Dovecot）

### 部署模式

| 参数 | 说明 | 使用场景 |
|------|------|---------|
| `--fresh` | 完全初始化 | 首次部署 |
| `--migrate` | 增量更新 | 日常更新（推荐） |
| `--auto` | 自动检测 | 无数据库=fresh，有=migrate |
| `--doctor` | 仅诊断 | 排查问题 |

---

## 第四步：Caddy 反向代理

TalentMail 使用宿主机 Caddy 作为反向代理，自动管理 HTTPS 证书。

### 安装 Caddy

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install caddy
```

### Caddyfile 配置

```caddyfile
mail.example.com {
    encode gzip zstd

    # 安全头
    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "strict-origin-when-cross-origin"
        Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
        -Server
    }

    # WebSocket
    @websocket {
        header Connection *Upgrade*
        header Upgrade websocket
    }
    handle @websocket {
        reverse_proxy 127.0.0.1:18000
    }

    # API 请求
    handle /api/* {
        reverse_proxy 127.0.0.1:18000
    }

    # 前端
    handle {
        reverse_proxy 127.0.0.1:13000
    }
}
```

```bash
# 重载 Caddy 配置
sudo systemctl reload caddy
```

Caddy 会自动从 Let's Encrypt 获取 SSL 证书。

---

## 第五步：增量更新

日常代码更新流程：

```bash
cd /opt/talentmail

# 拉取最新代码
git pull origin main

# 增量部署
bash deploy.sh --migrate
```

`--migrate` 会执行：
1. 重新构建变更的 Docker 镜像
2. 运行新的 Alembic 迁移
3. 重启受影响的服务
4. 验证健康检查

---

## 第六步：验证

```bash
# 1. 健康检查
curl -s https://mail.example.com/api/health | python3 -m json.tool

# 2. Web 访问
# 浏览器打开 https://mail.example.com
# 使用 admin@example.com + .env 中的 ADMIN_PASSWORD 登录

# 3. 发送测试邮件
# 登录后从 Web 界面发送一封测试邮件

# 4. 检查服务状态
docker compose ps
```

---

## 端口需求

| 端口 | 协议 | 用途 | 必须开放 |
|------|------|------|---------|
| 25 | TCP | SMTP (接收外部邮件) | 是 |
| 80 | TCP | HTTP → HTTPS 重定向 | 是 (Caddy) |
| 443 | TCP | HTTPS (Web 访问) | 是 (Caddy) |
| 465 | TCP | SMTPS (加密 SMTP) | 可选 |
| 587 | TCP | SMTP Submission | 可选 |
| 143 | TCP | IMAP | 可选 (外部客户端) |
| 993 | TCP | IMAPS (加密 IMAP) | 可选 (外部客户端) |

> **注意**: 某些云服务商（阿里云、AWS 等）默认封锁 25 端口，需提交工单申请开放。

---

## SSL 证书

### 自动管理 (Caddy)

Caddy 自动从 Let's Encrypt 获取和续期证书，无需手动配置。

### 邮件服务器证书

docker-mailserver 的 TLS 证书需要与 Caddy 同步：

```bash
# 查看 Caddy 证书路径
ls /var/lib/caddy/.local/share/caddy/certificates/

# 可通过 deploy.sh 脚本同步证书到 mailserver
bash deploy.sh --sync-certs
```

---

## 备份与恢复

### 数据库备份

```bash
# 备份
docker compose exec db pg_dump -U talentmail talentmail > backup_$(date +%Y%m%d).sql

# 恢复
docker compose exec -T db psql -U talentmail talentmail < backup_20260427.sql
```

### 文件备份

```bash
# 备份上传文件
tar czf uploads_backup_$(date +%Y%m%d).tar.gz backend/uploads/

# 备份配置
cp .env .env.backup
cp config.json config.json.backup
```

### 完整备份脚本

```bash
#!/bin/bash
BACKUP_DIR="/backup/talentmail/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# 数据库
docker compose exec -T db pg_dump -U talentmail talentmail > "$BACKUP_DIR/db.sql"

# 上传文件
tar czf "$BACKUP_DIR/uploads.tar.gz" backend/uploads/

# 配置文件
cp .env config.json "$BACKUP_DIR/"

echo "备份完成: $BACKUP_DIR"
```

建议使用 cron 每天自动备份：

```bash
0 3 * * * /opt/talentmail/scripts/backup.sh >> /var/log/talentmail-backup.log 2>&1
```

---

## 故障排查

```bash
# 诊断模式
bash deploy.sh --doctor

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f backend
docker compose logs -f mailserver

# 重启单个服务
docker compose restart backend
```

详见 [故障排查文档](./troubleshooting.md) 和 [调试技巧](../04-development/debugging.md)。

---

最后更新: 2026-04-27
