# 调试技巧

## 日志查看

### 查看各服务日志

```bash
# 后端日志（最常用）
docker compose logs -f backend

# 前端日志
docker compose logs -f frontend

# 邮件服务器日志
docker compose logs -f mailserver

# 数据库日志
docker compose logs -f db

# 反向代理日志
docker compose logs -f caddy

# 所有服务
docker compose logs -f

# 最近 100 行
docker compose logs --tail=100 backend
```

### 后端日志级别

后端使用 Python `logging` 模块，日志格式：

```
2026-04-27 10:00:00 | INFO | [main] TalentMail v2.0.0 启动中...
2026-04-27 10:00:01 | INFO | [imap_sync] IMAP 同步完成: 5 新邮件
2026-04-27 10:00:02 | ERROR | [mail] 发送失败: Connection refused
```

关键日志标签：
- `[main]` — 应用启动/关闭
- `[imap_sync]` — IMAP 同步任务
- `[lmtp]` — LMTP 邮件接收
- `[mail]` — 邮件发送
- `[auth]` — 认证相关
- `[ws]` — WebSocket 连接

## 常见错误排查

### 1. 邮件发送失败

**现象**: `POST /api/emails/send` 返回 500

**排查步骤**:
```bash
# 1. 检查 Postfix 是否运行
docker compose exec mailserver postfix status

# 2. 查看 Postfix 队列
docker compose exec mailserver mailq

# 3. 查看邮件日志
docker compose exec mailserver tail -100 /var/log/mail/mail.log

# 4. 测试 SMTP 连通性
docker compose exec backend python -c "
import smtplib
s = smtplib.SMTP('mailserver', 25)
s.ehlo()
print('SMTP OK')
s.quit()
"
```

### 2. IMAP 同步不工作

**现象**: 邮件在 Dovecot 中但不显示

```bash
# 检查 IMAP 连通性
docker compose exec backend python -c "
import imaplib
m = imaplib.IMAP4('mailserver', 143)
m.login('user@example.com', 'password')
m.select('INBOX')
typ, data = m.search(None, 'ALL')
print(f'Mailbox has {len(data[0].split())} messages')
m.logout()
"

# 检查后台任务是否在运行
docker compose logs backend | grep "imap_sync"
```

### 3. WebSocket 断连

**现象**: 实时通知不工作

```bash
# 测试 WebSocket 连接
# 先获取 token
TOKEN=$(curl -s -X POST https://mail.example.com/api/auth/login \
  -d "username=admin@example.com&password=xxx" | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 测试 WS 连接
curl -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     "https://mail.example.com/api/ws?token=$TOKEN" -v
```

### 4. 数据库连接失败

```bash
# 检查 PostgreSQL 状态
docker compose exec db pg_isready

# 检查连接数
docker compose exec db psql -U talentmail -c "SELECT count(*) FROM pg_stat_activity;"

# 检查数据库大小
docker compose exec db psql -U talentmail -c "SELECT pg_size_pretty(pg_database_size('talentmail'));"
```

### 5. 前端构建失败

```bash
# 查看构建日志
docker compose logs frontend

# 进入容器手动构建
docker compose exec frontend sh
npx nuxi build

# 检查 node_modules
docker compose exec frontend ls -la node_modules/.package-lock.json
```

## 数据库排查

### 常用查询

```sql
-- 连接到数据库
docker compose exec db psql -U talentmail

-- 查看用户列表
SELECT id, email, is_admin, is_active FROM users;

-- 查看最近邮件
SELECT id, subject, from_address, to_addresses, created_at
FROM emails ORDER BY created_at DESC LIMIT 10;

-- 查看临时邮箱状态
SELECT address, status, expires_at, created_at
FROM temp_mailboxes ORDER BY created_at DESC LIMIT 10;

-- 查看工作流执行日志
SELECT w.name, wl.status, wl.started_at, wl.error_message
FROM workflow_logs wl
JOIN workflows w ON w.id = wl.workflow_id
ORDER BY wl.started_at DESC LIMIT 20;

-- 查看迁移状态
SELECT * FROM alembic_version;
```

### 重置数据

```bash
# 重新初始化种子数据（不删除用户数据）
docker compose exec backend python -m initial.initial_data

# 完全重置数据库（危险！）
docker compose down -v  # 删除数据卷
docker compose up -d    # 重新创建
docker compose exec backend alembic upgrade head
docker compose exec backend python -m initial.initial_data
```

## 性能诊断

```bash
# 查看容器资源使用
docker stats

# 查看后端内存
docker compose exec backend python -c "
import psutil
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'CPU: {psutil.cpu_percent(1)}%')
"

# PostgreSQL 慢查询
docker compose exec db psql -U talentmail -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC
LIMIT 5;
"
```

## API 调试

### Swagger UI

开发环境可访问自动生成的 API 文档：
- **Swagger**: `http://127.0.0.1:18000/docs`
- **ReDoc**: `http://127.0.0.1:18000/redoc`

### cURL 调试

```bash
# 登录获取 token
TOKEN=$(curl -s -X POST http://127.0.0.1:18000/api/auth/login \
  -d "username=admin@example.com&password=xxx" | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 使用 token 请求
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:18000/api/users/me | python3 -m json.tool

# 健康检查
curl http://127.0.0.1:18000/api/health | python3 -m json.tool
```

## deploy.sh 诊断

```bash
# 仅诊断，不做任何修改
bash deploy.sh --doctor

# 输出详细日志
bash deploy.sh --migrate 2>&1 | tee deploy.log
```
