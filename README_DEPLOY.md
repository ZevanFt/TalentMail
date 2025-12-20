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

## 二、获取代码

### 1. 拉取代码
选择一个目录（例如 `/opt` 或用户主目录），克隆项目代码：

```bash
cd ~
git clone https://github.com/your-repo/talentmail.git
cd talentmail
```
*(注：请将 `https://github.com/your-repo/talentmail.git` 替换为您的实际仓库地址)*

## 三、配置环境

### 1. 创建生产环境配置文件
复制示例配置文件：

```bash
cp .env .env.prod
```

### 2. 修改配置
使用编辑器（如 `nano` 或 `vim`）修改 `.env.prod` 文件：

```bash
nano .env.prod
```

**必须修改的关键项：**

*   `DOMAIN`: 您的主域名 (例如 `talenting.vip`)
*   `MAIL_SERVER`: 您的邮件服务器域名 (例如 `mail.talenting.vip`)
*   `SECRET_KEY`: 生成一个新的强随机字符串 (可以使用 `openssl rand -hex 32` 生成)
*   `ADMIN_PASSWORD`: 设置初始管理员密码
*   `POSTGRES_PASSWORD`: 设置数据库密码

**保存并退出**: `Ctrl+O` -> `Enter` -> `Ctrl+X`

### 3. 重命名配置文件
为了让 Docker Compose 自动识别，将 `.env.prod` 重命名为 `.env`：

```bash
mv .env.prod .env
```

## 四、一键部署

我们提供了一个部署脚本来自动化构建和启动过程。

### 1. 运行部署脚本
```bash
chmod +x deploy.sh
./deploy.sh
```

### 2. 脚本执行过程
脚本会自动执行以下操作：
1.  停止旧的容器（如果有）。
2.  构建后端和前端的 Docker 镜像。
3.  启动所有服务（数据库、后端、前端、邮件服务器、Caddy 网关）。
4.  等待数据库启动。
5.  自动运行数据库迁移（更新表结构）。
6.  **自动初始化数据**：后端启动时会自动创建数据库表、默认管理员账户、默认套餐等。

## 五、验证部署

### 1. 检查服务状态
```bash
sudo docker compose ps
```
所有服务状态应为 `Up`。

### 2. 访问网站
在浏览器访问您的域名 (例如 `https://talenting.vip`)。
*   使用默认管理员账号登录：
    *   邮箱: `admin@您的域名` (例如 `admin@talenting.vip`)
    *   密码: 您在 `.env` 中设置的 `ADMIN_PASSWORD`

### 3. 检查邮件服务
确保您的 DNS 解析已正确配置：
*   `A` 记录: `mail.talenting.vip` -> 服务器 IP
*   `MX` 记录: `@` -> `mail.talenting.vip` (优先级 10)

## 六、常见问题与维护

### 数据库初始化需要手动操作吗？
**不需要**。后端服务在启动时会检查数据库，如果表不存在会自动创建，并初始化默认数据（管理员、套餐、模板等）。`deploy.sh` 脚本还会额外运行 `alembic upgrade head` 以确保数据库结构是最新的。

### 如何查看日志？
*   查看所有日志: `sudo docker compose logs -f`
*   查看后端日志: `sudo docker compose logs -f backend`
*   查看邮件服务日志: `sudo docker compose logs -f mailserver`

### 如何更新代码？
```bash
git pull
./deploy.sh