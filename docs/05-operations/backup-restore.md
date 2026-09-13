# 备份与恢复

TalentMail 支持 PostgreSQL 数据库备份，可由脚本、systemd timer 或管理端 API 触发。

## 1. 手动备份

```bash
# 需在项目根目录，且 .env / docker-compose 已就绪
./scripts/backup-db.sh
```

默认输出：`/var/backups/talentmail/talentmail-YYYYMMDD-HHMMSS.sql.gz`  
保留份数：最近 7 份（环境变量 `TALENTMAIL_BACKUP_KEEP` 可覆盖）

## 2. 定时备份（systemd）

```bash
sudo mkdir -p /opt/talentmail
# 假设项目已在 /opt/talentmail
sudo cp scripts/talentmail-backup.service scripts/talentmail-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now talentmail-backup.timer

# 查看下次触发时间
systemctl list-timers talentmail-backup.timer
```

默认每天 **03:17** 执行，带 5 分钟内随机延迟。

## 3. 管理端 API

管理员 JWT 鉴权：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/backups` | 列出备份文件 |
| POST | `/api/admin/backups/trigger` | 立即触发备份（5 分钟内最多 3 次） |
| GET | `/api/admin/audit/operations` | 查询操作审计流水 |

示例：

```bash
# 列出备份
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://mail.example.com/api/admin/backups

# 触发备份
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://mail.example.com/api/admin/backups/trigger
```

## 4. 恢复

```bash
# 交互式，恢复前会自动做安全备份
./scripts/restore-db.sh /var/backups/talentmail/talentmail-20260426-030000.sql.gz
```

**恢复会覆盖当前数据库，请务必先确认备份文件正确。**

## 5. 操作审计

关键动作会写入 `operation_audit_logs`：

- `auth.login` — 登录成功
- `backup.create` — 备份触发（成功/失败）
- 后续会逐步覆盖发信、删除、管理动作

查询：

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  "https://mail.example.com/api/admin/audit/operations?action=auth.login&limit=50"
```

保留策略：与 API Key 审计一致，默认 30 天（`AUDIT_LOG_RETENTION_DAYS`）。

## 6. 注意事项

- 备份脚本依赖运行中的 `db` 容器
- 生产建议同时备份 `backend/uploads` 附件目录（可用 rsync/tar）
- 备份文件含敏感数据，磁盘权限建议 `700`，不要放入公开目录
