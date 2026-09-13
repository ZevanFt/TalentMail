# Auth Center 对接说明

TalentMail **不是** OAuth 认证中心。  
它是 **Auth Center 的业务客户端（Relying Party）**：用户在认证中心登录，授权后跳回 TalentMail 建立本地会话。

```
┌──────────┐   1. /login?client_id&redirect_uri&state   ┌────────────────┐
│  用户     │ ─────────────────────────────────────────► │  Auth Center   │
│  浏览器   │ ◄───────────────────────────────────────── │  (你的服务)     │
└────┬─────┘   2. 同意页 → authorize → 302 redirect?code  └────────────────┘
     │
     │ 3. 前端把 code POST 给 TalentMail
     ▼
┌──────────────┐  4. POST /api/sso/token                ┌────────────────┐
│  TalentMail  │ ─────────────────────────────────────► │  Auth Center   │
│  (本项目)     │ ◄───────────────────────────────────── │                │
└──────────────┘  5. { user: UserPayload }               └────────────────┘
     │
     └─ 6. 关联/创建本地用户 → 签发 TalentMail JWT
```

## 1. 双方职责

| 角色 | 系统 | 负责 |
|------|------|------|
| 认证中心 | Auth Center `:8000` | 账号、密码、MFA、应用注册、授权码 |
| 业务站 | TalentMail | 邮箱业务、本地会话 JWT、邮件/日历等 |

## 2. Auth Center 需要做的事

1. **注册应用**（管理端 `/api/admin/apps`）
   - `client_id`：例如 `talentmail`
   - `allowed_redirect_uris`：必须包含  
     `https://mail.example.com/auth/sso/callback`
2. 把 `client_id` / `client_secret` 给到 TalentMail 的 `.env`

## 3. TalentMail 配置

```bash
SSO_ENABLED=true
SSO_AUTH_CENTER_URL=http://127.0.0.1:8000   # 不含尾斜杠；生产用 https
SSO_CLIENT_ID=talentmail
SSO_CLIENT_SECRET=...
SSO_REDIRECT_URI=https://mail.example.com/auth/sso/callback
```

前端回调页：`/auth/sso/callback`（已有）  
登录按钮：`GET /api/auth/sso/status` → `GET /api/auth/sso/login` 拿 `redirect_url`

## 4. 用到的 Auth Center 接口

| 接口 | TalentMail 用途 |
|------|----------------|
| `POST /api/sso/token` | 授权码换用户信息（登录回调） |
| `POST /api/sso/introspect` | 校验中心侧会话是否仍有效（单点登出/关键操作） |
| 管理端 `/api/admin/apps` | 人工注册客户端（不在 TalentMail 调） |

**请求/响应对齐情况（已核对 OpenAPI）：**

`POST /api/sso/token`  
请求：`{ client_id, client_secret, redirect_uri, code }`  
响应：`{ user: { id, username, display_name, mfa_enabled, is_admin?, email_verified? } }`

`POST /api/sso/introspect`  
请求：`{ client_id, client_secret?, username }`  
响应：`{ active, mfa_enabled, display_name }`

## 5. TalentMail 已提供

| 路径 | 说明 |
|------|------|
| `GET /api/auth/sso/status` | 是否启用 SSO |
| `GET /api/auth/sso/login` | 返回跳转认证中心的 URL |
| `POST /api/auth/sso/callback` | 用 code 换用户、建本地会话 |
| `POST /api/auth/sso/introspect` | 业务侧查中心会话（可选单点登出） |

## 6. 注意

- Auth Center 登录页地址由 **你的前端** 决定；TalentMail 默认拼的是  
  `{SSO_AUTH_CENTER_URL}/login?client_id=...&redirect_uri=...&state=...`  
  若你实际路径是 `/sso/login` 等，改 `SSO_AUTH_CENTER_URL` 或后续加 `SSO_LOGIN_PATH`。
- SSO 新用户会在 mailserver 自动建邮箱（随机邮件密码，Web 仍走 JWT）。
- CalDAV Basic Auth 对纯 SSO 用户无效，需先在 Web 设密码。

## 7. 相关代码

- `backend/api/sso.py` — 客户端回调与 introspect
- `backend/utils/sso_email.py` — 邮箱规范化
- `frontend/app/pages/auth/sso/callback.vue` — 前端回调
- `.env.example` — SSO 配置项
