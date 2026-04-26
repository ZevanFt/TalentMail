# Changelog

All notable changes to this project will be documented in this file.

Based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
adhering to [Semantic Versioning](https://semver.org/).

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
