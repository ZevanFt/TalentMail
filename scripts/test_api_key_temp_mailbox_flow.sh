#!/usr/bin/env bash
set -euo pipefail

# API Key 自动化闭环测试脚本
# 流程：
# 1) 登录获取 JWT
# 2) 创建 API Key
# 3) 用 API Key 创建临时邮箱
# 4) 拉取邮箱邮件列表
# 5) 拉取最新验证码
# 6) 查询 API Key 审计日志

BASE_URL="${BASE_URL:-https://mail.${BASE_DOMAIN:-localhost}}"
USER_EMAIL="${USER_EMAIL:-}"
USER_PASSWORD="${USER_PASSWORD:-}"
MAILBOX_PURPOSE="${MAILBOX_PURPOSE:-api-key-flow-test}"
EXPIRES_IN_DAYS="${EXPIRES_IN_DAYS:-30}"
RATE_LIMIT="${RATE_LIMIT:-120}"
INSECURE_TLS="${INSECURE_TLS:-0}"
IDEMPOTENCY_KEY="${IDEMPOTENCY_KEY:-}"

if [[ -z "${USER_EMAIL}" || -z "${USER_PASSWORD}" ]]; then
  echo "缺少必要环境变量: USER_EMAIL / USER_PASSWORD"
  echo "示例:"
  echo "  USER_EMAIL='admin@example.vip' USER_PASSWORD='123456' BASE_URL='https://mail.example.vip' bash scripts/test_api_key_temp_mailbox_flow.sh"
  exit 1
fi

curl_opts=("-sS")
if [[ "${INSECURE_TLS}" == "1" ]]; then
  curl_opts+=("-k")
fi

json_get() {
  local key="$1"
  python3 -c '
import json, sys
key = sys.argv[1]
data = json.load(sys.stdin)
val = data
for part in key.split("."):
    if isinstance(val, list):
        part = int(part)
    val = val[part]
if isinstance(val, (dict, list)):
    print(json.dumps(val, ensure_ascii=False))
else:
    print(val)
' "$key"
}

echo "[1/6] 登录获取 JWT ..."
login_resp="$(
  curl "${curl_opts[@]}" \
    -X POST "${BASE_URL}/api/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "username=${USER_EMAIL}" \
    --data-urlencode "password=${USER_PASSWORD}"
)"

if ! access_token="$(printf '%s' "${login_resp}" | json_get "access_token" 2>/dev/null)"; then
  echo "登录失败，返回内容:"
  echo "${login_resp}"
  exit 1
fi

if [[ -z "${access_token}" ]]; then
  echo "登录未返回 access_token:"
  echo "${login_resp}"
  exit 1
fi

echo "[2/6] 创建 API Key ..."
create_key_payload="$(cat <<JSON
{
  "description": "automation-flow-test",
  "scopes": [
    "temp_mailbox:create",
    "temp_mailbox:read",
    "temp_email:read",
    "temp_code:read",
    "temp_mailbox:extend",
    "temp_mailbox:restore"
  ],
  "expires_in_days": ${EXPIRES_IN_DAYS},
  "rate_limit_per_minute": ${RATE_LIMIT}
}
JSON
)"

create_key_resp="$(
  curl "${curl_opts[@]}" \
    -X POST "${BASE_URL}/api/api-keys/" \
    -H "Authorization: Bearer ${access_token}" \
    -H "Content-Type: application/json" \
    -d "${create_key_payload}"
)"

api_key="$(printf '%s' "${create_key_resp}" | json_get "api_key" 2>/dev/null || true)"
api_key_id="$(printf '%s' "${create_key_resp}" | json_get "key.id" 2>/dev/null || true)"
if [[ -z "${api_key}" || -z "${api_key_id}" ]]; then
  echo "创建 API Key 失败，返回内容:"
  echo "${create_key_resp}"
  exit 1
fi
echo "API Key 创建成功: id=${api_key_id}"

echo "[3/6] 使用 API Key 创建临时邮箱 ..."
create_mailbox_payload="$(cat <<JSON
{
  "purpose": "${MAILBOX_PURPOSE}",
  "auto_verify_codes": true
}
JSON
)"

create_mailbox_resp="$(
  if [[ -n "${IDEMPOTENCY_KEY}" ]]; then
    curl "${curl_opts[@]}" \
      -X POST "${BASE_URL}/api/automation/temp-mailboxes" \
      -H "Authorization: Bearer ${api_key}" \
      -H "Content-Type: application/json" \
      -H "Idempotency-Key: ${IDEMPOTENCY_KEY}" \
      -d "${create_mailbox_payload}"
  else
    curl "${curl_opts[@]}" \
      -X POST "${BASE_URL}/api/automation/temp-mailboxes" \
      -H "Authorization: Bearer ${api_key}" \
      -H "Content-Type: application/json" \
      -d "${create_mailbox_payload}"
  fi
)"

mailbox_id="$(printf '%s' "${create_mailbox_resp}" | json_get "id" 2>/dev/null || true)"
mailbox_email="$(printf '%s' "${create_mailbox_resp}" | json_get "email" 2>/dev/null || true)"
if [[ -z "${mailbox_id}" || -z "${mailbox_email}" ]]; then
  echo "创建临时邮箱失败，返回内容:"
  echo "${create_mailbox_resp}"
  exit 1
fi
echo "临时邮箱创建成功: ${mailbox_email} (id=${mailbox_id})"

echo "[4/6] 拉取临时邮箱邮件列表 ..."
emails_resp="$(
  curl "${curl_opts[@]}" \
    "${BASE_URL}/api/automation/temp-mailboxes/${mailbox_id}/emails?limit=10&include_body=false" \
    -H "Authorization: Bearer ${api_key}"
)"
emails_total="$(printf '%s' "${emails_resp}" | json_get "total" 2>/dev/null || echo "0")"
echo "当前邮件数: ${emails_total}"

echo "[5/6] 拉取最新验证码 ..."
code_resp="$(
  curl "${curl_opts[@]}" \
    "${BASE_URL}/api/automation/temp-mailboxes/${mailbox_id}/codes/latest?within_minutes=1440" \
    -H "Authorization: Bearer ${api_key}"
)"
if [[ "${code_resp}" == "null" ]]; then
  echo "当前未解析到验证码（可先向 ${mailbox_email} 发送验证码邮件后重试）"
else
  code_value="$(printf '%s' "${code_resp}" | json_get "code" 2>/dev/null || true)"
  if [[ -n "${code_value}" ]]; then
    echo "最新验证码: ${code_value}"
  else
    echo "验证码接口返回:"
    echo "${code_resp}"
  fi
fi

echo "[6/6] 查询 API Key 审计日志 ..."
audit_resp="$(
  curl "${curl_opts[@]}" \
    "${BASE_URL}/api/api-keys/audit/logs?key_id=${api_key_id}&limit=20" \
    -H "Authorization: Bearer ${access_token}"
)"
audit_count="$(printf '%s' "${audit_resp}" | python3 -c 'import json,sys; data=json.load(sys.stdin); print(len(data) if isinstance(data, list) else 0)')"
echo "审计日志条数: ${audit_count}"

echo
echo "闭环完成。关键结果："
echo "- API Key ID: ${api_key_id}"
echo "- Temp Mailbox: ${mailbox_email}"
echo "- Emails Total: ${emails_total}"
