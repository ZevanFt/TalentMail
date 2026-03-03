# 邮件投递修复 - dual-deliver 传输链路断裂

## 问题描述

**症状**：所有邮箱（包括主账户和临时邮箱）均无法收到外部邮件
**状态**：✅ **已修复**
**修复时间**：2026-03-03
**影响范围**：所有邮件投递（SMTP 接受邮件后无法入库）

## 问题根因分析

### 邮件投递架构

```
外部邮件 → Postfix (port 25) → virtual_transport → 邮件存储 → PostgreSQL
```

### 故障链

云端 `data/mailserver/config/user-patches.sh`（运行时配置，不在 git 中）配置了自定义 `dual-deliver` 传输，替代了默认的 Dovecot LMTP 投递。该脚本包含两个致命 bug：

#### Bug 1：竞态条件（临时文件提前删除）

```bash
# 后台进程还没读取文件就被删了
python3 /usr/local/bin/send-to-backend-lmtp.py "$SENDER" "$RECIPIENT" "$TMPFILE" &
rm -f "$TMPFILE"   # ← 立即删除，后台进程来不及读取
```

#### Bug 2：netcat LMTP 协议错误

```bash
{
    echo "LHLO localhost"
    echo "MAIL FROM:<$SENDER>"
    echo "RCPT TO:<$RECIPIENT>"
    echo "DATA"
    cat "$TMPFILE"
    echo "."
    echo "QUIT"
} | nc -U /var/run/dovecot/lmtp
# ↑ 不等待 LMTP 响应码就发送下一条命令，违反 LMTP 协议
```

#### Bug 3：mail_sync.py 不同步临时邮箱

```python
# 原代码只遍历 User 表
users = db.query(User).all()
for user in users:
    count = sync_user_mailbox(db, user)
# ← TempMailbox 表完全被忽略，临时邮箱即使 Dovecot 有邮件也无法入库
```

### 故障影响

| 投递路径 | 状态 | 原因 |
|---------|------|------|
| Postfix → dual-deliver → Dovecot | 失败 | netcat 不等响应 |
| Postfix → dual-deliver → Backend LMTP | 失败 | 临时文件被提前删除 |
| mail_sync.py → IMAP → PostgreSQL（用户邮箱） | 正常但无数据 | Dovecot 没收到邮件 |
| mail_sync.py → IMAP → PostgreSQL（临时邮箱） | 未实现 | 代码不遍历 TempMailbox |

### 验证证据

```
SMTP 发送 → 250 OK（Postfix 接受）
Dovecot IMAP 查询 → 0 封（投递失败，邮件在 deferred 队列）
Pool API 查询 → 0 封（PostgreSQL 无数据）
```

## 修复方案

### 策略：去掉 dual-deliver，回归标准 Dovecot 投递 + IMAP 同步

```
修复后架构：
外部邮件 → Postfix → Dovecot LMTP（默认）→ Dovecot 邮箱存储
                                              ↓
                              mail_sync.py (每30秒) 通过 Master user IMAP 同步
                                              ↓
                                         PostgreSQL → Pool API
```

### 修改文件

#### 1. `config/mail/user-patches.sh` — 邮件服务器启动脚本

- 移除 `dual-deliver` 传输配置
- 恢复 `virtual_transport=lmtp:unix:private/dovecot-lmtp`（docker-mailserver 默认值）
- 自动检测并清理已有的 dual-deliver 残留配置
- 使用 `99-talentmail.conf` 统一管理 Dovecot 扩展配置（master user、socket 权限）
- Master user 密码格式从 SHA512-CRYPT 简化为 PLAIN（Dovecot 内部通信，无安全风险）

#### 2. `backend/core/mail_sync.py` — 邮件同步服务

- 新增 `sync_temp_mailbox()` 函数，通过 Master user IMAP 同步临时邮箱
- 新增 `_sync_imap_inbox()` 通用同步函数，消除代码重复
- `sync_all_mailboxes()` 同时遍历 `User` 和 `TempMailbox` 表
- IMAP 登录失败降级为 debug 日志（临时邮箱可能未在邮件服务器注册）
- 默认同步间隔从 300 秒降至 30 秒

#### 3. `backend/main.py` — 同步间隔

- `periodic_sync(interval=300)` → `periodic_sync(interval=30)`

### 部署步骤

```bash
# 1. 在云服务器上拉取最新代码
cd /path/to/talentmail
git pull

# 2. 同步 user-patches.sh 到运行时目录
cp config/mail/user-patches.sh data/mailserver/config/user-patches.sh

# 3. 迁移部署（保留数据）
./deploy.sh --migrate
```

## 验证方法

### 1. 检查 Postfix 传输配置

```bash
# 进入 mailserver 容器
docker compose exec mailserver bash

# 检查 virtual_transport 是否已恢复
postconf virtual_transport
# 期望输出：virtual_transport = lmtp:unix:private/dovecot-lmtp

# 确认没有 dual-deliver 残留
grep "dual-deliver" /etc/postfix/master.cf
# 期望：无输出
```

### 2. 发送测试邮件

```bash
# 从本地发送测试邮件
python3 -c "
import smtplib
from email.mime.text import MIMEText
msg = MIMEText('Test 123456')
msg['Subject'] = 'Test Delivery'
msg['From'] = 'test@gmail.com'
msg['To'] = 'admin@talenting.vip'
smtp = smtplib.SMTP('maillink.talenting.vip', 25, timeout=30)
smtp.ehlo(); smtp.starttls(); smtp.ehlo()
smtp.sendmail('test@gmail.com', 'admin@talenting.vip', msg.as_string())
smtp.quit()
print('OK')
"
```

### 3. 检查 IMAP 收件

```bash
# 等待 30 秒后检查 API
curl -sL 'https://mail.talenting.vip/api/pool/stats' \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

## 经验总结

1. **不要覆盖 docker-mailserver 的默认 virtual_transport** — 自定义 pipe 传输容易引入 LMTP 协议兼容性问题
2. **gitignore 的 data/ 目录可能包含关键运行时配置** — 任何 `data/mailserver/config/` 的修改必须同步到 git 中的 `config/mail/`
3. **IMAP Master user 同步是最可靠的数据库入库方式** — 比自定义 LMTP 转发更简单、更不容易出错
4. **临时邮箱需要两步创建** — PostgreSQL 记录 + docker-mailserver 用户（`setup email add`），缺一不可

---

**创建时间**：2026-03-03
**状态**：✅ 已修复
**优先级**：紧急
