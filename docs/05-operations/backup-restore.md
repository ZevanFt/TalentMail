# 备份与恢复

TalentMail 支持 PostgreSQL 数据库备份，可由脚本、systemd timer 或管理端 API 触发。

## 1. 手动备份

```bash
# 需在项目根目录，且 .env / docker-compose 已就绪
./scripts/backup-db.sh
```

默认输出：`/var/backups/talentmail/talentmail-YYYYMMDD-HHMMSS.sql.gz`  
保留份数：最近 7 份（环境变量 `TALENTMAIL_BACKUP_KEEP` 可覆盖）

### 加密与附件打包

```bash
# 启用 openssl AES-256-GCM 加密
export TALENTMAIL_BACKUP_ENCRYPT=1
export TALENTMAIL_BACKUP_PASSPHRASE='请换成强口令'

# 同时打包 backend/uploads
export TALENTMAIL_BACKUP_UPLOADS=1
export TALENTMAIL_UPLOADS_DIR=/opt/talentmail/backend/uploads

./scripts/backup-db.sh
```

加密文件后缀为 `.enc`。解密示例：

```bash
openssl enc -d -aes-256-gcm -pbkdf2 -iter 200000 \
  -pass pass:"$TALENTMAIL_BACKUP_PASSPHRASE" \
  -in talentmail-xxx.sql.gz.enc -out talentmail-xxx.sql.gz
```

**口令务必单独保管，丢了备份就废了。**

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
- 生产建议开启 `TALENTMAIL_BACKUP_UPLOADS=1` 备份附件
- 建议开启 `TALENTMAIL_BACKUP_ENCRYPT=1`，口令放密码管理器
- 备份目录权限 `700`，文件 `600`（脚本已自动设置）
- 恢复加密备份前先解密，再 `restore-db.sh`
