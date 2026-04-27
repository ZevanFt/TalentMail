# TalentMail 系统架构设计

## 概览

TalentMail 是一个自托管邮件平台，采用 5 服务 Docker Compose 架构，提供完整的邮件收发、自动化工作流、云盘、日历等功能。

## 服务拓扑

```
┌─────────────────────────────────────────────────────────┐
│                     Caddy (反向代理)                      │
│              自动 HTTPS (Let's Encrypt)                   │
│         :443 → frontend:3000 / backend:8000               │
└────────────┬──────────────────────┬─────────────────────┘
             │                      │
    ┌────────▼────────┐   ┌────────▼────────┐
    │   Frontend       │   │   Backend        │
    │   Nuxt 4 (SSR)   │   │   FastAPI        │
    │   :3000           │   │   :8000          │
    └──────────────────┘   └────────┬─────────┘
                                    │
                   ┌────────────────┼────────────────┐
                   │                │                 │
          ┌────────▼────┐  ┌───────▼──────┐  ┌──────▼───────┐
          │ PostgreSQL   │  │ Mailserver   │  │ LMTP Server  │
          │ :5432        │  │ Postfix+     │  │ (内置 aio-   │
          │ 全文搜索     │  │ Dovecot      │  │  smtpd)      │
          └─────────────┘  │ :25/143/465/ │  └──────────────┘
                           │  587/993      │
                           └──────────────┘
```

## 请求流

### Web 请求

```
Browser → Caddy (:443) → Frontend (:3000)  [页面渲染]
Browser → Caddy (:443) → Backend (:8000)   [API 调用, /api/*)
```

### 邮件接收链路

```
外部 MTA → Postfix (:25) → LMTP → Backend 解析 → PostgreSQL 入库
                                                    ↓
                                          WebSocket 推送通知 → 前端实时显示
```

### 邮件发送链路

```
前端 ComposePanel → Backend API → Postfix (relay) → 目标 MTA
                                                      ↓
                                              SPF/DKIM 签名验证
```

### IMAP 同步

```
Backend 定时任务 (30s)
  → Dovecot IMAP (:143)
  → 增量同步 (基于 UID)
  → PostgreSQL 更新
```

### 外部账户同步

```
Backend 定时任务 (5min)
  → 外部 IMAP 服务器 (Gmail/Outlook/...)
  → AES 解密凭据
  → 增量同步到本地数据库
```

## WebSocket 通信

Backend 通过 WebSocket 推送实时事件：

| 事件类型 | 触发场景 |
|---------|---------|
| `new_email` | LMTP 收到新邮件 |
| `snooze_wakeup` | 贪睡邮件到期唤醒 |
| `notification` | 系统通知 |

客户端连接: `wss://mail.example.com/api/ws?token=<jwt>`

## 数据库设计

- **PostgreSQL 15** 作为唯一数据存储
- **54 个 SQLAlchemy 模型**，覆盖用户、邮件、附件、联系人、工作流、日历等
- **全文搜索**: `tsvector` 索引 + `ts_query` 中英文搜索
- **44 个 Alembic 迁移** 管理 schema 变更

详见 [数据库设计文档](./database-schema.md)

## 安全架构

### 认证层

```
JWT Access Token (15min) + Refresh Token (7d)
  → 类型强校验 (access/refresh 不可互换)
  → 设备/会话管理 + 远程登出
```

### 加密层

| 层级 | 技术 | 说明 |
|------|------|------|
| 传输加密 | TLS 1.3 (Caddy) | 全站 HTTPS |
| 邮件加密 | OpenPGP.js (客户端) | E2E 加密，服务端不触碰明文 |
| 凭据加密 | AES (服务端) | 外部账户密码存储 |
| 密码存储 | bcrypt | 用户密码哈希 |

### 防护措施

- 所有敏感端点 Rate Limiting
- SSRF 防护的图片代理
- DOMPurify + HTML 白名单双重 XSS 防护
- `hmac.compare_digest` 防时序攻击
- `X-Content-Type-Options: nosniff` 防 MIME 嗅探

## 文件存储

```
/app/uploads/
├── attachments/     # 邮件附件
├── drive/           # 云盘文件
├── avatars/         # 用户头像
└── temp/            # 临时文件
```

所有文件通过 Docker volume 持久化，上传时进行 MIME 类型校验和大小限制。

## 配置管理

- **`config.json`**: 域名、环境、功能开关（单一数据源）
- **`.env`**: 密钥、密码等敏感配置
- **`deploy.sh`**: 从 config.json 自动生成 `.env.domains`

详见 [API 设计文档](./api-design.md)
