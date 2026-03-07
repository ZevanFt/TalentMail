#!/bin/bash

set -euo pipefail

set -a
source .env
set +a

DOMAIN=$(grep -E '^DOMAIN=' .env.domains | cut -d'=' -f2-)
WEB_DOMAIN=$(grep -E '^WEB_DOMAIN=' .env.domains | cut -d'=' -f2-)
BASE_URL="https://${WEB_DOMAIN}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@${DOMAIN}}"
SUBJECT="[CLOSE_LOOP_$(date +%s)] API send test"

log() { echo "[INFO] $1"; }
fail() { echo "[ERROR] $1" >&2; exit 1; }

log "Login as ${ADMIN_EMAIL} via ${BASE_URL}"
LOGIN_RESPONSE=$(curl -sS -k -X POST "${BASE_URL}/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=${ADMIN_EMAIL}" \
  --data-urlencode "password=${ADMIN_PASSWORD}")

ACCESS_TOKEN=$(echo "${LOGIN_RESPONSE}" | jq -r '.access_token // empty')
[ -n "${ACCESS_TOKEN}" ] || fail "Login failed: ${LOGIN_RESPONSE}"

PAYLOAD=$(jq -n \
  --arg to "${ADMIN_EMAIL}" \
  --arg subject "${SUBJECT}" \
  '{to:[{name:"Admin",email:$to}],cc:[],bcc:[],subject:$subject,body_html:"<p>close loop test</p>"}')

log "Send email to self (subject=${SUBJECT})"
SEND_RESPONSE=$(curl -sS -k -X POST "${BASE_URL}/api/emails/send" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD}")

EMAIL_ID=$(echo "${SEND_RESPONSE}" | jq -r '.id // empty')
[ -n "${EMAIL_ID}" ] || fail "Send failed: ${SEND_RESPONSE}"

log "Trigger sync"
curl -sS -k -X POST "${BASE_URL}/api/emails/sync" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" >/dev/null

INBOX_ID=$(curl -sS -k "${BASE_URL}/api/folders" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" | jq -r '.data[] | select(.role=="inbox") | .id' | head -n1)
[ -n "${INBOX_ID}" ] || fail "Inbox folder not found"

MATCH=0
for i in 1 2 3 4 5 6; do
  curl -sS -k -X POST "${BASE_URL}/api/emails/sync" -H "Authorization: Bearer ${ACCESS_TOKEN}" >/dev/null
  MATCH=$(curl -sS -k -G "${BASE_URL}/api/emails" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    --data-urlencode "folder_id=${INBOX_ID}" \
    --data-urlencode "limit=100" | jq --arg s "${SUBJECT}" '[.data.items[] | select(.subject==$s)] | length')
  [ "${MATCH}" -gt 0 ] && break
  sleep 5
done

DETAIL=$(curl -sS -k "${BASE_URL}/api/emails/${EMAIL_ID}" -H "Authorization: Bearer ${ACCESS_TOKEN}")
DELIVERY_STATUS=$(echo "${DETAIL}" | jq -r '.data.delivery_status // .delivery_status // "unknown"')
DELIVERY_ERROR=$(echo "${DETAIL}" | jq -r '.data.delivery_error // .delivery_error // ""')

echo "BASE_URL=${BASE_URL}"
echo "ADMIN_EMAIL=${ADMIN_EMAIL}"
echo "SENT_EMAIL_ID=${EMAIL_ID}"
echo "SENT_DELIVERY_STATUS=${DELIVERY_STATUS}"
echo "SENT_DELIVERY_ERROR=${DELIVERY_ERROR}"
echo "INBOX_ID=${INBOX_ID}"
echo "SUBJECT=${SUBJECT}"
echo "INBOX_MATCH_COUNT=${MATCH}"

[ "${MATCH}" -gt 0 ] || fail "Close-loop failed: inbox not found subject ${SUBJECT}"
log "Close-loop success"
