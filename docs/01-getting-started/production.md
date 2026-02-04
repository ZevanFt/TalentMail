# TalentMail 生产环境部署指南

本指南将详细说明如何在全新的 Linux 服务器上从零开始部署 TalentMail 系统。

## 一、服务器准备

### 1. 系统要求
*   **操作系统**: 推荐 Ubuntu 20.04 LTS 或 22.04 LTS
*   **配置**: 至少 2核 CPU, 4GB 内存 (邮件服务和数据库较占资源)
*   **端口开放**: 确保云服务商的安全组或防火墙开放以下端口：
    *   `80` (HTTP)
    *   `443` (HTTPS)
    *   `25` (SMTP)
    *   `143` (IMAP)
    *   `587` (SMTP Submission)
    *   `993` (IMAPS)

### 2. 安装必要软件
登录服务器，更新系统并安装 Docker 和 Git：

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Git
sudo apt install git -y

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 验证 Docker 安装
sudo docker --version
sudo docker compose version
```

## 二、Cloudflare DNS 配置 (关键！)

在部署之前，请登录 Cloudflare 后台添加以下 DNS 记录。
假设您的域名是 `example.com`，服务器 IP 是 `1.2.3.4`。

**域名架构说明** (由 config.json 定义):
- `mail.example.com` - Web 应用 (webPrefix)
- `maillink.example.com` - 邮件服务器 (mailServerPrefix)

| 类型 | 名称 | 内容 | 代理状态 (Proxy Status) | 说明 |
|---|---|---|---|---|
| **A** | `mail` | `1.2.3.4` | ✅ **已代理 (橙色)** | Web 应用访问 |
| **A** | `maillink` | `1.2.3.4` | ❌ **仅 DNS (灰色)** | **必须关闭代理！** 邮件服务器 |
| **MX** | `@` | `maillink.example.com` | - | 优先级设为 10 |
| **TXT** | `@` | `v=spf1 mx ~all` | - | SPF 记录 |

> **特别提醒**：`maillink` 子域名必须是 **灰色云朵 (DNS Only)**，否则邮件发不出去也收不到！

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

**必填项说明：**

*   `CURRENT_ENVIRONMENT`: 设为 `production`
*   `DOMAIN`: 填入您的主域名 (如 `talenting.vip`)
*   `MAIL_SERVER`: 填入邮件服务器域名 (如 `mail.talenting.vip`)
*   `SECRET_KEY`: 随便乱打一串字符 (越长越乱越好)
*   `POSTGRES_PASSWORD`: 设置一个数据库密码
*   `ADMIN_EMAIL`: **必须是完整邮箱** (如 `admin@talenting.vip`)
*   `ADMIN_PASSWORD`: 设置管理员登录密码

**保存退出**: 按 `Ctrl+O` 回车保存，按 `Ctrl+X` 退出。

## 四、一键部署

```bash
chmod +x deploy.sh
./deploy.sh
```

脚本会自动构建镜像、启动服务并初始化数据库。

## 五、配置邮件客户端 SSL 证书 (可选)

首次部署时，邮件服务器使用自签名证书。如果您需要使用邮件客户端 (如 Outlook、Thunderbird) 连接，建议配置 Let's Encrypt 证书：

### 1. 等待 Caddy 获取证书
部署完成后，Caddy 会自动为您的域名申请 Let's Encrypt 证书。等待几分钟后，运行：

```bash
# 检查 Caddy 是否已获取证书
docker compose logs caddy | grep -i "certificate"
```

### 2. 同步证书到邮件服务器
```bash
chmod +x scripts/sync_mail_certs.sh
./scripts/sync_mail_certs.sh
```

脚本会自动：
- 从 Caddy 复制 Let's Encrypt 证书
- 更新邮件服务器配置
- 重启邮件服务器

### 3. 邮件客户端配置
配置完成后，使用以下设置连接邮件客户端：

| 协议 | 服务器 | 端口 | 加密方式 |
|---|---|---|---|
| IMAP | maillink.example.com | 993 | SSL/TLS |
| SMTP | maillink.example.com | 587 | STARTTLS |

## 六、常见问题 (FAQ)

### Q: 部署过程中断了怎么办？(例如按了 Ctrl+C 或网络断开)
**A: 不需要担心，直接重新运行 `./deploy.sh` 即可。**
Docker 的构建和启动过程是“幂等”的，重新运行会自动跳过已完成的步骤，并继续完成剩下的工作。

### Q: 我更新了代码 (git pull)，重新运行脚本会生效吗？
**A: 会的，一定会生效！**
`deploy.sh` 脚本中包含 `docker compose build` 命令。Docker 非常智能，它会检测文件是否发生了变化：
*   **如果代码变了**：Docker 会自动重新构建镜像，包含最新的代码。
*   **如果代码没变**：Docker 会使用缓存，跳过构建以节省时间。
所以，每次更新代码后，直接运行 `./deploy.sh` 是最安全、最正确的方法。

### Q: 数据库初始化需要手动操作吗？
**A: 不需要。**
后端服务启动时会自动检测并创建所有必要的数据库表、默认管理员账号、默认套餐等。

### Q: 如何查看日志？
*   查看所有日志: `sudo docker compose logs -f`
*   查看后端日志: `sudo docker compose logs -f backend`
*   查看邮件服务日志: `sudo docker compose logs -f mailserver`

### Q: 如何更新代码？
```bash
git pull
./deploy.sh
```

### Q: 邮件客户端提示证书不受信任？
**A: 这是因为邮件服务器使用的是自签名证书。**
请按照上面"配置邮件客户端 SSL 证书"章节的步骤，同步 Let's Encrypt 证书到邮件服务器。

### Q: 如何查看邮件服务器状态？
```bash
# 查看邮件服务器日志
docker compose logs -f mailserver

# 检查邮件队列
docker compose exec mailserver postqueue -p