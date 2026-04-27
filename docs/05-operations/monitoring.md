# 监控配置指南

## 健康检查端点

TalentMail 提供三个健康检查端点：

| 端点 | 用途 | 检查内容 |
|------|------|---------|
| `GET /api/health` | 综合健康检查 | API 服务 + 数据库连接 + 8 个后台任务存活状态 |
| `GET /api/readiness` | 就绪探针 | 服务是否可接受请求 |
| `GET /api/liveness` | 存活探针 | 服务是否在运行 |

### 响应示例

```json
// GET /api/health — 所有任务正常
{
  "status": "healthy",
  "service": "talentmail-backend",
  "database": "connected",
  "background_tasks": {
    "mail_sync": { "running": true, "last_heartbeat_ago_sec": 12.3 },
    "external_sync": { "running": true, "last_heartbeat_ago_sec": 45.1 },
    "session_cleanup": { "running": true, "last_heartbeat_ago_sec": 120.0 },
    "temp_mailbox_cleanup": { "running": true, "last_heartbeat_ago_sec": 90.5 },
    "scheduled_sender": { "running": true, "last_heartbeat_ago_sec": 8.2 },
    "orphan_attachment_cleanup": { "running": true, "last_heartbeat_ago_sec": 300.0 },
    "snooze_check": { "running": true, "last_heartbeat_ago_sec": 15.7 },
    "audit_log_cleanup": { "running": true, "last_heartbeat_ago_sec": 600.0 }
  }
}

// GET /api/health — 某个任务挂了（自动重启中）
{
  "status": "degraded",
  "service": "talentmail-backend",
  "database": "connected",
  "background_tasks": { ... },
  "dead_tasks": ["mail_sync"]
}
```

### 外部监控配置

```bash
# 简单的 cron 健康检查脚本
*/5 * * * * curl -sf https://mail.example.com/api/health > /dev/null || echo "TalentMail DOWN" | mail -s "Alert" admin@example.com
```

## Docker 内置健康检查

docker-compose.yml 已为各服务配置健康检查：

### Backend

```yaml
healthcheck:
  test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8000/api/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

> **Note**: v2.1.0 起使用 `wget` 替代 Python 解释器，避免每次健康检查产生 ~30MB 内存尖峰。

### Frontend

```yaml
healthcheck:
  test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30s
```

### PostgreSQL

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U talentmail"]
  interval: 10s
  timeout: 5s
  retries: 5
```

## 容器资源监控

### docker stats

```bash
# 实时资源使用
docker stats --no-stream

# 预期输出（v2.1.0 资源限制：总计 2.4GB）
CONTAINER          CPU %   MEM USAGE / LIMIT     NET I/O        BLOCK I/O
backend            2.5%    180MiB / 512MiB       10MB / 5MB     50MB / 20MB
frontend           0.3%    80MiB / 256MiB        5MB / 30MB     10MB / 5MB
db                 1.0%    350MiB / 768MiB       20MB / 15MB    100MB / 80MB
mailserver         0.5%    300MiB / 768MiB       2MB / 1MB      5MB / 2MB
caddy              0.1%    20MiB / 128MiB        50MB / 50MB    1MB / 1MB
```

### 磁盘使用

```bash
# Docker 磁盘使用概览
docker system df

# 详细
docker system df -v

# 上传目录大小
du -sh /root/work/TalentMail/backend/uploads/

# PostgreSQL 数据大小
docker compose exec db psql -U talentmail -c "
SELECT pg_size_pretty(pg_database_size('talentmail')) as db_size;"
```

## 日志管理

### 日志轮转

docker-compose.yml 已配置日志大小限制：

```yaml
logging:
  driver: json-file
  options:
    max-size: "10m"   # 单文件最大 10MB
    max-file: "3"     # 最多保留 3 个文件
```

### 日志查看

```bash
# 实时查看后端日志
docker compose logs -f backend

# 查看最近的错误
docker compose logs backend 2>&1 | grep -i error | tail -20

# 按时间筛选（Docker 原生）
docker compose logs --since 1h backend

# 导出日志用于分析
docker compose logs backend > /tmp/backend.log 2>&1
```

## 后台任务监控

TalentMail 有 8 个后台定时任务，由**任务注册表**统一管理，崩溃后 5 秒自动重启。

### 通过 API 监控（推荐）

```bash
# 查看所有后台任务状态
curl -s https://mail.example.com/api/health | python3 -m json.tool

# 检查是否有挂掉的任务
curl -s https://mail.example.com/api/health | python3 -c "
import json, sys
data = json.load(sys.stdin)
dead = data.get('dead_tasks', [])
print(f'Status: {data[\"status\"]}')
if dead:
    print(f'DEAD TASKS: {dead}')
else:
    print('All tasks running')
"
```

### 通过日志监控

```bash
# 查看后台任务运行状态
docker compose logs backend | grep -E "(TaskMonitor|IMAP 同步|定时发送|贪睡|临时邮箱|会话清理|附件清理|外部账户|审计日志)"

# 检查任务崩溃和重启事件
docker compose logs --since 1h backend | grep "TaskMonitor"
```

### 预期日志模式

| 任务名 | 间隔 | 正常日志 | 崩溃日志 |
|--------|------|---------|---------|
| `mail_sync` | 30s | `IMAP 同步完成: N 新邮件` | `[TaskMonitor] 后台任务 'mail_sync' 崩溃: ...` |
| `external_sync` | 5min | `外部账户同步完成` | 同上格式 |
| `scheduled_sender` | 60s | `定时发送检查完成` | |
| `snooze_check` | 60s | `贪睡检查完成` | |
| `temp_mailbox_cleanup` | 10min | `临时邮箱清理完成` | |
| `session_cleanup` | 24h | `过期会话清理完成` | |
| `orphan_attachment_cleanup` | 1h | `孤立附件清理完成` | |
| `audit_log_cleanup` | 24h | `审计日志清理完成` | |

## 邮件服务监控

```bash
# 查看 Postfix 队列
docker compose exec mailserver mailq

# 查看 Postfix 状态
docker compose exec mailserver postfix status

# 查看 Dovecot 连接数
docker compose exec mailserver doveadm who

# 查看 Fail2Ban 状态
docker compose exec mailserver fail2ban-client status
```

## 告警建议

| 指标 | 阈值 | 告警级别 |
|------|------|---------|
| `/api/health` 非 200 或 `status: "degraded"` | 连续 3 次 | Critical |
| Backend CPU | > 80% 持续 5min | Warning |
| Backend Memory | > 400MiB (of 512MiB limit) | Warning |
| DB 连接数 | > 24 (of 30 max) | Warning |
| 磁盘使用 | > 85% | Warning |
| Postfix 队列 | > 100 封 | Warning |
| 邮件发送失败率 | > 5% | Critical |

## 备份监控

```bash
# 检查最近的备份
ls -la /backup/talentmail/

# 验证备份完整性
pg_restore --list /backup/talentmail/latest.dump | head -5
```

详见 [部署指南](./deployment.md) 了解完整的备份配置。
