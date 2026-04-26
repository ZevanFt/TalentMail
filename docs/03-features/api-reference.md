# TalentMail Open API Reference

> Version: v2.0 | Auth: API Key (Bearer Token) | Base URL: `https://mail.example.com/api`

TalentMail provides a REST API for external systems to interact with temporary mailboxes. Common use cases:

- **CI/CD pipelines**: Create temp mailbox -> trigger signup -> poll for verification code -> complete registration
- **Automated testing**: Receive and verify email content in E2E tests
- **Bot integrations**: Monitor specific mailboxes for incoming emails
- **Third-party services**: Use TalentMail as an email verification backend

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [API Key Management](#2-api-key-management)
3. [Temp Mailbox API](#3-temp-mailbox-api)
4. [Error Handling](#4-error-handling)
5. [Rate Limiting](#5-rate-limiting)
6. [Quick Start Example](#6-quick-start-example)

---

## 1. Authentication

All automation API endpoints require an **API Key** passed as a Bearer token:

```
Authorization: Bearer tm_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Getting an API Key

1. Log in to TalentMail web UI
2. Go to **Settings** -> **API Keys**
3. Click **Create API Key**
4. Select required scopes (permissions)
5. Copy the key (shown **only once**)

### Key Format

- Prefix: `tm_` (configurable)
- Length: 43+ characters
- Storage: Only SHA-256 hash is stored server-side
- Example: `tm_A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8S9t0U1v2`

### Available Scopes

| Scope | Description |
|-------|-------------|
| `temp_mailbox:create` | Create new temporary mailboxes |
| `temp_mailbox:read` | List and view temporary mailboxes |
| `temp_mailbox:extend` | Extend mailbox expiry time |
| `temp_mailbox:restore` | Restore expired (recoverable) mailboxes |
| `temp_email:read` | Read emails in temporary mailboxes |
| `temp_code:read` | Extract verification codes from emails |

---

## 2. API Key Management

These endpoints use **JWT authentication** (logged-in user), not API Key auth.

### Create API Key

```
POST /api/api-keys/
```

**Request Body:**
```json
{
  "description": "CI/CD pipeline key",
  "scopes": ["temp_mailbox:create", "temp_email:read", "temp_code:read"],
  "expires_in_days": 90,
  "rate_limit_per_minute": 120
}
```

**Response (201):**
```json
{
  "api_key": "tm_A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8S9t0U1v2",
  "key": {
    "id": 1,
    "key_prefix": "tm_A1b2C3d4E5f6",
    "description": "CI/CD pipeline key",
    "scopes": ["temp_mailbox:create", "temp_email:read", "temp_code:read"],
    "rate_limit_per_minute": 120,
    "created_at": "2026-04-26T10:00:00Z",
    "expires_at": "2026-07-25T10:00:00Z",
    "last_used_at": null,
    "revoked_at": null
  }
}
```

> **Warning**: The `api_key` field is returned **only once**. Store it securely.

### List API Keys

```
GET /api/api-keys/?page=1&limit=20
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "key_prefix": "tm_A1b2C3d4E5f6",
      "description": "CI/CD pipeline key",
      "scopes": ["temp_mailbox:create", "temp_email:read", "temp_code:read"],
      "rate_limit_per_minute": 120,
      "created_at": "2026-04-26T10:00:00Z",
      "expires_at": "2026-07-25T10:00:00Z",
      "last_used_at": "2026-04-26T12:30:00Z",
      "revoked_at": null
    }
  ],
  "total": 1
}
```

### Revoke API Key

```
DELETE /api/api-keys/{key_id}
```

**Response (200):**
```json
{
  "status": "success",
  "message": "API Key 已撤销"
}
```

### Audit Logs

```
GET /api/api-keys/audit/logs?page=1&limit=50
```

Returns a log of all API key usage including allowed/denied requests with IP, method, path, and timestamps.

---

## 3. Temp Mailbox API

All endpoints below use **API Key authentication**.

### 3.1 Create Temp Mailbox

```
POST /api/automation/temp-mailboxes
Authorization: Bearer tm_xxxxx
Idempotency-Key: unique-request-id-123  (optional)
```

**Required scope**: `temp_mailbox:create`

**Request Body:**
```json
{
  "prefix": "test-signup",
  "purpose": "E2E signup test",
  "auto_verify_codes": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prefix` | string | No | Email prefix (max 64 chars). Random if omitted. |
| `purpose` | string | No | Description (max 200 chars) |
| `auto_verify_codes` | bool | No | Enable verification code extraction (default: true) |

**Response (201):**
```json
{
  "status": "success",
  "message": "临时邮箱创建成功",
  "mailbox": {
    "id": 42,
    "email": "test-signup@example.com",
    "purpose": "E2E signup test",
    "auto_verify_codes": true,
    "is_active": true,
    "status": "active",
    "created_at": "2026-04-26T10:00:00Z",
    "expires_at": "2026-04-27T10:00:00Z",
    "recovery_until": "2026-05-07T10:00:00Z",
    "unread_count": 0
  }
}
```

**Idempotency**: If `Idempotency-Key` header is provided and a mailbox with the same key already exists, the existing mailbox is returned instead of creating a duplicate.

### 3.2 List Temp Mailboxes

```
GET /api/automation/temp-mailboxes?page=1&limit=20
Authorization: Bearer tm_xxxxx
```

**Required scope**: `temp_mailbox:read`

**Response:**
```json
{
  "items": [
    {
      "id": 42,
      "email": "test-signup@example.com",
      "purpose": "E2E signup test",
      "is_active": true,
      "status": "active",
      "created_at": "2026-04-26T10:00:00Z",
      "expires_at": "2026-04-27T10:00:00Z",
      "unread_count": 3
    }
  ],
  "total": 1
}
```

### 3.3 Get Mailbox Emails

```
GET /api/automation/temp-mailboxes/{mailbox_id}/emails?include_body=true&page=1&limit=20
Authorization: Bearer tm_xxxxx
```

**Required scope**: `temp_email:read`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_body` | bool | false | Include full email body (body_text + body_html) |
| `page` | int | 1 | Page number |
| `limit` | int | 20 | Items per page |

**Response:**
```json
{
  "items": [
    {
      "id": 1001,
      "sender": "noreply@github.com",
      "subject": "Your verification code is 847291",
      "received_at": "2026-04-26T10:05:00Z",
      "is_read": false,
      "body_text": "Your verification code is 847291. It expires in 10 minutes.",
      "body_html": "<p>Your verification code is <strong>847291</strong>...</p>",
      "verification_code": "847291"
    }
  ],
  "total": 1
}
```

> `verification_code` is automatically extracted when `auto_verify_codes` is enabled on the mailbox.

### 3.4 Get Latest Verification Code

```
GET /api/automation/temp-mailboxes/{mailbox_id}/codes/latest
Authorization: Bearer tm_xxxxx
```

**Required scope**: `temp_code:read`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sender` | string | - | Filter by sender email (substring match) |
| `subject` | string | - | Filter by subject (substring match) |
| `within_minutes` | int | 10 | Only look at emails received within this window |
| `unread_only` | bool | true | Only consider unread emails |

**Response (200):**
```json
{
  "mailbox_id": 42,
  "mailbox_email": "test-signup@example.com",
  "email_id": 1001,
  "sender": "noreply@github.com",
  "subject": "Your verification code is 847291",
  "received_at": "2026-04-26T10:05:00Z",
  "code": "847291"
}
```

**Response (404) - No code found:**
```json
{
  "detail": "未找到匹配的验证码"
}
```

**Typical polling pattern:**
```bash
# Poll every 3 seconds for up to 60 seconds
for i in $(seq 1 20); do
  CODE=$(curl -s -H "Authorization: Bearer $API_KEY" \
    "$BASE_URL/api/automation/temp-mailboxes/$MAILBOX_ID/codes/latest?within_minutes=5" \
    | jq -r '.code // empty')
  if [ -n "$CODE" ]; then
    echo "Got code: $CODE"
    break
  fi
  sleep 3
done
```

### 3.5 Extend Mailbox

```
POST /api/automation/temp-mailboxes/{mailbox_id}/extend
Authorization: Bearer tm_xxxxx
```

**Required scope**: `temp_mailbox:extend`

**Request Body:**
```json
{
  "hours": 24
}
```

**Response:**
```json
{
  "status": "success",
  "message": "续期成功",
  "mailbox": {
    "id": 42,
    "email": "test-signup@example.com",
    "expires_at": "2026-04-28T10:00:00Z",
    "status": "active"
  }
}
```

### 3.6 Restore Expired Mailbox

```
POST /api/automation/temp-mailboxes/{mailbox_id}/restore
Authorization: Bearer tm_xxxxx
```

**Required scope**: `temp_mailbox:restore`

Only works on mailboxes in `expired_recoverable` status (within 10-day recovery window).

**Response:**
```json
{
  "status": "success",
  "message": "恢复成功",
  "mailbox": {
    "id": 42,
    "email": "test-signup@example.com",
    "status": "active",
    "expires_at": "2026-04-27T10:00:00Z"
  }
}
```

---

## 4. Error Handling

All errors follow a consistent format:

```json
{
  "detail": "Error message here"
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (invalid parameters) |
| 401 | Unauthorized (invalid/expired/revoked API key) |
| 403 | Forbidden (missing required scope) |
| 404 | Not Found |
| 409 | Conflict (e.g., quota exceeded) |
| 413 | Payload Too Large |
| 422 | Validation Error (Pydantic) |
| 429 | Too Many Requests (rate limited) |
| 500 | Internal Server Error |

### Common Error Examples

**Invalid API Key:**
```json
// 401
{ "detail": "API Key 无效" }
```

**Revoked API Key:**
```json
// 401
{ "detail": "API Key 已被撤销" }
```

**Missing Scope:**
```json
// 403
{ "detail": "Missing scopes: temp_mailbox:create" }
```

**Rate Limited:**
```json
// 429
{ "detail": "Rate limit exceeded for this API key" }
```

---

## 5. Rate Limiting

- Default: **120 requests/minute** per API key (configurable per key, 1-10,000)
- Rate limit window: sliding 1-minute window
- Rate limit is enforced **per API key**, not per IP
- Response header: rate limit status is logged in audit logs

When rate limited, wait until the next minute window before retrying.

---

## 6. Quick Start Example

### Complete E2E Flow: Sign Up Verification

```python
import requests
import time

BASE_URL = "https://mail.example.com/api"
API_KEY = "tm_your_api_key_here"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# Step 1: Create a temp mailbox
resp = requests.post(f"{BASE_URL}/automation/temp-mailboxes", 
    headers=HEADERS,
    json={"prefix": "e2e-test", "auto_verify_codes": True}
)
mailbox = resp.json()["mailbox"]
email = mailbox["email"]
mailbox_id = mailbox["id"]
print(f"Created: {email}")

# Step 2: Use this email to register on a third-party service
# ... your_app.register(email=email) ...

# Step 3: Poll for the verification code
code = None
for attempt in range(20):
    resp = requests.get(
        f"{BASE_URL}/automation/temp-mailboxes/{mailbox_id}/codes/latest",
        headers=HEADERS,
        params={"within_minutes": 5}
    )
    if resp.status_code == 200:
        code = resp.json()["code"]
        print(f"Got code: {code}")
        break
    time.sleep(3)

# Step 4: Complete registration with the code
if code:
    # ... your_app.verify(email=email, code=code) ...
    print("Registration complete!")
```

### cURL Examples

```bash
# Set your API key
export API_KEY="tm_your_api_key_here"
export BASE="https://mail.example.com/api"

# Create temp mailbox
curl -X POST "$BASE/automation/temp-mailboxes" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prefix":"demo","auto_verify_codes":true}'

# List mailboxes
curl "$BASE/automation/temp-mailboxes" \
  -H "Authorization: Bearer $API_KEY"

# Get latest verification code
curl "$BASE/automation/temp-mailboxes/42/codes/latest?within_minutes=10" \
  -H "Authorization: Bearer $API_KEY"

# Get emails (with body)
curl "$BASE/automation/temp-mailboxes/42/emails?include_body=true" \
  -H "Authorization: Bearer $API_KEY"

# Extend mailbox by 24 hours
curl -X POST "$BASE/automation/temp-mailboxes/42/extend" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"hours":24}'
```

---

## Mailbox Lifecycle

```
     Create
       |
       v
   [active] ----expires_at----> [expired_recoverable] ----recovery_until----> [purged]
       |                                  |
       |  extend (resets TTL)             |  restore (reactivates)
       |<---------------------------------|
```

| State | Can receive email | Can read email | Can extend | Can restore |
|-------|:-:|:-:|:-:|:-:|
| `active` | Yes | Yes | Yes | - |
| `expired_recoverable` | No | Yes | Yes | Yes |
| `purged` | No | No | No | No |

- **Default TTL**: 24 hours
- **Recovery window**: 10 days after expiry
- **Cleanup**: Background task runs every 10 minutes

---

## Verification Code Extraction

TalentMail auto-extracts verification codes from email content using these patterns:

| Pattern | Example Match |
|---------|--------------|
| `验证码[是]?[：:\s]*CODE` | "您的验证码是 847291" |
| `verification code[:\s]*CODE` | "Your verification code: 847291" |
| `code[:\s]+CODE` | "Code: A8B2C4" |
| `\d{4,8}` (standalone) | "847291" (4-8 digit standalone numbers) |

Supported code formats: 4-8 character alphanumeric (digits and/or letters).
