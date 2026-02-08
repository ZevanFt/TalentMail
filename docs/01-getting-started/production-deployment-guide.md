# 生产环境部署指南

本指南详细说明如何在 Linux 服务器上部署 TalentMail，使用 Cloudflare 作为 DNS 服务提供商。

## 目录

1. [服务器准备](#一服务器准备)
2. [Cloudflare DNS 配置](#二cloudflare-dns-配置)
3. [获取代码与配置](#三获取代码与配置)
4. [一键部署](#四一键部署)
5. [SSL 证书配置](#五ssl-证书配置)
6. [常见问题](#六常见问题)
7. [Nuxt.js 部署说明](#七nuxtjs-部署说明)

---

## 一、服务器准备

### 1. 系统要求

- **操作系统**: 推荐 Ubuntu 20.04 LTS 或 22.04 LTS
- **配置**: 至少 2核 CPU, 4GB 内存 (邮件服务和数据库较占资源)
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

| 类型 | 名称 | 内容 | 代理状态 | TTL | 说明 |
|------|------|------|----------|-----|------|
| **A** | `mail` | `1.2.3.4` | ✅ **已代理 (橙色)** | Auto | Web 应用，通过 Cloudflare CDN |
| **A** | `maillink` | `1.2.3.4` | ❌ **仅 DNS (灰色)** | Auto | **必须关闭代理！** |
| **MX** | `@` | `maillink.example.com` | - | Auto | 优先级设为 `10` |
| **TXT** | `@` | `v=spf1 mx ~all` | - | Auto | SPF 防伪造 |

### Cloudflare 配置步骤

1. **登录 Cloudflare Dashboard**
   - 访问 https://dash.cloudflare.com
   - 选择您的域名

2. **添加 Web 应用 A 记录**
   - 点击 "DNS" -> "Records" -> "Add record"
   - Type: `A`
   - Name: `mail`
   - IPv4 address: `您的服务器IP`
   - Proxy status: **Proxied** (橙色云朵) ✅
   - 点击 "Save"

3. **添加邮件服务器 A 记录**
   - 点击 "Add record"
   - Type: `A`
   - Name: `maillink`
   - IPv4 address: `您的服务器IP`
   - Proxy status: **DNS only** (灰色云朵) ❌
   - 点击 "Save"

4. **添加 MX 记录**
   - 点击 "Add record"
   - Type: `MX`
   - Name: `@`
   - Mail server: `maillink.example.com`
   - Priority: `10`
   - 点击 "Save"

5. **添加 SPF 记录**
   - 点击 "Add record"
   - Type: `TXT`
   - Name: `@`
   - Content: `v=spf1 mx ~all`
   - 点击 "Save"

### 可选：添加 DKIM 和 DMARC 记录

部署完成后，可以添加以下记录增强邮件安全性：

```
# DMARC 记录
Type: TXT
Name: _dmarc
Content: v=DMARC1; p=quarantine; rua=mailto:postmaster@example.com

# DKIM 记录（部署后从邮件服务器获取）
Type: TXT
Name: mail._domainkey
Content: [从邮件服务器获取的 DKIM 公钥]
```

### Cloudflare SSL/TLS 设置

1. 进入 **SSL/TLS** -> **Overview**
2. 选择 **Full (strict)** 模式
3. 进入 **Edge Certificates**
4. 确保 **Always Use HTTPS** 已开启

---

## 三、获取代码与配置

### 1. 拉取代码

```bash
cd ~
git clone https://github.com/your-repo/talentmail.git
cd talentmail
```

### 2. 创建配置文件

```bash
cp .env.example .env
```

### 3. 编辑配置文件

```bash
nano .env
```

**必填配置项：**

| 变量 | 说明 | 示例 |
|------|------|------|
| `CURRENT_ENVIRONMENT` | 环境类型 | `production` |
| `SECRET_KEY` | JWT 密钥（随机字符串） | `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | 数据库密码 | 设置强密码 |
| `ADMIN_PASSWORD` | 管理员登录密码 | 设置强密码 |

**配置示例：**

```env
CURRENT_ENVIRONMENT=production
SECRET_KEY=your-super-secret-key-here-make-it-long-and-random
POSTGRES_PASSWORD=your-database-password
ADMIN_PASSWORD=your-admin-password
```

保存退出: `Ctrl+O` 回车保存，`Ctrl+X` 退出。

---

## 四、一键部署

```bash
chmod +x deploy.sh
./deploy.sh
```

脚本会自动：
- 构建 Docker 镜像
- 启动所有服务
- 初始化数据库
- 创建管理员账户

### 验证部署

```bash
# 检查服务状态
docker compose ps

# 查看日志
docker compose logs -f
```

所有服务应该显示 `Up` 或 `healthy` 状态。

---

## 五、SSL 证书配置

### 自动证书（推荐）

Caddy 会自动为您的域名申请 Let's Encrypt 证书，无需额外配置。

### 邮件服务器证书

首次部署时，邮件服务器使用自签名证书。如需使用邮件客户端连接，请同步证书：

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

**A: 检查以下几点：**

1. **DNS 记录是否正确**：特别是 `maillink` 必须是灰色云朵（DNS only）
   ```bash
   # 检查 DNS 解析
   dig maillink.example.com +short
   dig MX example.com +short
   ```

2. **端口是否开放**：25, 587, 993 端口必须开放
   ```bash
   # 检查端口监听
   sudo netstat -tlnp | grep -E '25|587|993'
   ```

3. **邮件服务器日志**：
   ```bash
   docker compose logs -f mailserver
   ```

### Q: 部署中断了怎么办？

**A: 直接重新运行 `./deploy.sh` 即可。** Docker 构建是幂等的，会自动跳过已完成步骤。

### Q: 如何更新代码？

```bash
git pull
./deploy.sh
```

### Q: 邮件客户端提示证书不受信任？

**A: 运行证书同步脚本：**

```bash
./scripts/sync_mail_certs.sh
```

### Q: 如何查看邮件服务器状态？

```bash
# 查看邮件队列
docker compose exec mailserver postqueue -p

# 查看邮件日志
docker compose logs -f mailserver
```

---

## 七、Nuxt.js 部署说明

### 开发环境 vs 生产环境

#### 开发环境（当前配置）
- **运行方式**：`npm run dev`
- **特点**：
  - 实时编译，代码修改立即生效
  - 启用 HMR (Hot Module Replacement)
  - 包含开发工具和调试信息
  - 性能较慢，文件体积大

#### 生产环境
- **运行方式**：先 `npm run build`，再运行构建产物
- **特点**：
  - 预编译，优化后的静态文件
  - 无 HMR，不需要 WebSocket
  - 代码压缩、Tree-shaking
  - 性能优化，文件体积小

### Nuxt 3 生产部署流程

#### 1. 构建应用
```bash
cd frontend
npm run build
```

构建后会生成 `.output` 目录，包含：
- `.output/server/` - Node.js 服务器代码
- `.output/public/` - 静态资源文件

#### 2. 运行生产服务器

Nuxt 3 构建后是一个 Node.js 应用，运行方式：

```bash
# 方式 1：使用 node 直接运行
node .output/server/index.mjs

# 方式 2：使用 npm 脚本
npm run preview
```

默认监听 3000 端口。

### Docker 生产部署配置

#### 生产环境 Dockerfile

创建 `frontend/Dockerfile.prod`：

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# 复制 package 文件
COPY package*.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产镜像
FROM node:20-alpine

WORKDIR /app

# 只复制构建产物
COPY --from=builder /app/.output ./.output
COPY --from=builder /app/package*.json ./

# 安装生产依赖（可选，Nuxt 构建产物已包含所有必需代码）
# RUN npm ci --production

# 暴露端口
EXPOSE 3000

# 设置环境变量
ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3000

# 启动应用
CMD ["node", ".output/server/index.mjs"]
```

#### 生产环境 docker-compose.yml

```yaml
services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - NUXT_PUBLIC_BASE_DOMAIN=yourdomain.com
    restart: always
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
```

### 生产环境 Caddy 配置

生产环境不需要 WebSocket 代理（无 HMR），配置更简单：

```caddyfile
yourdomain.com {
    encode gzip zstd

    # API 请求代理到后端
    reverse_proxy /api/* backend:8000

    # 其他请求代理到前端
    reverse_proxy /* frontend:3000
}
```

### 部署步骤总结

#### 开发环境（当前）
1. `docker compose -f docker-compose.dev.yml up -d`
2. 前端运行 `npm run dev`
3. 支持热更新，需要 WebSocket

#### 生产环境
1. 构建前端：`npm run build`
2. 使用生产 Dockerfile 构建镜像
3. `docker compose -f docker-compose.yml up -d`
4. 前端运行 `node .output/server/index.mjs`
5. 无热更新，无 WebSocket，性能更好

### 性能对比

| 特性 | 开发环境 | 生产环境 |
|------|---------|---------|
| 启动时间 | 30-60秒 | 5-10秒 |
| 首次加载 | 2-5秒 | 0.5-1秒 |
| 文件大小 | 10-50MB | 1-5MB |
| 内存占用 | 200-500MB | 50-150MB |
| HMR | ✅ | ❌ |
| 代码压缩 | ❌ | ✅ |
| Tree-shaking | ❌ | ✅ |

### 常见问题

#### Q: 为什么开发环境需要 WebSocket？
A: 用于 HMR (Hot Module Replacement)，实现代码修改后自动刷新页面。

#### Q: 生产环境需要 WebSocket 吗？
A: 不需要。生产环境是预编译的静态文件，不需要热更新。

#### Q: 如何切换到生产模式？
A: 
1. 修改 `docker-compose.yml` 使用 `Dockerfile.prod`
2. 设置环境变量 `NODE_ENV=production`
3. 重新构建并启动容器

#### Q: 生产环境如何更新代码？
A: 
1. 修改代码
2. 重新构建：`docker compose build frontend`
3. 重启容器：`docker compose up -d frontend`

### 推荐的生产部署架构

```
Internet
    ↓
Caddy (HTTPS, 证书管理)
    ↓
┌─────────────┬─────────────┐
│   Frontend  │   Backend   │
│  (Nuxt SSR) │  (FastAPI)  │
│   Port 3000 │  Port 8000  │
└─────────────┴─────────────┘
         ↓
    PostgreSQL
    Port 5432
```

### 下一步

1. 创建 `frontend/Dockerfile.prod`
2. 创建 `docker-compose.yml`（生产配置）
3. 配置域名和 SSL 证书
4. 设置 CI/CD 自动部署

## 当前问题解决方案

现在您的开发环境应该可以正常工作了：
- ✅ HTTPS 已配置（自签名证书）
- ✅ WebSocket 代理已配置（支持 HMR）
- ✅ 所有服务健康检查正常
- ✅ Caddy 反向代理正常工作

请在浏览器中访问 **https://mail.talenting.test/login**，接受证书警告后应该能看到完整的登录页面。