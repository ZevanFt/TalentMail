# 监控配置指南

## 健康检查端点

TalentMail 提供三个健康检查端点：

| 端点 | 用途 | 检查内容 |
|------|------|---------|
| `GET /api/health` | 综合健康检查 | API 服务 + 数据库连接 |
| `GET /api/readiness` | 就绪探针 | 服务是否可接受请求 |
| `GET /api/liveness` | 存活探针 | 服务是否在运行 |

### 响应示例

```json
// GET /api/health
{
  "status": "healthy",
  "database": "connected",
  "version": "2.0.0",
  "timestamp": "2026-04-27T10:00:00Z"
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
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health').read()"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

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
docker stats

# 输出示例
CONTAINER          CPU %   MEM USAGE / LIMIT   NET I/O        BLOCK I/O
backend            2.5%    256MiB / 4GiB       10MB / 5MB     50MB / 20MB
frontend           0.5%    128MiB / 2GiB       5MB / 30MB     10MB / 5MB
db                 1.0%    512MiB / 2GiB       20MB / 15MB    100MB / 80MB
mailserver         0.3%    128MiB / 1GiB       2MB / 1MB      5MB / 2MB
caddy              0.1%    32MiB / 512MiB      50MB / 50MB    1MB / 1MB
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

TalentMail 有 7 个后台定时任务：

```bash
# 查看后台任务运行状态
docker compose logs backend | grep -E "(IMAP 同步|定时发送|贪睡|临时邮箱|会话清理|附件清理|外部账户)"

# 检查某个任务最近的运行记录
docker compose logs --since 10m backend | grep "imap_sync"
```

### 预期日志模式

| 任务 | 间隔 | 正常日志 |
|------|------|---------|
| IMAP Sync | 30s | `IMAP 同步完成: N 新邮件` |
| External Sync | 5min | `外部账户同步完成` |
| Scheduled Send | 60s | `定时发送检查完成` |
| Snooze Check | 60s | `贪睡检查完成` |
| Temp Cleanup | 10min | `临时邮箱清理完成` |
| Session Cleanup | 24h | `过期会话清理完成` |
| Orphan Cleanup | 1h | `孤立附件清理完成` |

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
| `/api/health` 非 200 | 连续 3 次 | Critical |
| Backend CPU | > 80% 持续 5min | Warning |
| Backend Memory | > 80% | Warning |
| DB 连接数 | > 80 | Warning |
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
