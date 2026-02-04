# 开发环境部署指南

本文档详细介绍如何在本地搭建 TalentMail 开发环境。

## 📋 前置要求

- **操作系统**: Linux, macOS 或 Windows (WSL2)
- **Docker**: 20.10+ 版本
- **Docker Compose**: 2.0+ 版本
- **Git**: 用于克隆代码
- **至少 4GB 可用内存**

## 🚀 快速部署（推荐）

### 1. 克隆项目

```bash
git clone <repository-url>
cd talentmail
```

### 2. 使用开发脚本一键部署

```bash
# 给脚本执行权限
chmod +x dev.sh

# 启动开发环境
./dev.sh
```

就是这么简单！`dev.sh` 脚本会自动完成所有配置和部署工作。

## 🛠️ 手动部署步骤

如果你想了解详细的部署过程，可以按照以下步骤手动部署：

### 1. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
nano .env
```

主要配置项说明：

| 配置项 | 说明 | 示例值 |
|--------|------|--------|
| `POSTGRES_USER` | 数据库用户名 | `user` |
| `POSTGRES_PASSWORD` | 数据库密码 | `password` |
| `POSTGRES_DB` | 数据库名称 | `talentmail` |
| `SECRET_KEY` | JWT 密钥 | 使用 `openssl rand -hex 32` 生成 |
| `ADMIN_PASSWORD` | 管理员密码 | `adminpassword` |

### 2. 配置本地域名

编辑 hosts 文件：

```bash
# Linux/macOS
sudo nano /etc/hosts

# Windows (管理员权限)
notepad C:\Windows\System32\drivers\etc\hosts
```

添加以下内容：

```
127.0.0.1 mail.talenting.test maillink.talenting.test
```

### 3. 启动服务

```bash
# 构建并启动所有服务
docker-compose -f docker-compose.dev.yml up --build -d

# 查看服务状态
docker-compose -f docker-compose.dev.yml ps
```

### 4. 初始化数据库

等待数据库启动完成后（约 10-20 秒），运行数据库迁移：

```bash
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head
```

## 📍 访问地址

部署成功后，可以通过以下地址访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| **Web 应用** | https://mail.talenting.test | 主应用入口（HTTPS） |
| **前端直连** | http://localhost:3000 | Nuxt 开发服务器 |
| **后端 API** | http://localhost:8000 | FastAPI 服务 |
| **API 文档** | http://localhost:8000/docs | Swagger UI |
| **数据库** | localhost:5432 | PostgreSQL |

**默认管理员账号**：
- 邮箱：`admin@talenting.test`
- 密码：在 `.env` 文件中的 `ADMIN_PASSWORD`

## 🔧 开发脚本命令

`dev.sh` 脚本提供了多个便捷命令：

```bash
# 启动开发环境
./dev.sh

# 查看服务日志
./dev.sh logs

# 停止所有服务
./dev.sh stop

# 重启服务
./dev.sh restart

# 清理并重建（保留数据）
./dev.sh clean
```

## 🐛 常见问题

### 1. 端口被占用

如果提示端口被占用，检查占用情况：

```bash
# 检查端口占用
sudo netstat -tlnp | grep -E ':(80|443|3000|8000|5432)'

# 停止占用的服务或修改 docker-compose.dev.yml 中的端口映射
```

### 2. Docker 权限问题

如果遇到权限错误：

```bash
# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录或执行
newgrp docker
```

### 3. 数据库连接失败

```bash
# 查看数据库日志
docker-compose -f docker-compose.dev.yml logs db

# 确保数据库服务健康
docker-compose -f docker-compose.dev.yml ps
```

### 4. 证书警告

开发环境使用自签名证书，浏览器会显示安全警告。选择"继续访问"即可。

## 📝 开发提示

1. **热重载**：前后端代码修改后会自动重载，无需重启服务
2. **查看日志**：使用 `./dev.sh logs` 实时查看所有服务日志
3. **数据持久化**：数据库数据保存在 Docker 卷中，停止服务不会丢失
4. **清理数据**：使用 `docker-compose -f docker-compose.dev.yml down -v` 清空所有数据

## 🔄 更新代码

```bash
# 拉取最新代码
git pull

# 重新构建并启动
./dev.sh clean
```

## 📚 相关文档

- [生产环境部署](./production.md)
- [系统架构设计](../02-architecture/system-design.md)
- [故障排查指南](../05-operations/troubleshooting.md)

---

最后更新：2025-02-01