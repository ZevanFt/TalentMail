# Changelog

All notable changes to this project will be documented in this file.

Based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
adhering to [Semantic Versioning](https://semver.org/).

---

## [2.1.0] - 2026-04-27

### Highlights
- 4 rounds of deep security audit + performance optimization for 2 vCPU / 4GB RAM deployment
- 6 critical security vulnerabilities fixed (2FA bypass, session revocation, Docker socket, attachment XSS, mail TLS)
- Background task registry with auto-restart and health monitoring
- GitHub Actions CI pipeline with ruff + pytest + nuxt build

### Security (P0 Critical)
- **2FA bypass fixed**: `2fa_pending` tokens now use dedicated `token_type` instead of reusing `access`, preventing them from being used as regular API tokens during the 5-minute window
- **Session revocation enforced**: `get_current_user()` now validates `UserSession.is_active` in DB on every request — revoking a session actually blocks the token immediately
- **Refresh token session propagation**: refreshed access tokens now carry forward the `session_id`, ensuring revocation works after token refresh
- **Attachment XSS prevention**: force `Content-Disposition: attachment` + `X-Content-Type-Options: nosniff`, only safe MIME types (images, PDF, text) allowed inline
- **Docker socket removed**: eliminated `/var/run/docker.sock` mount from both backend and mailserver containers, closing container-escape-to-host attack vector
- **Mail TLS enforced**: Dovecot `disable_plaintext_auth=yes`, Postfix `smtpd_tls_auth_only=yes`, submission port requires encryption
- **Hardcoded password removed**: `scripts/reset_passwords.py` now requires `RESET_PASSWORD` env var (8-char minimum)
- **scrypt upgrade**: password hashing parameter n upgraded from 2^14 to 2^16 with transparent rehash on login (backward compatible)

### Performance
- **2V4G server optimization**: Docker memory allocation reduced from 3.75GB to 2.4GB (ClamAV disabled, per-service limits tuned)
- **IMAP incremental sync**: `SEARCH ALL` replaced with `SEARCH SINCE` (7-day window), reducing IMAP traffic by orders of magnitude on large mailboxes
- **IMAP attachment preservation**: switched from `get_email_body()` to `get_email_body_and_attachments()`, matching LMTP behavior — attachments were previously silently dropped during IMAP sync
- **Drive upload crash fixed**: `len(content)` called after `content=None` replaced with `total_size` from streaming accumulator
- **IMAP sync non-blocking**: `sync_all_mailboxes()` now runs in `asyncio.to_thread()`, no longer blocking the event loop for 5-15 seconds every 30 seconds
- **PostgreSQL tuned**: `shared_buffers=192MB`, `effective_cache_size=512MB`, `work_mem=8MB`, `max_connections=30`
- **DB connection pool reduced**: 10+20 connections down to 5+10 (single worker doesn't need 30)
- **Snooze N+1 fixed**: replaced per-email folder query loop with single JOIN query
- **Orphan cleanup batched**: unlimited `.all()` replaced with `while True: ...limit(100)` batches
- **Drive upload streaming**: file content no longer accumulated in memory, streamed directly to disk
- **Composite indexes**: `blocked_senders(user_id, email)`, `trusted_senders(user_id, email)`, `verification_codes(email, purpose, is_used, expires_at)`
- **Uvicorn production flags**: `--timeout-keep-alive 65 --limit-concurrency 50 --limit-max-requests 10000`
- **Health check lightweight**: Python interpreter replaced with `wget` for Docker healthcheck

### Observability
- **Background task registry**: 8 bare `asyncio.create_task()` calls replaced with centralized `_register_task()` that tracks heartbeats and auto-restarts crashed tasks after 5-second delay
- **Health endpoint enhanced**: `/api/health` now returns per-task status (`running`, `last_heartbeat_ago_sec`) and overall `healthy`/`degraded` status based on task liveness
- **Shutdown simplified**: 80 lines of repetitive if-cancel-await blocks replaced with a 6-line unified loop

### Quality & CI
- **GitHub Actions CI**: 3 parallel jobs (ruff lint, pytest, nuxt build) with pip/npm caching
- **Pre-commit hooks**: ruff check+format, trailing-whitespace, end-of-file-fixer, check-yaml, check-added-large-files
- **Ruff config**: `pyproject.toml` with E/F/W/I rules, 120-char line length, isort with known-first-party
- **Pytest config**: asyncio auto mode, testpaths set

### Hardening
- **Caddy CSP**: `Content-Security-Policy` header with strict `default-src 'self'` and `frame-ancestors 'none'`
- **Caddy access logging**: request logs to `/var/log/caddy/access.log` with rotation (50MB, keep 5)
- **CORS tightened**: `allow_headers` from wildcard to `["Authorization", "Content-Type", "Accept", "X-Requested-With"]`
- **asyncio deprecation**: `get_event_loop()` replaced with `get_running_loop()` for Python 3.12+ compatibility
- **Contact export capped**: limit 10,000 rows to prevent OOM on large datasets
- **User deletion disk cleanup**: attachments and drive files now removed from disk after DB cascade
- **Dovecot auth socket**: mode changed from 0777 to 0660 with proper user/group
- **Fail2Ban hardened**: `bantime=1h`, `maxretry=3`, `findtime=10m`
- **Dockerfile pins**: `python:3.12-slim-bookworm` and `mailserver:14.0` (was `:latest`)
- **Frontend Dockerfile**: `npm install` replaced with `npm ci`, `NODE_ENV=production` added
- **Console.log stripped**: esbuild `drop: ['console', 'debugger']` in production builds
- **Static asset caching**: Caddy `immutable` cache headers for `/_nuxt/*` hash-named files
- **Frontend devtools disabled**: Vue devtools and PWA dev service worker off in production
- **Nitro compression**: `compressPublicAssets: true` for pre-compressed static assets
- **deploy.sh**: pre-migration `pg_dump` backup + `pg_isready` polling (replaced `sleep 10`)
- **Rate limiting**: added `SlidingWindowLimiter` to 9 API modules (folders, tags, aliases, calendar, signatures, api_keys, contacts, blocklist, spam)

### auth-center (companion project)
- **SQLite WAL mode**: eliminates `database is locked` under concurrent reads/writes
- **PRAGMA tuning**: `foreign_keys=ON`, `synchronous=NORMAL`, `cache_size=-8000`, `busy_timeout=5000`
- **cleanup() race fix**: `_last_cleanup` moved from unprotected class variable to lock-guarded access
- **SPA path traversal**: `is_relative_to()` replaces incomplete `.parents` check
- **Rate limiter hardened**: `request.client.host` instead of trusting `X-Forwarded-For`
- **Graceful shutdown**: FastAPI lifespan context manager runs cleanup on SIGTERM
- **PM2 logging**: log rotation (50MB max), date format, error/out file split
- **scrypt upgrade**: n=2^14 to 2^16 with backward-compatible `verify_password` returning `tuple[bool, bool]`
- **6 SQLite indexes**: sessions, login_attempts, audit_logs, user_emails
- **cleanup() throttled**: 5-minute interval, avoiding 5 DELETE statements per request

---

## [2.0.0] - 2026-04-26

### Highlights
- 18 rounds of comprehensive improvements across security, performance, UX, and features
- Complete Open API with API Key authentication for external automation
- Gmail-style undo for delete/archive operations
- BCC support in compose panel
- Comprehensive documentation rewrite

### Added (Rounds 5-18)

**Features**
- BCC (blind carbon copy) field in email compose panel
- Gmail-style undo toast for delete and archive operations (8-second window)
- Contact autocomplete with chip/tag input mode and email validation
- Email detail print view with clean formatting
- Email thread/conversation view (same thread_id grouping)
- Loading skeleton for email detail view
- Auto-save draft indicator (saving/saved/error states)
- Verification code detection and one-click copy in email detail
- Desktop notification support for new emails
- Advanced email search with 7 filter criteria (sender, recipient, date range, attachment, starred, read, folder)
- Remote image proxy with SSRF protection and user-controllable loading
- Keyboard shortcuts system with `?` help dialog
- Automation temp mailbox API with API Key authentication
- Idempotent temp mailbox creation via `Idempotency-Key` header
- API Key management UI (create, list, revoke, audit logs)
- Per-API-key rate limiting and scope-based permissions
- Error pages (404, 500) with helpful navigation
- Request timeout handling with user-friendly messages
- Session expiry detection with auto-redirect to login

**Security**
- Cryptographic verification codes (`secrets.choice` + `hmac.compare_digest`)
- TOTP 2FA setup, verify, and disable
- Login device/session management with remote revoke
- Password strength enforcement (8+ chars, upper/lower/digit)
- Rate limiting on login, register, send email, file upload, tracking pixel, password reset
- SSRF protection for image proxy (blocks private IPs, link-local, loopback)
- JWT token type enforcement (access vs refresh token separation)
- PDF export XSS prevention (HTML whitelist sanitizer)
- Image proxy content-type whitelist (only allows image/*)
- Reset password no longer reveals user existence
- Tracking pixel rate limiting (10/pixel/minute)
- File upload rate limiting (10/user/minute)
- External account passwords encrypted with AES
- `.dockerignore` to prevent secrets from entering images
- Caddy security headers (X-Frame-Options, X-Content-Type-Options, etc.)

**Performance**
- Database covering index `(folder_id, is_purged, received_at)` + 11 single-column indexes
- Workflow execution `workflow_id` index
- N+1 query fixes (tags with email count, user admin list)
- All list endpoints converted to paginated `{items, total}` format
- Atomic download counter updates (prevents concurrent write loss)
- Full-text search query deduplication
- Email polling optimization (adaptive interval)
- Lazy loading for heavy settings components

**Data Integrity**
- User deletion now cascades to all associated data (folders, emails, attachments, tags, contacts, signatures, aliases, drive files, subscriptions, sessions)
- Fixed tracking pixel writing to non-existent Email model attributes
- Removed dead code paths and unused imports

**UX Improvements**
- Glassmorphism UI with customizable background skins
- Auto-save indicator for drafts (Loader2/CheckCircle/XCircle icons)
- Email detail loading skeleton (prevents white flash)
- Toast notifications with action buttons (undo pattern)
- Mobile responsive toolbar and compose panel
- Pydantic Field constraints on all API inputs (max_length, ge, le)

**Documentation**
- Complete README rewrite with feature list, tech stack, and API overview
- Open API Reference document (temp mailbox automation + API keys)
- Updated changelog from v0.9.0-beta through v2.0.0

### Fixed
- `register.vue`: `config` used before definition causing ReferenceError crash
- `Detail.vue`: Duplicate `const toast = useToast()` declaration
- `changelog.py`: Missing `timezone` import causing NameError
- Frontend API consumers adapted for paginated backend responses
- Consistent `validate_password_strength` used across all password endpoints
- `pool.py`: `random.choices` replaced with `secrets.choice` for consistency

---

## [1.5.0] - 2025-01-30

### Added
- PWA support (installable as desktop app)
- System changelog/update log feature
- Complete visual workflow system with Vue Flow editor
- Email template system 1.0

### Fixed
- System workflow creation issues
- Workflow list UI improvements

## [1.4.0] - 2025-01-20

### Added
- Workflow engine base version
- 34 predefined node types
- Visual flow editor
- 3 system preset workflows

### Improved
- Backend API performance optimization
- Frontend loading speed improvements

## [1.3.0] - 2025-01-10

### Added
- Email template management
- Markdown editor support
- Variable substitution engine
- Template preview

### Fixed
- Email attachment loss on send
- Folder sort order
- Search result pagination

## [1.2.0] - 2024-12-20

### Added
- Two-factor authentication (2FA/TOTP)
- Login device management
- Session management
- Email tracking (open tracking)

### Improved
- Login security enhancements
- Responsive UI optimizations
- Better error messages

### Fixed
- Password reset email delivery failures
- Timezone display errors

## [1.1.0] - 2024-12-01

### Added
- Temp mailbox pool system
- Temporary email creation
- Verification code auto-extraction
- Subscription billing system

### Improved
- Database query optimization
- Caching strategy improvements
- UI interaction polish

### Security
- XSS vulnerability fixes
- CSRF protection enhancements

## [1.0.0] - 2024-11-15

### Added
- First official release
- Complete email send/receive
- User registration and login
- Folder management
- Email search
- Attachment upload/download
- Dark/light theme
- Real-time push notifications

### Known Issues
- Large attachment uploads may timeout
- Search only supports basic queries

## [0.9.0-beta] - 2024-10-20

### Added
- Beta release
- Basic email functionality
- User system framework
