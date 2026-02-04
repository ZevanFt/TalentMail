# 运维指南

本目录包含 TalentMail 的运维相关文档，帮助你部署、监控和维护系统。

## 📚 文档列表

- **[部署指南](./deployment.md)** - 详细的部署步骤和配置
- **[监控配置](./monitoring.md)** - 系统监控和告警设置（编写中）
- **[故障排查](./troubleshooting.md)** - 常见问题诊断和解决方案
- **[备份恢复](./backup-recovery.md)** - 数据备份和灾难恢复（编写中）
- **[性能优化](./performance.md)** - 系统性能调优指南（编写中）

## 🚀 快速导航

### 首次部署？
➡️ 查看 [部署指南](./deployment.md)
- 服务器要求
- 环境准备
- 部署步骤
- SSL 配置

### 遇到问题？
➡️ 查看 [故障排查](./troubleshooting.md)
- 常见问题列表
- 诊断命令
- 解决方案
- 紧急恢复

### 需要监控？
➡️ 查看 [监控配置](./monitoring.md)（编写中）
- 监控指标
- 告警规则
- 日志管理
- 性能分析

## 🔧 运维工具

### 常用脚本
```bash
# 部署脚本
./deploy.sh

# 同步邮件证书
./scripts/sync_mail_certs.sh

# 备份数据库
./scripts/backup.sh (待创建)
```

### Docker 命令
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f [服务名]

# 重启服务
docker-compose restart [服务名]

# 更新服务
docker-compose pull
docker-compose up -d
```

## 📊 系统架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Caddy     │────▶│   Frontend  │────▶│   Backend   │
│  (反向代理)  │     │   (Nuxt)    │     │  (FastAPI)  │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                    ┌─────────────┐            │
                    │ Mailserver  │◀───────────┤
                    │ (Postfix)   │            │
                    └─────────────┘            │
                                               ▼
                                        ┌─────────────┐
                                        │ PostgreSQL  │
                                        │  Database   │
                                        └─────────────┘
```

## 🏥 健康检查

### 服务健康状态
- **Frontend**: http://localhost:3000/health
- **Backend**: http://localhost:8000/health
- **Database**: 通过 pg_isready 检查
- **Mailserver**: 通过 postfix status 检查

### 监控指标
- CPU 使用率
- 内存使用率
- 磁盘空间
- 网络流量
- 响应时间
- 错误率

## 🔒 安全建议

### 基础安全
1. **定期更新系统**
   ```bash
   apt update && apt upgrade
   ```

2. **配置防火墙**
   ```bash
   ufw allow 22,80,443,25,143,587,993/tcp
   ufw enable
   ```

3. **设置强密码**
   - 数据库密码
   - 管理员密码
   - SMTP 密码

### 高级安全
- 启用 2FA 认证
- 配置 Fail2ban
- 使用 VPN 访问
- 定期安全审计

## 📈 性能优化

### 数据库优化
```sql
-- 定期清理
VACUUM ANALYZE;

-- 监控慢查询
SELECT * FROM pg_stat_statements
ORDER BY total_exec_time DESC LIMIT 10;
```

### Docker 优化
```yaml
# 资源限制
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
```

### 缓存策略
- 静态资源 CDN
- Redis 缓存（计划）
- 浏览器缓存头

## 🔄 维护计划

### 日常维护
- 检查服务状态
- 监控磁盘空间
- 查看错误日志
- 备份验证

### 周期维护
- 每周：全量备份
- 每月：安全更新
- 每季：性能评估
- 每年：架构审查

## 📞 紧急联系

发生严重故障时：
1. 查看故障排查文档
2. 收集诊断信息
3. 联系技术支持
4. 执行恢复流程

---

最后更新：2025-02-01