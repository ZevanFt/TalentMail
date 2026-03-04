#!/bin/bash
# =============================================================================
# TalentMail 临时邮箱收邮件修复 - 部署验证脚本
# 用法: bash scripts/verify_pool_lmtp_fix.sh
# =============================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "  ${GREEN}OK${NC} - $1"; }
fail() { echo -e "  ${RED}FAIL${NC} - $1"; FAILURES=$((FAILURES + 1)); }
warn() { echo -e "  ${YELLOW}WARN${NC} - $1"; }

FAILURES=0

echo ""
echo "=========================================="
echo "  临时邮箱收邮件修复 - 部署验证"
echo "=========================================="
echo ""

# --- 验证 1: 容器状态 ---
echo "=== 1. 容器状态 ==="
RUNNING=$(docker compose ps --format "{{.Name}}" 2>/dev/null | wc -l)
if [ "$RUNNING" -ge 5 ]; then
    pass "所有 ${RUNNING} 个容器运行中"
else
    fail "只有 ${RUNNING} 个容器运行（期望 >= 5）"
    docker compose ps --format "table {{.Name}}\t{{.Status}}"
fi
echo ""

# --- 验证 2: Dovecot SQL UNION 配置 ---
echo "=== 2. Dovecot SQL UNION 配置 ==="
UNION_COUNT=$(docker compose exec -T mailserver grep -c 'UNION ALL' /etc/dovecot/dovecot-sql.conf.ext 2>/dev/null || echo "0")
if [ "$UNION_COUNT" -ge 2 ]; then
    pass "找到 ${UNION_COUNT} 处 UNION ALL"
else
    fail "只找到 ${UNION_COUNT} 处 UNION ALL（期望 >= 2）"
    echo "  提示: 检查 config/mail/dovecot-sql.conf.ext 是否包含 temp_mailboxes UNION"
fi
echo ""

# --- 验证 3: 临时邮箱用户识别 ---
echo "=== 3. 临时邮箱用户识别 ==="
TEMP_EMAILS=$(docker compose exec -T db psql -U talentmail -d talentmail -t -c \
    "SELECT email FROM temp_mailboxes WHERE is_active = true LIMIT 3;" 2>/dev/null | grep '@' || true)

if [ -n "$TEMP_EMAILS" ]; then
    FIRST_EMAIL=$(echo "$TEMP_EMAILS" | head -1 | xargs)
    pass "数据库中有活跃临时邮箱: ${FIRST_EMAIL}"

    # 用 doveadm 测试该邮箱是否被 Dovecot 识别
    DOVEADM_RESULT=$(docker compose exec -T mailserver doveadm user "$FIRST_EMAIL" 2>&1 || true)
    if echo "$DOVEADM_RESULT" | grep -q 'uid'; then
        pass "Dovecot 识别临时邮箱: ${FIRST_EMAIL}"
    else
        fail "Dovecot 不识别临时邮箱: ${FIRST_EMAIL}"
        echo "  doveadm 输出: $DOVEADM_RESULT"
    fi
else
    warn "数据库中没有活跃的临时邮箱（无法测试 Dovecot 识别）"
fi
echo ""

# --- 验证 4: Postfix 传输配置 ---
echo "=== 4. Postfix 传输配置 ==="
VT=$(docker compose exec -T mailserver postconf -h virtual_transport 2>/dev/null || echo "unknown")
if echo "$VT" | grep -q 'lmtp'; then
    pass "virtual_transport = ${VT}"
else
    fail "virtual_transport = ${VT}（期望包含 lmtp）"
fi
echo ""

# --- 验证 5: Backend 同步日志 ---
echo "=== 5. Backend 邮件同步 ==="
SYNC_LOG=$(docker compose logs --tail=30 backend 2>/dev/null | grep -i "sync\|同步" | tail -3 || true)
if [ -n "$SYNC_LOG" ]; then
    pass "找到同步日志"
    echo "$SYNC_LOG" | sed 's/^/  /'
else
    warn "未找到同步日志（服务刚启动需等待 30 秒）"
fi
echo ""

# --- 验证 6: LMTP socket ---
echo "=== 6. Dovecot LMTP socket ==="
LMTP_SOCKET=$(docker compose exec -T mailserver ls -la /var/run/dovecot/lmtp 2>/dev/null || true)
if [ -n "$LMTP_SOCKET" ]; then
    pass "LMTP socket 存在"
else
    fail "LMTP socket 不存在"
fi
echo ""

# --- 结果汇总 ---
echo "=========================================="
if [ "$FAILURES" -eq 0 ]; then
    echo -e "  ${GREEN}全部验证通过！${NC}"
else
    echo -e "  ${RED}有 ${FAILURES} 项验证失败${NC}"
fi
echo "=========================================="
echo ""
