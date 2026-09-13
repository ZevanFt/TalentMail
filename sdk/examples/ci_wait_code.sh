#!/usr/bin/env bash
# CI 场景：创建临时邮箱并轮询验证码，拿到后输出到 stdout。
# 用法:
#   export TALENTMAIL_BASE_URL=https://mail.example.com/api
#   export TALENTMAIL_API_KEY=tm_xxx
#   ./ci_wait_code.sh [prefix] [timeout_seconds]
set -euo pipefail

BASE="${TALENTMAIL_BASE_URL:?请设置 TALENTMAIL_BASE_URL}"
KEY="${TALENTMAIL_API_KEY:?请设置 TALENTMAIL_API_KEY}"
PREFIX="${1:-ci-$(date +%s)}"
TIMEOUT="${2:-90}"
INTERVAL=3

resp=$(curl -sf -X POST "$BASE/automation/temp-mailboxes" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: ci-$PREFIX" \
  -d "{\"prefix\":\"$PREFIX\",\"auto_verify_codes\":true,\"purpose\":\"CI wait code\"}")

email=$(echo "$resp" | jq -r '.email')
mailbox_id=$(echo "$resp" | jq -r '.id')
echo "mailbox=$email id=$mailbox_id" >&2

deadline=$(( $(date +%s) + TIMEOUT ))
while [ "$(date +%s)" -lt "$deadline" ]; do
  code=$(curl -sf -H "Authorization: Bearer $KEY" \
    "$BASE/automation/temp-mailboxes/$mailbox_id/codes/latest?within_minutes=10" \
    | jq -r '.code // empty' || true)
  if [ -n "$code" ]; then
    echo "$code"
    exit 0
  fi
  sleep "$INTERVAL"
done

echo "timeout waiting for verification code" >&2
exit 3
