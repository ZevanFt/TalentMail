# 邮件投递修复 - dual-deliver 传输链路断裂

## 问题描述

**症状**：所有邮箱（包括主账户和临时邮箱）均无法收到外部邮件
**状态**：✅ **已修复（代码已推送，待部署）**
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

### 修改文件清单

| 文件 | 改动说明 |
|------|---------|
| `config/mail/user-patches.sh` | 移除 dual-deliver 传输，恢复默认 Dovecot LMTP，自动清理残留配置 |
| `backend/core/mail_sync.py` | 新增临时邮箱同步，通用 `_sync_imap_inbox()` 函数 |
| `backend/main.py` | 同步间隔从 300 秒降至 30 秒 |

---

## 完整部署步骤（保留数据）

### 前置条件

- SSH 已连接到云服务器
- 项目代码已推送到 GitHub master 分支
- 云服务器上已有 TalentMail 项目目录

### 第 1 步：进入项目目录

```bash
cd /root/projects/TalentMail
```

**期望输出**：无输出（正常进入目录）

**如果报错** `No such file or directory`：说明项目路径不对，用 `find / -name "TalentMail" -type d 2>/dev/null` 找到实际路径。

---

### 第 2 步：拉取最新代码

```bash
git pull origin master
```

**期望输出**（类似）：

```
remote: Enumerating objects: 15, done.
remote: Counting objects: 100% (15/15), done.
remote: Compressing objects: 100% (8/8), done.
remote: Total 10 (delta 5), reused 10 (delta 5), pack-reused 0
Unpacking objects: 100% (10/10), done.
From github.com:xxx/TalentMail
   abc1234..def5678  master     -> origin/master
Updating abc1234..def5678
Fast-forward
 backend/core/mail_sync.py          | 80 +++++++++++++++++++++---------
 backend/main.py                    |  2 +-
 config/mail/user-patches.sh        | 45 +++++++++++------
 3 files changed, 85 insertions(+), 42 deletions(-)
```

**关键确认**：输出中必须包含这 3 个文件：
- `config/mail/user-patches.sh` — 邮件服务器启动脚本（修复核心）
- `backend/core/mail_sync.py` — 邮件同步服务（新增临时邮箱同步）
- `backend/main.py` — 同步间隔调整

**如果输出** `Already up to date.`：说明代码没有更新，检查是否已经 push 到 master 分支，或检查是否在正确的分支上 (`git branch`)。

**如果报冲突**：不要用 `--force`，先 `git stash` 保存本地修改，再 `git pull`，再 `git stash pop` 恢复。

---

### 第 3 步：同步 user-patches.sh 到运行时目录（最关键！）

```bash
cp config/mail/user-patches.sh data/mailserver/config/user-patches.sh
```

**期望输出**：无输出（静默复制成功）

**为什么这一步最关键**：`data/` 目录被 `.gitignore` 忽略，`git pull` 不会更新它。但 docker-mailserver 容器启动时读取的是 `data/mailserver/config/user-patches.sh`，不是 `config/mail/user-patches.sh`。如果跳过这一步，容器重启后仍然使用有 bug 的旧版本。

**验证复制成功**：

```bash
diff config/mail/user-patches.sh data/mailserver/config/user-patches.sh
```

**期望输出**：无输出（两个文件完全一致）

**如果有输出**：说明两个文件不一致，重新执行 `cp` 命令。

---

### 第 4 步：迁移部署（保留所有数据）

```bash
./deploy.sh --migrate
```

**期望输出**（完整流程，按顺序）：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 TalentMail 生产环境部署
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ℹ️  部署模式: migrate

ℹ️  🛑 停止现有服务...
[+] Running 5/5
 ✔ Container talentmail-frontend-1    Removed
 ✔ Container talentmail-backend-1     Removed
 ✔ Container talentmail-mailserver-1  Removed
 ✔ Container talentmail-caddy-1       Removed
 ✔ Container talentmail-db-1          Removed

✅ 环境变量检查通过

ℹ️  ⚙️  根据 config.json 生成域名配置文件 (.env.domains)...
✅ 已生成 .env.domains

ℹ️  🔧 生成 Dovecot SQL 配置文件...
✅ 已生成 config/mail/dovecot-sql.conf.ext

ℹ️  🏗️  构建 Docker 镜像...
[+] Building ...（构建过程，可能需要几分钟）

ℹ️  ▶️  启动服务...
[+] Running 5/5
 ✔ Container talentmail-db-1          Started
 ✔ Container talentmail-mailserver-1  Started
 ✔ Container talentmail-backend-1     Started
 ✔ Container talentmail-frontend-1    Started
 ✔ Container talentmail-caddy-1       Started

ℹ️  ⏳ 等待数据库就绪...

ℹ️  📦 执行迁移部署...
ℹ️  🔄 运行数据库迁移...

ℹ️  🔍 检查管理员用户...
✅ 管理员用户已存在: admin@talenting.vip

ℹ️  🔧 自动修复邮件系统...
（邮件修复脚本输出）

ℹ️  🔐 自动配置 DKIM 邮件签名...
（DKIM 配置脚本输出）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 🎉 部署完成！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 访问信息：
   - Web 应用: https://mail.talenting.vip
   - 邮件服务器: maillink.talenting.vip
```

**如果构建失败**：检查 Docker 是否正常运行 (`docker info`)，磁盘空间是否充足 (`df -h`)。

**如果数据库迁移失败**：脚本会自动降级执行 `init_db()`，通常不影响已有数据。

---

### 第 5 步：等待 mailserver 完全启动

```bash
sleep 15
```

**为什么要等**：`user-patches.sh` 中的 Postfix 修复是延迟 10 秒执行的（等待 docker-mailserver 初始化完成），需要等它执行完毕。

---

## 部署后验证（5 项检查）

### 验证 1：检查所有容器运行状态

```bash
docker compose ps
```

**期望输出**（所有容器都是 `Up` 或 `running` 状态）：

```
NAME                        STATUS
talentmail-backend-1        Up
talentmail-caddy-1          Up
talentmail-db-1             Up (healthy)
talentmail-frontend-1       Up
talentmail-mailserver-1     Up
```

**如果有容器不是 Up**：查看该容器日志 `docker compose logs <容器名>`。

---

### 验证 2：检查 Postfix 传输配置已恢复

```bash
docker compose exec mailserver postconf virtual_transport
```

**期望输出**（必须完全匹配）：

```
virtual_transport = lmtp:unix:private/dovecot-lmtp
```

**如果输出是** `virtual_transport = dual-deliver`：说明第 3 步没有正确执行，重新执行：

```bash
cp config/mail/user-patches.sh data/mailserver/config/user-patches.sh
docker compose restart mailserver
sleep 15
```

---

### 验证 3：确认没有 dual-deliver 残留

```bash
docker compose exec mailserver grep "dual-deliver" /etc/postfix/master.cf
```

**期望输出**：无输出（空，没有任何匹配）

**如果有输出**：说明 master.cf 中还有 dual-deliver 残留，`user-patches.sh` 的清理逻辑没有执行。手动清理：

```bash
docker compose exec mailserver bash -c "sed -i '/dual-deliver/d' /etc/postfix/master.cf && postfix reload"
```

---

### 验证 4：检查 backend 邮件同步任务启动

```bash
docker compose logs --tail=30 backend | grep -i "sync\|同步\|mail_sync"
```

**期望输出**（应包含类似内容）：

```
INFO: 邮件同步任务启动，间隔 30 秒
INFO: 开始同步所有邮箱...
INFO: 同步完成，用户邮箱: X 封，临时邮箱: Y 封
```

**关键确认**：
- 同步间隔应该是 `30` 秒（不是旧的 `300` 秒）
- 应该有"临时邮箱"相关的日志（说明新代码生效）

**如果没有同步日志**：检查 backend 是否启动成功 `docker compose logs backend | tail -20`。

---

### 验证 5：发送测试邮件并验证收件

在云服务器上执行（或从任意能访问 `maillink.talenting.vip:25` 的机器上执行）：

```bash
python3 -c "
import smtplib
from email.mime.text import MIMEText
msg = MIMEText('Test delivery verification 123456')
msg['Subject'] = 'Mail Fix Verification'
msg['From'] = 'test@gmail.com'
msg['To'] = 'admin@talenting.vip'
smtp = smtplib.SMTP('maillink.talenting.vip', 25, timeout=30)
smtp.ehlo(); smtp.starttls(); smtp.ehlo()
smtp.sendmail('test@gmail.com', 'admin@talenting.vip', msg.as_string())
smtp.quit()
print('Sent OK')
"
```

**期望输出**：

```
Sent OK
```

**如果报错** `Connection refused`：检查端口 25 是否开放 (`netstat -tlnp | grep 25`)。
**如果报错** `Connection timed out`：检查防火墙是否放通端口 25。

#### 确认邮件已投递到 Dovecot

等待 5 秒后检查：

```bash
docker compose exec mailserver doveadm mailbox status messages INBOX -u admin@talenting.vip
```

**期望输出**（messages 数值 > 0）：

```
messages=1
```

**如果** `messages=0`：检查 Postfix 邮件队列 `docker compose exec mailserver postqueue -p`，看看邮件是否卡在队列中。

#### 确认邮件已同步到 PostgreSQL

等待 30 秒（一个同步周期）后检查 Web 端：

1. 浏览器打开 `https://mail.talenting.vip`
2. 用 `admin@talenting.vip` 登录
3. 查看收件箱，应该能看到标题为 `Mail Fix Verification` 的邮件

或者用 API 检查：

```bash
# 先登录获取 token
TOKEN=$(curl -s -X POST 'https://mail.talenting.vip/api/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@talenting.vip","password":"你的管理员密码"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

# 查询收件箱
curl -s 'https://mail.talenting.vip/api/emails/?folder=inbox&page=1&per_page=5' \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool
```

**期望输出**（JSON 格式，包含测试邮件）：

```json
{
    "emails": [
        {
            "subject": "Mail Fix Verification",
            "from_address": "test@gmail.com",
            ...
        }
    ],
    "total": 1
}
```

---

## 验证检查清单（复制到终端逐项执行）

```bash
echo "=== 验证 1: 容器状态 ==="
docker compose ps --format "table {{.Name}}\t{{.Status}}"
echo ""

echo "=== 验证 2: Postfix 传输配置 ==="
docker compose exec mailserver postconf virtual_transport
echo ""

echo "=== 验证 3: dual-deliver 残留检查 ==="
RESULT=$(docker compose exec mailserver grep "dual-deliver" /etc/postfix/master.cf 2>&1)
if [ -z "$RESULT" ]; then echo "OK - 无 dual-deliver 残留"; else echo "FAIL - 发现残留: $RESULT"; fi
echo ""

echo "=== 验证 4: Backend 同步日志 ==="
docker compose logs --tail=10 backend | grep -i "sync\|同步" || echo "未找到同步日志，请等待 30 秒后重试"
echo ""

echo "=== 验证 5: Dovecot LMTP socket ==="
docker compose exec mailserver ls -la /var/run/dovecot/lmtp 2>/dev/null && echo "OK - LMTP socket 存在" || echo "WARN - LMTP socket 不存在"
echo ""

echo "=== 所有验证完成 ==="
```

**全部通过的期望输出**：

```
=== 验证 1: 容器状态 ===
NAME                        STATUS
talentmail-backend-1        Up
talentmail-caddy-1          Up
talentmail-db-1             Up (healthy)
talentmail-frontend-1       Up
talentmail-mailserver-1     Up

=== 验证 2: Postfix 传输配置 ===
virtual_transport = lmtp:unix:private/dovecot-lmtp

=== 验证 3: dual-deliver 残留检查 ===
OK - 无 dual-deliver 残留

=== 验证 4: Backend 同步日志 ===
INFO: 同步完成，用户邮箱: 0 封，临时邮箱: 0 封

=== 验证 5: Dovecot LMTP socket ===
OK - LMTP socket 存在

=== 所有验证完成 ===
```

---

## 回滚方案（如果修复导致新问题）

```bash
# 1. 回退代码
cd /root/projects/TalentMail
git log --oneline -5          # 找到修复前的 commit hash
git checkout <修复前的hash> -- config/mail/user-patches.sh backend/core/mail_sync.py backend/main.py

# 2. 同步回退的 user-patches.sh
cp config/mail/user-patches.sh data/mailserver/config/user-patches.sh

# 3. 重新部署
./deploy.sh --migrate
```

---

## 经验总结

1. **不要覆盖 docker-mailserver 的默认 virtual_transport** — 自定义 pipe 传输容易引入 LMTP 协议兼容性问题
2. **gitignore 的 data/ 目录可能包含关键运行时配置** — 任何 `data/mailserver/config/` 的修改必须同步到 git 中的 `config/mail/`
3. **IMAP Master user 同步是最可靠的数据库入库方式** — 比自定义 LMTP 转发更简单、更不容易出错
4. **临时邮箱需要两步创建** — PostgreSQL 记录 + docker-mailserver 用户（`setup email add`），缺一不可

---

**创建时间**：2026-03-03
**状态**：✅ 已修复（代码已推送，待部署）
**优先级**：紧急
**文档路径**：`docs/troubleshooting/mail-delivery-fix.md`
