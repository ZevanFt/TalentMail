# 生产环境部署指南

本指南详细说明如何在 Linux 服务器上部署 TalentMail，使用 Cloudflare 作为 DNS 服务提供商。

## 目录

1. [服务器准备](#一服务器准备)
2. [Cloudflare DNS 配置](#二cloudflare-dns-配置)
3. [获取代码与配置](#三获取代码与配置)
4. [一键部署](#四一键部署)
5. [SSL 证书配置](#五ssl-证书配置)
6. [常见问题](#六常见问题)

---

## 一、服务器准备

### 1. 系统要求

- **操作系统**: 推荐 Ubuntu 20.04 LTS 或 22.04 LTS
- **配置**: 至少 2核 CPU, 4GB 内存
- **磁盘**: 至少 20GB 可用空间
- **端口开放**: 确保云服务商的安全组或防火墙开放以下端口：

| 端口 | 协议 | 用途 |
|------|------|------|
| 80 | TCP | HTTP（Caddy 自动重定向到 HTTPS） |
| 443 | TCP | HTTPS（Web 应用） |
| 25 | TCP | SMTP（接收邮件） |
| 143 | TCP | IMAP（不加密，可选） |
| 587 | TCP | SMTP Submission（发送邮件） |
| 993 | TCP | IMAPS（加密 IMAP） |

### 2. 安装必要软件

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Git
sudo apt install git -y

# 安装 Docker (官方脚本)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 验证安装
sudo docker --version
sudo docker compose version

# 将当前用户加入 docker 组（可选，避免每次都用 sudo）
sudo usermod -aG docker $USER
# 重新登录后生效
```

---

## 二、Cloudflare DNS 配置

> ⚠️ **这是最关键的一步！** DNS 配置错误会导致邮件无法收发。

### 域名架构说明

TalentMail 使用两个子域名（由 `config.json` 定义）：

| 子域名 | 用途 | 示例 |
|--------|------|------|
| `webPrefix` | Web 应用访问 | `mail.example.com` |
| `mailServerPrefix` | 邮件服务器 | `maillink.example.com` |

### 必需的 DNS 记录

假设您的域名是 `example.com`，服务器 IP 是 `1.2.3.4`。

| 类型 | 名称 | 内容 | 代理状态 | 说明 |
|------|------|------|----------|------|
| **A** | `mail` | `1.2.3.4` | ✅ **已代理 (橙色)** | Web 应用，通过 Cloudflare CDN |
| **A** | `maillink` | `1.2.3.4` | ❌ **仅 DNS (灰色)** | **必须关闭代理！** |
| **MX** | `@` | `maillink.example.com` | - | 优先级设为 `10` |
| **TXT** | `@` | `v=spf1 mx ~all` | - | SPF 防伪造 |

### Cloudflare 配置步骤

1. **登录 Cloudflare Dashboard** - https://dash.cloudflare.com
2. **添加 Web 应用 A 记录**: `mail` → 您的服务器IP → **Proxied** (橙色)
3. **添加邮件服务器 A 记录**: `maillink` → 您的服务器IP → **DNS only** (灰色)
4. **添加 MX 记录**: `@` → `maillink.example.com` → 优先级 `10`
5. **添加 SPF 记录**: `@` → `v=spf1 mx ~all`

### Cloudflare SSL/TLS 设置

1. 进入 **SSL/TLS** → **Overview** → 选择 **Full (strict)**
2. 进入 **Edge Certificates** → 确保 **Always Use HTTPS** 已开启

---

## 三、获取代码与配置

### 1. 拉取代码

```bash
cd ~
git clone https://github.com/your-repo/talentmail.git
cd talentmail
```

### 2. 修改核心配置文件 (config.json)

```bash
nano config.json
```

**需要修改的字段：**

```json
{
  "currentEnvironment": "production",  // 👈 改为 production
  "environments": {
    "production": {
      "baseDomain": "example.com",      // 👈 改为您的域名
      "webPrefix": "mail",
      "mailServerPrefix": "maillink"
    }
  }
}
```

### 3. 创建环境变量文件 (.env)

```bash
cp .env.example .env
nano .env
```

**必填配置清单：**

| 变量 | 说明 | 生成方法 |
|------|------|----------|
| `SECRET_KEY` | JWT 密钥 | `openssl rand -hex 32` |
| `ENCRYPTION_KEY` | 加密密钥 | `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | 数据库密码 | 自己设置强密码 |
| `DATABASE_URL_DOCKER` | 数据库连接串 | 替换密码 |
| `ADMIN_PASSWORD` | 管理员密码 | 自己设置强密码 |

**完整 .env 示例：**

```env
# 基础配置
CURRENT_ENVIRONMENT=production
TZ=Asia/Shanghai

# 安全配置
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
REFRESH_TOKEN_EXPIRE_DAYS=30
ENCRYPTION_KEY=your-encryption-key-here

# 数据库配置
POSTGRES_USER=talentmail
POSTGRES_PASSWORD=your-db-password
POSTGRES_DB=talentmail
DATABASE_URL_DOCKER=postgresql://talentmail:your-db-password@db:5432/talentmail

# 管理员账户
ADMIN_PASSWORD=your-admin-password

# 邮件服务器
MAILSERVER_CONTAINER_NAME=talentmail-mailserver-1
DEFAULT_MAIL_PASSWORD=your-mail-password
```

---

## 四、一键部署

```bash
chmod +x deploy.sh
./deploy.sh
```

### deploy.sh 执行流程

```
1. 停止现有服务
2. 检查 .env 必需变量
3. 从 config.json 生成 .env.domains（域名配置）
4. 生成 Dovecot SQL 配置（邮件认证）
5. 构建 Docker 镜像
6. 启动服务
7. 等待数据库就绪
8. 运行数据库迁移
```

### 验证部署

```bash
# 检查服务状态
docker compose ps

# 预期输出：所有服务显示 Up 或 healthy
```

### 查看日志

```bash
docker compose logs -f           # 所有服务
docker compose logs -f backend   # 后端
docker compose logs -f frontend  # 前端
docker compose logs -f mailserver # 邮件服务器
```

---

## 五、SSL 证书配置

### Web 应用证书

Caddy 会自动为您的域名申请 Let's Encrypt 证书，无需额外配置。

### 邮件服务器证书（可选）

首次部署时邮件服务器使用自签名证书。如需使用邮件客户端连接：

```bash
# 检查 Caddy 是否已获取证书
docker compose logs caddy | grep -i "certificate"

# 同步证书到邮件服务器
chmod +x scripts/sync_mail_certs.sh
./scripts/sync_mail_certs.sh
```

### 邮件客户端配置

| 协议 | 服务器 | 端口 | 加密方式 |
|------|--------|------|----------|
| IMAP | maillink.example.com | 993 | SSL/TLS |
| SMTP | maillink.example.com | 587 | STARTTLS |

---

## 六、常见问题

### Q: 邮件发送/接收失败？

**检查 DNS 配置：**
```bash
dig maillink.example.com +short    # 应返回服务器IP
dig MX example.com +short          # 应返回 maillink.example.com
```

**检查端口开放：**
```bash
sudo netstat -tlnp | grep -E '25|587|993'
```

### Q: 部署中断了怎么办？

直接重新运行 `./deploy.sh`。Docker 构建是幂等的，会自动跳过已完成步骤。

### Q: 如何更新代码？

```bash
git pull
./deploy.sh
```

### Q: 页面空白或样式错误？

1. 清除浏览器缓存
2. 检查前端构建是否成功：`docker compose logs frontend`
3. 确认 Caddy 代理正常：`docker compose logs caddy`

### Q: 如何查看邮件服务器状态？

```bash
docker compose logs -f mailserver
docker compose exec mailserver postqueue -p
```

---

## 🏗️ 生产环境技术架构

```
Internet
    ↓
Cloudflare (CDN + DDoS 防护)
    ↓
Caddy (Let's Encrypt 自动证书)
    ↓
┌─────────────┬─────────────┐
│   Frontend  │   Backend   │
│  (Nuxt SSR) │  (FastAPI)  │
│  构建产物   │  多进程     │
│  Port 3000  │  Port 8000  │
└─────────────┴─────────────┘
         ↓
    PostgreSQL
    Port 5432
```

**关键文件说明：**

| 文件 | 用途 |
|------|------|
| `docker-compose.yml` | 生产环境 Docker 编排 |
| `frontend/Dockerfile.prod` | 前端生产镜像（多阶段构建） |
| `backend/Dockerfile` | 后端镜像 |
| `config/caddy/Caddyfile.prod` | Caddy 生产配置（Let's Encrypt） |
| `deploy.sh` | 生产环境部署脚本 |
| `config.json` | 项目核心配置 |

### 开发环境 vs 生产环境对比

| 特性 | 开发环境 | 生产环境 |
|------|---------|---------|
| 前端运行方式 | `npm run dev` (热重载) | `node .output/server/index.mjs` |
| 后端运行方式 | `uvicorn --reload` | `uvicorn --workers 4` |
| SSL 证书 | mkcert 本地证书 | Let's Encrypt |
| 代码挂载 | volumes 热重载 | 镜像内构建产物 |
| 服务重启 | 手动 | 自动 (restart: unless-stopped) |
| 健康检查 | 开发调试用 | 生产监控必需 |

---

## 📚 相关文档

- [开发环境部署](./development.md)
- [系统架构设计](../02-architecture/README.md)
- [故障排查指南](../05-operations/troubleshooting.md)

---

最后更新：2026-02-08