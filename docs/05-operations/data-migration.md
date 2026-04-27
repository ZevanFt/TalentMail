# 数据迁移指南

## Alembic 数据库迁移

TalentMail 使用 Alembic 管理数据库 schema 变更，当前有 44 个迁移版本。

### 日常使用

```bash
# 执行所有待处理的迁移（升级到最新版本）
docker compose exec backend alembic upgrade head

# 查看当前迁移版本
docker compose exec backend alembic current

# 查看迁移历史
docker compose exec backend alembic history --verbose

# 查看待执行的迁移
docker compose exec backend alembic heads
```

### 新增模型后生成迁移

当修改或新增 SQLAlchemy 模型后：

```bash
# 1. 修改模型文件
#    例: backend/db/models/new_feature.py

# 2. 确保模型在 __init__.py 中导入
#    例: from .new_feature import NewFeature

# 3. 生成迁移文件
docker compose exec backend alembic revision --autogenerate -m "add new_feature table"

# 4. 检查生成的迁移文件
#    文件位于 backend/alembic/versions/xxxx_add_new_feature_table.py
#    重点检查:
#    - upgrade() 函数中的操作是否正确
#    - downgrade() 函数中的回滚操作是否正确
#    - 索引是否需要手动补充

# 5. 执行迁移
docker compose exec backend alembic upgrade head
```

### 回滚

```bash
# 回滚最近一个迁移
docker compose exec backend alembic downgrade -1

# 回滚到指定版本
docker compose exec backend alembic downgrade <revision_id>

# 回滚到初始状态（危险！）
docker compose exec backend alembic downgrade base
```

### 已知注意事项

1. **容器内代码同步**: 如果代码挂载为 volume，容器内的代码可能是旧版。运行 `autogenerate` 前确保容器内代码是最新的。

2. **新列检测问题**: Alembic `autogenerate` 对已有表的新列检测可能不完整，建议每次检查生成的迁移文件。

3. **默认值**: 给已有表添加 NOT NULL 列时，必须提供 `server_default` 或分两步迁移（先加 nullable → 回填 → 改 NOT NULL）。

4. **索引**: `autogenerate` 可能遗漏复合索引，需手动添加。

---

## 数据导出/导入

### 数据库备份与恢复

```bash
# 导出完整数据库
docker compose exec -T db pg_dump -U talentmail -Fc talentmail > backup.dump

# 恢复数据库（会覆盖现有数据！）
docker compose exec -T db pg_restore -U talentmail -d talentmail --clean --if-exists < backup.dump

# 仅导出数据（不含 schema）
docker compose exec -T db pg_dump -U talentmail --data-only talentmail > data_only.sql

# 仅导出特定表
docker compose exec -T db pg_dump -U talentmail -t emails -t attachments talentmail > emails.sql
```

### 邮件导出

| 格式 | 方法 | 说明 |
|------|------|------|
| EML | Web 界面「导出为 EML」 | 单封邮件的 RFC 822 原始格式 |
| PDF | Web 界面「导出为 PDF」 | 邮件打印视图 |

```bash
# 通过 API 批量导出
TOKEN="<your_jwt_token>"

# 导出单封邮件为 EML
curl -H "Authorization: Bearer $TOKEN" \
  "https://mail.example.com/api/emails/123/export/eml" \
  -o email_123.eml
```

### 邮件导入

支持批量导入 `.eml` 和 `.mbox` 文件：

```bash
# 通过 Web 界面: 设置 → 邮件导入 → 选择文件 → 导入

# 通过 API
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -F "file=@exported.mbox" \
  -F "folder_id=1" \
  "https://mail.example.com/api/emails/import"
```

限制：
- 文件大小: 最大 50MB
- .mbox 文件: 最多 500 封邮件
- 速率限制: 5 次 / 5 分钟 / 用户
- 按 Message-ID 自动去重

### 联系人导出/导入

| 格式 | 导入 | 导出 |
|------|------|------|
| vCard (.vcf) | 支持 | 支持 |
| CSV | 支持 | 支持 |

```bash
# 通过 Web 界面: 联系人页面 → 导入/导出按钮

# 通过 API - 导出 vCard
curl -H "Authorization: Bearer $TOKEN" \
  "https://mail.example.com/api/contacts/export?format=vcf" \
  -o contacts.vcf

# 通过 API - 导入 CSV
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -F "file=@contacts.csv" \
  "https://mail.example.com/api/contacts/import"
```

### 日历数据

目前支持 .ics 导入：

```bash
# 通过 Web 界面: 日历页面 → 导入 .ics

# 通过 API
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -F "file=@calendar.ics" \
  "https://mail.example.com/api/calendar/import-ics"
```

> 日历导出 (.ics) 功能规划中，详见 [未来规划](../06-roadmap/future-plans.md)。

---

## 服务器迁移

从旧服务器迁移到新服务器的完整流程：

### 1. 旧服务器：备份数据

```bash
cd /opt/talentmail

# 停止服务（减少数据不一致风险）
docker compose stop backend frontend

# 备份数据库
docker compose exec -T db pg_dump -U talentmail -Fc talentmail > /tmp/talentmail.dump

# 备份上传文件
tar czf /tmp/uploads.tar.gz backend/uploads/

# 备份配置
cp .env /tmp/talentmail.env
cp config.json /tmp/talentmail-config.json

# 重启服务
docker compose start backend frontend
```

### 2. 传输数据到新服务器

```bash
# 使用 scp 或 rsync
scp /tmp/talentmail.dump new-server:/tmp/
scp /tmp/uploads.tar.gz new-server:/tmp/
scp /tmp/talentmail.env new-server:/tmp/
scp /tmp/talentmail-config.json new-server:/tmp/
```

### 3. 新服务器：部署

```bash
# 克隆代码
git clone <repository-url> /opt/talentmail
cd /opt/talentmail

# 恢复配置
cp /tmp/talentmail.env .env
cp /tmp/talentmail-config.json config.json

# 首次部署（创建数据库容器）
bash deploy.sh --fresh

# 停止后端（准备恢复数据）
docker compose stop backend

# 恢复数据库
docker compose exec -T db pg_restore -U talentmail -d talentmail --clean --if-exists < /tmp/talentmail.dump

# 恢复上传文件
tar xzf /tmp/uploads.tar.gz -C .

# 运行迁移（确保 schema 是最新的）
docker compose exec backend alembic upgrade head

# 重启所有服务
docker compose up -d

# 验证
curl -s https://mail.example.com/api/health | python3 -m json.tool
```

### 4. DNS 切换

将域名 A 记录指向新服务器 IP：
- `mail.example.com` → 新服务器 IP
- `maillink.example.com` → 新服务器 IP

> DNS 切换后需等待 TTL 过期（通常 5-60 分钟），期间新旧服务器可能同时收到请求。

### 5. 验证

```bash
# 检查 Web 访问
curl -s https://mail.example.com/api/health

# 检查邮件收发
# 发送测试邮件并确认收发正常

# 检查 DKIM
# 确认 DKIM 密钥在新服务器上正确配置
docker compose exec mailserver cat /etc/opendkim/keys/example.com/mail.txt
```

---

## 注意事项

1. **迁移前备份**: 任何迁移操作前务必完整备份数据库
2. **测试环境验证**: 大版本升级建议先在测试环境验证
3. **回滚方案**: 始终保留回滚到上一个版本的能力
4. **停机窗口**: 数据库迁移期间建议短暂停机，避免数据不一致

---

最后更新: 2026-04-27
