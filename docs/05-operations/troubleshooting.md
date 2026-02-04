# 故障排查指南

本文档提供 TalentMail 常见问题的诊断和解决方案。

## 🔍 快速诊断流程

遇到问题时，按以下步骤排查：

1. **查看服务状态** - 确认所有服务正在运行
2. **检查日志** - 查看相关服务的错误日志
3. **验证配置** - 检查环境变量和配置文件
4. **测试连接** - 验证网络和端口连通性
5. **查阅本文档** - 寻找对应的解决方案

## 🚨 常见问题及解决方案

### 1. 服务启动失败

#### 症状
- Docker 容器无法启动
- 服务状态显示 `Exited` 或 `Restarting`

#### 诊断命令
```bash
# 查看服务状态
docker-compose -f docker-compose.dev.yml ps

# 查看具体服务日志
docker-compose -f docker-compose.dev.yml logs [服务名]
```

#### 常见原因及解决方案

**端口被占用**
```bash
# 检查端口占用
sudo netstat -tlnp | grep -E ':(80|443|3000|8000|5432|25|143|587|993)'

# 解决方案
# 1. 停止占用端口的服务
# 2. 或修改 docker-compose.yml 中的端口映射
```

**权限不足**
```bash
# 添加用户到 docker 组
sudo usermod -aG docker $USER
newgrp docker

# 重启 Docker 服务
sudo systemctl restart docker
```

**磁盘空间不足**
```bash
# 检查磁盘空间
df -h

# 清理 Docker 缓存
docker system prune -af
docker volume prune -f
```

### 2. 数据库连接失败

#### 症状
- 登录失败，提示"服务器错误"
- 后端日志显示数据库连接错误
- 数据库服务状态为 `unhealthy`

#### 诊断命令
```bash
# 检查数据库服务状态
docker-compose -f docker-compose.dev.yml ps db

# 查看数据库日志
docker-compose -f docker-compose.dev.yml logs db --tail 50

# 测试数据库连接
docker-compose -f docker-compose.dev.yml exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1"
```

#### 解决方案

**数据库未就绪**
```bash
# 重启数据库服务
docker-compose -f docker-compose.dev.yml restart db

# 等待数据库就绪后重启后端
sleep 10
docker-compose -f docker-compose.dev.yml restart backend
```

**数据库数据损坏**
```bash
# 备份当前数据（如果可能）
docker-compose -f docker-compose.dev.yml exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup.sql

# 清理并重建数据库
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
```

**环境变量配置错误**
```bash
# 检查 .env 文件配置
cat .env | grep -E "(POSTGRES_|DATABASE_URL)"

# 确保 DATABASE_URL_DOCKER 格式正确
# 格式：postgresql://用户名:密码@db:5432/数据库名
```

### 3. 邮件发送失败

#### 症状
- 发送邮件时提示失败
- 邮件卡在发件箱
- SMTP 认证失败

#### 诊断命令
```bash
# 查看邮件服务器日志
docker-compose -f docker-compose.dev.yml logs mailserver --tail 100 | grep -i error

# 测试 SMTP 连接
docker-compose -f docker-compose.dev.yml exec backend python -c "
import smtplib
server = smtplib.SMTP('maillink.talenting.test', 587)
server.starttls()
print('SMTP连接成功')
"
```

#### 解决方案

**SMTP 认证失败**
```bash
# 检查用户是否同步到邮件服务器
docker exec talentmail-mailserver-1 setup email list

# 手动添加邮件用户
docker exec -it talentmail-mailserver-1 setup email add user@domain password
```

**邮件服务器配置问题**
```bash
# 检查邮件服务器配置
cat config/mail/development/mailserver.env

# 重启邮件服务器
docker-compose -f docker-compose.dev.yml restart mailserver
```

### 4. 前端页面无法访问

#### 症状
- 浏览器显示"无法访问此网站"
- 页面加载超时
- 显示 502 Bad Gateway

#### 诊断命令
```bash
# 检查前端服务
docker-compose -f docker-compose.dev.yml logs frontend --tail 20

# 检查 Caddy 代理
docker-compose -f docker-compose.dev.yml logs caddy --tail 20

# 测试前端直连
curl http://localhost:3000
```

#### 解决方案

**前端构建失败**
```bash
# 重新构建前端
docker-compose -f docker-compose.dev.yml up -d --build frontend

# 查看构建日志
docker-compose -f docker-compose.dev.yml logs frontend
```

**Caddy 配置错误**
```bash
# 检查 Caddy 配置
cat config/caddy/Caddyfile

# 验证域名解析
nslookup mail.talenting.test
```

### 5. 登录认证问题

#### 症状
- 无法登录，提示密码错误
- Token 过期频繁
- 2FA 验证失败

#### 诊断命令
```bash
# 检查后端认证日志
docker-compose -f docker-compose.dev.yml logs backend | grep -i auth

# 验证管理员账户
docker-compose -f docker-compose.dev.yml exec backend python -c "
from db.database import SessionLocal
from db.models.user import User
db = SessionLocal()
admin = db.query(User).filter_by(email='admin@talenting.test').first()
print(f'Admin exists: {admin is not None}')
"
```

#### 解决方案

**重置管理员密码**
```bash
# 使用 Python 脚本重置密码
docker-compose -f docker-compose.dev.yml exec backend python -c "
from db.database import SessionLocal
from db.models.user import User
from core.security import get_password_hash
db = SessionLocal()
admin = db.query(User).filter_by(email='admin@talenting.test').first()
if admin:
    admin.hashed_password = get_password_hash('newpassword')
    db.commit()
    print('密码已重置')
"
```

### 6. 性能问题

#### 症状
- 页面加载缓慢
- API 响应超时
- 数据库查询慢

#### 诊断命令
```bash
# 查看资源使用情况
docker stats

# 检查数据库性能
docker-compose -f docker-compose.dev.yml exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;"
```

#### 优化方案

**增加服务资源**
```yaml
# 在 docker-compose.yml 中添加资源限制
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

**优化数据库**
```bash
# 运行 VACUUM 和 ANALYZE
docker-compose -f docker-compose.dev.yml exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "VACUUM ANALYZE;"

# 重建索引
docker-compose -f docker-compose.dev.yml exec db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "REINDEX DATABASE $POSTGRES_DB;"
```

## 📋 日志位置说明

| 服务 | 日志查看命令 | 日志内容 |
|------|--------------|----------|
| Frontend | `docker-compose logs frontend` | Nuxt 构建和运行日志 |
| Backend | `docker-compose logs backend` | API 请求和错误日志 |
| Database | `docker-compose logs db` | 数据库查询和连接日志 |
| Mailserver | `docker-compose logs mailserver` | 邮件收发日志 |
| Caddy | `docker-compose logs caddy` | HTTP 请求和证书日志 |

## 🛠️ 高级诊断工具

### 进入容器调试
```bash
# 进入后端容器
docker-compose -f docker-compose.dev.yml exec backend bash

# 进入数据库容器
docker-compose -f docker-compose.dev.yml exec db bash

# 进入前端容器
docker-compose -f docker-compose.dev.yml exec frontend sh
```

### 网络诊断
```bash
# 检查容器网络
docker network ls
docker network inspect talentmail_default

# 测试容器间连通性
docker-compose -f docker-compose.dev.yml exec backend ping db
```

### 数据库直连
```bash
# 使用 psql 客户端连接
psql -h localhost -p 5432 -U user -d talentmail
```

## 🚑 紧急恢复流程

如果系统完全无法使用：

1. **备份数据**
   ```bash
   # 备份数据库
   docker-compose -f docker-compose.dev.yml exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup_$(date +%Y%m%d).sql

   # 备份上传文件
   tar -czf uploads_backup.tar.gz backend/uploads/
   ```

2. **完全重置**
   ```bash
   # 停止所有服务
   docker-compose -f docker-compose.dev.yml down

   # 清理所有数据（谨慎！）
   docker-compose -f docker-compose.dev.yml down -v

   # 重新部署
   ./dev.sh clean
   ```

3. **恢复数据**
   ```bash
   # 恢复数据库
   docker-compose -f docker-compose.dev.yml exec -T db psql -U $POSTGRES_USER $POSTGRES_DB < backup_20250201.sql

   # 恢复文件
   tar -xzf uploads_backup.tar.gz
   ```

## 📞 获取帮助

如果以上方案都无法解决问题：

1. 收集诊断信息
   ```bash
   # 生成诊断报告
   ./dev.sh logs > diagnostic_$(date +%Y%m%d_%H%M%S).log
   docker-compose -f docker-compose.dev.yml ps >> diagnostic_*.log
   ```

2. 查看项目 Issues
3. 提交新的 Issue，附上诊断报告

---

最后更新：2025-02-01