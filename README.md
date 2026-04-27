<p align="center">
  <img src="logo.png" alt="Talenting Logo" width="400">
</p>

<h1 align="center">TalentMail</h1>

<p align="center">
  <strong>Modern Self-Hosted Email Platform</strong>
</p>

<p align="center">
  Nuxt 4 + FastAPI + PostgreSQL + docker-mailserver
</p>

<p align="center">
  <code>v2.0.0</code>&nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="docs/">Documentation</a>&nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="docs/03-features/api-reference.md">API Reference</a>&nbsp;&nbsp;|&nbsp;&nbsp;
  <a href="docs/07-reference/changelog.md">Changelog</a>
</p>

---

## Features

### Core Email
- Full SMTP/IMAP with attachments, HTML, BCC, scheduled send & auto-save drafts
- Folder management (inbox, sent, drafts, trash, archive, spam, custom)
- Full-text search with advanced filters (sender, recipient, date range, has attachment, starred, read)
- Email threading via In-Reply-To/References headers
- Email tracking pixels with open count, device analytics, resend on failure
- Email export as EML/PDF, print view
- Bulk operations (move, delete, archive, star, read) with Gmail-style undo
- **Email import**: batch import `.eml` / `.mbox` files with smart deduplication (by Message-ID)

### Cloud Drive
- File upload, download, sharing (public link with optional password & expiry)
- **Folder system**: 5-level nested folders, create / rename / move / recursive delete
- **File preview**: inline preview for images (JPEG/PNG/GIF/WebP), PDF, and text/code files
- Per-user storage quota management
- Shared file access with password protection

### Calendar
- Month-view calendar grid with event color coding (8 preset colors)
- Event CRUD: title, start/end time, all-day toggle, location, description, reminders
- **.ics import**: upload standard iCalendar files to batch-create events
- Navigate between months with event-per-day summary

### Temp Mailbox & Automation API
- Create disposable email addresses with auto-expiry (24h default, 10-day recovery)
- Auto-extract verification codes (4-8 chars, Chinese + English patterns)
- **REST API with API Key auth** for external automation (CI/CD, testing, bots)
- Idempotent creation via `Idempotency-Key` header
- Full audit logging with per-key rate limiting & scope-based permissions
- See [API Reference](docs/03-features/api-reference.md) for complete documentation

### Security & Encryption
- JWT auth with refresh tokens & token type enforcement
- TOTP two-factor authentication (2FA) with **backup recovery codes**
- **PGP end-to-end encryption**: client-side key generation (OpenPGP.js), public key exchange, encrypt-on-send, decrypt-on-read
- Login device/session management with remote revoke
- Password strength enforcement (8+ chars, upper/lower/digit)
- Rate limiting on all sensitive endpoints (login, register, send, upload, tracking)
- SSRF-protected image proxy for remote email images
- Constant-time verification code comparison (`hmac.compare_digest`)
- XSS sanitization (DOMPurify frontend + HTML whitelist backend)
- Encrypted external account passwords (AES)

### External Accounts
- **IMAP sync**: connect external email accounts (Gmail, Outlook, etc.) and sync messages on a 5-minute interval
- **Alias sending**: send emails as an external account's address
- Encrypted credential storage (AES)

### Workflow & Automation
- Visual drag-and-drop workflow editor (Vue Flow)
- 41 node handler types (email ops, HTTP, notifications, conditions, loops)
- BFS graph traversal execution engine with version history
- Rule engine with trigger-condition-action automation (13 action types)
- Template marketplace with pre-built workflows
- System workflows (welcome email, password change notification, etc.)

### Contacts
- Contact management with avatar, notes, and tags
- **Import/Export**: vCard (`.vcf`) and CSV bidirectional import & export
- Autocomplete chip input in compose

### Compose Templates
- User-defined compose templates for quick email drafting
- Variable placeholders with preview & one-click insertion
- Separate from system email templates (admin-managed)

### User Experience
- Glassmorphism UI with customizable background skins & transparency
- Dark/light theme with system auto-detect
- PWA support (installable desktop app)
- Full keyboard shortcuts (`?` to view help)
- WebSocket real-time notifications (new email, snooze wakeup)
- Responsive design (desktop + mobile)
- Rich text editor (TipTap with 13 extensions)
- Contact autocomplete with chip input
- Loading skeletons, undo toasts, auto-save indicators

### Administration
- User management (create, delete with full cascade, role assignment)
- Invite code system for controlled growth
- Subscription & billing with redemption codes
- Email template editor with variable insertion & test send
- Blocklist/whitelist management
- Reserved email prefix management
- System changelog publishing

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Frontend** | Nuxt.js | 4.x (Vue 3.5, TypeScript) |
| **Frontend** | Tailwind CSS | via @nuxtjs/tailwindcss 6.x |
| **Frontend** | Rich Editor | TipTap 3.x (13 extensions) |
| **Frontend** | Workflow Editor | Vue Flow 1.48+ |
| **Frontend** | PWA | @vite-pwa/nuxt |
| **Frontend** | PGP Encryption | OpenPGP.js 6.x (client-side E2E) |
| **Backend** | FastAPI | 0.122 (Python 3.12) |
| **Backend** | SQLAlchemy | 2.0 + Alembic migrations |
| **Backend** | Pydantic | V2 (2.12+) |
| **Backend** | LMTP | aiosmtpd 1.4+ |
| **Backend** | Calendar | icalendar 5.x (.ics parsing) |
| **Database** | PostgreSQL | 15 (full-text search, tsvector) |
| **Mail Server** | docker-mailserver | Postfix + Dovecot + Fail2Ban |
| **Reverse Proxy** | Caddy | Alpine (auto HTTPS) |
| **Runtime** | Docker Compose | v2 |

---

## Quick Start

### Requirements
- Docker & Docker Compose v2
- Git

### Development

```bash
# Clone & configure
git clone <repository-url>
cd talentmail
cp .env.example .env
nano .env          # Set SECRET_KEY, POSTGRES_PASSWORD, etc.

# Start (recommended)
chmod +x dev.sh && ./dev.sh

# Or manually
docker compose -f docker-compose.dev.yml up -d --build

# Initialize database (first time only)
docker compose -f docker-compose.dev.yml exec backend python -m initial.initial_data
```

| Service | URL |
|---------|-----|
| Web App | https://mail.talenting.test:18443 |
| Frontend | http://127.0.0.1:13000 |
| Backend API | http://127.0.0.1:18000 |
| API Docs (Swagger) | http://127.0.0.1:18000/docs |

**Default admin**: `admin@talenting.test` / `adminpassword`

### Production

```bash
# 1. Configure
cp .env.example .env && nano .env
nano config.json    # Set baseDomain, etc.

# 2. Deploy
chmod +x deploy.sh
bash deploy.sh --migrate

# 3. Configure reverse proxy (Caddy)
# See config/caddy/Caddyfile.prod for upstream config
```

**Deploy modes**: `--migrate` (incremental, recommended) | `--fresh` (wipe & rebuild) | `--auto` (detect) | `--doctor` (diagnose only)

### DNS Configuration

| Type | Name | Value | Proxy | Notes |
|------|------|-------|-------|-------|
| A | `mail` | Server IP | Proxied | Web app |
| A | `maillink` | Server IP | **DNS Only** | Mail server (must NOT be proxied) |
| MX | `@` | `maillink.example.com` | - | Priority 10 |
| TXT | `@` | `v=spf1 mx ~all` | - | SPF record |

---

## Configuration

### config.json (Single Source of Truth)

```json
{
  "currentEnvironment": "production",
  "environments": {
    "production": {
      "baseDomain": "example.com",
      "webPrefix": "mail",
      "mailServerPrefix": "maillink"
    }
  }
}
```

### Environment Variables (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | JWT signing key (`openssl rand -hex 32`) | Yes |
| `POSTGRES_PASSWORD` | Database password | Yes |
| `ADMIN_PASSWORD` | Initial admin password | Yes |
| `DEFAULT_MAIL_PASSWORD` | Mail account default password | Yes |
| `ENCRYPTION_KEY` | External account password encryption key | Yes |
| `MAIL_MASTER_PASSWORD` | Dovecot master user password | Yes |
| `ENABLE_INTERNAL_LMTP` | Use built-in LMTP server (default: `false`) | No |

---

## Project Structure

```
talentmail/
├── backend/                 # FastAPI backend (Python 3.12)
│   ├── api/                 # 33 API router modules
│   ├── core/                # Config, security, mail, LMTP, IMAP sync
│   ├── crud/                # Database CRUD operations
│   ├── db/models/           # 54 SQLAlchemy models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── initial/             # DB seed data (admin, templates, workflows)
│   ├── utils/               # Rate limiters, helpers
│   └── alembic/             # 44 database migrations
├── frontend/                # Nuxt 4 frontend
│   └── app/
│       ├── components/      # 53 Vue components (email/, common/, settings/, calendar/)
│       ├── pages/           # 14 pages
│       ├── composables/     # useApi, useEmails, useToast, usePGP, etc.
│       └── layouts/         # Default + blank layouts
├── config/                  # Infrastructure configs
│   ├── caddy/               # Caddyfile (dev + prod)
│   └── mail/                # docker-mailserver (Dovecot SQL auth, etc.)
├── docs/                    # 7-section documentation
├── scripts/                 # Helper scripts
├── config.json              # Domain & feature configuration
├── deploy.sh                # Production deployment script
└── docker-compose.yml       # Production compose (5 services)
```

---

## API Overview

### Public Endpoints (No Auth)
| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check (API + DB) |
| `GET /api/readiness` | Readiness probe |
| `GET /api/liveness` | Liveness probe |
| `GET /api/track/open/{pixel_id}` | Email tracking pixel (returns 1x1 GIF) |

### Automation API (API Key Auth)
| Endpoint | Scope | Description |
|----------|-------|-------------|
| `POST /api/automation/temp-mailboxes` | `temp_mailbox:create` | Create temp mailbox |
| `GET /api/automation/temp-mailboxes` | `temp_mailbox:read` | List temp mailboxes |
| `GET /api/automation/temp-mailboxes/{id}/emails` | `temp_email:read` | Get mailbox emails |
| `GET /api/automation/temp-mailboxes/{id}/codes/latest` | `temp_code:read` | Get latest verification code |
| `POST /api/automation/temp-mailboxes/{id}/extend` | `temp_mailbox:extend` | Extend mailbox TTL |
| `POST /api/automation/temp-mailboxes/{id}/restore` | `temp_mailbox:restore` | Restore expired mailbox |

> Full API documentation with request/response examples: [docs/03-features/api-reference.md](docs/03-features/api-reference.md)

---

## Background Tasks

| Task | Interval | Purpose |
|------|----------|---------|
| IMAP Sync | 30s | Sync mail from Dovecot (users + temp mailboxes) |
| External Account Sync | 5min | IMAP sync from connected external accounts |
| Scheduled Send | 60s | Send emails with `scheduled_send_at` |
| Snooze Check | 60s | Wake snoozed emails past due time |
| Temp Mailbox Cleanup | 10min | Lifecycle transitions + purge |
| Session Cleanup | 24h | Remove sessions inactive >30 days |
| Orphan Attachment Cleanup | 1h | Remove unlinked uploads >24h |

---

## Troubleshooting

```bash
# Check service status
docker compose ps

# View logs
docker compose logs -f backend
docker compose logs -f mailserver

# Migration diagnostics
bash deploy.sh --doctor

# Force reinitialize data
docker compose exec backend python -m initial.initial_data
```

See [docs/05-operations/troubleshooting.md](docs/05-operations/troubleshooting.md) for detailed guides.

---

## License

```
Copyright (c) 2025-2026 Talenting. All Rights Reserved.
Author: Zevan
```

<p align="center">
  <sub>Made with love by Zevan @ Talenting</sub>
</p>
