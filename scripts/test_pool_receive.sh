#!/bin/bash
# =============================================================================
# 临时邮箱收邮件 - 端到端测试
# 用法: bash scripts/test_pool_receive.sh
# 必须在云服务器上执行（本地 SPF 校验会失败）
# =============================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "  ${GREEN}OK${NC} - $1"; }
fail() { echo -e "  ${RED}FAIL${NC} - $1"; }
info() { echo -e "  ${YELLOW}..${NC} $1"; }

echo ""
echo "=========================================="
echo "  临时邮箱收邮件 - 端到端测试"
echo "=========================================="
echo ""

# 获取第一个活跃临时邮箱
TEMP_EMAIL=$(docker compose exec -T db psql -U talentmail -d talentmail -t -c \
    "SELECT email FROM temp_mailboxes WHERE is_active = true LIMIT 1;" 2>/dev/null | xargs)

if [ -z "$TEMP_EMAIL" ]; then
    fail "数据库中没有活跃的临时邮箱，无法测试"
    exit 1
fi

echo "=== 测试目标: ${TEMP_EMAIL} ==="
echo ""

# Step 1: 记录当前邮件数
echo "--- Step 1: 记录当前邮件数 ---"
BEFORE=$(docker compose exec -T mailserver doveadm mailbox status messages INBOX -u "$TEMP_EMAIL" 2>/dev/null | grep -oP 'messages=\K\d+' || echo "0")
info "当前 INBOX 邮件数: ${BEFORE}"
echo ""

# Step 2: 发送测试邮件（从 localhost 发送，绕过 SPF）
echo "--- Step 2: 发送测试邮件 ---"
python3 -c "
import smtplib
from email.mime.text import MIMEText
import time

msg = MIMEText('Your verification code is 654321. Test at ' + str(int(time.time())))
msg['Subject'] = 'Pool receive test - code 654321'
msg['From'] = 'admin@talenting.vip'
msg['To'] = '${TEMP_EMAIL}'

smtp = smtplib.SMTP('localhost', 25, timeout=30)
smtp.sendmail('admin@talenting.vip', '${TEMP_EMAIL}', msg.as_string())
smtp.quit()
print('OK')
"

if [ $? -eq 0 ]; then
    pass "邮件已发送到 ${TEMP_EMAIL}"
else
    fail "邮件发送失败"
    exit 1
fi
echo ""

# Step 3: 等待投递
echo "--- Step 3: 等待 Dovecot LMTP 投递 (10秒) ---"
sleep 10

# Step 4: 检查 Dovecot 是否收到
echo "--- Step 4: 检查 Dovecot 邮箱 ---"
AFTER=$(docker compose exec -T mailserver doveadm mailbox status messages INBOX -u "$TEMP_EMAIL" 2>/dev/null | grep -oP 'messages=\K\d+' || echo "0")
info "当前 INBOX 邮件数: ${AFTER}（之前: ${BEFORE}）"

if [ "$AFTER" -gt "$BEFORE" ]; then
    pass "Dovecot LMTP 投递成功！邮件数从 ${BEFORE} 增加到 ${AFTER}"
else
    fail "Dovecot 未收到邮件（数量未变化）"
    echo ""
    echo "  排查: 检查 Dovecot 日志"
    docker compose logs --tail=10 mailserver 2>/dev/null | grep -i "$TEMP_EMAIL" | tail -5 | sed 's/^/  /'
    exit 1
fi
echo ""

# Step 5: 等待 mail_sync 同步到 PostgreSQL
echo "--- Step 5: 等待 mail_sync 同步到 PostgreSQL (35秒) ---"
sleep 35

# Step 6: 检查 PostgreSQL 是否有邮件记录
echo "--- Step 6: 检查 PostgreSQL 邮件记录 ---"
MAILBOX_ID=$(docker compose exec -T db psql -U talentmail -d talentmail -t -c \
    "SELECT id FROM temp_mailboxes WHERE email = '${TEMP_EMAIL}';" 2>/dev/null | xargs)

DB_COUNT=$(docker compose exec -T db psql -U talentmail -d talentmail -t -c \
    "SELECT COUNT(*) FROM temp_emails WHERE mailbox_id = ${MAILBOX_ID};" 2>/dev/null | xargs)

if [ "$DB_COUNT" -gt 0 ]; then
    pass "mail_sync 同步成功！PostgreSQL 中有 ${DB_COUNT} 封邮件"
else
    fail "mail_sync 未同步到 PostgreSQL（0 封邮件）"
    echo ""
    echo "  排查: 检查 backend 同步日志"
    docker compose logs --tail=10 backend 2>/dev/null | grep -i "sync\|${TEMP_EMAIL}" | tail -5 | sed 's/^/  /'
fi
echo ""

# 结果汇总
echo "=========================================="
if [ "$AFTER" -gt "$BEFORE" ] && [ "$DB_COUNT" -gt 0 ]; then
    echo -e "  ${GREEN}端到端测试通过！${NC}"
    echo "  SMTP → Postfix → Dovecot LMTP → maildir → mail_sync → PostgreSQL"
elif [ "$AFTER" -gt "$BEFORE" ]; then
    echo -e "  ${YELLOW}Dovecot 投递成功，但 PostgreSQL 同步未完成${NC}"
    echo "  建议再等 30 秒后检查 backend 日志"
else
    echo -e "  ${RED}测试失败${NC}"
fi
echo "=========================================="
echo ""
